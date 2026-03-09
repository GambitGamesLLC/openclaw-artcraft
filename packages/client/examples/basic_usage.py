#!/usr/bin/env python3
"""Basic usage example for the ArtCraft Python client."""

from __future__ import annotations

import json

from artcraft_client import ArtCraftClient


def main() -> None:
    client = ArtCraftClient()

    print("ArtCraft Client - Basic Usage Example")
    print("=" * 50)

    # NOTE: The command name and payload schema are defined by the installed
    # ArtCraft build. Replace these with the commands you use.
    result = client.invoke(
        "generate:text-to-image",
        payload={
            "prompt": "futuristic cat robot in a cyberpunk city",
            "provider": "openai",
        },
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
