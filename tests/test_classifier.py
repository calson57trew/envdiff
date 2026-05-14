"""Tests for envdiff.classifier."""

from __future__ import annotations

import pytest

from envdiff.classifier import (
    UNCATEGORIZED,
    ClassifiedEnv,
    _classify_key,
    classify_env,
)


@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "abc123",
        "SMTP_HOST": "mail.example.com",
        "S3_BUCKET": "my-bucket",
        "LOG_LEVEL": "INFO",
        "FEATURE_DARK_MODE": "true",
        "APP_NAME": "envdiff",
        "HOST": "0.0.0.0",
        "PORT": "8080",
        "CUSTOM_WIDGET": "42",
    }


def test_classify_key_database():
    assert _classify_key("DB_HOST") == "database"
    assert _classify_key("POSTGRES_URI") == "database"


def test_classify_key_cache():
    assert _classify_key("REDIS_URL") == "cache"
    assert _classify_key("CACHE_TTL") == "cache"


def test_classify_key_auth():
    assert _classify_key("SECRET_KEY") == "auth"
    assert _classify_key("JWT_SECRET") == "auth"
    assert _classify_key("API_KEY") == "auth"


def test_classify_key_email():
    assert _classify_key("SMTP_HOST") == "email"
    assert _classify_key("MAIL_FROM") == "email"


def test_classify_key_storage():
    assert _classify_key("S3_BUCKET") == "storage"
    assert _classify_key("AWS_REGION") == "storage"


def test_classify_key_uncategorized():
    assert _classify_key("CUSTOM_WIDGET") == UNCATEGORIZED
    assert _classify_key("FOOBAR") == UNCATEGORIZED


def test_classify_key_case_insensitive():
    assert _classify_key("db_host") == "database"
    assert _classify_key("smtp_port") == "email"


def test_classify_env_groups_correctly(sample_env):
    result = classify_env(sample_env)
    assert isinstance(result, ClassifiedEnv)
    assert "DB_HOST" in result.keys_in("database")
    assert "DB_PASSWORD" in result.keys_in("database")
    assert "REDIS_URL" in result.keys_in("cache")
    assert "SECRET_KEY" in result.keys_in("auth")
    assert "SMTP_HOST" in result.keys_in("email")
    assert "S3_BUCKET" in result.keys_in("storage")
    assert "LOG_LEVEL" in result.keys_in("logging")
    assert "FEATURE_DARK_MODE" in result.keys_in("feature")
    assert "CUSTOM_WIDGET" in result.keys_in(UNCATEGORIZED)


def test_classify_env_all_categories_sorted(sample_env):
    result = classify_env(sample_env)
    cats = result.all_categories()
    assert cats == sorted(cats)


def test_classify_env_empty():
    result = classify_env({})
    assert result.categories == {}
    assert result.all_categories() == []


def test_classify_env_as_dict(sample_env):
    result = classify_env(sample_env)
    d = result.as_dict()
    assert isinstance(d, dict)
    assert "database" in d
    assert d["database"]["DB_HOST"] == "localhost"


def test_classify_env_preserves_none_values():
    env = {"DB_HOST": None, "CUSTOM": None}
    result = classify_env(env)
    assert result.categories["database"]["DB_HOST"] is None
    assert result.categories[UNCATEGORIZED]["CUSTOM"] is None
