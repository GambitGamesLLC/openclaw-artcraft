---
name: openclaw-artcraft
description: Optional OpenClaw skill for invoking ArtCraft Tauri commands via the ArtCraft CLI.
---

This skill exposes the **ArtCraft CLI invoke contract** for OpenClaw workflows.

## Contract

```bash
artcraft invoke <tauri_command_name> [--payload <json>] [--unsafe] --json
```

- For the full, up-to-date reference, run:
  - `artcraft invoke --help`
  - `openclaw-artcraft --help`

## Safety / unsafe gate

ArtCraft is the **authoritative enforcer** of the command allowlist and the unsafe gate.
This skill is a thin wrapper and should not assume it can bypass ArtCraft’s checks.

`--unsafe` is an **opt-in escalation**: only pass it with explicit user intent (never
silently or by default).

Unsafe invocations are **disabled by default** and require enabling **either**:

- `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1` (environment), **or**
- `~/.config/artcraft/cli.json` (user config), with:

  ```json
  { "enableUnsafeInvoke": true }
  ```

### Risk acknowledgement

Enabling unsafe invocation means you accept additional risk and potentially higher cost.
Use it sparingly.

## Exit codes

- `0` success
- `2` invalid args / unsafe gate disabled
- `3` disallowed
- `4` invoke error

## Examples

```bash
# Invoke a Tauri command (no payload)
artcraft invoke app.version --json

# Invoke with a JSON payload
artcraft invoke export.render --payload '{"format":"png"}' --json
```
