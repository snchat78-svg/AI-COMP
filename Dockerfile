FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY database/migrations ./database/migrations

RUN python -m pip install --no-cache-dir ".[postgres,server]"

# The factory validates required configuration before the service accepts requests.
CMD ["sh", "-c", "exec uvicorn ai_comp.api.runtime:create_runtime_app --factory --host 0.0.0.0 --port ${PORT:-8080}"]
