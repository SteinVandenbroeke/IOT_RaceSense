import json
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

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
    pool = websocket.app.state.db_pool

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

            clean_data_text = json.dumps(payload)

            async with pool.acquire() as connection:
                await connection.execute("""
                                         UPDATE sessions
                                         SET status = 'Completed'
                                         WHERE status = 'Active'
                                           AND last_activity < NOW() - INTERVAL '1 minute'
                                         """)

                session_row = await connection.fetchrow("SELECT id FROM sessions WHERE status = 'Active' LIMIT 1")

                if not session_row:
                    session_id = await connection.fetchval(
                        "INSERT INTO sessions (status) VALUES ('Active') RETURNING id")
                    print(f"New Session Started: {session_id}")
                else:
                    session_id = session_row['id']
                    await connection.execute("UPDATE sessions SET last_activity = NOW() WHERE id = $1", session_id)

                accel = sensor_readings.get("Accelerometer", {})
                temp_humid = sensor_readings.get("TempAndHumidity", {})
                press_alt = sensor_readings.get("PressureAndAltitude", {})
                accel_array = accel.get("acceleration", [None, None, None])

                await connection.execute("""
                                         INSERT INTO telemetry_raw (session_id, car_id,
                                                                    accel_roll, accel_pitch, accel_g_force,
                                                                    accel_x, accel_y, accel_z,
                                                                    temp_surface, temp_humidity,
                                                                    pressure, altitude,
                                                                    speed, rpm,
                                                                    payload)
                                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                                                 $15::jsonb)
                                         """,
                                         session_id, car_id,
                                         accel.get("roll"), accel.get("pitch"), accel.get("g_force"),
                                         accel_array[0] if len(accel_array) > 0 else None,
                                         accel_array[1] if len(accel_array) > 1 else None,
                                         accel_array[2] if len(accel_array) > 2 else None,
                                         temp_humid.get("temp"), temp_humid.get("humidity"),
                                         press_alt.get("pressure"), press_alt.get("altitude"),
                                         sensor_readings.get("Speed"), sensor_readings.get("RPM"),
                                         clean_data_text
                                         )

            await manager.broadcast_to_ui(clean_data_text)

    except WebSocketDisconnect:
        print("Coral Dev Board disconnected.")
    except Exception as e:
        print(f"Error processing message: {e}")


@router.get("/api/sessions")
async def get_all_sessions(request: Request):
    pool = request.app.state.db_pool
    async with pool.acquire() as connection:
        query = """
                SELECT s.id, \
                       s.status, \
                       TO_CHAR(s.start_time, 'Mon DD, YYYY HH24:MI') as date, \
                       'Spa-Francorchamps'                           as track, \
                       'Race'                                        as type, \
                       (SELECT COALESCE(
                                       json_agg(
                                               json_build_object(
                                                       'id', car_id,
                                                       'topSpeed', top_speed,
                                                       'laps', packet_count,
                                                       'bestLap', 'N/A'
                                               )
                                       ),
                                       '[]'::json
                               )
                        FROM (SELECT car_id,
                                     COALESCE(ROUND(MAX(speed)::numeric, 1), 0) as top_speed,
                                     COUNT(id)                                  as packet_count \
                              FROM telemetry_raw \
                              WHERE session_id = s.id \
                              GROUP BY car_id) sub)                  as cars
                FROM sessions s
                ORDER BY s.id DESC \
                """

        records = await connection.fetch(query)

        results = []
        for record in records:
            row = dict(record)
            if isinstance(row['cars'], str):
                row['cars'] = json.loads(row['cars'])
            results.append(row)

        return results