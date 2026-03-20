import shutil
import subprocess
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StartupCheck:
    name: str
    ok: bool
    detail: str | None = None


REQUIRED_TOOLS = (
    "subfinder",
    "dnsx",
    "httpx",
    "alterx",
    "ffuf",
    "nuclei",
    "waybackurls",
)


def collect_toolchain_checks(
    required_tools: Iterable[str] = REQUIRED_TOOLS,
    nuclei_timeout_seconds: int = 20,
) -> list[StartupCheck]:
    checks: list[StartupCheck] = []
    for tool in required_tools:
        tool_path = shutil.which(tool)
        checks.append(
            StartupCheck(
                name=tool,
                ok=bool(tool_path),
                detail=tool_path or "missing from PATH",
            )
        )

    if shutil.which("nuclei"):
        try:
            proc = subprocess.run(
                ["nuclei", "-tl"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=nuclei_timeout_seconds,
            )
            checks.append(
                StartupCheck(
                    name="nuclei_templates",
                    ok=proc.returncode == 0,
                    detail=None if proc.returncode == 0 else (proc.stderr.strip() or "nuclei template check failed"),
                )
            )
        except Exception as exc:
            checks.append(
                StartupCheck(
                    name="nuclei_templates",
                    ok=False,
                    detail=str(exc),
                )
            )
    else:
        checks.append(
            StartupCheck(
                name="nuclei_templates",
                ok=False,
                detail="nuclei binary missing",
            )
        )

    return checks


def startup_checks_ok(checks: Iterable[StartupCheck]) -> bool:
    return all(check.ok for check in checks)
