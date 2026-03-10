FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/api_gateway /app/backend/services/api_gateway

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]