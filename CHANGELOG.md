# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.0] — 2026-07-25

### Added
- **`slides-to-pdf` self-hosts the deck's fonts, so the PDF no longer depends on the font CDN.** The deck keeps its Google Fonts `<link>` — correct for an interactive page, small file, shared cache — but a PDF is a *snapshot* of whatever rendered, so a blocked or slow CDN is baked in permanently and silently, with nothing to re-try later. This is not hypothetical: Claude Cowork blocks `fonts.googleapis.com` outright, and a deck exported there produced a PDF in fallback fonts. Before rendering, the script now reads the families off the live page (`--brand-font-*`, so presets are covered too), fetches the woff2 from npm's `@fontsource*` packages — npm stays reachable where Google's CDN does not — and injects them as `data:` URI `@font-face` rules via `add_style_tag`. The deck itself is never modified, the same contract as every other override there. On by default; `--no-embed-fonts` restores the old behaviour, `--font-subsets` and `--font-dir` cover the rest
- Measured against the online-CDN render, with the deck's font host pointed at an unresolvable TLD. A 21-slide deck (Google Sans + JetBrains Mono): cover page **0.00%** of pixels differ with embedding vs **3.35%** without; a code-heavy slide **1.28%** vs **7.36%**. The residual 1.28% was checked rather than assumed — cropping the differing band from both renders shows identical letterforms, advances and line breaks, i.e. sub-pixel antialiasing between Fontsource's variable build and Google's, not a substitution. A 15-slide deck measured 0.19% vs 2.64% on the same test
- Default subsets are `latin,latin-ext,vietnamese`. Vietnamese is load-bearing rather than generous: without it the *diacritics alone* fall out of the embedded face and the browser substitutes a system font for those glyphs only, so a slide renders in two typefaces at once — harder to notice than a wholesale fallback
- Graceful degradation, both paths tested with `npm` stripped from `PATH`: without `--font-dir` it warns and still writes a valid PDF using whatever the page loaded; with `--font-dir` it embeds from pre-fetched `npm pack` tarballs and produces a size-identical result to the npm path. It never fails an export over fonts

### Changed
- **Code font is now Fira Code, replacing JetBrains Mono**, in the BigIn default and across both skills — `workshop-slides/assets/template.html`, `soft-visuals/assets/template.html`, `assets/gallery.html`, both `demo.html`, plus `README.md` and `CLAUDE.md`. Verified by rendering: `Fira Code 400` and `Google Sans 400 700` both load and `.code-block` / `code` compute to `"Fira Code", monospace`. Google Sans is untouched and still requested as a variable font over `wght 400..700`. Generated decks are static files, so existing ones keep whatever they were built with
- The custom-preset flow now suggests **Google Sans** as the first heading font instead of Inter, with the example preset JSON and its `googleFontsUrl` updated to the variable-font request form

### Fixed
- **Build scratch no longer lands in the user's deliverable folder.** `workshop-slides/SKILL.md` gave the build command with a bare relative fragment path, and on a sandboxed host the working directory *is* the user-visible `outputs/` folder — an observed Cowork run left `slides-fragment.html` and four `pgN.png` verification rasters sitting beside the deck, with the sandbox unable to delete them. The fragment now goes to `$TMPDIR`, with an explicit rule that scaffolding (fragments, page rasters, thumbnails) never enters the output folder and is deleted once the deck verifies
- **`slides-to-pdf` checks for an existing browser before attempting the Playwright CDN download.** Step 2 previously instructed `playwright install chromium` first and documented the npm fallback only afterwards, so on a host that blocks `playwright.azureedge.net` the first move was a guaranteed multi-minute stall on a ~130 MB download that cannot succeed — the probe answers the same question immediately
- A missing `npm` reported as `no Fontsource package for 'Google Sans'`, once per family, which reads as a misspelled font name and sends the reader off checking spellings. It now names npm as the cause and gives both ways forward
- `workshop-slides/SKILL.md` no longer implies a preset saved to `~/.workshop-slides-preset.json` always persists. Where `$HOME` is not writable or not retained, the save silently buys nothing; the skill now says to report that rather than quietly dropping the JSON into the output folder, which is what a Cowork run did

## [0.3.5] — 2026-07-25

### Added
- **`slides-to-pdf` now reports column overlap, a failure its clipping check structurally cannot see.** `.col` is `overflow: visible`, so a child wider than its column paints over its neighbour without changing the slide's `scrollWidth` — the existing measurement is taken on the slide, so it returns 0 and stays silent. Measured case: an `<svg width="700" height="660">` in a 568px column reaches **132px into the next column**, with `elementFromPoint` at that edge returning the neighbouring `<p>`. Reported per slide as `← OVERLAP (svg 132px past its column)` plus a summary naming the likely fix. Absolutely-positioned and hidden children are skipped, with 2px of slack for subpixel rounding; verified silent across all 15 slides of the reference deck and firing on exactly the one bad variant of four
- **`build.py` warns when a preset watermark points off-machine** — a remote URL renders as a broken-image box offline or once the URL rots, and a local path breaks as soon as the `.html` travels without it; both defeat the deck's self-contained promise. Found by hitting it: a test preset pointing at a non-existent `https://example.com/logo.svg` produced a broken-image box in the deck *and* the exported PDF, silently. Warns rather than errors, since `SKILL.md` does offer "Remote URL" as an option. Verified across five cases — remote URL and local path warn; `data:` URI, inline `<svg>` and watermark removal stay silent

### Fixed
- **Corrected the documented purpose of `class="diagram"`.** It was described as what stops portrait diagrams overflowing a slide. Measured against four variants, that is only true for an `<svg>` carrying explicit `width`/`height` attributes: there the class pulls a 700px SVG back to 536px and prevents a 132px overlap. For a `viewBox`-only SVG the column's flex layout already caps it and the class changes nothing measurable (536 × 435 either way). `CLAUDE.md` and `soft-visuals/SKILL.md` now say which case it is load-bearing for, so the rule does not read as redundant and get "simplified" away

## [0.3.4] — 2026-07-25

### Added
- **`workshop-slides/assets/build.py`** — assembles a deck from the template plus a slide fragment, so SKILL.md's "keep the `<head>` unchanged" rule is enforced by construction instead of by instruction. Motivated by measured drift, not theory: a deck generated on 2026-07-24 from an unmodified template had silently dropped all 18 `--dg-*` diagram tokens and the `.diagram` sizing rule while keeping the favicon, print block and script — so `soft-visuals` SVGs pasted into it would render with no fill and portrait diagrams would overflow the slide, with no error in either case. Standard library only, nothing to install. Verified: head and tail bytes identical to the template, 117 CSS rule pairs and 499 declarations preserved
- `build.py` also applies presets mechanically — substituting the individual `--brand-*` declarations, the Google Fonts `href` and the watermark block (or removing it for `"watermark": ""`), which were previously hand edits to the head, the exact place drift happens. It refuses to write when no slide carries `active` or more than one does, and warns without blocking on numbering that doesn't match slide position, hardcoded hex colors, a `<button>` in slide content, and a `.code-block` with no `.code-line` children
- **Browser-discovery fallback for `slides-to-pdf`** — `playwright install chromium` pulls from `playwright.azureedge.net`, and when that's blocked the failure reads as a stalled download. `find_browser()` now resolves `--browser-path`, `$SLIDES_TO_PDF_BROWSER`, `$PLAYWRIGHT_CHROMIUM_PATH`, `~/.cache/puppeteer` (populated by `npx puppeteer browsers install chrome-headless-shell`, which reaches googlechromelabs) and the usual Chrome/Chromium/Edge paths, passing the result as Playwright's `executable_path`. Verified end to end, and the test doubles as proof the workaround works: with only the PyPI packages installed and **no `playwright install chromium` at all**, it resolved the macOS `.app`-nested `Chromium 111.0.5555.0` from this machine's Puppeteer cache and exported a 15-page PDF — 960 × 540 pt (16:9), 15 bookmarks, text extractable, dark background and accent intact, real webfonts embedded
- Anti-drift verification snippet in `workshop-slides/SKILL.md` for when the script can't be run — presence checks rather than occurrence counts, since counts rot into false alarms as the template grows. Validated against both a fresh build (18 tokens, all present) and the real drifted deck (0 tokens, `.diagram` missing)

### Fixed
- **Corrected a false claim that appeared in two places: "the deck has no `@media print` rules".** The `workshop-slides` template has had an `@media print` block since v0.3.0 — `@page { size: 1280px 720px }`, `#deck` static, `.slide` back in the flow with `break-after: page`. The wrong statement sat in `CLAUDE.md:76`, where it also contradicted `CLAUDE.md:60` in the same file, and in `slides-to-pdf/SKILL.md:125`. Both now state the real reason `emulateMedia('screen')` is required: the print block is written for a paginated Cmd-P export and directly contradicts the script's per-slide `inset: 0` isolation. The old note's secondary claim — that print media would discard the dark theme — was also wrong; the print block sets `background: var(--brand-bg)`
- `find_browser()`'s Puppeteer-cache probe filters to executable files. An intermediate directory in that cache is also named `chrome`, so a plain glob returned a directory, which Playwright would reject at exec with an error that never names the cause

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
