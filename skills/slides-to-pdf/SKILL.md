---
name: slides-to-pdf
description: >
  Converts an HTML slide deck (produced by the workshop-slides skill) into a single
  multi-page PDF — one page per slide, at 1280×720 (16:9), with backgrounds, gradients,
  Google Fonts, and accent colors preserved exactly as they appear on screen. Renders
  each slide through headless Chromium's print-to-PDF via Playwright, then merges the
  pages with pypdf. Use this skill whenever the user wants to export, convert, download,
  print, or share a slide deck as a PDF. Triggers on phrases like "convert my slides to
  PDF", "export the deck as PDF", "turn this HTML deck into a PDF", "make a PDF of the
  slides", "print the deck", "I need a PDF version", "slides to pdf". Also trigger
  proactively right after generating a deck with workshop-slides if the user mentions
  emailing, uploading, printing, or handing out the slides.
---

# Slides → PDF

Exports a `workshop-slides` HTML deck to a single PDF, one page per slide.

The deck is an interactive single-page app: every `.slide` sits at `position: absolute; inset: 0` with `opacity: 0`, and only the `.active` slide is visible. Opening it in a print dialog therefore yields **one** page showing **one** slide. This skill works around that by driving the browser once per slide.

## How it works

1. Headless Chromium loads the deck (`file://` URL) at a 1280×720 viewport, `deviceScaleFactor: 2`.
2. Print-media emulation is switched **off** (`emulateMedia({ media: 'screen' })`) — the deck only ever styles the screen, so emulating `print` would strip its look.
3. An override stylesheet is injected: `@page { size: 1280px 720px; margin: 0 }`, `print-color-adjust: exact`, interactive chrome hidden, and `.slide` display forced off except for one tagged target.
4. For each slide: tag it, call `page.pdf({ printBackground: true, preferCSSPageSize: true })`, keep the bytes.
5. `pypdf` merges the one-page PDFs into one document, adding a bookmark per slide from its `.slide-title`.

## Output geometry

| Property | Value |
|---|---|
| Page size | 1280 × 720 px → **960 × 540 pt** → 13.333 × 7.5 in |
| Aspect ratio | 16:9 (identical to PowerPoint/Keynote widescreen) |
| Device scale | 2× (set, but see below) |
| Text | Vector, selectable and searchable |

**On "retina 2×" — the PDF is better than 2×, and not because of the device scale.** Print-to-PDF output is resolution-independent by construction:

- **Text** is emitted as Type3 fonts — glyph outlines drawn as vector procedures. It stays sharp at *any* zoom, and it remains selectable and searchable (verified: `extract_text()` returns the real slide copy).
- **Borders, gradients, and fills** are vector instructions.
- **Raster images** (a PNG logo in a custom preset) are passed through at their **native** resolution.

So `deviceScaleFactor` has no observable effect on the output. This was measured, not assumed: rendering the same deck at `--device-scale 1`, `2`, and `3` produces byte-identical 460 KB files with identical Type3 text, a PNG watermark embeds at its native 240×160 at every setting, and an `<img srcset="… 1x, … 2x">` selects the 2× variant even at DPR 1.

The flag stays (defaulting to 2) because it sets the browser's DPR, which matters only for a deck whose JS or `image-set()` branches on `devicePixelRatio`. **Do not tell the user that 2× doubles the PDF's resolution, or that lowering it shrinks the file** — neither is true.

## Step 1 — Locate the deck

Find the `.html` deck to convert. If the user just generated one in this session, use that path. If ambiguous, ask which file.

## Step 2 — Check dependencies

The script needs `playwright` (plus its Chromium binary) and `pypdf`:

```bash
python3 -c "import playwright, pypdf" 2>&1
```

If anything is missing, install it:

```bash
python3 -m pip install playwright pypdf && python3 -m playwright install chromium
```

**Check for an existing browser before running `playwright install chromium`:**

```bash
ls -d ~/.cache/puppeteer/*/*/*/ /Applications/Google\ Chrome.app 2>/dev/null | head
```

If that finds anything, skip the browser download entirely — the script's probe (below) will pick it up. This ordering matters on a sandboxed host: `playwright install chromium` pulls from `playwright.azureedge.net`, which Claude Cowork blocks, and the failure presents as a stalled ~130 MB download rather than a refusal. Spending a minute on a download that cannot succeed, then falling back, is the slow path through a problem the probe answers immediately.

`playwright install chromium` downloads a ~130 MB browser on first run. Tell the user this is happening — it takes a minute and looks like a hang otherwise. If the environment blocks `pip` (a managed/externally-managed Python), fall back to a venv:

```bash
python3 -m venv ~/.slides-to-pdf-venv && ~/.slides-to-pdf-venv/bin/pip install playwright pypdf && ~/.slides-to-pdf-venv/bin/python -m playwright install chromium
```

Then invoke the script with `~/.slides-to-pdf-venv/bin/python` instead of `python3`.

### If the browser download is blocked

`playwright install chromium` pulls from `playwright.azureedge.net`. Some networks block it, and the failure looks like a stalled download rather than a refusal. **The Python packages are still needed** (`playwright` and `pypdf` come from PyPI, a different host) — it's only the browser binary that has to come from somewhere else. Any Chromium-family binary works; Playwright drives it via `executable_path`.

The script probes for one automatically, in this order:

1. `--browser-path <path>`
2. `$SLIDES_TO_PDF_BROWSER`, then `$PLAYWRIGHT_CHROMIUM_PATH` (a non-existent path warns and falls through)
3. `~/.cache/puppeteer` — including the macOS `.app` bundle nesting
4. The usual Chrome / Chromium / Edge install paths on macOS and Linux

So in most cases an existing browser is found with no flag at all. To install one from a different host:

```bash
npx puppeteer browsers install chrome-headless-shell
```

That downloads from `googlechromelabs`, not Playwright's CDN. Then either let the probe find it, or be explicit:

```bash
python3 assets/slides_to_pdf.py deck.html --browser-path "$(ls -d ~/.cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell | tail -1)"
```

The script prints `using browser at <path>` when it drives an external binary, so the log says which one was used.

## Step 3 — Convert

Run `assets/slides_to_pdf.py` (in the same directory as this SKILL.md):

```bash
python3 assets/slides_to_pdf.py path/to/deck.html -o path/to/deck.pdf
```

Omit `-o` and the output lands next to the input with a `.pdf` extension. Progress prints one line per slide to stderr, flagging any slide whose content was cropped (see Troubleshooting).

### Options

| Flag | Default | Use when |
|---|---|---|
| `-o, --output` | `<input>.pdf` | Writing somewhere other than beside the input |
| `--width` / `--height` | `1280` / `720` | The user wants 4:3 (`1024`/`768`) or a different slide size |
| `--device-scale` | `2.0` | Rarely — it does not change the PDF (see above). Only for decks whose JS branches on `devicePixelRatio` |
| `--keep-ui` | off | The user explicitly wants on-screen chrome (navigator, theme/fullscreen toggles) visible in the PDF |
| `--theme` | `as-is` | The deck has a dark/light toggle and the user wants a specific mode — e.g. `--theme light` for a printer-friendly version |
| `--timeout` | `30000` | Slow network or a very large deck |
| `--no-embed-fonts` | off (fonts *are* embedded) | Rarely — only to reproduce the old CDN-dependent behaviour, or if npm is unavailable and its warning is noise |
| `--font-subsets` | `latin,latin-ext,vietnamese` | A deck in a script none of those cover (Cyrillic, Greek, CJK) |
| `--font-dir` | — | No npm registry access: point at pre-fetched `npm pack` tarballs |

### Fonts are embedded by default

The deck keeps its Google Fonts `<link>` — correct for an interactive page. A PDF cannot rely on that: it is a snapshot of whatever rendered, so a blocked or slow CDN is baked in **permanently and silently**, and the PDF simply *is* the fallback font with nothing to re-try later. Claude Cowork blocks `fonts.googleapis.com` outright, which is exactly this case.

So before rendering, the script reads the families off the live page (`--brand-font-*`, so a preset's fonts are picked up too), fetches the matching woff2 from npm's `@fontsource*` packages, and injects them as `data:` URI `@font-face` rules. Nothing is written to the deck — the same contract as every other override here. npm is used because it stays reachable in sandboxes that block Google's CDN.

Measured on the 15-slide reference deck, with the font CDN made unresolvable:

| Export | Page 1 vs the online-CDN render |
|---|---|
| Embedded (default) | **0.19%** of pixels differ — same typography |
| `--no-embed-fonts` | **2.64%** of pixels differ — fallback font |

It adds ~1 s and 177 KB of woff2 (Google Sans latin/latin-ext/vietnamese × upright+italic, Fira Code latin/latin-ext). It prefers each family's *variable* package, so weights 400–700 come from one file per subset rather than four static faces.

**Do not drop `vietnamese` from the subsets for a Vietnamese deck.** Without it the diacritics alone fall out of the embedded face and the browser substitutes a system font for those glyphs only — the slide then renders in two typefaces at once, which is harder to spot than a wholesale fallback.

If a family has no Fontsource package, the script warns and continues with whatever the page loaded; it never fails the export over fonts. One caveat worth passing on: `@fontsource-variable/google-sans` is new (published July 2026, from the Fontsource maintainers, declaring OFL-1.1), and Google Sans was historically Google-proprietary — confirm the licence before distributing PDFs that embed it. Fira Code, DM Sans and the other open families raise no such question.

## Step 4 — Verify before reporting

Confirm the page count matches the slide count, and confirm the geometry:

```bash
python3 -c "
from pypdf import PdfReader
r = PdfReader('deck.pdf'); b = r.pages[0].mediabox
print(len(r.pages), 'pages', float(b.width), 'x', float(b.height), 'pt')"
```

Expect `960.0 x 540.0` pt for the default 1280×720. Then report the real numbers — page count, dimensions, file size — rather than just declaring success.

**Do not judge text quality with pypdf's `extract_text()`.** It is fine for a rough word count, but it inserts spurious spaces at text-run boundaries, so a deck with accented text extracts as `"M ặ t h ạ n ch ế"` and a phrase search for `hạn chế` fails. This is an artifact of the extractor, **not** a defect in the PDF. The cause: Google Fonts splits families by `unicode-range`, so accented glyphs come from a different subset font (`M`→`BAAAAA+GoogleSans`, `ặ`→`CAAAAA+GoogleSans`), and Chrome emits a separate text run per font. Real viewers reconstruct words from glyph positions and search correctly — `pdfminer.six` extracts the same page as a clean `"Mặt hạn chế & điều cần lưu ý"`. If you genuinely need to verify text, use pdfminer, not pypdf.

## Troubleshooting

**`← CLIPPED (Npx too tall)` in the output** — that slide has more content than fits in 720 px. Because slides are pinned to the page box inside an `overflow: hidden` body, the excess is **silently cropped** rather than flowing onto a second page; the PDF still has one page per slide and looks structurally fine while the bottom of that slide is simply gone. The script measures each slide and reports this, so never dismiss it as cosmetic. Fix the *deck*, not the export: trim the slide or split it in two, then re-run. Always relay these warnings to the user.

**`← OVERLAP (svg 132px past its column)` in the output** — a *different* failure from clipping, and the reason the two are reported separately. Nothing is cropped here: `.col` is `overflow: visible`, so an oversized child paints over whatever sits in the next column while the slide's own `scrollWidth` stays unchanged — the slide-level measurement above cannot see it. The usual cause is an `<svg>` with `width`/`height` attributes and no `class="diagram"`; adding that class constrains it to the column. Relay this too: the PDF looks structurally fine while two columns are drawn on top of each other.

**`← SVG OUTSIDE VIEWBOX (2px, viewBox 460x306)` in the output** — a **third** failure mode, independent of the two above, and the reason it is reported separately: nothing is cropped at the slide level and no column overlaps, so both of the other measurements return zero. Content outside an `<svg>`'s own `viewBox` is not clipped with a warning — it is never drawn. Real case: a seven-card layer stack running to `y=308` inside `viewBox="0 0 460 306"`, where exactly one card lost its bottom border and rounded corners while the six above kept theirs, in the deck *and* the PDF, silently.

Fix the deck: grow the `viewBox` to cover the shapes, remembering that a stroke straddles the edge it sits on (a 1.75px-stroked card ending at 308 puts ink at 308.875), or move the content in. The reported number comes from `getBBox()`, which **excludes stroke width**, so it reads ~0.9px low on a 1.75px stroke — treat it as a floor, not the exact overflow. Relay this like the others; the PDF looks structurally perfect while an edge is missing.

**Fonts look wrong / fell back to a system sans** — first read the export log. `embedded Google Sans (6 face(s), 129 KB)` means the fonts were self-hosted and the PDF is fine regardless of the CDN. If instead you see `no Fontsource package for …`, that family is not on npm under its own name (check the spelling of the preset's `fontMain`), and the PDF used whatever the page had. If npm itself is missing or blocked, fetch the tarballs on a machine that has it (`npm pack @fontsource-variable/<family>`) and pass `--font-dir`. `--no-embed-fonts` is the only way to get the old CDN-dependent behaviour, and offline it gives a fallback font.

Note the deck's *interactive* view is unaffected either way: it still uses the CDN, so a deck generated in a sandbox looks wrong on screen while exporting correctly. That split is deliberate — see the workshop-slides skill.

**Backgrounds print white** — something dropped `printBackground` or the `print-color-adjust: exact` override. Both are set by the script; don't reimplement the export with a bare `chromium --print-to-pdf` CLI call, which cannot isolate slides and loses the per-slide loop entirely.

**`page.pdf()` raises "PDF generation is only supported in headless mode"** — the script launches headless; don't add `headless=False`.

## Do not

- **Don't use `chromium --headless --print-to-pdf` directly.** It renders the deck's single `.active` slide and produces a one-page PDF. The per-slide DOM manipulation is the whole point of driving Playwright.
- **Don't edit the deck's HTML to make slides visible.** All overrides are injected at runtime via `add_style_tag`; the source deck stays untouched and still works as an interactive presentation.
- **Don't leave `emulateMedia` at its default.** `page.pdf()` emulates `print` media unless told otherwise, and the deck **does** carry an `@media print` block — written for a hand-driven Cmd-P export, where `#deck` becomes `position: static; height: auto` and each `.slide` rejoins the flow at `position: relative` with `break-after: page`. Those rules fight the per-slide isolation this script injects (one `.pdf-print-target`, absolutely positioned at `inset: 0`). Emulating `screen` keeps the two paths independent.
