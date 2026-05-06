"""Load a validation schema from a TOML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from envdiff.validator import KeySchema


def _schema_from_dict(raw: dict) -> Dict[str, KeySchema]:
    """Convert a plain dict (from parsed config) to a schema mapping."""
    schema: Dict[str, KeySchema] = {}
    for key, spec in raw.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Schema entry for {key!r} must be a mapping, got {type(spec).__name__}")
        schema[key] = KeySchema(
            required=bool(spec.get("required", True)),
            pattern=spec.get("pattern") or None,
            allowed_values=spec.get("allowed_values") or None,
        )
    return schema


def load_schema(path: str | Path) -> Dict[str, KeySchema]:
    """Load a schema file and return a key -> :class:`KeySchema` mapping.

    Supported formats
    -----------------
    ``.json``
        A JSON object whose keys are env-var names and values are objects
        with optional fields ``required`` (bool), ``pattern`` (str),
        and ``allowed_values`` (list of str).
    ``.toml``
        Same structure in TOML format. Requires Python 3.11+ (``tomllib``)
        or the ``tomli`` back-port.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _schema_from_dict(raw)

    if suffix == ".toml":
        try:
            import tomllib  # type: ignore[import]  # Python 3.11+
        except ModuleNotFoundError:
            try:
                import tomli as tomllib  # type: ignore[import,no-redef]
            except ModuleNotFoundError as exc:
                raise ImportError(
                    "TOML schema files require Python 3.11+ or the 'tomli' package."
                ) from exc
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        return _schema_from_dict(raw)

    raise ValueError(f"Unsupported schema file format: {suffix!r}. Use .json or .toml.")
