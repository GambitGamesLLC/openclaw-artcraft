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

### Allowlist introspection (`--list-allowed`)

To see what your installed ArtCraft build will accept, query the reported allowlists:

```bash
artcraft invoke --list-allowed --json
```

Shape:

```json
{ "safe": ["..."], "unsafe": ["..."], "unsafeGateEnabled": true }
```

Semantics:

- `safe`: commands accepted without `--unsafe`
- `unsafe`: commands that require `--unsafe` (UNSAFE tier)
- `unsafeGateEnabled`: whether `--unsafe` is accepted at all

Treat this output as *runtime facts* about the installed ArtCraft build (it may vary by version/build/config).

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

### Supported UNSAFE readonly-network subset (network/account diagnostics)

Some ArtCraft builds also expose a small set of **read-only but network/account-touching**
commands in the UNSAFE allowlist (still gated behind the unsafe switch). When available,
these are useful for estimating costs and checking Storyteller account state.

Supported commands for this `readonly-network` subset:

- `estimate_image_cost_command`
- `estimate_video_cost_command`
- `storyteller_get_credits_command`
- `storyteller_get_subscription_command`

**Warning:** these calls may contact the network and/or your account, and may require
credentials depending on your ArtCraft configuration. Avoid logging full request/response
payloads (they may include sensitive fields).

See: [`packages/client/examples/unsafe_readonly_network_subset.py`](./packages/client/examples/unsafe_readonly_network_subset.py)

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

The unit tests are designed to be fast and hermetic (they use a fake `artcraft` executable).

Anything that talks to a real ArtCraft install, the network, or an account is **manual-only** and must be an explicit
human opt-in (it may incur cost and/or require credentials). A fuller “digital twin” harness is a possible future
direction, but is out of scope today.

## License

MIT. See [LICENSE](./LICENSE).
