from tests.e2e.url_utils import rewrite_minio_presigned_url_for_host


def test_rewrite_minio_presigned_url_when_host_port_is_configured() -> None:
    url = "http://minio:9000/reports/test.docx?X-Amz-Expires=3600"
    rewritten, changed, reason = rewrite_minio_presigned_url_for_host(url, "9000")

    assert rewritten == "http://localhost:9000/reports/test.docx?X-Amz-Expires=3600"
    assert changed is True
    assert reason == "rewritten_to_localhost"


def test_does_not_rewrite_when_host_port_is_missing() -> None:
    url = "http://minio:9000/reports/test.docx?X-Amz-Expires=3600"
    rewritten, changed, reason = rewrite_minio_presigned_url_for_host(url, "")

    assert rewritten == url
    assert changed is False
    assert reason == "minio_host_port_not_configured"


def test_does_not_rewrite_non_minio_hostname() -> None:
    url = "http://localhost:9000/reports/test.docx?X-Amz-Expires=3600"
    rewritten, changed, reason = rewrite_minio_presigned_url_for_host(url, "9000")

    assert rewritten == url
    assert changed is False
    assert reason == "hostname_not_minio"


def test_does_not_rewrite_when_host_port_is_invalid() -> None:
    url = "http://minio:9000/reports/test.docx?X-Amz-Expires=3600"
    rewritten, changed, reason = rewrite_minio_presigned_url_for_host(url, "abc")

    assert rewritten == url
    assert changed is False
    assert reason == "invalid_minio_host_port"
