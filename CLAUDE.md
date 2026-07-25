# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Code plugin** (`tammai-tools`) by Tam Mai — a collection of skills (slash commands) for workshop and presentation tooling, built on the BigIn design system.

There is no build system, package manager, or test suite. Assets are plain files consumed directly by Claude Code at runtime, with two executable exceptions — `slides-to-pdf/assets/export.py` and `workshop-slides/assets/build.py`, both standard library only. `export.py` shells out to a headless Chromium, which is the repo's one external requirement.

## Structure

```
.claude-plugin/plugin.json     — plugin metadata (name, version, description)
.claude-plugin/marketplace.json — plugin marketplace metadata (owner, source, license, keywords)
skills/
  workshop-slides/
    SKILL.md                   — the skill's instruction document (Claude reads this at invocation)
    assets/template.html       — the base HTML template for generated slide decks
    assets/build.py            — assembler: template + slide fragment → deck
                                 (stdlib only; makes the "head unchanged" rule mechanical)
    assets/favicon.ico         — tab icon, inlined into the template as base64
    demo.html                  — 15-slide reference deck; every slide is labelled
                                 with the components and layout it demonstrates
  slides-to-pdf/
    SKILL.md                   — the skill's instruction document
    assets/export.py           — deck → single PDF, one headless-Chromium
                                 --print-to-pdf run (stdlib only)
  soft-visuals/
    SKILL.md                   — the skill's instruction document
    assets/template.html       — viewer shell (tokens + dark/light toggle)
    assets/gallery.html        — reference: every shape, connector and layout
    demo.html                  — worked example: all nine types on one product,
                                 each captioned with the prompt that produced it
```

Skills are discovered automatically from the `skills/` directory. Each skill folder must contain a `SKILL.md` with YAML frontmatter (`name`, `description`, `triggers`).

## workshop-slides skill

The skill generates self-contained HTML slide decks. Key design constraints:

- **Output is a single `.html` file** — no server, no JS bundler, no external runtime dependencies at view-time (fonts load from Google Fonts CDN when online). The deck keeps that CDN `<link>` on purpose and neither tool embeds fonts: `slides-to-pdf` renders in a local browser, so the PDF gets whatever the deck got. Where that CDN is unreachable both fall back to `system-ui`.
- **Template is read at generation time** — the skill reads `assets/template.html`, replaces only the `<div id="deck">` contents, and saves the result. The `<head>`, `#bg`, `#watermark`, `#navigator`, and `<script>` blocks are preserved byte-for-byte.
- **Branding via CSS variables** — the `BRAND CONFIGURATION` `:root` block in the template controls accent color, background, and fonts. Custom presets are saved to `~/.workshop-slides-preset.json` and injected at generation time.
- **BigIn defaults**: dark slate (`#020617`) + orange accent (`#f97316`), **Google Sans for headings *and* body**, **Fira Code for code only** (`--brand-font-code` is referenced by just `.code-block` and inline `code`). Google Sans is requested as a variable font over `wght 400..700` because the deck uses 400/500/600/700 — a fixed `wght@400;500;700` list leaves 600 to be synthesised.

### Generation goes through `assets/build.py`, not hand-assembly

SKILL.md tells the agent to keep the `<head>`, chrome and `<script>` unchanged and replace only the contents of `<div id="deck">`. When the agent writes the whole file out itself, that guarantee is aspirational and **it fails in practice**: a deck generated on 2026-07-24 from an unmodified template had dropped all 18 `--dg-*` tokens and the `.diagram` rule while keeping everything else, so pasted `soft-visuals` SVGs would render with no fill and portrait diagrams would overflow — with no error either way.

`build.py` takes a slide fragment and splices it between the template's real bytes, so the carry-over is structural rather than retyped. It also applies presets by substituting the individual `--brand-*` declarations, the fonts `href` and the watermark block — the three head edits SKILL.md used to ask for by hand.

One thing about it that looks like a bug but is not:

- **`set_var` replaces only the first match.** `--brand-bg` is declared twice; the second is the `:root[data-theme="light"]` override, which must stay light or light mode renders a dark page.

Blocking errors are only "no `active` slide" and "more than one"; everything else warns, because a check that cries wolf on the reference deck is worse than no check. Two of its checks were written wrong first and caught by running them against `demo.html`: the cover legitimately puts kicker text in `.slide-num`, and a `.code-block`'s first child is `.code-lang`, not `.code-line`.

### Slide HTML rules

- First slide: `class="slide slide--cover active"` — no `slide-body`
- Section dividers: `class="slide slide--section"` — no `slide-body`
- All other slides: `class="slide"`
- Slide numbers are zero-padded two digits: `01`, `02`, …
- Only one slide may carry the `active` class

### Template runtime features

The template is a **fixed 1280×720 stage** scaled to the viewport by `scaleDeck()`, not a fluid layout. Consequences worth knowing before editing it:

- Slides are exactly 720 px tall with `overflow: hidden`. Overrunning content is **silently cropped**, never scrolled or paginated — in the browser and in the exported PDF alike. Nothing detects it any more: the in-browser `scrollHeight` measurement went with the Playwright script, so keeping slides sparse is the only defence.
- **Cropping and overlap are two different failures, and a slide-level scroll measurement only ever found the first.** `.col` is `overflow: visible`, so a child wider than its column paints over its neighbour without changing the slide's `scrollWidth` — measured: an `<svg width="700" height="660">` in a 568px column reaches 132px into the next column, `elementFromPoint` there returns the neighbour's `<p>`, and nothing is cropped. `class="diagram"` (`width: 100%; max-height: 100%`) is what constrains it, so it earns its place *for SVGs with explicit width/height attributes*; a `viewBox`-only SVG is already capped by the column's flex layout, where the class measurably changes nothing. `build.py` warns when an attribute-sized `<svg>` wider than 536px (the widest a constrained diagram gets) lacks the class. That is a **proxy**, not the measurement the runtime `OVERLAP` report made: it has no column width, so it flags a shape that *could* overlap rather than one that does. The threshold is what keeps it from crying wolf on inline icons.
- The 16:9 lock is written **twice, on purpose**: `#deck { transform: scale(var(--deck-scale)) }` with the value set by an `@supports`-gated pure-CSS `min(100vw / 1280px, 100dvh / 720px)`, *and* by `scaleDeck()` writing the same number to `--deck-scale` inline. CSS holds the ratio on first paint and with JS stripped; JS covers browsers without length-÷-length `calc()` and is what makes the zero-viewport guard possible. Both must stay in agreement — change one, change the other.
- `scaleDeck()` guards against a zero/NaN viewport — without it, a hidden iframe or snapshot renderer computes `scale(0)` and the deck renders blank. Don't remove the guard. It holds at 1:1 rather than scaling, which is only safe *because* a `ResizeObserver` on `documentElement` re-runs it: a `resize` event fires for the window only, so a deck revealed from `display:none` (lazily-shown pane, iframe embed) would otherwise stay stuck at a hard 1280×720 and get cropped by its container. Don't drop the observer to "simplify" back to `resize`.
- Measure `documentElement.clientWidth/clientHeight`, **not** `window.innerWidth/innerHeight` — the former is the CSS layout box the deck is centred in (scrollbars excluded) and tracks the mobile visible viewport. For the same reason `html, body` height is `100dvh` (with a `100vh` fallback line first): `vh` is the *large* viewport, so on a phone with the address bar showing, the body is taller than the visible area and the centred deck sits under the chrome.
- Dark/light mode keys off `[data-theme]` on `<html>`, seeded from `localStorage` (`workshop-deck-theme`), defaulting to dark. Light mode reverses the `--slate-*` scale, so **slide markup must never hardcode hex colors** — use `var(--brand-accent)` and `--slate-*` or the deck breaks in light mode.
- Interactive chrome lives outside `#deck` (`#navigator`, `#themeToggle`, `#fullscreenToggle`); slide content contains no `<button>`. `slides-to-pdf` relies on that split to strip chrome — keep new controls outside `#deck`.
- The `@media print` block gives a dependency-free Cmd-P export. `slides-to-pdf` injects its own copy of these rules *after* this block, so the two **cascade** rather than being independent: whatever this block prints that the injected one does not override still shapes the PDF (notably the `.slide-body img` clamp). `PRINT_CSS` in `slides-to-pdf/assets/export.py` is a deliberate fork of this block — change one, change both, the same standing rule as the `--dg-*` tokens.

### Syntax highlight classes (inside `.code-block`)

`.kw` = keyword (orange), `.fn` = function name (light), `.str` = string (muted), `.cmt` = comment (dim)

`.code-block` is **not** a `<pre>` — every line needs its own `.code-line` element (`.code-line.blank` for a gap), or raw newlines collapse and the snippet reflows into a single paragraph.

## slides-to-pdf skill

Exports a generated deck to a single PDF, one page per slide. `assets/export.py` is stdlib-only: **one** headless-Chromium `--print-to-pdf` invocation, no `playwright`, no per-slide loop, no merge step, and `pypdf` only as an optional nicety for the page report. It replaced a 761-line Playwright driver that did all of those things; if you are tempted to add any of them back, read the two measured findings below first.

The shape: copy the deck to `<deck>.pdfexport-tmp.html` **beside the original** (so a preset's local logo still resolves), inject a print stylesheet before `</head>`, run the browser once, delete the copy. The source deck is never modified and stays usable as an interactive presentation.

**Inject the print CSS — never depend on the deck's own `@media print` block.** The deck stacks every `.slide` at `position: absolute; inset: 0` with `opacity: 0` and reveals only `.active`, so a deck *without* print rules exports as **one page at 612 × 792 pt** (US Letter, first slide, silently). Measured: strip the block from a deck that renders 8 pages and it collapses to 1; inject ~15 lines and it is back to 8 at 960 × 540, visually indistinguishable from the template's own print path. That is also why the old script's `emulateMedia('screen')` dance is gone — this path *wants* print media, so the two exports no longer need to be kept independent.

**A modern full Chrome hangs forever on `--print-to-pdf`.** Chrome for Testing 150 produced nothing under plain `--headless`, `--headless=old`, `--headless --no-sandbox --disable-dev-shm-usage`, and `--headless=new --run-all-compositor-stages-before-draw` — all four timed out at 40 s. `chromium_headless_shell` 141 exports the same deck in 1.6 s and Chromium 111 in 3.3 s. So `find_browser()` resolves headless-shell **before** full Chrome (`--browser-path` → `$SLIDES_TO_PDF_BROWSER` → `chrome-headless-shell`/`headless_shell` in the Playwright and Puppeteer caches → full builds → installed apps), and the run is wrapped in a hard `timeout` that kills and explains rather than waiting. Each cache is walked **once**, bucketing shell and full hits as it goes, and pruned below 7 path components — the deepest real launcher is at 6, and everything deeper is `.app` framework and `.lproj` trees: measured, 523 entries instead of 2039 and 12 ms instead of 100 ms, and ~300 ms saved on the fallback path that used to re-walk every cache per name set. Ordering within a class is best-effort by the largest number in the path, because the revision sits in a different component per cache (`chromium_headless_shell-1228` vs `chrome/mac-150.0.7871.24`) — keying off a fixed position scored every Puppeteer build 0. `_runnable()` requires `is_file()`: an intermediate *directory* is also named `chrome`, and exec on a directory fails with an error that never names the cause.

Measured output: an 8-slide fixture → 8 pages in 1.6 s; the real 25-slide `wordpress-setup-slides.html` → 25 pages in 1.9 s; every page 960 × 540 pt (true 16:9), text extractable, no trailing blank page. Inspected as images: dark background, radial glows, accent, Google Sans, Vietnamese diacritics, `.code-block` syntax colors, `.cmp-table`, `.stat-block`, tags, watermark and pasted `soft-visuals` SVGs all vector and correct.

**Forcing a theme needs a script, not an attribute.** Stamping `data-theme` on `<html>` does nothing: the deck's inline script re-sets it from `localStorage` after load, and a fresh headless profile has no entry, so it lands on the deck's default (dark). Proof that it silently no-ops: `--theme light` produced a **byte-identical** PDF. The injected script seeds `workshop-deck-theme` *and* re-asserts the attribute on `load` — which fires after the deck's own script — so it works without knowing any particular deck's storage key. `as-is` (the default) leaves the deck alone.

**Verifying a theme headlessly needs the attribute set *before* load, not toggled after.** Both templates put `transition: background 0.25s` on `html, body`, and under `--virtual-time-budget` a transition never advances — so a theme forced after load leaves the page background frozen at the old value while untransitioned properties (an `h1` colour) flip immediately. That renders as dark-text-on-dark and reads exactly like a broken light mode; it cost one false bug report. Measured: computed `body` background stayed `rgb(2,6,23)` 900 ms after the switch, and was correct the moment `data-theme` was set in the source instead. The PDF path is immune because the injected `@media print` block re-declares the background with no transition on it.

**Chrome hiding is deliberately generic.** Newer deck templates keep adding fixed controls — the template here has only `#navigator`, but decks in the wild also carry `#themeToggle` and `#fullscreenToggle`. Rather than chase a hardcoded id list, the CSS hides `#navigator` plus `button:not(#deck button)`; slide content contains no buttons, every control does. Add new ids only if a control is not a `<button>`.

**Fonts are not embedded, and don't need to be.** The export renders in a local browser, where the deck's CDN `<link>` just works — the old `@fontsource` woff2 fetching, family renaming and subset matching all existed to survive a host that blocked `fonts.googleapis.com`, and are gone with it. Where that CDN is unreachable the deck falls back to `system-ui` on screen and in the PDF alike, which is a template concern, not this skill's.

**Don't diagnose a webfont failure from the PDF's font names.** `pypdf` reports page-1 `/BaseFont` values like `/AAAAAA+Helvetica` and `/Courier` for a deck whose fonts loaded perfectly — print-to-PDF labels embedded subsets generically, and Google Sans comes through as `Type3 /None` (vector glyph procedures) rather than a named font program. Render the PDF to an image instead — `qlmanage -t -s 1400 -o thumbs deck.pdf` — and look at the letterforms.

**There is no `--device-scale`, on purpose.** Print-to-PDF output is resolution-independent: text is Type3 vector glyph procedures, gradients and borders are vector, raster images pass through at native resolution. Measured on the old script: the same deck at `--device-scale 1`, `2` and `3` produced byte-identical files. Don't re-add the flag; it only ever set the browser DPR.

Prior art worth reading before changing any of this: `~/.hermes/skills/html-slides-to-pdf/SKILL.md` arrived at the same one-command approach independently. Its two fallbacks both need Playwright; the injection step above removes the need for either.

## soft-visuals skill

Generates nine visual types as inline SVG in a flat pastel style — flowchart, architecture, wireframe, mindmap, org chart, sequence diagram, Gantt timeline, kanban board, user journey map. Output is a single `.html` viewer.

The shape/component vocabulary was derived by exploring Whimsical's own tool palettes, so the taxonomy deliberately mirrors a tool people already know. Star and Cross exist there but were scoped out here as decorative.

**The `--dg-*` token block is duplicated verbatim in `soft-visuals/assets/template.html` and `workshop-slides/assets/template.html`.** That duplication is deliberate — it is what lets a generated `<svg>` be pasted into a slide deck untouched. If you add or rename a token, change **both** files; a token one side doesn't define renders as no fill, silently, with no error.

Constraints that are load-bearing, not stylistic preference:

- **No shadows, and never `filter:`/`feDropShadow`.** Measured: a filtered region makes Chrome's print-to-PDF rasterise that area into a bitmap, so a deck containing the diagram stops being pure vector. A faked offset-rect shadow also peeks out from under a shape's own border in light mode. The style is flat — leave it flat.
- **Translucent hue fills** (`color-mix(… 16%, transparent)`), not per-theme solids. One value reads correctly over both the dark and the light page.
- **Connectors are drawn before shapes**, start on the source's edge, and stop ~6px short of the target's. Arrowheads landing inside shapes is the most common way these look sloppy; a line that *begins* in the gap beside its source is the second, because it reads as belonging to nothing. Derive both ends from real geometry, and watch the shapes whose edge is not their bounding box — a `cylinder` drawn from `y=309` with `ry=9` has its visible top at 300.
- **Marker ids must be unique per document.** Multiple `<svg>` blocks in one file each need their own suffixed marker id; duplicates are invalid HTML and all references resolve to the first.
- Content outside a `viewBox` is silently invisible — verify with `getBBox()` against `viewBox.baseVal`. **This is now checked mechanically at assembly time**, because the documented DevTools snippet caught nothing: a deck shipped on 2026-07-25 with a seven-card stack running to `y=308` inside `viewBox="0 0 460 306"`, so one card lost its bottom border and rounded corners while six kept theirs — invisible in the browser, invisible in the PDF, and invisible to the slide-overflow and column-overlap checks, since neither the slide nor the column was violated. `build.py`'s `check_svg_viewbox()` warns from attributes alone at assembly time. It is the **only** remaining check: the `getBBox()` measurement that ran at export time went with the Playwright script, and a visual saved outside a deck is measured by nothing.
  - The static check is **deliberately partial**: transformed elements, relative or curved paths, and text *width* are skipped rather than estimated, because a check that misfires on the reference deck gets ignored and then deleted. Verified firing on the real bad deck and silent across eight known-good files (both templates, both demos, the gallery, and two shipped decks).
  - Two traps it hit in development, both worth not re-learning: both templates *mention* `<svg>` in prose (one in a CSS comment, one in an HTML comment), and a naive `<svg…>(.*?)</svg>` pairs that prose opening with the real diagram's closing tag — the check then silently never fires on any deck built from the template. Comments are stripped first and each opening is resolved against the next `</svg>` independently. Separately, `getBBox()` **excludes stroke width**, so a 2.875px overflow of a 1.75px-stroked edge measures as 2.0 — worth knowing if you re-add a runtime measurement, since the number is a floor, not the true overflow.

`assets/gallery.html` is generated, not hand-maintained in place; it is the reference the skill tells Claude to copy from, so keep its coverage complete when adding a shape. **A geometry or hue mistake in the gallery is not a cosmetic bug — it propagates into every visual generated from that pattern**, since SKILL.md explicitly tells Claude to copy rather than author. `demo.html` is the end-to-end check on that: all nine types built the way the skill prescribes, so a defect in a gallery pattern shows up there rather than in a user's output.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with the required YAML frontmatter.
2. Add any static assets under `skills/<skill-name>/assets/`.
3. Reference assets by relative path from `SKILL.md` (e.g. `assets/template.html`).
