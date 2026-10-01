# Change Log

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
