# Security Gate: Base image minimized
FROM python:3.12-alpine

WORKDIR /app

# Security Gate: Non-root user setup
RUN addgroup -S appuser && adduser -S appuser -G appuser

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Security Gate: Run as non-root
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
