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

Some commands/payloads may require `--unsafe`. Unsafe invocations are **disabled by default** and require **either**:

- `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1` (environment), **or**
- `~/.config/artcraft/cli.json` enabling unsafe invoke.

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
