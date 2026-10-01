from fasthtml.common import *
from pathlib import Path

_CHANGELOG = Path(__file__).resolve().parent.parent / "docs" / "change_log.md"


def changelog_page():
    try:
        md = _CHANGELOG.read_text()
    except Exception:
        md = "# Change Log\n\nNot available."
    return Div(
        Section(
            Div(
                H1("Changelog", cls="public-page-title"),
                P("What's new in eesti.chat.", cls="public-page-intro"),
                cls="portal-container public-hero-content",
            ),
            cls="public-page-hero",
        ),
        Section(
            Div(
                Div(id="changelog-md", cls="public-reading-column changelog-body"),
                Script(md, id="changelog-src", type="text/markdown"),
                Script(src="/static/marked.min.js"),
                Script(NotStr(
                    "(function(){var s=document.getElementById('changelog-src');"
                    "var o=document.getElementById('changelog-md');"
                    "o.innerHTML=(window.marked?marked.parse(s.textContent):"
                    "'<pre>'+s.textContent.replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];})+'</pre>');})();"
                )),
                cls="portal-container",
            ),
            cls="public-section public-section-alt",
        ),
    )
