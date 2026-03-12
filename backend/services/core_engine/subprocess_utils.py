import asyncio
import json
import os
import tempfile
from typing import AsyncIterator

from backend.shared.exceptions import ScanTimeoutError, ScanError
from backend.shared.logging import get_logger

logger = get_logger("core_engine.subprocess")


async def run_tool_communicate(
    args: list[str],
    timeout: int,
    label: str,
    success_on_empty: bool = True,
) -> tuple[str, str]:
    """
    Run a subprocess using communicate() — safe for tools with bounded output.
    Use for: nuclei, httpx (fingerprint), dnsx, alterx, waybackurls.

    Returns (stdout_text, stderr_text).
    Raises ScanTimeoutError on timeout, ScanError on non-zero exit > 1.

    Never use this for amass/subfinder — their output can exceed the OS pipe buffer.
    Use run_tool_streaming() for those instead.
    """
    logger.info(f"Running {label}", args=args[0], timeout=timeout)
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise ScanTimeoutError(f"{label} timed out after {timeout}s")

    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")

    # nuclei exits 1 on zero findings — that is not a real error
    if proc.returncode is not None and proc.returncode > 1:
        raise ScanError(
            f"{label} exited with code {proc.returncode}. "
            f"stderr: {stderr_text[:500]}"
        )
    return stdout_text, stderr_text


async def run_tool_streaming(
    args: list[str],
    timeout: int,
    label: str,
) -> list[str]:
    """
    Run a subprocess with streaming readline — safe for tools with large output.
    Use for: subfinder (thousands of subdomains).

    Returns list of non-empty decoded lines.
    """
    logger.info(f"Running {label} (streaming)", args=args[0], timeout=timeout)
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    lines: list[str] = []

    async def _read() -> None:
        assert proc.stdout is not None
        async for raw_line in proc.stdout:
            decoded = raw_line.decode(errors="replace").strip()
            if decoded:
                lines.append(decoded)

    try:
        await asyncio.wait_for(
            asyncio.gather(_read(), proc.wait()),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        logger.warning(f"{label} timed out — returning partial results",
                       lines_so_far=len(lines))
    return lines


async def run_tool_with_target_file(
    args_template: list[str],
    targets: list[str],
    timeout: int,
    label: str,
    target_flag: str = "-l",
) -> tuple[str, str]:
    """
    Write targets to a temp file and pass via flag to the tool.
    Use for: nuclei -l, httpx -l, dnsx -l.

    Temp file is always cleaned up — even on exception.
    args_template should use TARGET_FILE as a placeholder for the targets path.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as tf:
        tf.write("\n".join(targets))
        targets_path = tf.name

    # Replace TARGET_FILE sentinel with actual path
    args = [targets_path if a == "TARGET_FILE" else a for a in args_template]

    try:
        return await run_tool_communicate(args, timeout=timeout, label=label)
    finally:
        if os.path.exists(targets_path):
            os.unlink(targets_path)


def parse_jsonl(text: str) -> list[dict]:
    """
    Parse newline-delimited JSON output from tools like nuclei, httpx.
    Silently skips lines that are not valid JSON objects.
    nuclei -silent outputs a mix of status lines and JSON — filter by '{'.
    """
    results = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                results.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return results