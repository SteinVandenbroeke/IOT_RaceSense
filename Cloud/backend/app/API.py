import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func

# Import our database engine, session dependency, and our new Data Models
from app.database import engine, get_session
from app.models import Session, TelemetryRaw

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_ui_connections: list[WebSocket] = []

    async def connect_ui(self, websocket: WebSocket):
        await websocket.accept()
        self.active_ui_connections.append(websocket)

    def disconnect_ui(self, websocket: WebSocket):
        if websocket in self.active_ui_connections:
            self.active_ui_connections.remove(websocket)

    async def broadcast_to_ui(self, message: str):
        for connection in self.active_ui_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


def pycom_rtc_to_iso(rtc_array):
    if isinstance(rtc_array, list) and len(rtc_array) >= 7:
        try:
            dt = datetime(
                year=rtc_array[0], month=rtc_array[1], day=rtc_array[2],
                hour=rtc_array[3], minute=rtc_array[4], second=rtc_array[5],
                microsecond=rtc_array[6], tzinfo=timezone.utc
            )
            return dt.isoformat()
        except Exception:
            pass
    return rtc_array


@router.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    await manager.connect_ui(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_ui(websocket)


@router.websocket("/ws/coral")
async def websocket_coral_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data_text = await websocket.receive_text()
            payload = json.loads(data_text)
            car_id = 0

            if "processed_value" in payload:
                sensor_readings = payload["processed_value"]
                car_id = sensor_readings.get("CarId", 0)

                if "time" in sensor_readings:
                    sensor_readings["time"] = pycom_rtc_to_iso(sensor_readings["time"])
                for sensor in ["TempAndHumidity", "Accelerometer", "PressureAndAltitude"]:
                    if sensor in sensor_readings and "timestamp" in sensor_readings[sensor]:
                        sensor_readings[sensor]["timestamp"] = pycom_rtc_to_iso(sensor_readings[sensor]["timestamp"])

            # Extract variables safely
            accel = sensor_readings.get("Accelerometer", {})
            temp_humid = sensor_readings.get("TempAndHumidity", {})
            press_alt = sensor_readings.get("PressureAndAltitude", {})
            accel_array = accel.get("acceleration", [None, None, None])

            # --- ORM DATABASE TRANSACTIONS ---
            # WebSockets don't use standard FastAPI 'Depends', so we open a session manually
            async with AsyncSession(engine) as db_session:

                # 1. Update stale sessions
                one_min_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
                await db_session.exec(
                    update(Session)
                    .where(Session.status == "Active")
                    .where(Session.last_activity < one_min_ago)
                    .values(status="Completed")
                )

                # 2. Find or Create Active Session
                result = await db_session.exec(select(Session).where(Session.status == "Active"))
                active_session = result.first()

                if not active_session:
                    active_session = Session(status="Active")
                    db_session.add(active_session)
                    await db_session.commit()
                    await db_session.refresh(active_session)
                    print(f"New Session Started: {active_session.id}")
                else:
                    active_session.last_activity = datetime.now(timezone.utc)
                    db_session.add(active_session)

                # 3. Insert Telemetry Object
                new_telemetry = TelemetryRaw(
                    session_id=active_session.id,
                    car_id=car_id,
                    accel_roll=accel.get("roll"),
                    accel_pitch=accel.get("pitch"),
                    accel_g_force=accel.get("g_force"),
                    accel_x=accel_array[0] if len(accel_array) > 0 else None,
                    accel_y=accel_array[1] if len(accel_array) > 1 else None,
                    accel_z=accel_array[2] if len(accel_array) > 2 else None,
                    temp_surface=temp_humid.get("temp"),
                    temp_humidity=temp_humid.get("humidity"),
                    pressure=press_alt.get("pressure"),
                    altitude=press_alt.get("altitude"),
                    speed=sensor_readings.get("Speed"),
                    rpm=sensor_readings.get("RPM"),
                    payload=payload  # Python Dict goes directly into the JSONB column!
                )
                db_session.add(new_telemetry)
                await db_session.commit()

            # --- BROADCAST ---
            await manager.broadcast_to_ui(json.dumps(payload))

    except WebSocketDisconnect:
        print("Coral Dev Board disconnected.")
    except Exception as e:
        print(f"Error processing message: {e}")


@router.get("/api/sessions")
async def get_all_sessions(db_session: AsyncSession = Depends(get_session)):
    """
    Fetches all sessions and dynamically aggregates car telemetry statistics!
    """
    # 1. Fetch all sessions from the database
    sessions_result = await db_session.exec(select(Session).order_by(Session.id.desc()))
    db_sessions = sessions_result.all()

    # 2. Ask the database to efficiently calculate Top Speed and Packet Count per car/session
    stats_stmt = (
        select(
            TelemetryRaw.session_id,
            TelemetryRaw.car_id,
            func.max(TelemetryRaw.speed).label("top_speed"),
            func.count(TelemetryRaw.id).label("packet_count")
        )
        .group_by(TelemetryRaw.session_id, TelemetryRaw.car_id)
    )
    stats_result = await db_session.exec(stats_stmt)
    car_stats = stats_result.all()  # Returns a list of tuples: (session_id, car_id, top_speed, packet_count)

    # 3. Stitch it together into a perfect JSON tree using Python!
    results = []
    for s in db_sessions:
        # Find all car stats that belong to this specific session
        session_cars = []
        for stat in car_stats:
            if stat.session_id == s.id and stat.car_id is not None:
                session_cars.append({
                    "id": stat.car_id,
                    "topSpeed": round(stat.top_speed, 1) if stat.top_speed else 0,
                    "laps": stat.packet_count,
                    "bestLap": "N/A"
                })

        results.append({
            "id": s.id,
            "status": s.status,
            # Format the datetime cleanly for the UI
            "date": s.start_time.strftime("%b %d, %Y %H:%M"),
            "track": "Spa-Francorchamps",
            "type": "Race",
            "cars": session_cars
        })

    return results


@router.get("/api/analytics/{session_id}/{car_id}")
async def get_analytics_data(session_id: int, car_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Fetches raw telemetry for a specific car and session, formatted for ECharts.
    """
    # Fetch all telemetry packets, ordered by time
    stmt = (
        select(TelemetryRaw)
        .where(TelemetryRaw.session_id == session_id)
        .where(TelemetryRaw.car_id == car_id)
        .order_by(TelemetryRaw.id.asc())
    )
    result = await db_session.exec(stmt)
    telemetry = result.all()

    # Prepare our data arrays
    # Prepare our data arrays
    data = {
        "timestamps": [],
        "traction_circle": [],
        "roll": [],
        "pitch": [],
        "temp": [],
        "pressure": [],
        "vertical_g": []
    }

    if not telemetry:
        return data

    # Use the first packet as "Time 0.0s"
    start_time = telemetry[0].received_at

    for t in telemetry:
        relative_time = (t.received_at - start_time).total_seconds()
        data["timestamps"].append(round(relative_time, 2))

        lat_g = t.accel_y if t.accel_y is not None else 0
        lon_g = t.accel_x if t.accel_x is not None else 0
        data["traction_circle"].append([round(lat_g, 2), round(lon_g, 2)])

        data["roll"].append(round(t.accel_roll, 2) if t.accel_roll else 0)
        data["pitch"].append(round(t.accel_pitch, 2) if t.accel_pitch else 0)

        data["temp"].append(round(t.temp_surface, 1) if t.temp_surface else 0)
        data["pressure"].append(round(t.pressure, 2) if t.pressure else 0)

        data["vertical_g"].append(round(t.accel_z, 2) if t.accel_z else 0)

    return data