# OpenClaw ArtCraft (Python client)

`openclaw-artcraft` is a small Python wrapper around the shipped ArtCraft CLI:

```bash
artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json
```

The client stays intentionally low-level and exposes a single core method:
`ArtCraftClient.invoke()`.

## Install (editable)

```bash
cd packages/client
python3 -m pip install -e .
```

## Configure the ArtCraft binary

By default, the client runs `artcraft` from your `PATH`.

You can override the executable with:

- `ARTCRAFT_BIN=/path/to/artcraft` (env var), or
- `ArtCraftClient(artcraft_bin="/path/to/artcraft")`

## Usage

```python
from artcraft_client import ArtCraftClient

client = ArtCraftClient()

# Call an ArtCraft tauri command and pass a JSON payload.
result = client.invoke(
    "generate:text-to-image",
    payload={
        "prompt": "futuristic cat robot in a cyberpunk city",
        "provider": "openai",
    },
)

print(result)
```

## Tiers (safe vs unsafe)

ArtCraft is the **authoritative enforcer** of the command allowlist and unsafe gate.
In the Python client, unsafe invocation is an explicit opt-in via a **tier**:

- `tier="safe"` (default) → does *not* pass `--unsafe`
- `tier="unsafe"` → passes `--unsafe` to `artcraft invoke`

Example:

```python
client.invoke(
    "some:unsafe-command",
    payload={...},
    tier="unsafe",
)
```

To allow `artcraft invoke --unsafe`, enable unsafe invocation in ArtCraft via **either**:

- `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1` (environment), **or**
- `~/.config/artcraft/cli.json` with:

  ```json
  { "enableUnsafeInvoke": true }
  ```

### Risk acknowledgement

Enabling unsafe invocation means you accept additional risk and potentially higher cost.
Use it sparingly.

If unsafe is disabled in the installed ArtCraft build, the client raises
`UnsafeGateDisabled`.

## Allowlist introspection

You can query the allowlisted commands reported by your installed ArtCraft build:

```python
allowed = client.list_allowed()
print(allowed.safe)
print(allowed.unsafe)
print(allowed.unsafe_gate_enabled)
```

This calls:

```bash
artcraft invoke --list-allowed --json
```

and parses a response shaped like:

```json
{ "safe": ["..."], "unsafe": ["..."], "unsafeGateEnabled": true }
```

## Exceptions

On failures (`returncode != 0`), the client prefers parsing a JSON error payload and
uses `error_details.code` for deterministic exception mapping.

Common mappings:

- `InvalidArgs`
- `UnsafeGateDisabled`
- `DisallowedCommand`
- `InvokeError`
- `Timeout` (subprocess timeout)

On failures, exceptions include snippets of stdout/stderr to speed up debugging.

## Testing

```bash
cd packages/client
python3 -m pip install -e "./.[dev]"
python3 -m pytest -q
```
