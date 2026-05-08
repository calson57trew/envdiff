"""Audit trail: record who compared what and when."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from envdiff.differ import DiffResult


@dataclass
class AuditEntry:
    timestamp: str
    base_file: str
    compare_file: str
    missing_in_compare: int
    missing_in_base: int
    mismatched: int
    label: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "base_file": self.base_file,
            "compare_file": self.compare_file,
            "missing_in_compare": self.missing_in_compare,
            "missing_in_base": self.missing_in_base,
            "mismatched": self.mismatched,
            "label": self.label,
        }


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_audit(
    result: DiffResult,
    base_file: str,
    compare_file: str,
    audit_path: Path,
    label: Optional[str] = None,
) -> AuditEntry:
    """Append a new audit entry to *audit_path* (JSON lines) and return it."""
    entry = AuditEntry(
        timestamp=_now_iso(),
        base_file=os.fspath(base_file),
        compare_file=os.fspath(compare_file),
        missing_in_compare=len(result.missing_in_compare),
        missing_in_base=len(result.missing_in_base),
        mismatched=len(result.mismatched),
        label=label,
    )
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.as_dict()) + "\n")
    return entry


def load_audit_log(audit_path: Path) -> AuditLog:
    """Load all entries from a JSON-lines audit file."""
    audit_path = Path(audit_path)
    log = AuditLog()
    if not audit_path.exists():
        return log
    with audit_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            log.append(AuditEntry(**data))
    return log
