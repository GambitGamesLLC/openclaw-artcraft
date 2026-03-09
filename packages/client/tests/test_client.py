#!/usr/bin/env python3
"""Tests for the ArtCraft python client.

These are intentionally *unit-ish* tests and do not require a real ArtCraft
installation. We generate a tiny fake `artcraft-cli.sh` and point the client at
it so the suite is stable in CI and on dev machines.

Run with:
    python -m pytest -q
"""

from __future__ import annotations

from pathlib import Path

import pytest

from artcraft_client import ArtCraftClient
from artcraft_client.exceptions import CommandNotFoundError


@pytest.fixture
def fake_cli(tmp_path: Path) -> Path:
    """Create a fake artcraft-cli.sh that returns deterministic JSON."""
    cli_path = tmp_path / "artcraft-cli.sh"
    cli_path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-}"

case "$cmd" in
  generate:text-to-image|generate:image-to-video|generate:edit-image)
    echo '{"status":"simulated"}'
    ;;
  queue:list)
    # simulated means the client should treat this as empty queue
    echo '{"status":"simulated"}'
    ;;
  queue:dismiss|queue:purge|download)
    # success with no output
    exit 0
    ;;
  *)
    echo '{"status":"simulated"}'
    ;;
esac
""",
        encoding="utf-8",
    )
    cli_path.chmod(0o755)
    return cli_path


@pytest.fixture
def client(fake_cli: Path) -> ArtCraftClient:
    return ArtCraftClient(cli_path=str(fake_cli))


class TestClientInitialization:
    def test_client_initialization_with_default_path_raises_when_missing(self, tmp_path: Path, monkeypatch):
        # This should not depend on a user's real ~/.openclaw workspace.
        monkeypatch.setenv("HOME", str(tmp_path))
        with pytest.raises(CommandNotFoundError):
            ArtCraftClient()

    def test_client_initialization_with_custom_path(self, client: ArtCraftClient):
        assert client.cli_path.exists()


class TestGenerateTextToImage:
    def test_generate_text_to_image_simulation(self, client: ArtCraftClient):
        result = client.generate_text_to_image(prompt="test prompt", wait=False)
        assert result.task_id.startswith("simulated-")
        assert result.status == "submitted"
        assert result.input_prompt == "test prompt"

    def test_generate_with_provider(self, client: ArtCraftClient):
        result = client.generate_text_to_image(
            prompt="test with provider",
            provider="openai",
            wait=False,
        )
        assert result.task_id.startswith("simulated-")


class TestTaskQueue:
    def test_get_task_queue(self, client: ArtCraftClient):
        tasks = client.get_task_queue()
        assert isinstance(tasks, list)

    def test_get_task_status_not_found(self, client: ArtCraftClient):
        task = client.get_task_status("non-existent")
        assert task.status == "not_found"


class TestWaitForCompletion:
    def test_wait_timeout(self, client: ArtCraftClient):
        with pytest.raises(Exception):
            client.wait_for_completion("non-existent-task", timeout=2, poll_interval=0.2)


class TestQueueManagement:
    def test_dismiss_task(self, client: ArtCraftClient):
        assert isinstance(client.dismiss_task("non-existent"), bool)

    def test_purge_queue(self, client: ArtCraftClient):
        assert isinstance(client.purge_queue(), bool)
