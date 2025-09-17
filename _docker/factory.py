"""Create, build and run docker containers with test commands."""

from __future__ import annotations

import sys
from typing import TypedDict

import docker
from docker.errors import DockerException

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
