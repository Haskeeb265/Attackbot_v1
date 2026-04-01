FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /app/requirements/base.txt
COPY backend/services/reporter/requirements.txt /app/backend/services/reporter/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/services/reporter/requirements.txt

# Mandatory package roots for backend.* imports
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py

COPY backend/shared /app/backend/shared
COPY backend/services/reporter /app/backend/services/reporter

RUN mkdir -p /tmp/attackbot-reports

EXPOSE 8003

CMD ["uvicorn", "backend.services.reporter.main:app", "--host", "0.0.0.0", "--port", "8003"]
