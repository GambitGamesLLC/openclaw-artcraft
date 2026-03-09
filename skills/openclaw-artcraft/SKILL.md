---
name: openclaw-artcraft
description: Optional OpenClaw skill for invoking ArtCraft Tauri commands via the ArtCraft CLI.
---

This skill documents the **ArtCraft CLI invoke contract** for OpenClaw workflows.

ArtCraft is the **authoritative policy enforcer** for:

- the command allowlist (what can be invoked), and
- the unsafe gate (whether unsafe invocations are permitted at all).

This skill is intentionally a thin wrapper and must not assume it can bypass ArtCraft checks.

## Contract (ArtCraft CLI)

```bash
artcraft invoke <tauri_command> [--payload <json>] [--unsafe] --json
```

- Inspect the installed ArtCraft allowlists:

  ```bash
  artcraft invoke --list-allowed --json
  ```

  Expected JSON shape:

  ```json
  { "safe": ["..."], "unsafe": ["..."], "unsafeGateEnabled": true }
  ```

- For wrapper tooling and debugging helpers:
  - `openclaw-artcraft --help`
  - `openclaw-artcraft invoke --help`
  - `openclaw-artcraft list-allowed --help`

## Safety model: strict SAFE vs UNSAFE tiers

OpenClaw-facing wrappers should treat invocation as a **two-tier model**:

- **SAFE tier (default):** does *not* pass `--unsafe`.
  - Only SAFE-allowlisted commands should be used.
- **UNSAFE tier (explicit opt-in):** passes `--unsafe` through to `artcraft invoke`.
  - Command must be UNSAFE-allowlisted *and* the ArtCraft unsafe gate must be enabled.

### Recommendation (don’t tell users to pass `--unsafe` directly)

Prefer tiered APIs/CLIs so “unsafe” is an explicit, reviewable opt-in:

- Python client: `tier="unsafe"`
- CLI helper: `openclaw-artcraft invoke --tier unsafe ...`

Only use `artcraft invoke --unsafe ...` when you are deliberately testing the raw ArtCraft contract.

## Enabling UNSAFE invocation (ArtCraft gate)

Unsafe invocation is **disabled by default**. To allow UNSAFE tier calls, enable **either**:

- `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1` (environment), **or**
- `~/.config/artcraft/cli.json` (user config), containing:

  ```json
  { "enableUnsafeInvoke": true }
  ```

### Risk acknowledgement

Enabling unsafe invocation means you accept additional risk (security / foot-guns) and potentially higher cost.
Use it sparingly and only when the user explicitly requests it.

## Exit codes (ArtCraft CLI)

- `0` success
- `2` invalid args / unsafe gate disabled
- `3` disallowed
- `4` invoke error

## Examples

### SAFE: platform info (no payload)

```bash
artcraft invoke platform_info_command --json
```

### SAFE: flip an image (base64 payload)

```bash
# 1x1 transparent PNG (base64)
IMG_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X8f5cAAAAASUVORK5CYII="

artcraft invoke flip_image \
  --payload "{\"image_base64\":\"${IMG_B64}\",\"flip\":\"horizontal\"}" \
  --json
```

### UNSAFE readonly subset (requires gate + UNSAFE tier)

Some ArtCraft builds expose a small set of **read-only** introspection commands in the
UNSAFE allowlist (still gated behind the unsafe switch). When available, these are
useful for diagnostics and UI state without mutating anything:

- `get_app_info_command`
- `get_provider_order_command`
- `get_task_queue_command`
- `get_app_preferences_command`

```bash
# Prefer the tiered wrapper (explicit opt-in):
ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 \
openclaw-artcraft invoke get_app_info_command --tier unsafe

ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 \
openclaw-artcraft invoke get_provider_order_command --tier unsafe

ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 \
openclaw-artcraft invoke get_task_queue_command --tier unsafe

ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 \
openclaw-artcraft invoke get_app_preferences_command --tier unsafe

# (Raw contract, generally not recommended for OpenClaw workflows)
# ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 artcraft invoke get_app_info_command --unsafe --json
```
