#!/usr/bin/env python3
"""Example: calling ArtCraft from an OpenClaw workflow.

In OpenClaw, you typically want a single "invoke" primitive you can wrap with
retry/timeout logic. This client provides that primitive.
"""

from __future__ import annotations

from artcraft_client import ArtCraftClient


def generate_concept_art(concept_description: str) -> dict:
    client = ArtCraftClient()

    # Replace the command name + payload schema with the ones supported by your
    # installed ArtCraft build.
    return client.invoke(
        "generate:text-to-image",
        payload={
            "prompt": f"professional concept art: {concept_description}",
            "provider": "openai",
        },
        timeout=120,
    )


def main() -> None:
    result = generate_concept_art("steampunk airship with brass details")
    print(result)


if __name__ == "__main__":
    main()
