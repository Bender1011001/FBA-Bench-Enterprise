from pathlib import Path

import pytest

from fba_bench_core.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    # Ensure clean settings on every test
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_and_env_precedence(monkeypatch):
    # Ensure no overlay or env for these keys
    monkeypatch.delenv("FBA_CONFIG_PATH", raising=False)
    monkeypatch.delenv("API_RATE_LIMIT", raising=False)

    # Defaults
    s = get_settings()
    assert s.api_rate_limit == "100/minute"

    # Env overrides defaults
    monkeypatch.setenv("API_RATE_LIMIT", "250/minute")
    get_settings.cache_clear()
    s = get_settings()
    assert s.api_rate_limit == "250/minute"


def test_yaml_overlay_precedence(monkeypatch, tmp_path: Path):
    # Skip if PyYAML isn't available (overlay is a no-op in that case)
    try:
        import yaml  # noqa: F401
    except Exception:
        pytest.skip("PyYAML not installed; YAML overlay not applicable")

    # Prepare overlay file
    overlay = tmp_path / "overlay.yaml"
    overlay.write_text(
        "\n".join(
            [
                "environment: development",
                "api:",
                '  rate_limit: "123/minute"',
            ]
        ),
        encoding="utf-8",
    )

    # Point to YAML overlay and clear env var
    monkeypatch.setenv("FBA_CONFIG_PATH", str(overlay))
    monkeypatch.delenv("API_RATE_LIMIT", raising=False)

    # YAML should apply
    get_settings.cache_clear()
    s = get_settings()
    assert s.api_rate_limit == "123/minute"

    # Env should override YAML
    monkeypatch.setenv("API_RATE_LIMIT", "777/minute")
    get_settings.cache_clear()
    s = get_settings()
    assert s.api_rate_limit == "777/minute"


@pytest.mark.parametrize(
    "env_value, protected, enabled, protect_docs, test_bypass",
    [
        ("production", True, True, True, False),
        ("prod", True, True, True, False),
        ("staging", True, True, True, False),
        ("development", False, False, False, True),
        ("dev", False, False, False, True),
        ("", False, False, False, True),
    ],
)
def test_protected_env_defaults(
    monkeypatch, env_value, protected, enabled, protect_docs, test_bypass
):
    monkeypatch.setenv("ENVIRONMENT", env_value)
    # Clear explicit auth envs
    monkeypatch.delenv("AUTH_ENABLED", raising=False)
    monkeypatch.delenv("AUTH_PROTECT_DOCS", raising=False)
    monkeypatch.delenv("AUTH_TEST_BYPASS", raising=False)
    monkeypatch.delenv("FBA_CONFIG_PATH", raising=False)

    get_settings.cache_clear()
    s = get_settings()
    assert s.is_protected_env is protected
    assert s.auth_enabled is enabled
    assert s.auth_protect_docs is protect_docs
    assert s.auth_test_bypass is test_bypass


def test_db_url_preference(monkeypatch):
    # Prefer FBA_BENCH_DB_URL over DATABASE_URL when both present
    monkeypatch.setenv("FBA_BENCH_DB_URL", "sqlite:///./preferred.db")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./legacy.db")
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_db_url == "sqlite:///./preferred.db"

    # Fall back to DATABASE_URL if FBA_BENCH_DB_URL missing
    monkeypatch.delenv("FBA_BENCH_DB_URL", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_db_url == "sqlite:///./legacy.db"

    # Fall back to None if neither set (caller may provide own default)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_db_url is None


def test_redis_url_preference(monkeypatch):
    # Prefer FBA_BENCH_REDIS_URL over REDIS_URL
    monkeypatch.setenv("FBA_BENCH_REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_redis_url == "redis://localhost:6379/1"

    # Fall back to REDIS_URL
    monkeypatch.delenv("FBA_BENCH_REDIS_URL", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_redis_url == "redis://localhost:6379/0"

    # None if neither set
    monkeypatch.delenv("REDIS_URL", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert s.preferred_redis_url is None


def test_logging_settings(monkeypatch):
    # Default include_tracebacks True when unset
    monkeypatch.delenv("FBA_LOG_INCLUDE_TRACEBACKS", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert s.logging_include_tracebacks is True

    # Explicit env override to false
    monkeypatch.setenv("FBA_LOG_INCLUDE_TRACEBACKS", "false")
    get_settings.cache_clear()
    s = get_settings()
    assert s.logging_include_tracebacks is False

    # Level/format/file passthrough
    monkeypatch.setenv("FBA_LOG_LEVEL", "debug")
    monkeypatch.setenv("FBA_LOG_FORMAT", "json")
    monkeypatch.setenv("FBA_LOG_FILE", "app.log")
    get_settings.cache_clear()
    s = get_settings()
    assert (s.logging_level or "").lower() == "debug"
    assert (s.logging_format or "").lower() == "json"
    assert s.logging_file == "app.log"


def test_cors_defaults_and_override(monkeypatch):
    # Default local dev origins when not configured
    monkeypatch.delenv("FBA_CORS_ALLOW_ORIGINS", raising=False)
    get_settings.cache_clear()
    s = get_settings()
    assert "http://localhost:3000" in s.cors_allow_origins

    # Comma-separated env override
    monkeypatch.setenv("FBA_CORS_ALLOW_ORIGINS", "https://example.com, http://localhost:5555")
    get_settings.cache_clear()
    s = get_settings()
    assert s.cors_allow_origins == ["https://example.com", "http://localhost:5555"]
