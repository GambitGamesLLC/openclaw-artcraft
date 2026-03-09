#!/usr/bin/env python3
"""Tests for the ArtCraft python client.

These tests do not require a real ArtCraft install.

We generate a tiny fake `artcraft` executable and point the client at it so the
suite is stable in CI and on dev machines.

Run with:
    python -m pytest -q
"""

from __future__ import annotations

from pathlib import Path

import pytest

from artcraft_client import ArtCraftClient
from artcraft_client.exceptions import (
    CommandNotFoundError,
    DisallowedCommand,
    InvalidArgs,
    InvokeError,
    Timeout,
    UnsafeGateDisabled,
)


@pytest.fixture
def fake_artcraft(tmp_path: Path) -> Path:
    """Create a fake `artcraft` executable that implements `artcraft invoke ... --json`."""

    exe = tmp_path / "artcraft"

    # A bash script that delegates to python so argument parsing is easy/robust.
    exe.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

python3 - "$@" <<'PY'
import json
import sys
import time

args = sys.argv[1:]

if len(args) < 3 or args[0] != 'invoke':
    print('invalid args', file=sys.stderr)
    sys.exit(2)

command = args[1]
rest = args[2:]

payload = None
unsafe = False
saw_json = False

it = iter(rest)
for tok in it:
    if tok == '--payload':
        try:
            payload = json.loads(next(it))
        except StopIteration:
            print('missing payload', file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError:
            print('payload not json', file=sys.stderr)
            sys.exit(2)
    elif tok == '--unsafe':
        unsafe = True
    elif tok == '--json':
        saw_json = True
    else:
        print(f'unknown arg: {tok}', file=sys.stderr)
        sys.exit(2)

if not saw_json:
    print('missing --json', file=sys.stderr)
    sys.exit(2)

if command == 'ok':
    print(json.dumps({'ok': True, 'command': command, 'payload': payload}))
    sys.exit(0)

if command == 'badjson':
    print('{not-json')
    sys.exit(0)

if command == 'invalidargs':
    print('nope', file=sys.stderr)
    sys.exit(2)

if command == 'unsafe_gate_disabled':
    # Simulate a build where unsafe is not permitted.
    print('Unsafe gate disabled', file=sys.stderr)
    sys.exit(2)

if command == 'disallowed':
    print('disallowed', file=sys.stderr)
    sys.exit(3)

if command == 'runtime':
    print('runtime error', file=sys.stderr)
    sys.exit(4)

if command == 'sleep':
    time.sleep(2)
    print(json.dumps({'ok': True}))
    sys.exit(0)

print('unknown command', file=sys.stderr)
sys.exit(3)
PY
""",
        encoding="utf-8",
    )
    exe.chmod(0o755)
    return exe


@pytest.fixture
def client(fake_artcraft: Path) -> ArtCraftClient:
    return ArtCraftClient(artcraft_bin=str(fake_artcraft))


class TestClientInitialization:
    def test_client_initialization_with_missing_bin_raises(self):
        with pytest.raises(CommandNotFoundError):
            ArtCraftClient(artcraft_bin="/no/such/artcraft")

    def test_client_initialization_with_env_var(self, fake_artcraft: Path, monkeypatch):
        monkeypatch.setenv("ARTCRAFT_BIN", str(fake_artcraft))
        c = ArtCraftClient()
        assert c.artcraft_bin == str(fake_artcraft)


class TestInvoke:
    def test_invoke_success_no_payload(self, client: ArtCraftClient):
        out = client.invoke("ok")
        assert out["ok"] is True
        assert out["payload"] is None

    def test_invoke_success_with_payload(self, client: ArtCraftClient):
        out = client.invoke("ok", payload={"a": 1, "b": "two"})
        assert out["payload"] == {"a": 1, "b": "two"}

    def test_invoke_stdout_must_be_json_object(self, client: ArtCraftClient):
        with pytest.raises(InvokeError) as ei:
            client.invoke("badjson")
        # include a useful snippet in the message
        assert "stdout" in str(ei.value).lower()

    def test_invoke_exit_code_2_invalid_args(self, client: ArtCraftClient):
        with pytest.raises(InvalidArgs):
            client.invoke("invalidargs")

    def test_invoke_exit_code_2_unsafe_gate_disabled(self, client: ArtCraftClient):
        with pytest.raises(UnsafeGateDisabled):
            client.invoke("unsafe_gate_disabled", unsafe=True)

    def test_invoke_exit_code_3_disallowed(self, client: ArtCraftClient):
        with pytest.raises(DisallowedCommand):
            client.invoke("disallowed")

    def test_invoke_exit_code_4_runtime(self, client: ArtCraftClient):
        with pytest.raises(InvokeError):
            client.invoke("runtime")

    def test_timeout(self, client: ArtCraftClient):
        with pytest.raises(Timeout):
            client.invoke("sleep", timeout=0.05)
