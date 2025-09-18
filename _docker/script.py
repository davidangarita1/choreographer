from __future__ import annotations

import asyncio
import re
import subprocess
import sys

# ruff: noqa: T201 allow print in CLI


async def run(
    commands: list[str], *, verbose: bool = False
) -> tuple[bytes, bytes, int | None]:
    if verbose:
        print(f"- {' '.join(commands)}")
    try:
        p = await asyncio.create_subprocess_exec(
            *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
    else:
        return (*(await p.communicate()), p.returncode)


async def download_browser() -> str:
    out, err, _ = await run(
        ["uv", "run", "choreo_get_chrome"],
        verbose=True,
    )
    certif_reg = re.compile("certificate verify failed")
    if re.search(certif_reg, err.decode()):
        print(
            "Please install the system's CA certificates",
            file=sys.stderr,
        )
    return out.decode().strip()


async def get_browser_version(path: str) -> str:
    try:
        out, err, _ = await run([path, "--version"], verbose=True)
        if err:
            return ""
        return out.decode()
    except FileNotFoundError as e:
        print(f"Message: {e}")
        return ""


async def main() -> None:
    try:
        chrome_path = await download_browser()
        if not chrome_path:
            return

        chrome_ver = await get_browser_version(chrome_path)
        if not chrome_ver:
            return
    except (PermissionError, Exception) as e:
        print(f"ERROR: {e}")


asyncio.run(main())
