#!/usr/bin/env python3
"""UNSAFE readonly subset example.

This example demonstrates calling a small set of *read-only* introspection commands
that are commonly present in the UNSAFE allowlist of some ArtCraft builds.

IMPORTANT:
- These calls still require the ArtCraft unsafe gate to be enabled.
- Do NOT print full payloads for preferences/config in real logs; they may contain
  secrets depending on the ArtCraft build.

Run:
    ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 python3 examples/unsafe_readonly_subset.py
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

from artcraft_client import ArtCraftClient
from artcraft_client.exceptions import ArtCraftError


def _first_str(d: Dict[str, Any], keys: Iterable[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _first_list_of_str(d: Dict[str, Any], keys: Iterable[str]) -> Optional[List[str]]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            return v
    return None


def _summarize_app_info(result: Dict[str, Any]) -> Dict[str, Any]:
    name = _first_str(result, ["name", "appName", "app_name"])
    version = _first_str(result, ["version", "appVersion", "app_version", "buildVersion"])
    platform = _first_str(result, ["platform", "os", "target"])

    return {
        "keys": sorted(result.keys()),
        "name": name,
        "version": version,
        "platform": platform,
    }


def _summarize_provider_order(result: Dict[str, Any]) -> Dict[str, Any]:
    order = _first_list_of_str(result, ["providerOrder", "provider_order", "order", "providers"])

    return {
        "keys": sorted(result.keys()),
        "provider_order": order,
        "provider_count": (len(order) if order is not None else None),
    }


def _summarize_task_queue(result: Dict[str, Any]) -> Dict[str, Any]:
    tasks = result.get("tasks")
    if isinstance(tasks, list):
        task_count: Optional[int] = len(tasks)
    else:
        task_count = None

    return {
        "keys": sorted(result.keys()),
        "task_count": task_count,
    }


def _summarize_preferences(result: Dict[str, Any]) -> Dict[str, Any]:
    # Intentionally avoid dumping values (may include tokens/keys depending on build).
    return {
        "keys": sorted(result.keys()),
        "note": "values intentionally omitted (may include secrets)",
    }


def main() -> None:
    if os.environ.get("ARTCRAFT_ENABLE_UNSAFE_INVOKE") != "1":
        raise SystemExit(
            "This example requires ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 (unsafe gate).\n"
            "Example: ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 python3 examples/unsafe_readonly_subset.py"
        )

    client = ArtCraftClient("/usr/bin/artcraft")

    calls = [
        ("get_app_info_command", _summarize_app_info),
        ("get_provider_order_command", _summarize_provider_order),
        ("get_task_queue_command", _summarize_task_queue),
        ("get_app_preferences_command", _summarize_preferences),
    ]

    for command, summarizer in calls:
        print(f"\n== {command} (tier='unsafe') ==")
        try:
            result = client.invoke(command, tier="unsafe")
        except ArtCraftError as e:
            print(f"ERROR: {e}")
            continue

        summary = summarizer(result)

        # Print only high-level fields.
        for k in sorted(summary.keys()):
            print(f"{k}: {summary[k]}")


if __name__ == "__main__":
    main()
