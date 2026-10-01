# eesti.chat visual system

## Direction

An official, editorial state-portal interface: precise typography, thin rules, confident blue, and generous white space. The home page opens with one dark AI-first hero; all other public surfaces remain light. The /app workspace is operational and quiet, with the same blue system carried through active states and focus.

## Tokens

- `--blue`: `#0030DE`
- `--blue-deep`: `#000087`
- `--blue-ice`: `#CEE2FD`
- `--blue-bright`: `#0062F5` (focus, hover)
- `--spark`: `#00C3FF` (fills only)
- `--ink`: `#0F172A`
- `--ink-2`: `#3D4B5E`
- `--ink-3`: `#64748B`
- `--line`: `#CBD5E1`
- `--bg-alt`: `#F1F5F9`
- surfaces: `#FFFFFF`

## Type

Headlines use the local Aino headline face. Body text uses local Aino regular/bold/italic faces. No external font requests.

## Shape and depth

Cards use 6px corners, controls use 4px corners, and chips use 3px corners. Borders are 1px. Shadows are limited to `shadow-sm`-scale utility for small overlays only.

## Responsive behavior

Public pages collapse to a single column below 768px. The chat workspace preserves its existing fixed mobile drawers, overlays, and z-index hierarchy.

## Logo & icons

The mark is a talking stone: an Estonian-blue block with 16-unit radii and one square corner (bottom-left), holding a geometric white e. The header, footer and workspace use the horizontal lockup (`utils/brand.py` `Wordmark()`), and assistant replies use the mark as their avatar. Icons are a 24 px, 2 px-stroke outline set (`Icon(name)`), and most leave one small opening in the outline. Chat bubbles are 16 px stones whose square corner points at the speaker: ice for the user, white with a border for the assistant. The full kit and its rules are in `static/brand/README.md`.
