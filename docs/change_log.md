# Change Log

## v1.0.3 — 2026-10-01

**Add visitestonia.com to the official links in the chat sidebar.**

- New sidebar link: visitestonia.com (official tourism), alongside eesti.ee, eesti.ai,
  e-resident.gov.ee, rik.ee, emta.ee, ria.ee and err.ee.

## v1.0.2 — 2026-10-01

**Full UI localization for all nine languages — German, French, Swedish, Russian, Finnish, Latvian and Lithuanian now render natively (no more English fallback).**

- Translated the entire UI catalog (nav, hero, features, how-it-works, footer, chat,
  suggestions, the six assistant names/descriptions and four categories) into de, fr, sv,
  ru, fi, lv, lt — alongside the existing en and et.
- Translations now live in per-language `locales/<lang>.json` files, merged into the catalog
  at import by `_merge_locales()`; en + et remain inline. Easy to extend/edit going forward.
- Combined with IP geolocation (v1.0.1): a visitor from Sweden now sees Swedish, Germany
  German, etc., and the language switcher shows fully localized pages.

## v1.0.1 — 2026-10-01

**IP-based language defaulting — Estonian from an Estonian IP, each language from its own country, English everywhere else.**

- New `utils/geo.py`: layered IP→country detection (CDN country headers → ipapi.co / ip-api.com →
  emergency EE prefixes), stdlib-only, cached per IP, skips private IPs, short timeout, never blocks render.
- Country→language map: EE→et, RU→ru, DE/AT→de, FR→fr, SE→sv, LV→lv, FI→fi, LT→lt; anything else → English.
- A beforeware now sets the session language from the visitor's IP on first visit (a manual language
  choice always takes precedence). Previously the IP detection code never actually ran.

## v1.0.0 — 2026-10-01

**First versioned release of eesti.chat — the AI front door to Estonia.**

- AI chat portal with six specialist assistants (e-Residency & company, living & moving,
  taxes & finance, digital ID & e-services, public services, discover Estonia). Answers are
  grounded in official Estonian sources via live search and always cite their links, in the
  user's selected language.
- Access: 5 free questions, then Google SSO or email sign-up. Chat history persists for both
  guests and signed-in users (and recovers gracefully from stale sessions).
- Context-sensitive follow-up suggestion chips under the composer — starters by default and
  tailored follow-ups after each answer, so the user is never stuck.
- Working indicator rotates playful "thinking" synonyms per language; underlying tool calls
  (e.g. web search) are never surfaced in the UI.
- Official links in the sidebar: eesti.ee, eesti.ai, e-resident.gov.ee, rik.ee, emta.ee,
  ria.ee, err.ee.
- "Powered by Predictive Labs OÜ" and the app version shown near sign-in (version links here).
- White / black / Estonia-blue design in the Aino typeface; English + Estonian; live at
  https://eesti.chat. Inspired by america.gov and the U.S. State Department's ShareAmerica.
