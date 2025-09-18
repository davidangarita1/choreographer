"""Create, build and run docker containers with test commands."""

from __future__ import annotations

import pathlib
import sys
import time
from typing import TypedDict

import docker
from docker.errors import DockerException, ImageNotFound

# ruff: noqa: T201 allow print in CLI


try:
    client = docker.from_env()
    client.ping()
except DockerException:
    print("Docker is not running. Please start the Docker daemon and try again.")
    sys.exit(1)


class DockerConfig(TypedDict):
    """Type a docker config."""

    name: str
    os_name: str
    commands: list[str]


cmd_certif = "apt-get update && apt-get install -y ca-certificates"
cfg_list: list[DockerConfig] = [
    {"name": "py312_trixie", "os_name": "python:3.12-slim-trixie", "commands": []},
    {"name": "py311_slim", "os_name": "python:3.11-slim", "commands": []},
    {"name": "py310_slim", "os_name": "python:3.10-slim", "commands": []},
    {
        "name": "debian_bookworm",
        "os_name": "debian:bookworm-slim",
        "commands": [cmd_certif],
    },
    {
        "name": "debian_bullseye",
        "os_name": "debian:bullseye-slim",
        "commands": [cmd_certif],
    },
    {"name": "ubuntu_latest", "os_name": "ubuntu:latest", "commands": [cmd_certif]},
    {"name": "ubuntu_20", "os_name": "ubuntu:20.04", "commands": [cmd_certif]},
    {"name": "fedora_latest", "os_name": "fedora:latest", "commands": []},
]


def _generate_file(df_name: str, os_name: str, commands: list[str]) -> None:
    has_py = pathlib.Path("pyproject.toml").exists()
    has_lock = pathlib.Path("uv.lock").exists()
    deps = []
    if has_py:
        deps.append("COPY pyproject.toml /app/pyproject.toml")
    if has_lock:
        deps.append("COPY uv.lock /app/uv.lock")
    content = f"""FROM {os_name}
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
{"\n".join(deps) if deps else ""}
ENV UV_LINK_MODE=copy
ADD . /app
RUN uv sync --locked
{"\n".join(f"RUN {cmd}" for cmd in commands) if commands else ""}
"""
    pathlib.Path(df_name).write_text(content)


def _build(image_tag: str, df_name: str):
    start_time = time.time()
    client.images.build(
        path=".",
        dockerfile=df_name,
        tag=image_tag,
        rm=True,
        forcerm=True,
    )
    secs = time.time() - start_time
    size = client.images.get(image_tag).attrs["Size"] / (1024 * 1024)
    print(f"[{image_tag}] \033[94m{size:.1f} MB\033[0m | \033[93m{secs:.1f}s\033[0m")


for cfg in cfg_list:
    name = cfg["name"]
    os_name = cfg["os_name"]
    commands = cfg["commands"]
    df_name = f"Dockerfile.{name}"

    try:
        _generate_file(df_name, os_name, commands)
        _build(name, df_name)
    except ImageNotFound:
        pathlib.Path(df_name).unlink(missing_ok=True)
    finally:
        pathlib.Path(df_name).unlink(missing_ok=True)
