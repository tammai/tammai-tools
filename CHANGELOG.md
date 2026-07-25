# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.3.3] — 2026-07-25

### Changed
- Font request trimmed from `JetBrains+Mono:wght@400;500` to `wght@400` — nothing in either skill ever used mono at 500. Verified rather than assumed: all 65 mono-rendered elements in `workshop-slides/demo.html` compute to weight 400, no rule sets a weight on `.code-block`, `code` or their descendants, and in `soft-visuals` the two mono selectors (`.figure-note code`, `.shape-cell figcaption code`) inherit 400 — the four `font-weight` declarations there apply to `.kicker`, `h1`, `.figure-label` and `.figure-group-title`, none of which is a mono ancestor. Applied to all five files carrying the `<link>`: both skills' `assets/template.html`, both `demo.html`, and `soft-visuals/assets/gallery.html`
- Google Sans is untouched and still requested as a variable font over `wght 400..700`, so the 500/600/700 weights the decks use stay real instances rather than synthesised. Post-trim render is byte-for-byte equivalent: 258 Google Sans + 65 JetBrains Mono elements, same weight spread, all three faces loading

### Fixed
- **The 16:9 stage no longer loses its ratio when a deck loads inside a container that starts at zero size.** `scaleDeck()` ran once at load, hit its zero-viewport guard, fell back to `scale(1)` — and never recovered, because `resize` fires for the *window* only and nothing fires when a `display:none` container is revealed. A deck opened in a lazily-shown pane, an iframe embed or a background tab therefore rendered at a hard 1280×720 and was cropped by its container instead of fitting it. Reproduced in a 640×900 hidden-then-shown iframe: the deck stayed 1280×720 permanently; it now rescales to 640×360 on reveal. A `ResizeObserver` on `documentElement` drives the rescale, so the 1:1 fallback is now a hold rather than a dead end
- **The ratio is also locked in CSS**, via `#deck { transform: scale(var(--deck-scale)) }` with an `@supports`-gated `min(100vw / 1280px, 100dvh / 720px)`. The lock now holds on first paint (no one-frame flash at scale 1) and survives JS being stripped; `scaleDeck()` writes the same value inline for browsers without length-÷-length `calc()`. Both paths measured identical at 1200×480 → `scale(0.6667)` → 853×480
- `scaleDeck()` measures `documentElement.clientWidth/clientHeight` instead of `window.innerWidth/innerHeight` — the layout box the deck is actually centred in, scrollbars excluded, and on mobile the visible viewport rather than the large one
- `html, body` height is now `100dvh` (after a `100vh` fallback line). `vh` resolves against the large viewport, so on a phone with the address bar showing the body was taller than the visible area and the vertically centred deck sat partly under the browser chrome
- Added `visualViewport` resize handling, which pinch-zoom and mobile toolbar show/hide trigger without always firing a window `resize`
- Applied to `skills/workshop-slides/assets/template.html` **and** the copy inside `skills/workshop-slides/demo.html`. Verified unchanged for the PDF path: at the exporter's 1280×720 viewport both drivers compute exactly `1`, and `slides-to-pdf` resets `.slide` transforms, never `#deck`'s

## [0.3.2] — 2026-07-25

### Fixed
- **Numbered list markers no longer sit above the text they label.** `.list.numbered li::before` combined a smaller `font-size` with `line-height: inherit` — a unitless inherited line-height multiplies the *marker's own* font-size, so the digit's line box was 1.28rem inside a list item whose first line box is 2.13rem. Pinned to the top of that shorter box, the number rendered like a superscript, roughly 7px above the content baseline. `line-height: calc(1.5 / 0.6)` scales the marker's line box back to the item's `1.5em`, putting the two baselines within ~1px
- Double-digit markers no longer crowd the text. `width: auto` left-aligned the digits, so `10` and `11` grew rightward into the 26px text column while `1` sat alone; digits now hang right-aligned in a fixed 16px box with `font-variant-numeric: tabular-nums`, so the gap before the text is identical at every index
- Marker size is unchanged in appearance but now expressed in `em` (`0.6em` × the item's `1.42rem` ≈ the previous `0.85rem`), so a per-slide font-size override keeps the marker in proportion instead of leaving it at a fixed rem
- `.list.numbered` container padding dropped from `4px` to `0`, so numbered lists share the bulleted list's left edge
- Applied to `skills/workshop-slides/assets/template.html` **and** the CSS copy inside `skills/workshop-slides/demo.html`. The `1.5` and `0.6` constants are derived from `.list li` — a comment in the template records that changing that rule's line-height means updating them

## [0.3.1] — 2026-07-25

### Changed
- Plugin keywords widened to cover every `soft-visuals` type, not just the three that happened to be listed. `flowchart`, `architecture`, `org-chart`, `sequence-diagram`, `gantt`, `timeline`, `roadmap`, `kanban` and `user-journey` added; `diagram`, `wireframe`, `mindmap` and `svg` kept. Six of the nine visual types were previously unsearchable in the marketplace despite being fully implemented
- Plugin description now reads "…diagrams, wireframes, mindmaps, boards and timelines" — the board and timeline types (kanban, Gantt, journey map) were absent from it
- Both changes applied to `plugin.json` **and** `.claude-plugin/marketplace.json`, which carry the description and keyword list separately

## [0.3.0] — 2026-07-25

### Added
- **`soft-visuals` skill** — generates soft, flat, pastel visuals (the Whimsical-style look) as self-contained inline SVG in a single `.html` file with a dark/light toggle:
  - **Nine visual types**: flowchart, architecture diagram, wireframe (desktop + mobile), mindmap, org chart, sequence diagram, Gantt timeline, kanban board, user journey map
  - **18 shapes** — card, pill, diamond, cylinder, hexagon, parallelogram (+ flipped), trapezoid, triangle, circle, doc, note, annotation (pointer tail), bracket, actor, sequence actor, cloud, dashed group boundary
  - **22 wireframe components** — button (+ outline), text input, textarea, dropdown, checkbox, radio, toggle, slider, progress bar, tabs (horizontal/vertical/mobile), tooltip, modal overlay, stars, tag, video, map, image, avatar, text block — and **5 device frames** (plain, window, phone, tablet, watch)
  - Six connector styles — straight, rounded elbow, curve, dashed, labelled chip, hue-matched — plus annotation leaders (dashed, no arrowhead, since an arrow means flow and a note is not a step)
  - Layout rules encoded per type: Gantt bars positioned in **column units** rather than by eye; org-chart edges deliberately arrowless; sequence returns dashed and mint so round trips read without labels; journey-map *Feeling* row uses mood faces so the emotional dip is visible without reading
  - `assets/gallery.html` renders every shape, connector and layout as a copy-from reference, each `<svg>` self-contained with its own uniquely-named marker so single cells can be lifted out
  - `--dg-*` tokens are shared **verbatim** with the `workshop-slides` template, so a generated `<svg>` pastes into a slide deck with no edits
  - `.figure.narrow` / `.figure.medium` cap portrait and small visuals instead of stretching a phone mockup to full canvas width
  - `skills/soft-visuals/demo.html` — worked example and end-to-end check: all nine visual types describing one product so the types can be compared, each figure captioned with the prompt that produced it. Because it is built the way the skill prescribes, a defect in a `gallery.html` pattern surfaces here rather than in a user's output
  - Hue is treated as a cross-figure vocabulary, not per-figure decoration — the same system keeps its hue in every figure of a file, and two different kinds of thing (internal compute vs. a third-party `cloud`) must not collide on one hue
  - Connectors must **start** on their source's edge as well as stopping short of the target's; a line beginning in the gap beside its source reads as belonging to nothing. Shapes whose visible edge is not their bounding box are called out (a `cylinder` drawn from `y=309` with `ry=9` has its top at 300)
  - The one-accent rule is **at most** one, not exactly one: kanban boards (hue lives in the tags) and journey maps (hue is sentiment) carry their meaning entirely in hue and correctly take no accent at all
- **`slides-to-pdf` skill** — exports a `workshop-slides` HTML deck to a single multi-page PDF, one page per slide
- `skills/slides-to-pdf/assets/slides_to_pdf.py` — Playwright + pypdf converter:
  - Drives headless Chromium's print-to-PDF once per slide, since the deck stacks all slides at `inset: 0` and shows only the `.active` one — a plain `chromium --print-to-pdf` yields a single-page PDF
  - 1280 × 720 px pages (960 × 540 pt, 13.333 × 7.5 in) — true 16:9, matching PowerPoint/Keynote widescreen
  - Resolution-independent output: vector text (selectable and searchable), vector gradients and borders, raster images passed through at native resolution — sharp at any zoom without a 2× raster pass. `deviceScaleFactor` is set to 2 but measurably does not alter the PDF (identical output at 1×/2×/3×)
  - `printBackground: true` + `print-color-adjust: exact` — dark background, radial gradients, accent colors, callout tints, and code-block fills all survive
  - `emulateMedia({ media: 'screen' })` so the deck's screen styling is what gets printed
  - Waits on `document.fonts.ready` for Google Fonts, warning and falling back rather than failing when offline
  - Hides interactive chrome by default — `#navigator` plus any `<button>` outside `#deck`, which covers the theme and fullscreen toggles
  - Merges pages with pypdf, adding a PDF bookmark per slide from its `.slide-title`
  - Measures each slide against the page box and warns when content was silently cropped — slides are pinned inside an `overflow: hidden` body, so overflow is cut off rather than spilling onto a second page
  - Flags: `--output`, `--width`, `--height`, `--device-scale`, `--keep-ui`, `--theme dark|light|as-is`, `--timeout`
- **Soft, flat diagram style** — `--dg-*` tokens plus a `.diagram` class for inline-SVG architecture/flow diagrams: rounded cards with translucent hue fills and matching borders, title + muted caption per card, and neutral rounded elbow connectors with arrow markers. Hue fills are translucent so a single value reads as a muted tint on the dark page and a pastel on the light one. Deliberately **shadowless**: `feDropShadow` was measured to rasterise the filtered region into a bitmap in the PDF export, and a faked offset-rect shadow peeked out under the card border in light mode. Token set extended with `rose`, `cyan`, `--dg-border` and `--dg-surface` so it matches `soft-visuals` exactly
- New template components: `.cmp-table` (criterion comparison table), `.tag-block` / `.tag-main` / `.tag-sub` (stacked value+label chips), `.callout.compact`, `.code-line` / `.code-line.blank` (code blocks are not `<pre>`, so each line needs its own element or the snippet reflows into a paragraph), `.list li .src` (inline source citation)
- Inline `<code>` now uses the mono family explicitly instead of the browser default
- `<em>` renders accent-colored and non-italic inside `.list` items and `.callout` too, not just `.text` — one consistent rule wherever authors use it

### Changed
- **`workshop-slides` template overhauled** — brought in line with the newer deck structure that had drifted ahead of this repo. BigIn colors (orange `#f97316` / slate `#020617`) are unchanged:
  - Dark/light mode toggle (button or **T**), persisted in `localStorage` as `workshop-deck-theme`; light mode reverses the slate scale and keeps the accent
  - Fullscreen toggle (button or **F**)
  - Fixed 1280×720 stage that scales to any viewport, so decks render identically on laptop, projector, and phone
  - Swipe navigation for phones and tablets
  - `@media print` block for one-slide-per-page Cmd-P export
  - `text-wrap: balance` on titles, `pretty` + `62ch` cap on subtitles
- **Typography simplified** — Google Sans for headings *and* body; JetBrains Mono reserved for code only (`.code-block` plus inline `<code>`). Space Grotesk dropped. Google Sans is requested as a variable font over `wght 400..700` rather than a fixed `400;500;700` list, because the deck uses weight 600 in several places and it was previously being synthesised
- **`demo.html` rebuilt as a 15-slide reference deck** — every slide carries an HTML comment naming the components and layout it demonstrates, so generation can copy a working pattern instead of inventing markup. Covers cover, section dividers, 1/2/3-column bodies, bullet + numbered lists, prose, callouts (full + compact), bash and yaml code blocks (including two side by side), comparison table, stat blocks, tag blocks, tags, an inline-SVG diagram, source citations, and spacers
- List bullets are absolutely positioned instead of flex-centered — on a wrapped multi-line item the bullet aligns to the first line rather than floating to the vertical middle
- `.stat-number` reduced from 7.5rem to 4.2rem with `nowrap`, so multi-character stats like `6 min` no longer wrap

### Fixed
- Deck scaling guarded against a zero or NaN viewport (hidden iframe, snapshot renderer, or a call before first layout), which previously computed `scale(0)` and rendered a completely blank deck

## [0.2.2] — 2026-06-22

### Changed
- Custom preset flow now presents the full Tailwind accent palette (17 colors, 500-shade) and full Tailwind neutral palette (5 scales, 950-shade) via `AskUserQuestion` when collecting accent and background colors

## [0.2.1] — 2026-06-22

### Fixed
- `marketplace.json` schema corrected to match Claude Cowork format — replaced invented fields (`categories`, `tags`, `pricing`, `icon`) with the proper structure (`name`, `description`, `owner`, `plugins[]`)

## [0.2.0] — 2026-06-22

### Added
- `.claude-plugin/marketplace.json` — Claude Cowork marketplace metadata: categories, tags, pricing, icon, license, repository, and homepage

### Changed
- Navigator layout changed from vertical (column, 80 px wide) to horizontal (row, 48 px tall, width auto)
- Navigator chevron icons updated from up/down to left/right to match horizontal orientation

## [0.1.0] — 2026-06-22

### Added
- `workshop-slides` skill — generates self-contained HTML slide decks from a topic or outline
- Base HTML template (`assets/template.html`) with BigIn design system defaults:
  - Dark slate background (`#020617`) + orange accent (`#f97316`)
  - Google Sans / Space Grotesk / JetBrains Mono via Google Fonts
  - Slide variants: cover, content, section-divider
  - Body layouts: 1, 2, and 3-column
  - Content components: bullet lists, numbered lists, callouts, code blocks, stat blocks, tags, spacer
  - Keyboard navigation (← → Space PageUp PageDown)
  - Horizontal bottom-right navigator with page indicator
  - BigIn watermark (swappable)
  - Ambient radial-gradient background decoration
- Custom branding presets saved to `~/.workshop-slides-preset.json`
- Demo deck (`demo.html`) showcasing all slide components and layouts
- Plugin metadata (`.claude-plugin/plugin.json`) — name `tammai-tools`, version `0.1.0`
