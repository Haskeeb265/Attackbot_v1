FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/browser_worker /app/backend/services/browser_worker

ENV PYTHONPATH=/app

CMD ["celery", "-A", "backend.services.browser_worker.worker", "worker", "-Q", "browser.jobs", "-c", "2", "--loglevel=info"]