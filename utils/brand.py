"""eesti.chat brand assets: the talking-stone mark, wordmark and icon set.

Icons are drawn on a 24 px grid with a 2 px round stroke; most leave one
small opening in their outline. See static/brand/README.md for usage rules.
"""

from __future__ import annotations

from fasthtml.common import A, Link, Meta, NotStr, Span

SITE_NAME = "eesti.chat"
SITE_DESCRIPTION = ("Ask anything about Estonia: e-Residency, taxes, digital ID, moving and "
                    "public services, answered with links to official sources.")
OG_IMAGE = "https://eesti.chat/static/og-image.png"

BLUE = "#0030DE"
WHITE = "#FFFFFF"
INK = "#0F172A"

# The stone: a 52 u block with 16 u radii and one square "speaker" corner
# (bottom-left), drawn in a 64 u box.
STONE_D = "M6 58V22A16 16 0 0 1 22 6h20a16 16 0 0 1 16 16v20a16 16 0 0 1-16 16Z"
E_D = "M20 32h24a12 12 0 1 0-4.3 9.2"
# Heavier e for 16-32 px renderings.
E_SMALL_D = "M19 32h26a13 13 0 1 0-4.6 10"

ICONS: dict[str, str] = {
    # Specialist topics
    "residency": "M13 5h6a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5M7 11a2 2 0 1 0 4 0a2 2 0 1 0-4 0M6 16.5c.6-1.5 1.7-2.2 3-2.2s2.4.7 3 2.2M14.5 10h3.5M14.5 13.5h2.5",
    "moving": "M3.5 11 12 4l8.5 7M6 9.5v2M6 14.5V20h12V9.5M10 20v-4.5h4V20",
    "tax": "M6 13v8l2-1.4 2 1.4 2-1.4 2 1.4 2-1.4 2 1.4V3H6v7M9.5 14.5l5-5M10 9.75h.01M14 14.25h.01",
    "digital": "M17 9.5V20a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 7 20V4a1.5 1.5 0 0 1 1.5-1.5h7A1.5 1.5 0 0 1 17 4v2.5M10.5 18.5h3M9.5 11.5h.01M12 11.5h.01M14.5 11.5h.01",
    "services": "M3 9 12 4l9 5M4.5 9.5h15M6.5 12v5M10.5 12v5M13.5 12v5M17.5 12v5M4 20h7M14 20h6",
    "discover": "M21 12a9 9 0 1 1-3.2-6.9M15.6 8.4l-2 5.2-5.2 2 2-5.2z",
    # Interface
    "chat": "M4 20V10a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v4a6 6 0 0 1-6 6H7.5",
    "new-chat": "M4 20V10a6 6 0 0 1 6-6h1.5M20 13.5v.5a6 6 0 0 1-6 6H7.5M17 3v6M14 6h6",
    "send": "M12 19V5M6 11l6-6 6 6",
    "source": "M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4zM20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z",
    "external": "M14 4h6v6M20 4l-8 8M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4",
    "search": "M17 10.5a6.5 6.5 0 1 0-1.9 4.6M15.5 15.5 20 20",
    "globe": "M21 12a9 9 0 1 1-9-9a9 9 0 0 1 9 9M3.5 12h17M12 3c2.4 2.5 3.6 5.5 3.6 9s-1.2 6.5-3.6 9M12 3c-2.4 2.5-3.6 5.5-3.6 9s1.2 6.5 3.6 9",
    "menu": "M4 7h16M4 12h16M4 17h10",
    "close": "M6 6l12 12M18 6 6 18",
    "user": "M8.5 7.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0M5 20c.8-3.4 3.5-5.5 7-5.5s6.2 2.1 7 5.5",
    "settings": "M4 7h9M17 7h3M4 17h3M11 17h9M15 5v4M9 15v4",
    "share": "M12 3v12M7.5 7.5 12 3l4.5 4.5M8 11H6v9h12v-9h-2",
    "copy": "M9 9h9.5a1.5 1.5 0 0 1 1.5 1.5v8a1.5 1.5 0 0 1-1.5 1.5h-8A1.5 1.5 0 0 1 9 18.5zM15 6v-.5A1.5 1.5 0 0 0 13.5 4h-8A1.5 1.5 0 0 0 4 5.5v8A1.5 1.5 0 0 0 5.5 15H6",
    "check": "M4.5 12.5l5 5 10-10.5",
    "arrow-right": "M4 12h15M13 6l6 6-6 6",
    "info": "M21 12a9 9 0 1 1-4.5-7.8M12 11v5.5M12 7.5h.01",
    "warning": "M10.3 4.5 3.2 17a2 2 0 0 0 1.7 3h14.2a2 2 0 0 0 1.7-3L13.7 4.5a2 2 0 0 0-3.4 0zM12 9.5v4M12 16.5h.01",
    "history": "M4 12a8 8 0 1 0 2.3-5.7M4 4v4h4M12 8v4l3 2",
    "link": "M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7",
    "panel": "M9 4v16M20 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2",
}

AGENT_ICONS = {
    "eresidency": "residency",
    "moving": "moving",
    "tax": "tax",
    "services": "services",
    "digital": "digital",
    "explore": "discover",
}

CATEGORY_ICONS = {
    "business": "residency",
    "living": "moving",
    "digital": "digital",
    "discover": "discover",
}


def brand_head():
    """Favicons, PWA manifest, theme colour and social-share tags."""
    return (
        Link(rel="icon", href="/static/favicon.ico", sizes="48x48"),
        Link(rel="icon", href="/static/favicon.svg", type="image/svg+xml"),
        Link(rel="apple-touch-icon", href="/static/apple-touch-icon.png"),
        Link(rel="mask-icon", href="/static/safari-pinned-tab.svg", color=BLUE),
        Link(rel="manifest", href="/static/manifest.json"),
        Meta(name="theme-color", content=BLUE),
        Meta(name="description", content=SITE_DESCRIPTION),
        Meta(property="og:site_name", content=SITE_NAME),
        Meta(property="og:type", content="website"),
        Meta(property="og:title", content="eesti.chat · Ask anything about Estonia"),
        Meta(property="og:description", content=SITE_DESCRIPTION),
        Meta(property="og:image", content=OG_IMAGE),
        Meta(property="og:image:width", content="1200"),
        Meta(property="og:image:height", content="630"),
        Meta(property="og:image:alt", content="eesti.chat — Ask anything about Estonia."),
        Meta(name="twitter:card", content="summary_large_image"),
        Meta(name="twitter:image", content=OG_IMAGE),
    )


def icon_svg(name: str, size: int = 20, cls: str = "icon", stroke: float = 2) -> str:
    d = ICONS.get(name, ICONS["chat"])
    return (
        f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{d}"/></svg>'
    )


def Icon(name: str, size: int = 20, cls: str = "icon", stroke: float = 2):
    return NotStr(icon_svg(name, size, cls, stroke))


def mark_svg(size: int = 32, cls: str = "brand-mark", reversed_: bool = False) -> str:
    """The stone mark. Primary: blue stone, white e. Reversed: white stone, blue e."""
    stone, e = (WHITE, BLUE) if reversed_ else (BLUE, WHITE)
    e_d, e_w = (E_SMALL_D, 7.5) if size <= 20 else (E_D, 6)
    return (
        f'<svg class="{cls}" width="{size}" height="{size}" viewBox="6 6 52 52" '
        f'aria-hidden="true" focusable="false"><path d="{STONE_D}" fill="{stone}"/>'
        f'<path d="{e_d}" fill="none" stroke="{e}" stroke-width="{e_w}" stroke-linecap="round"/></svg>'
    )


def Mark(size: int = 32, cls: str = "brand-mark", reversed_: bool = False):
    return NotStr(mark_svg(size, cls, reversed_))


def Wordmark(href: str = "/", cls: str = "", mark_size: int = 28, tag=A, **kw):
    """Horizontal lockup: mark + lowercase wordmark with .chat in blue."""
    inner = (Mark(mark_size), Span("eesti", Span(".chat", cls="wordmark-suffix"), cls="wordmark-text"))
    if tag is A:
        return A(*inner, href=href, cls=f"wordmark {cls}".strip(), aria_label="eesti.chat", **kw)
    return tag(*inner, cls=f"wordmark {cls}".strip(), **kw)
