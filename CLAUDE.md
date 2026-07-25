# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Cowork plugin** (`tammai-tools`) by Tam Mai — a collection of skills (slash commands) for workshop and presentation tooling, built on the BigIn design system. The plugin is distributed as a `.plugin` file (git-ignored) bundled from this directory.

There is no build system, package manager, or test suite. All assets are plain files consumed directly by Claude Code at runtime.

## Structure

```
.claude-plugin/plugin.json     — plugin metadata (name, version, description)
.claude-plugin/marketplace.json — Claude Cowork marketplace config (categories, tags, pricing, icon)
skills/
  workshop-slides/
    SKILL.md                   — the skill's instruction document (Claude reads this at invocation)
    assets/template.html       — the base HTML template for generated slide decks
  slides-to-pdf/
    SKILL.md                   — the skill's instruction document
    assets/slides_to_pdf.py    — Playwright + pypdf converter (deck → single PDF)
  soft-visuals/
    SKILL.md                   — the skill's instruction document
    assets/template.html       — viewer shell (tokens + dark/light toggle)
    assets/gallery.html        — reference: every shape, connector and layout
    demo.html                  — worked example: all nine types on one product,
                                 each captioned with the prompt that produced it
```

Skills are discovered automatically by Claude Cowork from the `skills/` directory. Each skill folder must contain a `SKILL.md` with YAML frontmatter (`name`, `description`, `triggers`).

## workshop-slides skill

The skill generates self-contained HTML slide decks. Key design constraints:

- **Output is a single `.html` file** — no server, no JS bundler, no external runtime dependencies at view-time (fonts load from Google Fonts CDN when online).
- **Template is read at generation time** — the skill reads `assets/template.html`, replaces only the `<div id="deck">` contents, and saves the result. The `<head>`, `#bg`, `#watermark`, `#navigator`, and `<script>` blocks are preserved byte-for-byte.
- **Branding via CSS variables** — the `BRAND CONFIGURATION` `:root` block in the template controls accent color, background, and fonts. Custom presets are saved to `~/.workshop-slides-preset.json` and injected at generation time.
- **BigIn defaults**: dark slate (`#020617`) + orange accent (`#f97316`), **Google Sans for headings *and* body**, **JetBrains Mono for code only** (`--brand-font-code` is referenced by just `.code-block` and inline `code`). Google Sans is requested as a variable font over `wght 400..700` because the deck uses 400/500/600/700 — a fixed `wght@400;500;700` list leaves 600 to be synthesised.

### Slide HTML rules

- First slide: `class="slide slide--cover active"` — no `slide-body`
- Section dividers: `class="slide slide--section"` — no `slide-body`
- All other slides: `class="slide"`
- Slide numbers are zero-padded two digits: `01`, `02`, …
- Only one slide may carry the `active` class

### Template runtime features

The template is a **fixed 1280×720 stage** scaled to the viewport by `scaleDeck()`, not a fluid layout. Consequences worth knowing before editing it:

- Slides are exactly 720 px tall with `overflow: hidden`. Overrunning content is **silently cropped**, never scrolled or paginated. `slides-to-pdf` detects and reports this; the browser does not.
- The 16:9 lock is written **twice, on purpose**: `#deck { transform: scale(var(--deck-scale)) }` with the value set by an `@supports`-gated pure-CSS `min(100vw / 1280px, 100dvh / 720px)`, *and* by `scaleDeck()` writing the same number to `--deck-scale` inline. CSS holds the ratio on first paint and with JS stripped; JS covers browsers without length-÷-length `calc()` and is what makes the zero-viewport guard possible. Both must stay in agreement — change one, change the other.
- `scaleDeck()` guards against a zero/NaN viewport — without it, a hidden iframe or snapshot renderer computes `scale(0)` and the deck renders blank. Don't remove the guard. It holds at 1:1 rather than scaling, which is only safe *because* a `ResizeObserver` on `documentElement` re-runs it: a `resize` event fires for the window only, so a deck revealed from `display:none` (lazily-shown pane, iframe embed) would otherwise stay stuck at a hard 1280×720 and get cropped by its container. Don't drop the observer to "simplify" back to `resize`.
- Measure `documentElement.clientWidth/clientHeight`, **not** `window.innerWidth/innerHeight` — the former is the CSS layout box the deck is centred in (scrollbars excluded) and tracks the mobile visible viewport. For the same reason `html, body` height is `100dvh` (with a `100vh` fallback line first): `vh` is the *large* viewport, so on a phone with the address bar showing, the body is taller than the visible area and the centred deck sits under the chrome.
- Dark/light mode keys off `[data-theme]` on `<html>`, seeded from `localStorage` (`workshop-deck-theme`), defaulting to dark. Light mode reverses the `--slate-*` scale, so **slide markup must never hardcode hex colors** — use `var(--brand-accent)` and `--slate-*` or the deck breaks in light mode.
- Interactive chrome lives outside `#deck` (`#navigator`, `#themeToggle`, `#fullscreenToggle`); slide content contains no `<button>`. `slides-to-pdf` relies on that split to strip chrome — keep new controls outside `#deck`.
- The `@media print` block gives a dependency-free Cmd-P export. `slides-to-pdf` deliberately bypasses it via `emulateMedia('screen')`, so the two paths are independent — a change to one does not affect the other.

### Syntax highlight classes (inside `.code-block`)

`.kw` = keyword (orange), `.fn` = function name (light), `.str` = string (muted), `.cmt` = comment (dim)

`.code-block` is **not** a `<pre>` — every line needs its own `.code-line` element (`.code-line.blank` for a gap), or raw newlines collapse and the snippet reflows into a single paragraph.

## slides-to-pdf skill

Exports a generated deck to a single PDF, one page per slide. `assets/slides_to_pdf.py` is the only skill asset in this repo that is executable code with third-party dependencies (`playwright`, `pypdf`) — everything else is static.

The constraint that shapes the whole design: the deck stacks every `.slide` at `position: absolute; inset: 0` with `opacity: 0` and reveals only `.active`. A plain `chromium --headless --print-to-pdf` therefore yields a **one-page** PDF of whichever slide is active. The script instead loops in-browser — tagging one slide visible at a time via an injected stylesheet, calling `page.pdf()` per slide, then merging with pypdf.

Three non-obvious details that will silently break the output if changed:

- **`emulateMedia(media='screen')` is required.** `page.pdf()` emulates `print` media by default, and the deck has no `@media print` rules — the dark theme would be discarded.
- **`printBackground=True` plus `print-color-adjust: exact`** are both needed to keep the dark background, radial gradients, callout tints, and code-block fills.
- **Overrides are injected at runtime** with `add_style_tag`; the source deck is never modified and stays usable as an interactive presentation.

**Chrome hiding is deliberately generic.** Newer deck templates keep adding fixed controls — the `workshop-slides` template in this repo has only `#navigator`, but decks in the wild also carry `#themeToggle` and `#fullscreenToggle`. Rather than chase a hardcoded id list, the CSS hides `#navigator` plus `button:not(#deck button)`; slide content contains no buttons, every control does. Add new ids only if a control is not a `<button>`.

Decks with a dark/light toggle key off `[data-theme]` on `<html>`, seeded from `localStorage`, so a fresh headless profile gets the deck's own default (dark). `--theme dark|light` overrides it after load; `as-is` (the default) leaves it alone.

Defaults: 1280 × 720 px pages (→ 960 × 540 pt, true 16:9), `deviceScaleFactor: 2`, navigator hidden.

**`--device-scale` provably does nothing to the PDF** — don't "fix" it or build features on it. Print-to-PDF output is resolution-independent already: text is emitted as Type3 fonts (vector glyph procedures, still selectable and searchable), gradients and borders are vector, and raster images pass through at native resolution. Measured, not assumed: the same deck at `--device-scale 1`, `2`, and `3` yields byte-identical 460 KB files; a 240×160 PNG watermark embeds at 240×160 at every setting; `<img srcset="… 1x, … 2x">` picks the 2× variant even at DPR 1. The flag is retained only because it sets the browser DPR for decks whose JS branches on `devicePixelRatio`.

## soft-visuals skill

Generates nine visual types as inline SVG in a flat pastel style — flowchart, architecture, wireframe, mindmap, org chart, sequence diagram, Gantt timeline, kanban board, user journey map. Output is a single `.html` viewer.

The shape/component vocabulary was derived by exploring Whimsical's own tool palettes, so the taxonomy deliberately mirrors a tool people already know. Star and Cross exist there but were scoped out here as decorative.

**The `--dg-*` token block is duplicated verbatim in `soft-visuals/assets/template.html` and `workshop-slides/assets/template.html`.** That duplication is deliberate — it is what lets a generated `<svg>` be pasted into a slide deck untouched. If you add or rename a token, change **both** files; a token one side doesn't define renders as no fill, silently, with no error.

Constraints that are load-bearing, not stylistic preference:

- **No shadows, and never `filter:`/`feDropShadow`.** Measured: a filtered region makes Chrome's print-to-PDF rasterise that area into a bitmap, so a deck containing the diagram stops being pure vector. A faked offset-rect shadow also peeks out from under a shape's own border in light mode. The style is flat — leave it flat.
- **Translucent hue fills** (`color-mix(… 16%, transparent)`), not per-theme solids. One value reads correctly over both the dark and the light page.
- **Connectors are drawn before shapes**, start on the source's edge, and stop ~6px short of the target's. Arrowheads landing inside shapes is the most common way these look sloppy; a line that *begins* in the gap beside its source is the second, because it reads as belonging to nothing. Derive both ends from real geometry, and watch the shapes whose edge is not their bounding box — a `cylinder` drawn from `y=309` with `ry=9` has its visible top at 300.
- **Marker ids must be unique per document.** Multiple `<svg>` blocks in one file each need their own suffixed marker id; duplicates are invalid HTML and all references resolve to the first.
- Content outside a `viewBox` is silently invisible — verify with `getBBox()` against `viewBox.baseVal`.

`assets/gallery.html` is generated, not hand-maintained in place; it is the reference the skill tells Claude to copy from, so keep its coverage complete when adding a shape. **A geometry or hue mistake in the gallery is not a cosmetic bug — it propagates into every visual generated from that pattern**, since SKILL.md explicitly tells Claude to copy rather than author. `demo.html` is the end-to-end check on that: all nine types built the way the skill prescribes, so a defect in a gallery pattern shows up there rather than in a user's output.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with the required YAML frontmatter.
2. Add any static assets under `skills/<skill-name>/assets/`.
3. Reference assets by relative path from `SKILL.md` (e.g. `assets/template.html`).
