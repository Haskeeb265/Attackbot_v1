from __future__ import annotations

from urllib.parse import urlparse


def rewrite_minio_presigned_url_for_host(
    download_url: str,
    minio_host_port: str | None,
) -> tuple[str, bool, str]:
    parsed = urlparse(download_url)
    if not (minio_host_port or "").strip():
        return download_url, False, "minio_host_port_not_configured"
    if parsed.hostname != "minio":
        return download_url, False, "hostname_not_minio"

    port = str(minio_host_port).strip()
    if ":" in port:
        port = port.rsplit(":", 1)[-1]
    if not port.isdigit():
        return download_url, False, "invalid_minio_host_port"

    rewritten = parsed._replace(netloc=f"localhost:{port}").geturl()
    return rewritten, True, "rewritten_to_localhost"
