from __future__ import annotations

from seo_engine.safety import SafetyPolicy, validate_edit


def test_validate_ok_when_only_link_added():
    original = "<html><body><p>Buy running shoes today.</p></body></html>"
    edited = "<html><body><p>Buy <a href='/s'>running shoes</a> today.</p></body></html>"
    result = validate_edit(original, edited, policy=SafetyPolicy())
    assert result.ok
    assert result.errors == []


def test_validate_rejects_visible_text_change():
    original = "<html><body><p>Buy running shoes today.</p></body></html>"
    # 'today' was silently deleted -> content loss
    edited = "<html><body><p>Buy <a href='/s'>running shoes</a>.</p></body></html>"
    result = validate_edit(original, edited, policy=SafetyPolicy())
    assert not result.ok
    assert any(i.code == "text_changed" for i in result.errors)


def test_validate_rejects_injected_script():
    original = "<html><body><p>Hello world</p></body></html>"
    edited = "<html><body><p>Hello world</p><script>alert(1)</script></body></html>"
    result = validate_edit(original, edited, policy=SafetyPolicy())
    assert not result.ok
    assert any(i.code == "script_injected" for i in result.errors)


def test_validate_allows_intended_text_delta():
    original = "<html><body><p>Read the guide.</p></body></html>"
    # We intentionally added the anchor words "marathon tips" as new visible text.
    edited = "<html><body><p>Read the guide. <a href='/m'>marathon tips</a></p></body></html>"
    result = validate_edit(
        original, edited, policy=SafetyPolicy(), expect_text_delta="marathon tips"
    )
    assert result.ok


def test_policy_is_immutable():
    policy = SafetyPolicy()
    try:
        policy.max_links_per_page = 99  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised
