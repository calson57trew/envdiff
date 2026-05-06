"""Snapshot support: save and load .env diff results to/from JSON files."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from envdiff.differ import DiffResult

_SNAPSHOT_VERSION = 1


def save_snapshot(result: DiffResult, path: str, label: str = "") -> None:
    """Serialise a DiffResult to a JSON snapshot file."""
    payload: dict[str, Any] = {
        "version": _SNAPSHOT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "missing_in_compare": sorted(result.missing_in_compare),
        "missing_in_base": sorted(result.missing_in_base),
        "mismatched": {
            k: {"base": v[0], "compare": v[1]}
            for k, v in sorted(result.mismatched.items())
        },
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def load_snapshot(path: str) -> tuple[DiffResult, dict[str, Any]]:
    """Deserialise a snapshot file back into a DiffResult.

    Returns the DiffResult and the raw metadata dict (version, created_at, label).
    """
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if payload.get("version") != _SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {payload.get('version')!r}"
        )

    mismatched = {
        k: (v["base"], v["compare"])
        for k, v in payload.get("mismatched", {}).items()
    }

    result = DiffResult(
        missing_in_compare=set(payload.get("missing_in_compare", [])),
        missing_in_base=set(payload.get("missing_in_base", [])),
        mismatched=mismatched,
    )
    meta = {
        "version": payload["version"],
        "created_at": payload.get("created_at", ""),
        "label": payload.get("label", ""),
    }
    return result, meta
