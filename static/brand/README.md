# eesti.chat brand kit

The idea is **talking stones**: solid, rounded blocks that carry a conversation. The mark is one stone in Estonian blue with a single square corner. That corner always points at whoever is speaking. A geometric **e**, for eesti, sits inside.

eesti.chat is an independent service. The kit borrows a few things from Brand Estonia (the palette names and the Aino typeface) but it is not part of Brand Estonia or the state's logo system.

## Files

| File | Use |
| --- | --- |
| `logo.svg` | Horizontal lockup on white or light grounds (default) |
| `logo-reversed.svg` | On Estonian blue |
| `logo-ink.svg` | On ink / dark grounds |
| `mark.svg`, `mark-reversed.svg`, `mark-mono.svg` | Mark only: avatars, small slots |
| `app-icon.svg`, `app-icon-maskable.svg` | Sources for the PNG app icons |
| `icons/*.svg`, `icons/sprite.svg` | 24 px icon set (`<use href="sprite.svg#i-name">`) |
| `../favicon.svg`, `../favicon.ico` | Browser tab (heavy-e variant, dark-mode aware) |
| `../apple-touch-icon.png`, `../icon-192.png`, `../icon-512.png`, `../icon-maskable-512.png` | iOS / PWA |
| `../og-image.png` | 1200 × 630 social share image |

In Python templates use `utils/brand.py`: `Wordmark()`, `Mark()`, `Icon(name)`, `brand_head()`.

## Logo rules

- Clear space is half the height of the mark on every side.
- Minimum sizes: mark 16 px, horizontal lockup 96 px wide.
- Colourways:
  - Primary: blue stone, white e, ink `eesti`, blue `.chat`.
  - On blue or ink grounds: white stone, white `eesti`, and `.chat` in Pärnu ice.
- Don't round the speaker corner, fill the mark with flag stripes or other colours, stretch it, or retype the wordmark. It stays lowercase, in Aino Bold at −3.5 % tracking.

## Colour

| Name | Hex | Token |
| --- | --- | --- |
| Estonian blue | `#0030DE` | `--blue` |
| Liivi deep | `#000087` | `--blue-deep` |
| Paldski blue | `#0062F5` | `--blue-bright` (focus, hover) |
| Pärnu ice | `#CEE2FD` | `--blue-ice` (user bubbles, halos) |
| Narva spark | `#00C3FF` | `--spark` (fills only, never text on white) |
| Mustkivi ink | `#0F172A` | `--ink` |
| Majakivi | `#3D4B5E` | `--ink-2` |
| Kabelikivi | `#64748B` | `--ink-3` |
| Hellamaa | `#CBD5E1` | `--line` |
| Pahkla | `#F1F5F9` | `--bg-alt` |

## Type

- Aino Headline: display only, 32 px and up.
- Aino Regular and Bold: everything else.
- Fallback stack: `Aino, Verdana, system-ui, sans-serif`.

## Icons

- 24 px grid, 2 px stroke, round caps and joins, outline only.
- Most icons leave one small opening in the outline.
- Colour with `currentColor`.

## Shapes

- Bubbles and hero stones use a 16 px radius with one square corner:
  - bottom-left when eesti.chat is speaking
  - bottom-right when the user is speaking
- Cards use 6 px, controls 4 px, and pills are fully round.
- Use flat fills only: no gradients, glows or shadows on stones.
