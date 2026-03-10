FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/scenario_runner /app/backend/services/scenario_runner

ENV PYTHONPATH=/app

CMD ["celery", "-A", "backend.services.scenario_runner.worker", "worker", "-Q", "scenario.jobs", "-c", "1", "--loglevel=info"]