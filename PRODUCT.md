# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

People in Estonia and people planning to move, work, study, start a company, or use public services in Estonia. They use the portal when they need a plain-language answer and a direct path to authoritative Estonian sources.

## Product Purpose

eesti.chat is a conversational front door to Estonian public services. It routes questions to specialist assistants, searches official sources, and returns a clear answer with links so people can verify the guidance.

## Positioning

The product combines a single conversational entry point with specialist routing and live grounding in official Estonian domains.

## Operating Context

The public site introduces the service and its topics. The /app workspace supports asking questions, reviewing a streamed answer, switching specialist assistants, opening artifacts, and returning to saved sessions.

## Capabilities and Constraints

- FastHTML renders the public pages and chat workspace.
- Specialist LangGraph agents cover e-Residency, moving, taxes, digital identity, services, and discovery.
- Chat responses use official Estonian sources and expose source links.
- English and Estonian are supported through the existing language switcher.
- Existing routes, SSE streaming, sharing, authentication, i18n strings, and mobile pane behavior must remain functional.

## Brand Commitments

The name is eesti.chat. The visual direction follows the user-supplied Brand Estonia-derived palette and Aino type family. The wordmark stays lowercase with the `.chat` suffix in Estonian blue, paired with the talking-stone mark. The identity is original. It does not use or imitate the official Brand Estonia logo system.

## Evidence on Hand

Existing copy and specialist-agent definitions in the repository are the source of truth. No testimonials, customer claims, or official-government affiliation should be fabricated.

## Product Principles

- Make public-service guidance feel approachable without weakening trust.
- Put the user's question at the center of the experience.
- Keep source verification visible and easy.
- Use specialist routing to reduce navigation overhead.

## Accessibility & Inclusion

The web experience must render in light mode, maintain high text contrast, keep visible keyboard focus, and remain usable at 375px wide. Reduced-motion preferences should be respected.
