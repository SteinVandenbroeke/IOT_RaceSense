import os
import asyncpg
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

DB_URL = os.getenv("DATABASE_URL")


async def init_tables(pool):
    async with pool.acquire() as connection:
        await connection.execute("""
                                 CREATE TABLE IF NOT EXISTS sessions
                                 (
                                     id            SERIAL PRIMARY KEY,
                                     status        VARCHAR(20) DEFAULT 'Active',
                                     start_time    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
                                     last_activity TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
                                 );

                                 CREATE TABLE IF NOT EXISTS telemetry_raw
                                 (
                                     id            SERIAL PRIMARY KEY,
                                     session_id    INTEGER REFERENCES sessions (id),
                                     car_id        INTEGER,
                                     accel_roll    REAL,
                                     accel_pitch   REAL,
                                     accel_g_force REAL,
                                     accel_x       REAL,
                                     accel_y       REAL,
                                     accel_z       REAL,
                                     temp_surface  REAL,
                                     temp_humidity REAL,
                                     pressure      REAL,
                                     altitude      REAL,
                                     speed         REAL,
                                     rpm           INTEGER,
                                     payload       JSONB,
                                     received_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 );
                                 """)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Attempting to connect to PostgreSQL...")
    for _ in range(5):
        try:
            app.state.db_pool = await asyncpg.create_pool(DB_URL)
            print("Successfully connected to the database!")
            await init_tables(app.state.db_pool)
            break
        except Exception as e:
            print(f"Database not ready yet, retrying in 2 seconds... ({e})")
            await asyncio.sleep(2)
    else:
        raise Exception("Failed to connect to the database after 5 attempts.")

    yield
    await app.state.db_pool.close()