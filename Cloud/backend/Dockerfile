# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

# Install the build tools needed for C-extensions (like asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the uv binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

# Copy the dependency management files
COPY pyproject.toml uv.lock ./

# Create the virtual environment and compile dependencies
# We strictly use Python 3.11 to avoid the 3.14 version mismatch
RUN uv sync --frozen --no-install-project --python 3.11

# ==========================================
# STAGE 2: Runner
# ==========================================
FROM python:3.11-slim

WORKDIR /code

# Copy ONLY the compiled virtual environment from the builder stage
# This leaves all the heavy compilers behind!
COPY --from=builder /code/.venv /code/.venv

# Copy your FastAPI application code
COPY ./app /code/app

# Add the compiled virtual environment to the system PATH
ENV PATH="/code/.venv/bin:$PATH"

# Command to run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]