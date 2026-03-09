# openclaw-artcraft

Utilities and client libraries for interacting with ArtCraft from OpenClaw workflows.

## Packages

### `packages/client` (Python)

Python client library that wraps the `artcraft-cli.sh` CLI.

- Install (editable):

```bash
cd packages/client
python3 -m pip install -e .
```

- Run tests:

```bash
cd packages/client
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

## License

MIT. See [LICENSE](./LICENSE).
