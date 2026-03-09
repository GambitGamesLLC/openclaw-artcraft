# openclaw-artcraft

Utilities and client libraries for interacting with ArtCraft from OpenClaw workflows.

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
