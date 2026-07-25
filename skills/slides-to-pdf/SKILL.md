---
name: slides-to-pdf
description: >
  Exports an HTML slide deck (from the workshop-slides skill, or any deck whose slides
  carry class="slide") to a single multi-page PDF — one page per slide at 1280×720
  (true 16:9), with the dark background, gradients, webfonts, accent colors and inline
  SVG diagrams exactly as they appear on screen. Runs one headless-Chromium
  print-to-PDF command; no Playwright, no per-slide loop, no merge step. Use this skill
  whenever the user wants to export, convert, download, print, or share a slide deck as
  a PDF. Triggers on phrases like "convert my slides to PDF", "export the deck as PDF",
  "turn this HTML deck into a PDF", "make a PDF of the slides", "print the deck", "I
  need a PDF version", "slides to pdf". Also trigger proactively right after generating
  a deck with workshop-slides if the user mentions emailing, uploading, printing, or
  handing out the slides.
---

# Slides → PDF

One command. `assets/export.py` copies the deck, injects a print stylesheet, and lets
Chromium's own `--print-to-pdf` paginate it.

**Requires a local headless Chromium** — that is the skill's one prerequisite, and it
fails fast with an install command if none is found. Everything else is Python stdlib: no
`playwright`, no required `pypdf`, no network.

## Step 1 — Find the deck

Use the `.html` deck the user just generated. If several exist or it's ambiguous, ask
which file.

## Step 2 — Export

```bash
python3 skills/slides-to-pdf/assets/export.py path/to/deck.html
```

Writes `path/to/deck.pdf`. It resolves a browser itself, preferring a
`chrome-headless-shell` build (see *Pitfalls* — this matters), and prints the page count
and page size when it's done:

```
browser: …/chromium_headless_shell-1228/…/chrome-headless-shell
wrote …/deck.pdf — 25 page(s), 960 × 540 pt, 799,003 bytes
```

| Option | Default | |
|---|---|---|
| `-o, --out` | `<deck>.pdf` | output path |
| `--theme dark\|light\|as-is` | `as-is` | forces the deck's theme; `as-is` takes its own default (dark) |
| `--page WxH` | `1280x720` | stage size in px. **A deck built on another stage needs this** — the injected CSS sizes every slide to it, so a 1600×900 deck left at the default is silently cropped |
| `--browser-path` | auto | a specific headless Chromium |
| `--timeout` | `120` | seconds before the browser is killed |
| `--keep-temp` | off | keeps the injected copy for debugging |

It also counts the deck's `class="slide"` elements and warns if the PDF's page count doesn't match — that is the one check on the injected CSS's assumptions, so don't ignore it.

## Step 3 — Report

Tell the user the path, the page count, and that it's 960 × 540 pt (13.333 × 7.5 in) —
the same 16:9 as PowerPoint and Keynote widescreen. Text stays vector, selectable and
searchable. To verify independently:

```bash
python3 -c "from pypdf import PdfReader; r=PdfReader('deck.pdf'); print(len(r.pages), r.pages[0].mediabox)"
```

To *look* at a page rather than trust it, render one to an image —
`qlmanage -t -s 1400 -o thumbs deck.pdf` gives page 1; split first with `pypdf` for the
rest.

## If no browser is found

The script says so and stops. Install the headless shell (~150 MB, no Playwright
needed):

```bash
npx puppeteer browsers install chrome-headless-shell
```

Failing that, a deck from `workshop-slides` also exports correctly by hand: open it in
any browser and Cmd-P → Save as PDF. Its own `@media print` block produces the same
1280×720 pages (measured equivalent to this script's output). Say that plainly rather
than shipping a broken PDF.

## Pitfalls

Each of these was measured, not assumed.

- **A modern full Chrome hangs forever on `--print-to-pdf`.** Chrome for Testing 150
  produced nothing under plain `--headless`, `--headless=old`,
  `--headless --no-sandbox`, and `--run-all-compositor-stages-before-draw` — every one
  timed out. `chrome-headless-shell` 141 and the old Chromium 111 both export in under
  4 s. That is why the resolver prefers headless-shell over full Chrome, and why
  `--timeout` kills rather than waits.
- **Never rely on the deck's own `@media print` block.** A deck without one exports as
  **one page of US Letter** — the first slide, silently. The injected stylesheet is what
  guarantees the pagination, and it makes the export work on old decks and hand-written
  ones. It does not override everything, though: the injected rules land *after* the
  deck's own print block and cascade with it, so a deck that prints
  `.slide { display: none }` still exports blank — measured. The page-count warning is
  what catches that.
- **Stamping `data-theme` on `<html>` does not switch the theme.** The deck's inline
  script re-sets that attribute from `localStorage` after load, so the export injects a
  script that seeds the key *and* re-asserts on `load`.
- **`opacity: 0` still renders to PDF** — hiding a slide needs `display: none` or the
  absolute positioning the injected CSS undoes.
- **Playwright's `page.pdf()` renders *screen* media** unless you call
  `emulateMedia({media:'print'})` first. `--print-to-pdf` uses print media natively,
  which is why this skill needs no Playwright at all.
- **`task_policy_set TASK_CATEGORY_POLICY` on macOS is harmless noise** — the PDF still
  writes.
- **Don't diagnose a webfont failure from the PDF's font names.** `pypdf` reports
  page-1 `/BaseFont` values like `/AAAAAA+Helvetica` for a deck whose fonts loaded
  perfectly — print-to-PDF labels embedded subsets generically, and Google Sans comes
  through as `Type3 /None`. Render the page to an image and look at the letterforms
  instead.

Prior art: `~/.hermes/skills/html-slides-to-pdf/SKILL.md` reached the same one-command
approach independently; this skill adds the injection step (which removes its two
Playwright fallbacks) and the browser-choice constraint above.
