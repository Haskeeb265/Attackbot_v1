# backend/shared/storage.py
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from backend.shared.exceptions import StorageError
from backend.shared.logging import get_logger

log = get_logger(__name__)

_client: Minio | None = None


def init_storage(
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool = False,
) -> None:
    """
    Initialize the MinIO client. Call once at service startup.
    """
    global _client
    _client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    log.info("minio_connected", endpoint=endpoint, secure=secure)


def _get_client() -> Minio:
    if _client is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _client


def get_presigned_url(bucket: str, object_name: str, expires_hours: int = 1) -> str:
    """
    Generate a pre-signed GET URL for a MinIO object.
    All report and evidence downloads must use this — never expose direct bucket access.
    """
    try:
        return _get_client().presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(hours=expires_hours),
        )
    except S3Error as e:
        raise StorageError(f"Failed to generate presigned URL for {bucket}/{object_name}") from e


def upload_bytes(bucket: str, object_name: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes to MinIO."""
    try:
        _get_client().put_object(
            bucket,
            object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        log.info("storage_upload_success", bucket=bucket, object_name=object_name)
    except S3Error as e:
        raise StorageError(f"Upload failed for {bucket}/{object_name}") from e


def download_bytes(bucket: str, object_name: str) -> bytes:
    """Download an object from MinIO as raw bytes."""
    try:
        response = _get_client().get_object(bucket, object_name)
        return response.read()
    except S3Error as e:
        raise StorageError(f"Download failed for {bucket}/{object_name}") from e


def check_storage_health() -> bool:
    """Ping MinIO by listing buckets. Used by /health endpoints."""
    try:
        list(_get_client().list_buckets())
        return True
    except Exception as e:
        log.warning("minio_health_check_failed", error=str(e))
        return False