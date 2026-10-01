"""Inline SVG flags used by the language switchers."""

FLAG_SVGS: dict[str, str] = {
    "en": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-en-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-en-clip)">'
        '<rect width="24" height="18" fill="#012169"/>'
        '<path d="M0 0L24 18M24 0L0 18" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="butt"/>'
        '<path d="M0 0L24 18M24 0L0 18" fill="none" stroke="#C8102E" stroke-width="1.4" stroke-linecap="butt"/>'
        '<path d="M0 9H24M12 0V18" fill="none" stroke="#FFFFFF" stroke-width="6" stroke-linecap="butt"/>'
        '<path d="M0 9H24M12 0V18" fill="none" stroke="#C8102E" stroke-width="3" stroke-linecap="butt"/>'
        '</g></svg>'
    ),
    "et": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-et-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-et-clip)">'
        '<rect width="24" height="6" fill="#0072CE"/>'
        '<rect y="6" width="24" height="6" fill="#000000"/>'
        '<rect y="12" width="24" height="6" fill="#FFFFFF"/>'
        '</g></svg>'
    ),
    "ru": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-ru-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-ru-clip)">'
        '<rect width="24" height="6" fill="#FFFFFF"/>'
        '<rect y="6" width="24" height="6" fill="#0039A6"/>'
        '<rect y="12" width="24" height="6" fill="#D52B1E"/>'
        '</g></svg>'
    ),
    "de": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-de-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-de-clip)">'
        '<rect width="24" height="6" fill="#000000"/>'
        '<rect y="6" width="24" height="6" fill="#DD0000"/>'
        '<rect y="12" width="24" height="6" fill="#FFCE00"/>'
        '</g></svg>'
    ),
    "fr": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-fr-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-fr-clip)">'
        '<rect width="8" height="18" fill="#0055A4"/>'
        '<rect x="8" width="8" height="18" fill="#FFFFFF"/>'
        '<rect x="16" width="8" height="18" fill="#EF4135"/>'
        '</g></svg>'
    ),
    "sv": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-sv-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-sv-clip)">'
        '<rect width="24" height="18" fill="#006AA7"/>'
        '<rect x="7" width="4" height="18" fill="#FECC02"/>'
        '<rect y="7.25" width="24" height="3.5" fill="#FECC02"/>'
        '</g></svg>'
    ),
    "lv": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-lv-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-lv-clip)">'
        '<rect width="24" height="18" fill="#9E3039"/>'
        '<rect y="7" width="24" height="4" fill="#FFFFFF"/>'
        '</g></svg>'
    ),
    "fi": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-fi-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-fi-clip)">'
        '<rect width="24" height="18" fill="#FFFFFF"/>'
        '<rect x="7" width="4.5" height="18" fill="#002F6C"/>'
        '<rect y="7.25" width="24" height="3.5" fill="#002F6C"/>'
        '</g></svg>'
    ),
    "lt": (
        '<svg width="20" height="15" viewBox="0 0 24 18" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" '
        'focusable="false">'
        '<defs><clipPath id="flag-lt-clip"><rect width="24" height="18" rx="2.5"/></clipPath></defs>'
        '<g clip-path="url(#flag-lt-clip)">'
        '<rect width="24" height="6" fill="#FDB913"/>'
        '<rect y="6" width="24" height="6" fill="#008A44"/>'
        '<rect y="12" width="24" height="6" fill="#C1272D"/>'
        '</g></svg>'
    ),
}


def flag_svg(code: str) -> str:
    """Return the inline SVG for a language code, if one is defined."""
    return FLAG_SVGS.get(code, "")
