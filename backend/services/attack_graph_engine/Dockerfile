FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/attack_graph_engine /app/backend/services/attack_graph_engine

ENV PYTHONPATH=/app

EXPOSE 8006

CMD ["uvicorn", "backend.services.attack_graph_engine.main:app", "--host", "0.0.0.0", "--port", "8006"]