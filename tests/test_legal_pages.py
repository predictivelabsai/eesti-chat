from fasthtml.common import to_xml

from chat.components import left_pane
from components.layout import AskBubble, PageFooter
from pages.home import home_page
from pages.legal import delete_account_page, privacy_page


def test_footers_link_agentic_state():
    public = to_xml(PageFooter())
    sidebar = to_xml(left_pane())
    for html in (public, sidebar):
        assert 'href="https://agenticstate.org"' in html
        assert "Agentic State" in html


def test_home_and_ask_bar_have_a_microphone():
    home = to_xml(home_page())
    bubble = to_xml(AskBubble())
    assert "hero-voice-btn" in home
    assert "toggleVoice(event)" in home
    assert "ask-bubble-voice" in bubble
    assert "toggleVoice(event)" in bubble


def test_privacy_page_discloses_core_mobile_data_flows():
    html = to_xml(privacy_page())

    assert "Predictive Labs Ltd" in html
    assert "AI chat prompts" in html
    assert "OpenAI or xAI" in html
    assert "Google Sign-In" in html
    assert "Postmark" in html
    assert 'href="/delete-account"' in html


def test_delete_account_page_has_in_app_and_web_request_paths():
    html = to_xml(delete_account_page())

    assert "Delete in the app" in html
    assert "Request deletion without the app" in html
    assert "mailto:info@eesti.chat" in html
