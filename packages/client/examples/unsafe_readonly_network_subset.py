#!/usr/bin/env python3
"""UNSAFE readonly-network subset example.

This example demonstrates calling a small set of *read-only* commands that may still
be **network/account-touching** (e.g., Storyteller account state and cost estimates).

IMPORTANT:
- These calls require the ArtCraft unsafe gate to be enabled.
- These calls may contact the network and/or your account and may require
  credentials depending on your ArtCraft configuration.
- Avoid printing full request/response payloads in real logs (they may include
  sensitive fields).

Run:
    ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 python3 examples/unsafe_readonly_network_subset.py

Optional:
    # Some builds require a payload for cost-estimate commands.
    # Provide it via env var (do NOT log it).
    ARTCRAFT_READONLY_NETWORK_PAYLOAD_JSON='{"provider":"...","model":"..."}' \
      ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 \
      python3 examples/unsafe_readonly_network_subset.py
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, Optional

from artcraft_client import ArtCraftClient
from artcraft_client.exceptions import ArtCraftError


def _first_str(d: Dict[str, Any], keys: Iterable[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _first_number(d: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _summarize_estimate(result: Dict[str, Any]) -> Dict[str, Any]:
    # Best-effort extraction; shapes vary across ArtCraft builds.
    cost = _first_number(result, [
        "cost",
        "estimatedCost",
        "estimated_cost",
        "usd",
        "priceUsd",
        "price_usd",
    ])
    currency = _first_str(result, ["currency", "currencyCode", "currency_code"])

    return {
        "keys": sorted(result.keys()),
        "estimated_cost": cost,
        "currency": currency,
        "note": "values are best-effort; response shape varies by build",
    }


def _summarize_credits(result: Dict[str, Any]) -> Dict[str, Any]:
    credits = _first_number(result, [
        "credits",
        "remainingCredits",
        "remaining_credits",
        "balance",
        "creditBalance",
        "credit_balance",
    ])

    return {
        "keys": sorted(result.keys()),
        "credits": credits,
    }


def _summarize_subscription(result: Dict[str, Any]) -> Dict[str, Any]:
    status = _first_str(result, ["status", "subscriptionStatus", "subscription_status"])
    plan = _first_str(result, ["plan", "planName", "plan_name", "tier"])
    renewal = _first_str(result, [
        "renewalDate",
        "renewal_date",
        "currentPeriodEnd",
        "current_period_end",
        "expiresAt",
        "expires_at",
    ])

    return {
        "keys": sorted(result.keys()),
        "status": status,
        "plan": plan,
        "renewal": renewal,
    }


def main() -> None:
    if os.environ.get("ARTCRAFT_ENABLE_UNSAFE_INVOKE") != "1":
        raise SystemExit(
            "This example requires ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 (unsafe gate).\n"
            "Example: ARTCRAFT_ENABLE_UNSAFE_INVOKE=1 python3 examples/unsafe_readonly_network_subset.py"
        )

    estimate_payload: Optional[Dict[str, Any]]
    payload_json = os.environ.get("ARTCRAFT_READONLY_NETWORK_PAYLOAD_JSON")
    if payload_json:
        try:
            estimate_payload = json.loads(payload_json)
            if not isinstance(estimate_payload, dict):
                raise ValueError("payload must be a JSON object")
        except Exception as e:  # pragma: no cover (example script)
            raise SystemExit(
                "ARTCRAFT_READONLY_NETWORK_PAYLOAD_JSON must be a JSON object (dict).\n"
                f"Parse error: {e}"
            )
    else:
        estimate_payload = None

    client = ArtCraftClient()

    calls = [
        ("estimate_image_cost_command", _summarize_estimate, estimate_payload),
        ("estimate_video_cost_command", _summarize_estimate, estimate_payload),
        ("storyteller_get_credits_command", _summarize_credits, None),
        ("storyteller_get_subscription_command", _summarize_subscription, None),
    ]

    for command, summarizer, payload in calls:
        print(f"\n== {command} (tier='unsafe') ==")
        try:
            result = client.invoke(command, payload=payload, tier="unsafe")
        except ArtCraftError as e:
            print(f"ERROR: {e}")
            continue

        summary = summarizer(result)

        # Print only high-level fields (avoid dumping full payloads).
        for k in sorted(summary.keys()):
            print(f"{k}: {summary[k]}")


if __name__ == "__main__":
    main()
