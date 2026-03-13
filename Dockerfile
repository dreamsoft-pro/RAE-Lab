FROM python:3.10-slim

WORKDIR /app

RUN pip install fastapi uvicorn mcp sse-starlette requests pydantic psutil

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "metrics_aggregator.py"]
