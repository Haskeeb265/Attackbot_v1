# backend/shared/models/__init__.py
"""
SQLAlchemy ORM models for AttackBot v1.

This module contains all shared database models used across services.
"""

from backend.shared.models.scans import Scan
from backend.shared.models.idempotency import IdempotencyKey

__all__ = ["Scan", "IdempotencyKey"]
