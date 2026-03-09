#!/usr/bin/env python3
"""artcraft_client.client

Python wrapper around the shipped ArtCraft CLI contract:

    artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json

This client intentionally stays low-level: it exposes a small set of primitives
that map ArtCraft CLI failures into typed Python exceptions.

Key design points:
- Safety tiering: callers opt into unsafe invocation via `tier="unsafe"`.
- Deterministic error mapping: on non-zero exit codes, we prefer JSON error
  payloads that include `error_details.code`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Literal

from .exceptions import (
    ArtCraftError,
    CommandNotFoundError,
    DisallowedCommand,
    InvalidArgs,
    InvokeError,
    Timeout,
    UnsafeGateDisabled,
)


Tier = Literal["safe", "unsafe"]

_SNIPPET_CHARS = 400


def _snippet(s: Optional[str], limit: int = _SNIPPET_CHARS) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[:limit] + "…"


def _resolve_executable(exe: str) -> str:
    """Resolve an executable path.

    If `exe` looks like a path, return it as-is (expanded). Otherwise resolve it
    via PATH.
    """

    exe = os.path.expanduser(exe)
    if os.path.sep in exe or (os.path.altsep and os.path.altsep in exe):
        return exe

    resolved = shutil.which(exe)
    return resolved or exe


def _try_parse_json(text: Optional[str]) -> Tuple[Optional[Any], Optional[Exception]]:
    """Attempt to parse JSON from a string.

    Returns:
        (parsed, error) where only one is non-None.
    """

    if text is None:
        return None, None
    t = text.strip()
    if not t:
        return None, None
    try:
        return json.loads(t), None
    except Exception as e:  # JSONDecodeError, etc.
        return None, e


def _normalize_error_code(code: str) -> str:
    return code.strip().lower().replace("-", "_")


@dataclass(frozen=True)
class InvokeResult:
    """Returned value for `invoke_raw` (primarily for debugging)."""

    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class AllowedCommands:
    """Parsed response from `artcraft invoke --list-allowed --json`."""

    safe: List[str]
    unsafe: List[str]
    unsafe_gate_enabled: bool


class ArtCraftClient:
    """Client for the `artcraft` CLI."""

    def __init__(self, artcraft_bin: Optional[str] = None):
        """Create a client.

        Resolution order for the executable:
        1) constructor arg `artcraft_bin`
        2) environment variable `ARTCRAFT_BIN`
        3) `artcraft` on PATH
        """

        candidate = artcraft_bin or os.environ.get("ARTCRAFT_BIN") or "artcraft"
        resolved = _resolve_executable(candidate)

        # Validate executable exists.
        if os.path.sep in resolved or (os.path.altsep and os.path.altsep in resolved):
            if not os.path.exists(resolved):
                raise CommandNotFoundError(
                    f"ArtCraft executable not found: {resolved}",
                    command=None,
                    returncode=None,
                    stdout=None,
                    stderr=None,
                )
            if not os.access(resolved, os.X_OK):
                raise CommandNotFoundError(
                    f"ArtCraft executable is not executable: {resolved}",
                    command=None,
                    returncode=None,
                    stdout=None,
                    stderr=None,
                )
        else:
            # If it wasn't a path and which() didn't resolve, we'll find out on
            # the first invocation, but fail early if possible.
            if shutil.which(candidate) is None:
                raise CommandNotFoundError(
                    f"ArtCraft executable not found on PATH: {candidate}",
                    command=None,
                    returncode=None,
                    stdout=None,
                    stderr=None,
                )

        self._artcraft_bin = resolved

    @property
    def artcraft_bin(self) -> str:
        return self._artcraft_bin

    def _run(
        self,
        args: List[str],
        *,
        logical_command: Optional[str],
        timeout: Optional[float],
    ) -> InvokeResult:
        try:
            completed = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise Timeout(
                f"ArtCraft invoke timed out after {timeout}s: {logical_command}",
                command=logical_command,
                returncode=None,
                stdout=(e.stdout if isinstance(e.stdout, str) else None),
                stderr=(e.stderr if isinstance(e.stderr, str) else None),
            )
        except FileNotFoundError:
            raise CommandNotFoundError(
                f"ArtCraft executable not found: {self._artcraft_bin}",
                command=logical_command,
                returncode=None,
                stdout=None,
                stderr=None,
            )
        except OSError as e:
            raise CommandNotFoundError(
                f"Failed to execute ArtCraft binary {self._artcraft_bin}: {e}",
                command=logical_command,
                returncode=None,
                stdout=None,
                stderr=None,
            )

        return InvokeResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    def _raise_for_failure(
        self,
        raw: InvokeResult,
        *,
        command: Optional[str],
    ) -> None:
        """Raise a typed exception for a non-zero CLI exit.

        Preferred signal: JSON error payload with `error_details.code`.
        Fallback: returncode mapping + minimal stderr heuristics.
        """

        msg = (raw.stderr or "").strip() or (raw.stdout or "").strip()
        details = (f"stdout: {_snippet(raw.stdout)}\n" f"stderr: {_snippet(raw.stderr)}").strip()

        parsed_stdout, _ = _try_parse_json(raw.stdout)
        parsed_stderr, _ = _try_parse_json(raw.stderr)

        parsed = parsed_stdout if isinstance(parsed_stdout, dict) else None
        if parsed is None and isinstance(parsed_stderr, dict):
            parsed = parsed_stderr

        error_code: Optional[str] = None
        if parsed is not None:
            ed = parsed.get("error_details")
            if isinstance(ed, dict):
                c = ed.get("code")
                if isinstance(c, str) and c.strip():
                    error_code = _normalize_error_code(c)

        if error_code is not None:
            exc_type = {
                "invalid_args": InvalidArgs,
                "unsafe_gate_disabled": UnsafeGateDisabled,
                "disallowed_command": DisallowedCommand,
                "invoke_error": InvokeError,
            }.get(error_code, InvokeError)

            raise exc_type(
                f"ArtCraft error ({error_code}) for command {command}. {msg}\n{details}",
                command=command,
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        # Fallback (JSON absent or not in expected shape).
        if raw.returncode == 2:
            lowered = (raw.stderr or "").lower()
            if "unsafe" in lowered and ("disabled" in lowered or "gate" in lowered):
                raise UnsafeGateDisabled(
                    f"Unsafe gate disabled for command {command}. {msg}\n{details}",
                    command=command,
                    returncode=raw.returncode,
                    stdout=raw.stdout,
                    stderr=raw.stderr,
                )
            raise InvalidArgs(
                f"Invalid args for command {command}. {msg}\n{details}",
                command=command,
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        if raw.returncode == 3:
            raise DisallowedCommand(
                f"Disallowed/unknown command {command}. {msg}\n{details}",
                command=command,
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        raise InvokeError(
            f"Unexpected ArtCraft exit code {raw.returncode} for command {command}. {msg}\n{details}",
            command=command,
            returncode=raw.returncode,
            stdout=raw.stdout,
            stderr=raw.stderr,
        )

    def invoke_raw(
        self,
        command: str,
        payload: Optional[Dict[str, Any]] = None,
        tier: Tier = "safe",
        timeout: Optional[float] = None,
    ) -> InvokeResult:
        """Invoke a tauri command and return raw stdout/stderr.

        Most callers should use :meth:`invoke` instead.
        """

        if tier not in ("safe", "unsafe"):
            raise ValueError(f"Invalid tier: {tier!r}. Expected 'safe' or 'unsafe'.")

        args = [self._artcraft_bin, "invoke", command]
        if payload is not None:
            args.extend(["--payload", json.dumps(payload)])
        if tier == "unsafe":
            args.append("--unsafe")
        args.append("--json")

        return self._run(args, logical_command=command, timeout=timeout)

    def invoke(
        self,
        command: str,
        payload: Optional[Dict[str, Any]] = None,
        tier: Tier = "safe",
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Invoke a tauri command via the `artcraft` CLI.

        Args:
            command: Tauri command name.
            payload: Optional JSON-serializable dict passed to `--payload`.
            tier: Either "safe" (default) or "unsafe" (adds `--unsafe`).
            timeout: Optional subprocess timeout in seconds.

        Returns:
            Parsed JSON object (from stdout).

        Raises:
            InvalidArgs, UnsafeGateDisabled, DisallowedCommand, InvokeError, Timeout,
            CommandNotFoundError.
        """

        raw = self.invoke_raw(command, payload=payload, tier=tier, timeout=timeout)

        if raw.returncode != 0:
            self._raise_for_failure(raw, command=command)

        out = (raw.stdout or "").strip()
        if not out:
            return {}

        try:
            parsed = json.loads(out)
        except json.JSONDecodeError as e:
            raise InvokeError(
                "ArtCraft returned non-JSON stdout. "
                f"command={command} error={e}. "
                f"stdout: {_snippet(raw.stdout)}\n"
                f"stderr: {_snippet(raw.stderr)}",
                command=command,
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        if not isinstance(parsed, dict):
            raise InvokeError(
                f"ArtCraft returned JSON that is not an object for command {command}: {type(parsed).__name__}",
                command=command,
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        return parsed

    def list_allowed(self, timeout: Optional[float] = None) -> AllowedCommands:
        """Return the allowlisted commands reported by ArtCraft.

        Calls:
            artcraft invoke --list-allowed --json

        Expected response JSON shape:
            { safe: [...], unsafe: [...], unsafeGateEnabled: bool }
        """

        args = [self._artcraft_bin, "invoke", "--list-allowed", "--json"]
        raw = self._run(args, logical_command="--list-allowed", timeout=timeout)

        if raw.returncode != 0:
            self._raise_for_failure(raw, command="--list-allowed")

        out = (raw.stdout or "").strip()
        if not out:
            raise InvokeError(
                "ArtCraft returned empty stdout for --list-allowed",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        try:
            parsed = json.loads(out)
        except json.JSONDecodeError as e:
            raise InvokeError(
                "ArtCraft returned non-JSON stdout for --list-allowed. "
                f"error={e}. stdout: {_snippet(raw.stdout)}\n"
                f"stderr: {_snippet(raw.stderr)}",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        if not isinstance(parsed, dict):
            raise InvokeError(
                f"ArtCraft returned JSON that is not an object for --list-allowed: {type(parsed).__name__}",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        safe = parsed.get("safe")
        unsafe = parsed.get("unsafe")
        unsafe_gate_enabled = parsed.get("unsafeGateEnabled")

        if not (isinstance(safe, list) and all(isinstance(x, str) for x in safe)):
            raise InvokeError(
                "ArtCraft --list-allowed returned invalid 'safe' list",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )
        if not (isinstance(unsafe, list) and all(isinstance(x, str) for x in unsafe)):
            raise InvokeError(
                "ArtCraft --list-allowed returned invalid 'unsafe' list",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )
        if not isinstance(unsafe_gate_enabled, bool):
            raise InvokeError(
                "ArtCraft --list-allowed returned invalid 'unsafeGateEnabled' boolean",
                command="--list-allowed",
                returncode=raw.returncode,
                stdout=raw.stdout,
                stderr=raw.stderr,
            )

        return AllowedCommands(
            safe=safe,
            unsafe=unsafe,
            unsafe_gate_enabled=unsafe_gate_enabled,
        )


def main() -> None:
    """Developer-friendly CLI wrapper around the ArtCraft client.

    This is *not* the ArtCraft CLI itself. It's a thin helper primarily useful
    for debugging.

    Examples:
        openclaw-artcraft invoke my_command --payload '{"x": 1}'
        openclaw-artcraft invoke my_command --tier unsafe
        openclaw-artcraft list-allowed
    """

    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="openclaw-artcraft")
    sub = parser.add_subparsers(dest="subcmd", required=True)

    p_invoke = sub.add_parser("invoke", help="Invoke an ArtCraft tauri command")
    p_invoke.add_argument("command", help="Tauri command name")
    p_invoke.add_argument("--payload", help="JSON payload string", default=None)
    p_invoke.add_argument(
        "--tier",
        choices=["safe", "unsafe"],
        default="safe",
        help="Invocation tier (unsafe passes --unsafe to artcraft)",
    )
    p_invoke.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    p_invoke.add_argument("--bin", dest="artcraft_bin", default=None, help="Override ArtCraft binary")

    p_allowed = sub.add_parser("list-allowed", help="Print the ArtCraft allowlist")
    p_allowed.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    p_allowed.add_argument("--bin", dest="artcraft_bin", default=None, help="Override ArtCraft binary")

    args = parser.parse_args()

    client = ArtCraftClient(artcraft_bin=getattr(args, "artcraft_bin", None))

    if args.subcmd == "invoke":
        payload_obj = None
        if args.payload is not None:
            try:
                payload_obj = json.loads(args.payload)
            except json.JSONDecodeError as e:
                print(f"Invalid --payload JSON: {e}", file=sys.stderr)
                return sys.exit(2)

        try:
            result = client.invoke(
                args.command,
                payload=payload_obj,
                tier=args.tier,
                timeout=args.timeout,
            )
        except ArtCraftError as e:
            print(str(e), file=sys.stderr)
            return sys.exit(1)

        print(json.dumps(result))
        return

    if args.subcmd == "list-allowed":
        try:
            allowed = client.list_allowed(timeout=args.timeout)
        except ArtCraftError as e:
            print(str(e), file=sys.stderr)
            return sys.exit(1)

        print(
            json.dumps(
                {
                    "safe": allowed.safe,
                    "unsafe": allowed.unsafe,
                    "unsafeGateEnabled": allowed.unsafe_gate_enabled,
                }
            )
        )
        return


if __name__ == "__main__":
    main()
