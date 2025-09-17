"""Create, build and run docker containers with test commands."""

import sys

import docker
from docker.errors import DockerException

# ruff: noqa: T201 allow print in CLI

try:
    client = docker.from_env()
    client.ping()
except DockerException:
    print("Docker is not running. Please start the Docker daemon and try again.")
    sys.exit(1)
