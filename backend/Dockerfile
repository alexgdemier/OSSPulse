FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system osspulse \
    && useradd --system --gid osspulse --home-dir /app osspulse

COPY pyproject.toml README.md LICENSE ./
COPY backend ./backend
COPY alembic.ini ./

RUN python -m pip install --no-cache-dir --no-compile .

USER osspulse
EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/api/v1/ready', timeout=3)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
