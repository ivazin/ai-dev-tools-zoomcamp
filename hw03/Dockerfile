# Use official Astral uv image to copy the uv binary
FROM ghcr.io/astral-sh/uv:latest AS uv

# Use official lightweight Python base image
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Copy uv binary from uv image
COPY --from=uv /uv /uvx /bin/

# Set environment variables for Python and uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code
COPY . .

# Install project into virtual environment
RUN uv sync --frozen --no-dev

# Place virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose FastAPI port
EXPOSE 8000

# Run uvicorn binding to 0.0.0.0
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
