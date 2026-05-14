"""Classify .env keys into logical categories based on naming conventions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Patterns map category name -> list of regex patterns
_CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "database": [r"DB_", r"DATABASE_", r"POSTGRES", r"MYSQL", r"SQLITE", r"MONGO"],
    "cache": [r"REDIS_", r"MEMCACHE", r"CACHE_"],
    "auth": [r"SECRET", r"TOKEN", r"AUTH_", r"JWT_", r"OAUTH", r"API_KEY"],
    "email": [r"SMTP_", r"MAIL_", r"EMAIL_", r"SENDGRID", r"MAILGUN"],
    "storage": [r"S3_", r"AWS_", r"GCS_", r"BUCKET", r"STORAGE_"],
    "logging": [r"LOG_", r"LOGGING_", r"SENTRY_", r"DATADOG"],
    "feature": [r"FEATURE_", r"FLAG_", r"FF_", r"ENABLE_", r"DISABLE_"],
    "network": [r"HOST", r"PORT", r"URL", r"ENDPOINT", r"BASE_URL", r"DOMAIN"],
    "app": [r"APP_", r"APPLICATION_", r"SERVICE_", r"ENV", r"ENVIRONMENT", r"DEBUG"],
}

_COMPILED: Dict[str, List[re.Pattern]] = {
    cat: [re.compile(p, re.IGNORECASE) for p in patterns]
    for cat, patterns in _CATEGORY_PATTERNS.items()
}

UNCATEGORIZED = "uncategorized"


@dataclass
class ClassifiedEnv:
    """Result of classifying an env dict into categories."""

    categories: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    def keys_in(self, category: str) -> List[str]:
        return sorted(self.categories.get(category, {}).keys())

    def all_categories(self) -> List[str]:
        return sorted(self.categories.keys())

    def as_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {cat: dict(entries) for cat, entries in sorted(self.categories.items())}


def _classify_key(key: str) -> str:
    """Return the first matching category for *key*, or UNCATEGORIZED."""
    for category, patterns in _COMPILED.items():
        for pattern in patterns:
            if pattern.search(key):
                return category
    return UNCATEGORIZED


def classify_env(env: Dict[str, Optional[str]]) -> ClassifiedEnv:
    """Group *env* keys into named categories based on naming conventions.

    Args:
        env: Mapping of key -> value (value may be None).

    Returns:
        A :class:`ClassifiedEnv` instance with keys grouped by category.
    """
    result: Dict[str, Dict[str, Optional[str]]] = {}
    for key, value in env.items():
        category = _classify_key(key)
        result.setdefault(category, {})[key] = value
    return ClassifiedEnv(categories=result)
