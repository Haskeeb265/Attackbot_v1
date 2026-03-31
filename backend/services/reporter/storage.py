from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import Tuple

from minio.error import S3Error

from backend.shared import storage as shared_storage
from backend.shared.storage import get_presigned_url, upload_bytes


class ReporterStorage:
    def __init__(self, reports_bucket: str, evidence_bucket: str = "evidence") -> None:
        self._reports_bucket = reports_bucket
        self._evidence_bucket = evidence_bucket

    async def upload_report(self, report_id: str, format_name: str, local_path: str) -> Tuple[str, int]:
        file_size = os.path.getsize(local_path)
        key = f"reports/{report_id}/report.{format_name}"
        content_type = (
            "application/pdf"
            if format_name == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        payload = Path(local_path).read_bytes()
        upload_bytes(self._reports_bucket, key, payload, content_type)
        return key, file_size

    async def get_presigned_download_url(self, storage_path: str, expiry_seconds: int) -> str:
        expires_hours = max(1, math.ceil(expiry_seconds / 3600.0))
        return get_presigned_url(self._reports_bucket, storage_path, expires_hours=expires_hours)

    async def object_exists(self, bucket: str, key: str) -> bool:
        client = shared_storage._get_client()  # noqa: SLF001 - internal helper reused in service layer
        try:
            client.stat_object(bucket, key)
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                return False
            raise

    async def download_temp_object(self, bucket: str, key: str, tmp_dir: str) -> str:
        client = shared_storage._get_client()  # noqa: SLF001 - internal helper reused in service layer
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        output_path = str(Path(tmp_dir) / f"evidence-{uuid.uuid4().hex}{Path(key).suffix}")
        client.fget_object(bucket, key, output_path)
        return output_path

    def get_evidence_bucket(self) -> str:
        return self._evidence_bucket
