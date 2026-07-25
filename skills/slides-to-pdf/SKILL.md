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

`playwright install chromium` downloads a ~130 MB browser on first run. Tell the user this is happening — it takes a minute and looks like a hang otherwise. If the environment blocks `pip` (a managed/externally-managed Python), fall back to a venv:

```bash
python3 -m venv ~/.slides-to-pdf-venv && ~/.slides-to-pdf-venv/bin/pip install playwright pypdf && ~/.slides-to-pdf-venv/bin/python -m playwright install chromium
```

Then invoke the script with `~/.slides-to-pdf-venv/bin/python` instead of `python3`.

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

**Fonts look wrong / fell back to a system sans** — the deck loads Google Fonts from a CDN, so conversion needs network access. The script warns on `stderr` and continues rather than failing. Re-run when online, or accept the fallback.

**Backgrounds print white** — something dropped `printBackground` or the `print-color-adjust: exact` override. Both are set by the script; don't reimplement the export with a bare `chromium --print-to-pdf` CLI call, which cannot isolate slides and loses the per-slide loop entirely.

**`page.pdf()` raises "PDF generation is only supported in headless mode"** — the script launches headless; don't add `headless=False`.

## Do not

- **Don't use `chromium --headless --print-to-pdf` directly.** It renders the deck's single `.active` slide and produces a one-page PDF. The per-slide DOM manipulation is the whole point of driving Playwright.
- **Don't edit the deck's HTML to make slides visible.** All overrides are injected at runtime via `add_style_tag`; the source deck stays untouched and still works as an interactive presentation.
- **Don't leave `emulateMedia` at its default.** `page.pdf()` emulates `print` media unless told otherwise, and the deck has no `@media print` rules.
