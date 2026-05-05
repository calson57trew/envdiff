"""Parser for .env files."""

import re
from pathlib import Path
from typing import Dict, Optional


ENV_LINE_RE = re.compile(
    r'^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$'
)
COMMENT_RE = re.compile(r'^\s*#.*$')


def parse_env_file(path: str | Path) -> Dict[str, Optional[str]]:
    """Parse a .env file and return a dict of key-value pairs.

    - Blank lines and comment lines (starting with #) are ignored.
    - Values may be optionally quoted with single or double quotes.
    - Keys without values are stored as None.

    Args:
        path: Path to the .env file.

    Returns:
        Dictionary mapping variable names to their values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    result: Dict[str, Optional[str]] = {}

    with env_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or COMMENT_RE.match(line):
                continue
            match = ENV_LINE_RE.match(line)
            if match:
                key = match.group("key")
                value: Optional[str] = match.group("value").strip()
                value = _strip_quotes(value) if value else None
                result[key] = value

    return result


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value
