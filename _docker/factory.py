"""Create, build and run docker containers with test commands."""

from __future__ import annotations

import sys
from typing import TypedDict

import docker
from docker.errors import DockerException

# ruff: noqa: T201 allow print in CLI


class DockerConfig(TypedDict):
    """Type a docker config."""

    name: str
    os_name: str
    commands: list[str]


try:
    client = docker.from_env()
    client.ping()
except DockerException:
    print("Docker is not running. Please start the Docker daemon and try again.")
    sys.exit(1)
