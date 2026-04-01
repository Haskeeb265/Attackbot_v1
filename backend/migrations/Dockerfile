FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

# Copy shared library and migrations
COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/migrations /app/backend/migrations

ENV PYTHONPATH=/app

CMD ["alembic", "--config", "backend/migrations/alembic.ini", "upgrade", "head"]