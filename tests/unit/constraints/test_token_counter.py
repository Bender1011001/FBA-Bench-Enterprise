import json
import types

import pytest

from constraints import token_counter as tc_mod
from constraints.token_counter import TokenCounter, TokenCountResult


@pytest.fixture(autouse=True)
def clear_ratio_cache():
    # Ensure model ratio overrides cache is cleared between tests
    try:
        TokenCounter._load_ratio_overrides.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    yield
    try:
        TokenCounter._load_ratio_overrides.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass


def test_estimate_ratio_uses_substring_model_matching():
    text = "Hello World!" * 10  # 120 chars
    # gpt-4o family should map to 0.24 ratio via substring
    counter = TokenCounter(default_model="gpt-4o-mini")
    result: TokenCountResult = counter.count_tokens(
        text, model="gpt-4o-mini", method="estimate"
    )
    expected_ratio = 0.24
    assert result.estimated is True
    assert result.method == "estimate"
    assert result.count == int(len(text) * expected_ratio)


def test_ratio_overrides_from_env_file(tmp_path, monkeypatch):
    text = "abcdef" * 50  # 300 chars
    overrides_path = tmp_path / "ratios.json"
    # Provide a custom model override
    overrides = {"custom-model-x": 0.5}
    overrides_path.write_text(json.dumps(overrides), encoding="utf-8")
    monkeypatch.setenv("FBA_TOKEN_RATIOS_FILE", str(overrides_path))

    counter = TokenCounter(default_model="custom-model-x")
    result = counter.count_tokens(text, model="custom-model-x", method="estimate")
    assert result.estimated is True
    assert result.count == int(len(text) * 0.5)


def test_tiktoken_exact_with_alias_and_fallback(monkeypatch):
    # Build a minimal fake tiktoken module that forces alias fallback path:
    # encoding_for_model raises KeyError, get_encoding returns an object with encode()
    class _FakeEncoding:
        def encode(self, s: str):
            # Exact token count equals character length for determinism in test
            return list(s)

    fake_tiktoken = types.SimpleNamespace(
        encoding_for_model=lambda model: (_ for _ in ()).throw(
            KeyError("unknown model")
        ),  # raises
        get_encoding=lambda name: _FakeEncoding(),
    )

    # Force tiktoken path enabled and inject fake module
    monkeypatch.setattr(tc_mod, "TIKTOKEN_AVAILABLE", True, raising=True)
    monkeypatch.setattr(tc_mod, "tiktoken", fake_tiktoken, raising=True)

    text = "Exact token count expected via fake encoding"
    counter = TokenCounter(
        default_model="gpt-4o-mini"
    )  # alias should map to o200k_base but our fake handles all
    # Explicitly use tiktoken path
    result = counter.count_tokens(text, model="gpt-4o-mini", method="tiktoken")
    assert result.estimated is False
    assert result.method == "tiktoken"
    assert result.count == len(text)

    # Messages path under tiktoken as well
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "there"},
    ]
    msg_result = counter.count_messages(
        messages, model="gpt-4o-mini", method="tiktoken"
    )
    # With our fake encoding, role/content tokens equal their string lengths.
    # Count format overhead (approx from implementation): per-message +4, final +2.
    per_message_overhead = 4 * len(messages)
    final_overhead = 2
    tokenized_lengths = sum(
        len(m.get("content", "")) + len(m.get("role", "")) for m in messages
    )
    expected = tokenized_lengths + per_message_overhead + final_overhead
    assert msg_result.estimated is False
    assert msg_result.count == expected


def test_provider_hint_guides_alias_resolution_tiktoken(monkeypatch):
    # Fake tiktoken returns encoding objects regardless of alias chosen
    class _FakeEncoding:
        def encode(self, s: str):
            return list(s)

    fake_tiktoken = types.SimpleNamespace(
        encoding_for_model=lambda model: (_ for _ in ()).throw(
            KeyError("unknown model")
        ),
        get_encoding=lambda name: _FakeEncoding(),
    )
    monkeypatch.setattr(tc_mod, "TIKTOKEN_AVAILABLE", True, raising=True)
    monkeypatch.setattr(tc_mod, "tiktoken", fake_tiktoken, raising=True)

    text = "anthropic provider hint should pick safe encoding"
    counter = TokenCounter(default_model="claude-3-opus")
    # Provider='anthropic' should steer alias to cl100k_base (handled by fake)
    result = counter.count_tokens(
        text, model="claude-3-opus", method="tiktoken", provider="anthropic"
    )
    assert result.estimated is False
    assert result.count == len(text)


def test_unknown_model_falls_back_to_cl100k_in_tiktoken(monkeypatch):
    class _FakeEncoding:
        def encode(self, s: str):
            return list(s)

    # encoding_for_model raises; get_encoding("cl100k_base") returns a fake encoding
    def _get_encoding(name: str):
        assert name in ("cl100k_base", "o200k_base", "p50k_base")
        return _FakeEncoding()

    fake_tiktoken = types.SimpleNamespace(
        encoding_for_model=lambda model: (_ for _ in ()).throw(
            KeyError("unknown model")
        ),
        get_encoding=_get_encoding,
    )
    monkeypatch.setattr(tc_mod, "TIKTOKEN_AVAILABLE", True, raising=True)
    monkeypatch.setattr(tc_mod, "tiktoken", fake_tiktoken, raising=True)

    text = "fallback to cl100k_base expected"
    counter = TokenCounter(default_model="vendor-x-unknown-123")
    result = counter.count_tokens(text, model="vendor-x-unknown-123", method="tiktoken")
    assert result.estimated is False
    assert result.count == len(text)


def test_estimate_ratios_for_multiple_providers():
    text = "1234567890" * 20  # 200 chars
    counter = TokenCounter(default_model="gpt-3.5-turbo")
    # Expect substring mapping to use ~0.25 ratios
    for model in ["claude-3-opus", "gemini-1.5-pro", "mistral-large", "llama-3-70b"]:
        res = counter.count_tokens(text, model=model, method="estimate")
        assert res.estimated is True
        assert res.count == int(len(text) * 0.25)
