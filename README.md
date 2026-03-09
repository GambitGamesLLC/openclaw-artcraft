# openclaw-artcraft

Utilities and client libraries for interacting with ArtCraft from OpenClaw workflows.

## Safety model (allowlist + unsafe gate)

ArtCraft is the **authoritative policy enforcer** for:

- the command allowlist (what can be invoked), and
- the `--unsafe` gate (whether unsafe invocations are permitted at all).

This repo’s OpenClaw skill and Python client are thin wrappers around `artcraft invoke`.
They do not (and should not) attempt to bypass ArtCraft’s checks. If ArtCraft rejects a
command/payload or unsafe is disabled, the invocation will fail.

### Using the unsafe tier from OpenClaw

In OpenClaw-facing wrappers, unsafe invocation should be an explicit opt-in via a
**tier** (e.g. `tier="unsafe"` or CLI `--tier unsafe`).

Selecting the unsafe tier is an **opt-in escalation**: only do it when the user
explicitly requests it and understands the implications; do not auto-enable or
silently “upgrade” calls.

Under the hood, the unsafe tier is implemented by passing `--unsafe` through to
`artcraft invoke`.

### Supported UNSAFE readonly subset (diagnostics)

Some ArtCraft builds expose a small set of **read-only** introspection commands in the
UNSAFE allowlist (still gated behind the unsafe switch). When available, prefer the
tiered wrappers:

- Python client: `tier="unsafe"`
- CLI helper: `openclaw-artcraft invoke --tier unsafe ...`

Commands commonly used for this readonly subset:

- `get_app_info_command`
- `get_provider_order_command`
- `get_task_queue_command`
- `get_app_preferences_command`

### Enabling unsafe invocation in ArtCraft

Unsafe invocation is disabled by default. To allow `artcraft invoke --unsafe`, enable one
of the following:

- Environment variable (per-process):
  - `ARTCRAFT_ENABLE_UNSAFE_INVOKE=1`
- User config file:
  - `~/.config/artcraft/cli.json`
  - contents:

    ```json
    { "enableUnsafeInvoke": true }
    ```

### Risk acknowledgement

Enabling unsafe invocation means you accept additional risk (security / foot-guns) and
potentially higher cost. Use it sparingly and only when you intend to run unsafe
operations.

## Optional OpenClaw Skill

A minimal optional skill lives in [`skills/openclaw-artcraft`](./skills/openclaw-artcraft).

Enable it by copying or symlinking the folder into your OpenClaw workspace:

```bash
mkdir -p ~/.openclaw/workspace/skills
ln -s "$(pwd)/skills/openclaw-artcraft" ~/.openclaw/workspace/skills/openclaw-artcraft
```

It should be picked up **next turn** (typically no Gateway restart required).

## Packages

### `packages/client` (Python)

Python client library that wraps the shipped ArtCraft CLI contract:

```bash
artcraft invoke <tauri_command_name> [--payload ...] [--unsafe] --json
```

- Install (editable):

```bash
cd packages/client
python3 -m pip install -e .
```

- Run tests:

```bash
cd packages/client
python3 -m pip install -e "./.[dev]"
python3 -m pytest -q
```

## License

MIT. See [LICENSE](./LICENSE).
