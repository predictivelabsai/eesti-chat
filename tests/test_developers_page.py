"""Developers section: copy buttons copy only the command (no prompt, no output)."""

from fasthtml.common import to_xml

from pages.developers import CLAUDE_CMD, developers_section


def test_copy_buttons_and_languages():
    en = to_xml(developers_section("en"))
    et = to_xml(developers_section("et"))
    assert f'data-copy="{CLAUDE_CMD}"' in en
    assert 'data-copy="$' not in en and "data-copy=\"→" not in en
    assert en.count('class="dev-copy"') >= 7
    assert "Example output, illustrative." in en and "Näidisväljund" in et
    for name in ("ChatGPT", "Claude", "Grok", "Cursor"):
        assert name in en
    assert "<svg" in en  # inline client logos
