FROM python:3.14-rc-slim
WORKDIR /app
COPY packages/rae-lab .
COPY packages/rae-core /app/packages/rae-core
RUN pip install fastapi uvicorn pydantic pyyaml &&     pip install -e packages/rae-core
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "rae_lab.main:app", "--host", "0.0.0.0", "--port", "8011"]
