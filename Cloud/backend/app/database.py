import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# We MUST import the models here so SQLModel knows they exist before creating tables
from app.models import Session, TelemetryRaw

# SQLAlchemy needs a specific prefix to know we are using the asyncpg driver
DB_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

# Create the async engine
engine = create_async_engine(DB_URL, echo=False)

async def init_db():
    async with engine.begin() as conn:
        # This tells SQLModel to build the tables based on our Python classes
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing SQLModel Database...")
    await init_db()
    print("Database tables verified!")
    yield
    await engine.dispose()

# This is a FastAPI dependency we will use to inject the DB session into our routes
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session