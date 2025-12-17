# Security Gate: Base image minimized (Slim preferred for ML compatibility over Alpine)
FROM python:3.12-slim

WORKDIR /app

# Install build dependencies for ML packages (gcc, g++, headers)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Security Gate: Non-root user setup
RUN groupadd -r appuser && useradd -m -r -g appuser appuser

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .
# Only COPY alembic.ini if it exists, otherwise ignore or ensure project structure
# Looking at file list earlier, alembic folder exists.

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Ensure cache directory exists and is writable
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser

# Security Gate: Run as non-root
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
