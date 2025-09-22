# /// script
# requires-python = ">=3.8"
# dependencies = ["pyelftools"]
# ///

from __future__ import annotations

import asyncio
import pathlib
import platform
import re
import subprocess
import sys

from elftools.elf.elffile import ELFFile

# ruff: noqa: T201 allow print in CLI


class IncompatibleLibrariesError(OSError):
    pass


class DependencyNotFoundError(FileNotFoundError):
    def __init__(
        self,
        dependencies: list[str],
    ) -> None:
        super().__init__()

        self.dependencies = dependencies

    def __str__(self):
        return f"\n{'\n'.join(f'{dep}' for dep in self.dependencies)}"


async def run(
    commands: list[str], *, verbose: bool = False
) -> tuple[bytes, bytes, int | None]:
    if verbose:
        print(f"{' '.join(commands)}")
    try:
        p = await asyncio.create_subprocess_exec(
            *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
    else:
        return (*(await p.communicate()), p.returncode)


def get_os_libc() -> str:
    name, _ = platform.libc_ver()
    if name == "glibc":
        return name
    elif name in ("libc", "musl"):
        return "musl"
    else:
        return ""


def get_file_libc(file_path: str) -> str:
    path = pathlib.Path(file_path)
    f = path.open("rb")
    elffile = ELFFile(f)
    interp = ""
    for s in elffile.iter_segments():
        if s.header.p_type == "PT_INTERP":
            interp = s.data().decode().strip()
            break

    if "ld-musl" in interp:
        return "musl"
    elif "ld-linux" in interp:
        return "glibc"
    else:
        return ""


def get_libc_info(chrome_path: str) -> str:
    os_libc = get_os_libc()
    chrome_libc = get_file_libc(chrome_path)
    if os_libc == chrome_libc:
        return os_libc
    else:
        raise IncompatibleLibrariesError(
            f"Libc mismatch: system uses '{os_libc}', "
            f"Chrome binary uses '{chrome_libc}'."
        )


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


async def ldd_browser(path: str) -> None:
    _, err, _ = await run(["ldd", "--version"])
    if err:
        print(err.decode())
        return
    info, _, _ = await run(["ldd", path], verbose=True)
    if missing_libs := re.findall(
        r"^\s*(lib[\w\-\.]+\.so(?:\.\d+)?) => not found$",
        info.decode(),
        re.MULTILINE,
    ):
        raise DependencyNotFoundError(missing_libs)


async def main() -> None:
    try:
        chrome_path = await download_browser()
        if not chrome_path:
            return
        libc = get_libc_info(chrome_path)
        if libc:
            await ldd_browser(chrome_path)

        chrome_ver = await get_browser_version(chrome_path)
        if not chrome_ver:
            return

        print(chrome_ver)
    except (
        PermissionError,
        DependencyNotFoundError,
        IncompatibleLibrariesError,
        Exception,
    ) as e:
        print(f"{type(e).__name__}:\n{e}")


asyncio.run(main())
