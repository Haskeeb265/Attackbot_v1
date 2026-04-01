FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
# Install dependencies first (cached layer)
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

# Copy shared library
COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py

# Copy service code
COPY backend/services/scraper /app/backend/services/scraper

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "backend.services.scraper.main:app", "--host", "0.0.0.0", "--port", "8001"]