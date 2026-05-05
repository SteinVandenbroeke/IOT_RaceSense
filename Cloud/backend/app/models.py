from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Column
from sqlalchemy.dialects.postgresql import JSONB


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="Active", max_length=20)
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetryRaw(SQLModel, table=True):
    __tablename__ = "telemetry_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="sessions.id")
    car_id: Optional[int] = Field(default=None)

    # Extracted Data
    accel_roll: Optional[float] = Field(default=None)
    accel_pitch: Optional[float] = Field(default=None)
    accel_g_force: Optional[float] = Field(default=None)
    accel_x: Optional[float] = Field(default=None)
    accel_y: Optional[float] = Field(default=None)
    accel_z: Optional[float] = Field(default=None)

    temp_surface: Optional[float] = Field(default=None)
    temp_humidity: Optional[float] = Field(default=None)

    pressure: Optional[float] = Field(default=None)
    altitude: Optional[float] = Field(default=None)

    speed: Optional[float] = Field(default=None)
    rpm: Optional[int] = Field(default=None)

    # JSONB explicitly defined for PostgreSQL
    payload: dict = Field(default={}, sa_column=Column(JSONB))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))