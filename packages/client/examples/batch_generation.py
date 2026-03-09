#!/usr/bin/env python3
"""Batch example using the low-level `invoke()` API."""

from __future__ import annotations

import json

from artcraft_client import ArtCraftClient


def main() -> None:
    client = ArtCraftClient()

    prompts = [
        "cyberpunk city at night",
        "fantasy castle in mountains",
        "sci-fi spaceship interior",
    ]

    results = []
    for prompt in prompts:
        results.append(
            client.invoke(
                "generate:text-to-image",
                payload={"prompt": prompt, "provider": "openai"},
            )
        )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
