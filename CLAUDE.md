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
  workshop-handbook/
    SKILL.md                   — the skill's instruction document
    assets/template.html       — viewer shell: sidebar bookmarks + flowing document
    assets/build.py            — assembler: template + content fragment → handbook
                                 (stdlib only; same shape as workshop-slides/build.py)
    assets/favicon.ico         — tab icon, inlined into the template as base64
    demo.html                  — 6-chapter reference document; every chapter is
                                 labelled with the components it demonstrates
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
  antv-infographic/
    SKILL.md                   — the skill's instruction document; HTML shell
                                 (title/desc header, dark/light toggle, SVG
                                 export button) lives inline in the template
                                 block, extracted at generation time
  doc-quality/
    SKILL.md                   — the skill's instruction document (4-pass workflow)
    assets/vale/               — .vale.ini, .vale-social.ini, TamMai / TamMaiVI
    assets/rubric.md           — the doc-mode LLM-judge rubric
    assets/rubric-social.md    — the social-mode rubric + character limits
    assets/fixture.md          — bilingual fixture; one planted hit per rule
    assets/fixture-social.md   — social fixture; emoji off, other rules armed
    assets/selftest.py         — asserts every rule fires (stdlib; needs vale)
```

Skills are discovered automatically from the `skills/` directory. Each skill folder must contain a `SKILL.md` with YAML frontmatter (`name` and `description`). There is no `triggers` key — trigger phrases go in the `description` prose, which is what the marketplace routes on.

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

## workshop-handbook skill

The long-form counterpart to `workshop-slides`: one self-contained `.html` file, one scrolling
document, a sidebar of bookmarks. Same design tokens, same preset file, inverted constraint — a
deck crops what overruns a 720px stage, a handbook flows and the length is free.

Deliberately **not** a variant of the deck template. The two share the `BRAND CONFIGURATION` block,
the slate scale, the light-mode reversal and the `--dg-*` tokens verbatim; everything below that is
different, because a fixed-stage presentation and a scrolling document have almost no layout in
common. Trying to unify them would mean one template carrying both a `scaleDeck()` and a scrollspy.

### The preset file is shared on purpose

`build.py --preset` reads the same `~/.workshop-slides-preset.json`, with the same schema and the
same `apply_preset()` logic. A handbook is normally handed out alongside the deck it accompanies, so
one brand means one file, and a user who already configured their slides answers no questions here.
The consequence to remember: **"Update my preset" in either skill changes both.** SKILL.md says so
out loud at the point of asking.

`set_var` replaces only the first match, same as the slides version — but here `--brand-bg` is
declared **three** times: `:root`, the `[data-theme="light"]` override, and the `@media print` block.
The last two must stay light or light mode and every printed page render on a dark background.

### Headings are unnumbered, and that is what removed a whole bug class

v0.7.0 dropped chapter and section numbering entirely. Before that, numbers had **two independent
producers** — CSS counters for the page, `buildToc()` counting document position for the sidebar —
and nothing enforced that they agreed. Two ways they drifted during development, both real:

- **A `.chapter` with no `<h2>`.** CSS incremented for every `.chapter`; `buildToc()` bailed before
  counting, so one headingless chapter put every later sidebar row one behind its own numeral.
- **An `<h3>` nested inside a `<div>` or `<figure>`.** CSS matched `.chapter h3` (descendant) while
  the script collected `:scope > h3`, so a nested one bumped the section counter without ever
  appearing in the sidebar.

Both are now structurally impossible: there is no counter to disagree with. Emphasis comes from an
`<em>` run inside the heading instead, which also survives being lifted verbatim into a sidebar row.
`figure` is the only counter left.

What survived from that episode, because both are still real failures:

- A headingless `.chapter` is a **blocking error** — `buildToc()` skips it, so it is unreachable.
- A nested `<h3>` **warns** — it renders as a heading but never becomes a bookmark.
- A hand-typed `1.` or `4.2` at the start of a heading **warns**: it reintroduces the numbering and
  lands in the bookmark too, since the row takes the heading's own text.

### There is no mobile header bar — the controls float, and there's no chrome left to reserve space for them

The first responsive pass put a sticky `#topbar` across the top of narrow viewports, with the
drawer trigger and a compact theme toggle embedded in it (mirroring a reference layout the user
supplied). That bar is gone. `#menuToggle` and `#themeToggle` are now `position: fixed`
`.float-btn`s, body-level, pinned to the top corners — `#themeToggle` at every viewport width,
`#menuToggle` only below the drawer breakpoint. Removing the bar meant nothing reserved vertical
space for them any more, so without a fix the mobile `.cover`'s kicker line would start at `y:32`
— inside the buttons' own `y:20–58` band — and render half-hidden underneath them; the mobile
`#handbook` padding-top is now `74px` specifically to clear that.

**`#scrim` lives inside `#shell`, not beside it.** `#shell` is `position: relative; z-index: 1`,
which makes it a stacking context — so `#sidebar`'s `z-index: 80` is only ever compared *inside*
it, and from outside the whole shell is just "1". A body-level scrim therefore out-ranked the
entire shell and painted over the open drawer no matter how high the drawer's own z-index went.
Moving the scrim inside fixes it.

**The backdrop has to beat the floating controls outright, not tie with them.** `.float-btn` and
`#shell.drawer-open` were both `z-index: 65` at first — an equal value resolves by DOM order, and
since both buttons are later siblings of `#shell`, they painted *over* the dimmed backdrop instead
of being dimmed with everything else on the page. Verified with `elementFromPoint` at the theme
button's own coordinates: it hit `#themeToggle` before the fix and `#scrim` after. The fix was
lowering `.float-btn` to `50`, strictly below the drawer-open value — a tie is fragile precisely
because "should win" and "does win" are unrelated facts about it.

Beware measuring any of this too early — the drawer has a `0.24s` transform transition, and an
`elementFromPoint` fired synchronously after `.click()` still reads the closed position and reports
the wrong element on top. That looked exactly like the bug it had just fixed, twice, in two
different sessions. `computer{action:"wait"}` for even a second between the click and the read is
enough; there is no shortcut that avoids it.

Two more that only showed up under real key/pointer events:

- **`e.target.matches(...)` in a keydown guard throws when the target is not an Element.** With
  nothing focused the target can be `document`, which has no `.matches` — the TypeError killed the
  handler *before* the Escape branch ran, so Escape-to-close silently did nothing. Both keydown
  handlers now go through a shared `isTyping(e)` that type-checks first.
- **`#scrim.is-open` is not media-scoped.** Pressing **C** above the breakpoint dimmed the whole
  page over a sidebar that had never moved. `setOpen()` now bails when the drawer media query does
  not match.

### The sidebar head is two columns, and the logo anchors to the sidebar's bottom, not its top

`.sidebar-head` is a flex row of exactly two children: `.sidebar-head-text` (title + subtitle,
stacked, `flex: 1` so it takes whatever width the close button doesn't) and `#closeToc`. Keeping
the title and subtitle as separate divs inside one flex item — rather than two direct flex
children — is what lets them stack vertically while the row itself stays horizontal.

The watermark moved from the top of `<aside>` to its bottom, after `<nav id="toc">`. Sequencing it
last in the DOM is necessary but not sufficient — a short bookmark list would still leave it
stranded right under the last row instead of flush with the sidebar's bottom edge. `#toc { flex: 1
}` is what closes that gap: inside `#sidebar`'s flex column, the nav grows to fill whatever height
its content doesn't use, which pushes the watermark to the true bottom regardless of how many
chapters the handbook has. A long list still scrolls normally, because the overflow is `#sidebar`'s
to carry, not `#toc`'s.

### Icons are genuine Lucide markup, not approximations

Every control icon — menu, close, sun, moon, copy, check, the back-to-top arrow — is Lucide's own
path data at its native `24 24` viewBox, `stroke-width="2"`, round caps and joins. Earlier versions
had hand-tuned 16×16 paths at odd stroke widths (1.4–1.7) that only *looked* similar. There is no
Lucide dependency to install: these are static SVG paths copied in, the same self-contained-file
approach the rest of the skill uses. Rendered size is still controlled entirely by CSS (`.float-btn
svg`, `#backToTop svg`, etc.) — changing the viewBox doesn't change how big an icon looks on the
page, only how its internal coordinate space maps to that size.

### A flex `<li>` needs the author's content wrapped, or every inline child shrinks on its own

`.list.check li` is `display: flex`, and the load-time script used to only *prepend* the
`.check-icon` span. Everything the author wrote stayed a direct child, so each inline tag **and each
plain-text run** became its own flex item — and with the default `flex-shrink: 1` / `min-width:
auto`, a `<code>` was squeezed below its natural width on a tight row. The base `code { word-break:
break-word }` then hyphenated *inside* the pill. Measured at a 420px viewport: `hr.bigin.tech`
rendered 56.2px wide and 75.5px tall — the token broken across three lines within its own box —
against 117.4 × 22.7 once wrapped. Moving the content into one `.check-content` span
(`flex: 1 1 auto; min-width: 0`) is the fix; the icon stays the only other flex item.

The demo never caught it because its checklist items were plain text plus one short
`<code>build.py</code>`, which is too narrow to be squeezed. **A short inline `<code>` is not a test
case, and neither is a whole-item one** — a `<li>` whose entire content is wrapped in `<code>` is a
single flex item already. The regression case is a long token inside a longer sentence, which is
what `demo.html`'s checklist now carries.

Worth generalising before adding any other script-injected chrome to a flex container: the guard is
`:scope > .check-icon`, so the pass stays idempotent, but a *second* injected sibling would
reintroduce exactly this problem.

Wrapping the content is also what made the row's `align-items` matter. It was `center`, which is
exact on a one-line item and puts the mark in the vertical middle of a wrapped one — level with
nothing, and now that a checklist item can carry a URL or a command it wraps often. The row is
`flex-start` with the icon nudged down by `calc((1lh - 18px) / 2)`, which resolves to **4.71875px**
at the current type scale — the same position `center` produced on a one-line item, so nothing moved
for the common case. Deriving it from `1lh` rather than typing a number is the point: it is what the
absolute-positioned `::before` this replaced could never do, and it is why the old comment's warning
about hand-tuned offsets does not apply to it. A plain `margin-top: 5px` precedes the `calc()` as
the fallback wherever the `lh` unit is unsupported.

### Two print bugs found by rendering, not by reading

Both were invisible in the source and obvious the moment the page was actually printed. Worth
knowing before touching the `@media print` block:

- **`transform: none` on `#sidebar` is load-bearing.** A printed page is ~816 CSS px wide (US Letter
  at 96dpi), which is *inside* the `max-width: 1080px` drawer breakpoint — so the responsive rule
  applies while printing and translates the sidebar 100% off its own box. The print block reset
  `position` but not `transform`, and the contents page came out **completely blank**, with an empty
  first page as the only symptom. Measured on the demo before and after.
- **`#skip-link` needs hiding by id.** Chrome hides the controls via `button`, which is enough for
  every control *except* the skip link — it has to be a real `<a href>` for keyboard users, and a
  `position: fixed` element with a `translateY(-200%)` still lays out on paper. It printed as a grey
  pill in the middle of page one.

Measured output after both fixes: the 6-chapter `demo.html` → 12 pages at 612 × 792 pt, contents
page first, then cover, then chapters one per page, forced light palette, diagrams vector.

### `build.py` checks, and the one thing that would have killed them

Same shape as the slides script — blocking errors only for structural breakage, everything else a
warning — plus checks a handbook can fail that a deck cannot: duplicate `id`, a cross-reference to
an id nothing produces (the ids are computed by mirroring the runtime's `slug()` in Python), a
skipped heading level, an `<h1>` outside the cover, a `.code-block` with no `<pre>`.

The one that matters most in practice is **`SLIDE_ISMS`**: `.slide-body`, `.cols-2`, `.code-line`,
`.cmp-table`, `.stat-block` and six more have no rule in this stylesheet, so they render as unstyled
prose with no error and no visual cue. An agent that has just read `workshop-slides/SKILL.md`
reaches for them by reflex, which makes this the likeliest failure mode of the whole skill.

**Every markup scan runs against `strip_code_samples()` first**, which blanks comments and the
inside of `<pre>`/`<code>` space-for-character. Without it the checks are actively harmful here: a
handbook's job is often to *document* markup, so its code samples are full of `id="…"`,
`class="slide-body"` and `href="#…"` that are text, not structure. The demo alone would have
reported a phantom `#handbook` anchor and, had a snippet shown the same `id=` twice, a false
duplicate — which is precisely how a warning list gets ignored and then deleted.

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

Generates nine visual types as inline SVG in a flat pastel style — flowchart, architecture, wireframe, mindmap, org chart, sequence diagram, Gantt timeline, kanban board, user journey map. Output is a single `.html` viewer. **Infographic requests (data storytelling: stats, steps, comparisons, SWOT, quadrants, org trees, charts, wordclouds) delegate to the `antv-infographic` skill** — see below.

The shape/component vocabulary was derived by exploring Whimsical's own tool palettes, so the taxonomy deliberately mirrors a tool people already know. Star and Cross exist there but were scoped out here as decorative.

**The `--dg-*` token block is duplicated verbatim in three files** — `soft-visuals/assets/template.html`, `workshop-slides/assets/template.html` and `workshop-handbook/assets/template.html`. That duplication is deliberate: it is what lets a generated `<svg>` be pasted into a slide deck *or* a handbook untouched. If you add or rename a token, change **all three**; a token one side doesn't define renders as no fill, silently, with no error. Each consumer's `build.py` has a `check_carryover()` that diffs its own template's token set against the generated file, so a *dropped* token is caught — but nothing cross-checks the three templates against each other, so an *added* one is on you.

Constraints that are load-bearing, not stylistic preference:

- **No shadows, and never `filter:`/`feDropShadow`.** Measured: a filtered region makes Chrome's print-to-PDF rasterise that area into a bitmap, so a deck containing the diagram stops being pure vector. A faked offset-rect shadow also peeks out from under a shape's own border in light mode. The style is flat — leave it flat.
- **Translucent hue fills** (`color-mix(… 16%, transparent)`), not per-theme solids. One value reads correctly over both the dark and the light page.
- **Connectors are drawn before shapes**, start on the source's edge, and stop ~6px short of the target's. Arrowheads landing inside shapes is the most common way these look sloppy; a line that *begins* in the gap beside its source is the second, because it reads as belonging to nothing. Derive both ends from real geometry, and watch the shapes whose edge is not their bounding box — a `cylinder` drawn from `y=309` with `ry=9` has its visible top at 300.
- **Marker ids must be unique per document.** Multiple `<svg>` blocks in one file each need their own suffixed marker id; duplicates are invalid HTML and all references resolve to the first.
- Content outside a `viewBox` is silently invisible — verify with `getBBox()` against `viewBox.baseVal`. **This is now checked mechanically at assembly time**, because the documented DevTools snippet caught nothing: a deck shipped on 2026-07-25 with a seven-card stack running to `y=308` inside `viewBox="0 0 460 306"`, so one card lost its bottom border and rounded corners while six kept theirs — invisible in the browser, invisible in the PDF, and invisible to the slide-overflow and column-overlap checks, since neither the slide nor the column was violated. `build.py`'s `check_svg_viewbox()` warns from attributes alone at assembly time. It is the **only** remaining check: the `getBBox()` measurement that ran at export time went with the Playwright script, and a visual saved outside a deck is measured by nothing.
  - The static check is **deliberately partial**: transformed elements, relative or curved paths, and text *width* are skipped rather than estimated, because a check that misfires on the reference deck gets ignored and then deleted. Verified firing on the real bad deck and silent across eight known-good files (both templates, both demos, the gallery, and two shipped decks).
  - Two traps it hit in development, both worth not re-learning: both templates *mention* `<svg>` in prose (one in a CSS comment, one in an HTML comment), and a naive `<svg…>(.*?)</svg>` pairs that prose opening with the real diagram's closing tag — the check then silently never fires on any deck built from the template. Comments are stripped first and each opening is resolved against the next `</svg>` independently. Separately, `getBBox()` **excludes stroke width**, so a 2.875px overflow of a 1.75px-stroked edge measures as 2.0 — worth knowing if you re-add a runtime measurement, since the number is a floor, not the true overflow.

`assets/gallery.html` is generated, not hand-maintained in place; it is the reference the skill tells Claude to copy from, so keep its coverage complete when adding a shape. **A geometry or hue mistake in the gallery is not a cosmetic bug — it propagates into every visual generated from that pattern**, since SKILL.md explicitly tells Claude to copy rather than author. `demo.html` is the end-to-end check on that: all nine types built the way the skill prescribes, so a defect in a gallery pattern shows up there rather than in a user's output.

## antv-infographic skill

Infographics are rendered by the **AntV Infographic** engine (open-source, MIT; ~54 built-in templates) rather than hand-drawn SVG. `SKILL.md` carries the full template list, the DSL syntax rules, and the complete HTML shell inline in its template block — there is no `assets/` directory, and the shell is extracted from `SKILL.md` at generation time, so the demo files stay in sync with the skill by construction.

Design decisions worth keeping in mind:

- **HTML shell matches `soft-visuals`** — same header structure (kicker / `h1` / lede / orange rule), same button vocabulary: a dark/light toggle (38×38, top-right) and an `SVG Export` button (bottom-right, icon + label). Both buttons restyle through CSS variables (`--btn-*`, `--page-*`) toggled by a `dark` class on `<html>`, so theme switching restyles the whole page, not just the canvas.
- **Dark/light re-renders, not re-styles.** The infographic itself is a canvas re-rendered from the DSL with `theme.type dark|light` injected (or swapped in place — the toggle's regex must keep the `type` line's leading indentation: use `[ \t]*`, never `\s*`, or the line loses its indent and `palette` gets eaten).
- **Exported SVG gets a sans-serif fallback.** AntV puts text in `<foreignObject>` divs plus a `font-family` on the root `<svg>`; the export post-processes the serialized SVG with `applyFontFallback()`, which rewrites every `Google Sans` reference (attribute, inline style, root) to a full `'Google Sans', system-ui, …, sans-serif` chain. Without this, a standalone SVG whose webfont fails renders in default serif.
- **`{title}`/`{desc}` placeholders** feed both the page `<title>` and the `<h1>`/`.lede` header; `{syntax}` is the DSL, `{slug}` the filename stem.

## doc-quality skill

Four passes over a markdown document or social post: drafting rules, a Vale lint as a
hard gate, a compression rewrite, and an LLM-judge rubric. Two modes, `doc` and `social`,
each selecting a rubric and a Vale config. The lint targets are bilingual; every
model-facing file here stays English.

### Every bug in the first draft of this config reported "0 errors"

That is the thing to internalise before touching `assets/vale/`. A broken Vale config and
a clean document produce byte-identical output, so the config cannot be verified by
running it on real docs and seeing no complaints — which is exactly how it shipped with
two fatal bugs and one false rationale.

- **`TokenIgnores` matched the whole document.** The value was `` `[^`]+` `` — backticks
  intended as delimiters. Vale's INI parser strips them, leaving `[^`]+`, which matches
  every run of non-backtick characters. Every rule was silenced. Measured on the fixture:
  0 findings with it, 5 with `BlockIgnores` alone, 11 with neither.
- **Both directives were redundant anyway.** Vale's default markdown scoping already skips
  fenced blocks and inline code — verified against planted violations in both. `fixture.md`
  keeps that control section so the property stays asserted rather than assumed.
- **Vale concatenates `raw` entries; it does not OR them.** `raw: ["alpha", "beta"]` matches
  only `alphabeta`. Both `TamMaiVI` files listed 9–10 phrases as separate entries and so
  compiled into a regex demanding all of them in sequence — neither had ever matched
  anything. Continuation lines now carry a leading `|`. The English styles were unaffected
  only because they happen to have one `raw` entry each, which is luck, not design.
- **`tokens` handles Vietnamese diacritics fine.** The original rationale for `raw` was that
  Vale wraps `tokens` in ASCII `\b`. True, but these phrases begin and end on ASCII letters,
  so `tokens: ["nhằm mục đích"]` matches. `raw` is still needed — for the anchored
  `^…Việc` branch and the inline alternations — just not for that reason.

`assets/selftest.py` asserts **per-rule** counts, not a total: one rule can go dead while
another over-fires and keeps the sum intact. It also asserts no alert lands on the two clean
control lines. Verified to fail on both bugs above when reintroduced. Run it after touching
anything under `assets/vale/`.

**A repo-wide lint will always report the fixtures.** `fixture.md` and `fixture-social.md`
carry planted violations by design, so `vale skills/doc-quality/assets/*.md` reports 14 errors
on a healthy repo. Lint `rubric*.md` explicitly rather than globbing the directory, or the
fixtures read as regressions.

### Pass 2 is sized by measurement because a quota on a ratio always "succeeds"

The original Pass 2 said "cut ~40% of words". The failure mode is not that the model refuses
— it is that the model **complies**. Once genuine redundancy runs out, the next 30% has to
come from substance, and the output still reports success, because the target was a ratio and
the ratio was met. It also contradicted `rubric.md` step 3, which says to rewrite *only the
cited lines*.

Found by smoke-testing this repo's `README.md`: Pass 1 clean, judge scores `redundancy 4,
coherence 4, density 4, tone 5`, and the only genuine redundancy was four spans totalling ~3%
of the words. Hitting 40% there meant deleting fact tables.

Pass 2 now scores first and derives the target from the score (5 → no cut, 4 → cited spans
only, 3 → ~25%, ≤2 → 40%+), with the cut **bounded by the citations**: nothing cited, nothing
cut. The percentages are calibration, not targets. Two properties are what make it work, and
both are easy to erode:

- **The bound is the citation list, not the number.** Re-adding "aim for X%" anywhere in that
  pass restores the original bug regardless of what the table says.
- **A document that resists the cut is evidence about the document.** Pass 0's
  `README ≤ 150 lines` budget has the same shape — this README is a justified 170.

`social` mode needs its own table, because `rubric-social.md` scores neither redundancy nor
density — the doc table has no input there. It keys on **hook** and **single idea** instead,
the two social dimensions that measure text not earning its place: a low hook cites
throat-clearing before the first claim, a low single-idea cites the digressions. The platform
character limit is a hard bound applied before either, since an over-limit post cannot ship at
any score.

**The percentage measures material removed, not net length change** — stated in Pass 2's rules
because the alternative reading makes two of its own lines contradict each other. The measured
case: a draft scoring `hook 2, single idea 2, concreteness 1, voice 1` hit the `≤ 2` row's
40%+ demand by cutting 100% of its sentences, and still came out 10% longer. Read "cut 40%" as
net length and those two facts look mutually exclusive, which is how a model ends up either
refusing to add specifics or deleting substance to force a shrink — the exact failure Pass 2
exists to prevent.

**Concreteness and voice are never cut signals**, and that is the part most likely to get
"simplified" back out. A post scoring low on concreteness needs specifics *added*. Measured on
a real draft scoring `hook 2, single idea 2, concreteness 1, voice 1`: the correct rewrite
stripped every slop phrase and still came out 10% longer, because what it lacked was numbers
and a named failure. Under the old quota that is a failed pass; it is the right answer.

### The two rubrics disagree on purpose

`rubric.md` scores rhetorical questions and rule-of-three as tone=1, and the `doc` Vale config
bans emoji at **error** level — the Pass 1 hard gate. Run a LinkedIn post through `doc` mode
and it fails on devices that are legitimate there, which is the whole reason `social` mode
exists rather than a "relaxed docs" flag. `rubric-social.md` scores hook / single idea /
concreteness / voice instead, and names emoji, rhetorical questions, fragments and
rule-of-three as *deliberately not penalised* — scored under Voice only when they read as
generated rather than chosen. Slop words stay banned in both; AI slop is worse on LinkedIn
than in a README, not better.

`.vale-social.ini` differs from `.vale.ini` by exactly one line, `TamMai.Emoji = NO`. **Vale
ignores an unrecognised key silently**, so a typo leaves the rule armed and the mode quietly
broken. `selftest.py` asserts zero emoji hits *and* that `TamMai.BannedWords` and
`TamMaiVI.Intensifiers` still fire in the same run — the second half is the load-bearing one,
since a wholly broken config also scores zero emoji. Verified: typo the key and the test
reports emoji armed; break the config outright and it reports the other rules dead.

### Rule overlap double-reports

`in order to` was in both `TamMai/Fillers.yml` and `TamMai/Substitutions.yml`, so it reported
the same span twice. `Substitutions` owns it, because it names the replacement. Worth checking
for whenever a phrase is added to either file.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with the required YAML frontmatter.
2. Add any static assets under `skills/<skill-name>/assets/`.
3. Reference assets by relative path from `SKILL.md` (e.g. `assets/template.html`).

### `description` has a hard 1024-character limit, and blowing it blocks the install

Not a lint warning — the plugin fails to install. Two descriptions were over when this was
found (`soft-visuals` at 1287, `workshop-handbook` at 1147) and nothing in the repo measured
them, so the only symptom was a failed install with the skill unnamed.

The limit applies to the **folded** value, not the raw block. These are `>` block scalars, so
YAML joins the lines with single spaces and drops the 2-space indents — measuring the raw
frontmatter text overcounts by roughly 2 chars per line and can report a passing description
as failing. Fold before counting.

What to cut, in order: **visual and implementation detail** (`soft-visuals` was spending ~105
chars on stroke weights and connector style, which the body already covers), then **trigger
phrases that duplicate each other** (`"diagram this"` next to `"draw a diagram"`, `"playbook"`
in both the noun list and the trigger list). What to keep: the trigger phrase list is what the
marketplace routes on, and so is any **negative** rule — `soft-visuals`' "Do NOT use for data
charts" is what keeps charting requests off it.

Trimming `workshop-handbook` also turned up a description claiming **"auto-numbered chapters
and sections"**, which v0.7.0 removed. A description is documentation that nothing renders, so
it goes stale invisibly — reread it whenever the skill's behaviour changes.
