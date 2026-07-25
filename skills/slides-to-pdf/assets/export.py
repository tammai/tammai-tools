#!/usr/bin/env python3
"""Export an HTML slide deck to a multi-page PDF — one page per slide.

Stdlib only. One headless-Chromium invocation, no Playwright, no merge step.

The deck is a single-page app: every `.slide` sits at `position: absolute; inset: 0`
with `opacity: 0`, and only `.active` is visible. A print stylesheet is injected into
a copy of the deck to return the slides to the flow at the page size with a break
after each, which is what turns one command into a full deck.

Injecting rather than relying on the deck's own `@media print` block is deliberate:
a deck without one exports as a single US Letter page (measured), and the injected
rules also carry `--theme`, so no browser scripting is needed for either case.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

# Injected before </head>, so it lands after the deck's own <style> and wins on
# cascade order. This is a deliberate **fork** of the `@media print` block in
# `workshop-slides/assets/template.html` — the deck keeps its copy for a
# dependency-free Cmd-P export, and this one exists because a deck *without* that
# block exports as a single US Letter page. The two are not independent: rules the
# template prints that this block does not override still apply, so a change to
# either belongs in both. (Same standing rule as the shared `--dg-*` tokens.)
#
# `.slide:last-child` releases the break so the deck does not end on a blank page.
# print-color-adjust keeps the dark background, the radial glows, the callout tints
# and the code-block fills.
PRINT_CSS = """<style id="pdf-export-overrides">
@page { size: __W__px __H__px; margin: 0; }
@media print {
  /* margin: 0 matters for decks without their own reset — the browser's default
     8px body margin pushes the last slide onto an extra page. */
  html, body { width: auto; height: auto; overflow: visible; display: block;
               margin: 0; background: var(--brand-bg); }
  #deck { position: static !important; width: __W__px; height: auto !important;
          transform: none !important; }
  .slide { position: relative !important; inset: auto !important; opacity: 1 !important;
           pointer-events: auto; transform: none !important; transition: none !important;
           width: __W__px; height: __H__px; box-sizing: border-box; overflow: hidden;
           break-after: page; page-break-after: always; }
  .slide:last-child { break-after: auto; page-break-after: auto; }
  #navigator, button:not(#deck button) { display: none !important; }
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
}
</style>"""

# Chromium's own print-to-PDF. `--virtual-time-budget` gives webfonts and layout time
# to settle before the snapshot; the page is a file:// URL so this is the only wait.
CHROME_ARGS = [
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--no-pdf-header-footer",
    "--virtual-time-budget=10000",
]


def fail(msg: str) -> NoReturn:
    sys.exit("error: " + msg)


def print_css(width: int, height: int) -> str:
    return PRINT_CSS.replace("__W__", str(width)).replace("__H__", str(height))


def theme_script(theme: str) -> str:
    """Force a theme on a deck that picks its own.

    Stamping `data-theme` on <html> is not enough: the deck's inline script runs at the
    end of <body> and *unconditionally* re-sets the attribute from localStorage (which a
    fresh headless profile lacks, so it lands on its default). Seeding the key handles
    decks that read it; re-asserting on `load` — which fires after that inline script —
    wins for every other deck without knowing its storage key. The bare call covers a
    deck with no theme script at all.
    """
    t = json.dumps(theme)
    return (
        "<script>(function(){var t=%s;"
        "try{localStorage.setItem('workshop-deck-theme',t)}catch(e){}"
        "var s=function(){document.documentElement.setAttribute('data-theme',t)};s();"
        "window.addEventListener('load',s)})();</script>" % t
    )


# ─────────────────────────────────────────────────────────────────────────────
# Browser discovery
#
# headless-shell is preferred over full Chrome, and not as a style choice:
# `--print-to-pdf` on a modern full Chrome (tested: Chrome for Testing 150) hangs
# forever with no output, under plain --headless, --headless=old, --no-sandbox and
# --run-all-compositor-stages-before-draw alike. headless-shell 141 and the old
# Chromium 111 both export in under 4s.
# ─────────────────────────────────────────────────────────────────────────────

SHELL_NAMES = ("headless_shell", "chrome-headless-shell")
FULL_NAMES = ("Chromium", "Google Chrome for Testing", "chrome", "Google Chrome")

# Deepest launcher observed is 6 components in (…/chrome-mac-x64/Google Chrome for
# Testing.app/Contents/MacOS/…). Pruning below that skips the framework and .lproj
# trees inside every .app bundle: measured on a real cache, 523 entries instead of
# 2039, 12ms instead of 100ms.
MAX_DEPTH = 7

CACHES = (
    Path.home() / "Library/Caches/ms-playwright",
    Path.home() / ".cache/ms-playwright",
    Path.home() / ".cache/puppeteer",
)

INSTALLED = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
)


def _runnable(p: Path) -> bool:
    # is_file() matters: an intermediate *directory* named `chrome` exists in the
    # Puppeteer cache, and exec on a directory fails with an error that never says why.
    return p.is_file() and os.access(p, os.X_OK)


def _revision(rel: Path) -> int:
    # Best-effort "newest build first" within a class. The revision sits in a different
    # component per cache — Playwright's `chromium_headless_shell-1228` versus
    # Puppeteer's `chrome/mac-150.0.7871.24` — so the largest number anywhere in the
    # path is used rather than a fixed position, which scored every Puppeteer build 0.
    # `rel` must be relative to the cache root: over an absolute path, digits in the
    # user's home directory swamp the revision and tie every candidate.
    return max((int(n) for n in re.findall(r"\d+", str(rel))), default=0)


def _scan(cache: Path) -> tuple[list[tuple[int, Path]], list[tuple[int, Path]]]:
    """Return (headless-shell, full-browser) binaries in one cache, each with its revision."""
    shell: list[tuple[int, Path]] = []
    full: list[tuple[int, Path]] = []
    if not cache.is_dir():
        return shell, full
    for root, dirs, files in os.walk(cache):
        rel = Path(root).relative_to(cache)
        if len(rel.parts) >= MAX_DEPTH:
            dirs[:] = []
        for name in files:
            if name in SHELL_NAMES or name in FULL_NAMES:
                p = Path(root, name)
                if _runnable(p):
                    hit = (_revision(rel / name), p)
                    (shell if name in SHELL_NAMES else full).append(hit)
    return shell, full


def find_browser(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            fail(f"--browser-path does not exist: {p}")
        if p.is_dir():
            fail(f"--browser-path is a directory, not an executable: {p}")
        if not _runnable(p):
            fail(f"--browser-path is not executable: {p}")
        return p

    if env := os.environ.get("SLIDES_TO_PDF_BROWSER"):
        p = Path(env).expanduser()
        if _runnable(p):
            return p

    shell: list[tuple[int, Path]] = []
    full: list[tuple[int, Path]] = []
    for cache in CACHES:
        s, f = _scan(cache)
        shell += s
        full += f
    for group in (shell, full):
        if group:
            return max(group, key=lambda hit: hit[0])[1]

    for path in INSTALLED:
        if _runnable(Path(path)):
            return Path(path)

    fail(
        "no headless Chromium found. Install one with:\n"
        "  npx puppeteer browsers install chrome-headless-shell\n"
        "or pass --browser-path /path/to/headless_shell"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────


def prepare(deck: Path, theme: str, page: tuple[int, int]) -> tuple[str, int]:
    """Return the HTML to export and the slide count to expect. Writes nothing.

    Nothing is written here so that a deck which is not HTML fails before the browser
    caches are walked, without leaving a scratch file behind if the browser lookup
    then fails too.
    """
    html = deck.read_text(encoding="utf-8")
    if "</head>" not in html:
        fail(f"{deck.name} has no </head> — is it an HTML deck?")

    # Count elements whose class list carries the `slide` token, so `.slide-header`
    # and friends don't inflate it. report() compares this to the page count.
    # Comments are stripped first: the template's own placeholder block *documents*
    # `class="slide slide--cover active"` in prose, which otherwise counts as three
    # slides that will never paginate — the same trap build.py's check_svg_viewbox
    # documents. Both quote styles are accepted.
    body = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    slides = sum(
        1 for cls in re.findall(r"""class\s*=\s*["']([^"']*)["']""", body) if "slide" in cls.split()
    )

    inject = print_css(*page) + (theme_script(theme) if theme != "as-is" else "")
    return html.replace("</head>", inject + "\n</head>", 1), slides


def report(pdf: Path, slides: int) -> None:
    size = f"{pdf.stat().st_size:,} bytes"
    try:
        from pypdf import PdfReader  # optional — only used to describe the result
    except ImportError:
        print(f"wrote {pdf} — {slides} slide(s) in, {size} (install pypdf for a page report)", flush=True)
        return

    pages = PdfReader(pdf).pages
    boxes = {(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in pages}
    geom = "{} × {} pt".format(*boxes.pop()) if len(boxes) == 1 else f"mixed sizes {sorted(boxes)}"
    print(f"wrote {pdf} — {len(pages)} page(s), {geom}, {size}", flush=True)
    if len(pages) != slides:
        print(
            f"warning: the deck has {slides} slide(s) but the PDF has {len(pages)} page(s). "
            'Slides that do not carry class="slide", or a print rule in the deck that '
            "hides them, do not paginate.",
            file=sys.stderr,
        )


def page_size(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)x(\d+)", text.strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(f"expected WIDTHxHEIGHT in px, e.g. 1280x720 (got {text!r})")
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck", type=Path, help="the .html slide deck")
    ap.add_argument("-o", "--out", type=Path, help="output PDF (default: <deck>.pdf)")
    ap.add_argument("--theme", choices=("dark", "light", "as-is"), default="as-is")
    ap.add_argument("--page", type=page_size, default=(1280, 720),
                    help="stage size in px (default: 1280x720, the workshop-slides stage)")
    ap.add_argument("--browser-path", help="headless Chromium to use")
    ap.add_argument("--timeout", type=int, default=120, help="seconds (default: 120)")
    ap.add_argument("--keep-temp", action="store_true", help="keep the injected copy")
    args = ap.parse_args()

    deck = args.deck.expanduser().resolve()
    if not deck.is_file():
        fail(f"no such deck: {deck}")
    out = args.out.expanduser().resolve() if args.out else deck.with_suffix(".pdf")

    # Validated before the browser caches are walked, so a deck that is not HTML
    # fails immediately — but nothing is on disk yet if the lookup below fails.
    html, slides = prepare(deck, args.theme, args.page)
    browser = find_browser(args.browser_path)
    print(f"browser: {browser}", flush=True)

    # Scratch lives in a temp dir, not beside the user's deliverable — except the deck
    # copy, which must sit next to the original for relative asset paths (a preset's
    # local logo) to resolve.
    scratch = tempfile.mkdtemp(prefix="slides-to-pdf-")
    tmp = deck.with_suffix(".pdfexport-tmp.html")

    # Chromium writes here, not to `out`: a run that fails or hangs must not touch an
    # existing PDF, and a stale one must never be mistaken for this run's output.
    raw = Path(scratch, "out.pdf")
    cmd = [
        str(browser), *CHROME_ARGS,
        f"--user-data-dir={Path(scratch, 'profile')}",
        f"--print-to-pdf={raw}",
        tmp.as_uri(),
    ]
    try:
        tmp.write_text(html, encoding="utf-8")
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=args.timeout, text=True)
        except subprocess.TimeoutExpired:
            fail(
                f"{browser.name} hung for {args.timeout}s and was killed.\n"
                "  A modern full Chrome cannot do --print-to-pdf from the command line.\n"
                "  Install the headless shell instead:\n"
                "    npx puppeteer browsers install chrome-headless-shell"
            )
        if not raw.is_file() or raw.stat().st_size == 0:
            tail = (proc.stderr or "").strip().splitlines()[-3:]
            fail(f"{browser.name} wrote no PDF (exit {proc.returncode}). " + " | ".join(tail))
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(raw), out)  # only now does `out` change
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        if args.keep_temp:
            print(f"kept {tmp}", flush=True)
        else:
            tmp.unlink(missing_ok=True)

    report(out, slides)
    return 0


if __name__ == "__main__":
    sys.exit(main())
