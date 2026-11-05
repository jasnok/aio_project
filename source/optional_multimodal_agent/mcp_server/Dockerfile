FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY mcp_server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY mcp_server /app/mcp_server
RUN useradd --create-home appuser && mkdir -p /app/storage && chown -R appuser:appuser /app

USER appuser
EXPOSE 8020

CMD ["python", "-m", "mcp_server.main"]
