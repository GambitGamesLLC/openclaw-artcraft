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

### Unsafe commands

ArtCraft is the **authoritative enforcer** of the command allowlist and unsafe gate.
Passing `unsafe=True` only adds `--unsafe` to the CLI invocation; ArtCraft may still
reject the request (e.g., if unsafe is disabled).

`--unsafe` is an **opt-in escalation**: only use it with explicit user intent.

If a command requires `--unsafe`, pass `unsafe=True`:

```python
client.invoke("some:unsafe-command", payload={...}, unsafe=True)
```

To allow `artcraft invoke --unsafe`, enable unsafe invocation in ArtCraft via **either**:

- `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1` (environment), **or**
- `~/.config/artcraft/cli.json` with:

  ```json
  { "enableUnsafeInvoke": true }
  ```

#### Risk acknowledgement

Enabling unsafe invocation means you accept additional risk and potentially higher cost.
Use it sparingly.

If unsafe is disabled in the installed ArtCraft build, the client raises
`UnsafeGateDisabled`.

## Exceptions

ArtCraft exit codes are mapped to typed exceptions:

- `InvalidArgs` (exit code 2)
- `UnsafeGateDisabled` (exit code 2, detected via stderr)
- `DisallowedCommand` (exit code 3)
- `InvokeError` (exit code 4, or JSON parse errors)
- `Timeout` (subprocess timeout)

On failures, exceptions include snippets of stdout/stderr to speed up debugging.

## Testing

```bash
cd packages/client
python3 -m pip install -e "./.[dev]"
python3 -m pytest -q
```
