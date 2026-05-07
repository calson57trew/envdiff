"""Generate .env.example files from a parsed env, redacting values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import is_sensitive


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    comment: Optional[str] = None


@dataclass
class EnvTemplate:
    entries: List[TemplateEntry] = field(default_factory=list)

    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.placeholder for e in self.entries}


def _make_placeholder(key: str, value: Optional[str]) -> str:
    """Return an appropriate placeholder string for a key/value pair."""
    if value is None or value == "":
        return ""
    if is_sensitive(key):
        return ""
    # Preserve non-sensitive values as-is so the example is useful.
    return value


def build_template(
    env: Dict[str, Optional[str]],
    sensitive_placeholder: str = "",
) -> EnvTemplate:
    """Build an EnvTemplate from a parsed env mapping.

    Sensitive keys have their values replaced with *sensitive_placeholder*.
    Non-sensitive keys keep their original values so the template is useful
    as documentation.
    """
    entries: List[TemplateEntry] = []
    for key in sorted(env.keys()):
        value = env[key]
        if is_sensitive(key):
            placeholder = sensitive_placeholder
        else:
            placeholder = value if value is not None else ""
        entries.append(TemplateEntry(key=key, placeholder=placeholder))
    return EnvTemplate(entries=entries)


def render_template(template: EnvTemplate) -> str:
    """Render an EnvTemplate to a .env.example string."""
    lines: List[str] = []
    for entry in template.entries:
        if entry.comment:
            lines.append(f"# {entry.comment}")
        lines.append(f"{entry.key}={entry.placeholder}")
    return "\n".join(lines) + ("\n" if template.entries else "")
