#!/usr/bin/env python3
"""Convert a workshop-slides HTML deck into a single multi-page PDF.

The deck is an interactive single-page app: every `.slide` is absolutely
positioned at `inset: 0` with `opacity: 0`, and only the `.active` one is
visible. Printing it as-is yields one page showing one slide.

So this script drives headless Chromium (Playwright's `page.pdf()`, which is
Chrome's print-to-PDF) once per slide — forcing exactly that slide visible each
time — then merges the one-page PDFs with pypdf.

Usage:
    python3 slides_to_pdf.py deck.html [-o deck.pdf]
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

MISSING = []
try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:
    MISSING.append("playwright")
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    MISSING.append("pypdf")

if MISSING:
    sys.exit(
        "Missing dependencies: {}\n\n"
        "  python3 -m pip install {}\n"
        "  python3 -m playwright install chromium\n\n"
        "If the browser download is blocked, install one from a different host\n"
        "and point this script at it — no Playwright browser needed:\n\n"
        "  npx puppeteer browsers install chrome-headless-shell\n"
        "  {} deck.html --browser-path <path>\n\n"
        "An existing Chrome/Chromium/Edge install is found automatically.".format(
            ", ".join(MISSING), " ".join(MISSING), Path(sys.argv[0]).name
        )
    )


# Injected as the last stylesheet so it wins over the deck's own rules.
# WIDTH/HEIGHT are substituted before injection.
PRINT_CSS = """
@page { size: WIDTHpx HEIGHTpx; margin: 0; }

html, body {
  width: WIDTHpx !important;
  height: HEIGHTpx !important;
  overflow: hidden !important;
  /* Keep the deck's dark background and gradients in the PDF. */
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}

/* `position: fixed` is unreliable in paged output — pin decoration to the page. */
#bg { position: absolute !important; inset: 0 !important; }
#watermark { position: absolute !important; }

/* Print exactly one slide — the one tagged by the driver below. */
.slide { display: none !important; }
.slide.pdf-print-target {
  display: flex !important;
  position: absolute !important;
  inset: 0 !important;
  opacity: 1 !important;
  transform: none !important;
  transition: none !important;
  animation: none !important;
  pointer-events: auto !important;
}
"""

# Interactive chrome has no meaning on paper. Newer deck templates keep adding
# controls (navigator, theme toggle, fullscreen toggle), so rather than chase a
# hardcoded id list, hide every button that lives outside #deck — slide content
# never contains one, every control does.
CHROME_CSS = """
#navigator { display: none !important; }
button:not(#deck button) { display: none !important; }
"""

# Isolate one slide; report its title (for the bookmark) and whether its content
# exceeds the page box (for the clipping warning).
SELECT_SLIDE_JS = """(index) => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  slides.forEach((el, i) => {
    // .active / .exit drive the deck's own opacity transitions — drop them so
    // only the injected .pdf-print-target rule decides what is visible.
    el.classList.remove('active', 'exit');
    el.classList.toggle('pdf-print-target', i === index);
  });

  const el = slides[index];
  if (!el) return { title: '', overflowY: 0, overflowX: 0 };

  // Two separate lookups, not one selector list: on section dividers the
  // .section-label sits *before* the .slide-title, and querySelector returns
  // whichever comes first in the document, not first in the selector list.
  const t = el.querySelector('.slide-title') || el.querySelector('.section-label');
  // innerText, not textContent: titles wrap words in <br>, which textContent
  // would splice into "Beautiful DecksInstantly".
  const title = t ? (t.innerText || t.textContent).trim().replace(/\\s+/g, ' ') : '';

  // The slide is pinned to the page box inside an overflow:hidden body, so
  // content that does not fit is silently cropped rather than pushed onto a
  // second PDF page. Measure it instead of trusting the page count.
  return {
    title,
    overflowY: Math.max(0, el.scrollHeight - el.clientHeight),
    overflowX: Math.max(0, el.scrollWidth - el.clientWidth),
  };
}"""


# Playwright's own browser download (`playwright install chromium`) comes off
# playwright.azureedge.net, which some networks block outright. Any
# Chromium-family binary already on the machine works instead — Playwright takes
# it via `executable_path`. Checked in order; first hit wins.
BROWSER_ENV_VARS = ("SLIDES_TO_PDF_BROWSER", "PLAYWRIGHT_CHROMIUM_PATH")

BROWSER_FALLBACK_PATHS = (
    # Puppeteer's cache — `npx puppeteer browsers install chrome-headless-shell`
    # reaches a different host (googlechromelabs) than Playwright's CDN.
    "~/.cache/puppeteer",
    # Ordinary desktop installs.
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)


def find_browser(explicit: str | None) -> str | None:
    """Resolve a Chromium binary, or None to let Playwright use its own."""
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            sys.exit("browser not found at --browser-path {}".format(p))
        return str(p)

    for var in BROWSER_ENV_VARS:
        val = os.environ.get(var)
        if val:
            p = Path(val).expanduser()
            if p.exists():
                return str(p)
            print(
                "warning: {}={} does not exist — ignoring".format(var, val),
                file=sys.stderr,
            )

    for entry in BROWSER_FALLBACK_PATHS:
        p = Path(entry).expanduser()
        if p.is_file():
            return str(p)
        if p.is_dir():
            # Puppeteer nests the binary under a versioned directory, and on
            # macOS inside an .app bundle:
            #   ~/.cache/puppeteer/chrome/mac-1095492/chrome-mac/
            #       Chromium.app/Contents/MacOS/Chromium
            # An intermediate *directory* is also named `chrome`, so match
            # executable files only — handing Playwright a directory fails at
            # exec, with an error that does not name the real cause.
            for name in ("chrome-headless-shell", "Chromium", "chrome", "chromium"):
                hits = [
                    h
                    for h in sorted(p.glob("**/" + name))
                    if h.is_file() and os.access(h, os.X_OK)
                ]
                if hits:
                    # Lexicographically last ≈ highest version directory.
                    return str(hits[-1])
    return None


def render_slides(
    html: Path,
    width: int,
    height: int,
    device_scale: float,
    keep_ui: bool,
    theme: str,
    timeout_ms: int,
    browser_path: str | None = None,
) -> list[tuple[bytes, str]]:
    """Return one (single-page PDF bytes, slide title) tuple per slide."""
    css = PRINT_CSS.replace("WIDTH", str(width)).replace("HEIGHT", str(height))
    if not keep_ui:
        css += CHROME_CSS

    out: list[tuple[bytes, str]] = []

    with sync_playwright() as pw:
        launch_kwargs = {}
        if browser_path:
            launch_kwargs["executable_path"] = browser_path
            print("using browser at {}".format(browser_path), file=sys.stderr)

        browser = pw.chromium.launch(
            **launch_kwargs,
            args=[
                # Deterministic glyph rasterization and no color-profile shift,
                # so the PDF matches the on-screen deck.
                "--font-render-hinting=none",
                "--force-color-profile=srgb",
            ]
        )
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale,
        )
        page = context.new_page()
        page.goto(html.resolve().as_uri(), wait_until="load", timeout=timeout_ms)

        # page.pdf() emulates print media by default; the deck styles the screen.
        page.emulate_media(media="screen")

        # Newer templates ship a dark/light toggle driven by [data-theme] on
        # <html>, seeded from localStorage (so a fresh headless profile gets the
        # deck's own default). Override it only when explicitly asked.
        if theme != "as-is":
            page.evaluate(
                "t => document.documentElement.setAttribute('data-theme', t)", theme
            )

        page.add_style_tag(content=css)

        # Google Fonts come off a CDN. Wait for them, but degrade to fallback
        # families rather than failing the whole conversion when offline.
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            page.evaluate("document.fonts.ready")
        except PlaywrightError:
            print(
                "warning: webfonts did not finish loading — the PDF may use "
                "fallback fonts",
                file=sys.stderr,
            )

        total = page.eval_on_selector_all(".slide", "els => els.length")
        if not total:
            browser.close()
            sys.exit(f"no .slide elements found in {html} — is this a slide deck?")

        clipped: list[str] = []

        for i in range(total):
            info = page.evaluate(SELECT_SLIDE_JS, i)
            title = info["title"]
            pdf = page.pdf(
                width=f"{width}px",
                height=f"{height}px",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            out.append((pdf, title))

            # 2px tolerance absorbs sub-pixel layout rounding.
            over_y, over_x = info["overflowY"], info["overflowX"]
            note = ""
            if over_y > 2 or over_x > 2:
                dims = ", ".join(
                    part
                    for part in (
                        f"{over_y:.0f}px too tall" if over_y > 2 else "",
                        f"{over_x:.0f}px too wide" if over_x > 2 else "",
                    )
                    if part
                )
                note = f"  ← CLIPPED ({dims})"
                clipped.append(f"slide {i + 1} ({title or 'untitled'}): {dims}")
            print(
                f"  [{i + 1}/{total}] {title or '(untitled)'}{note}", file=sys.stderr
            )

        browser.close()

    if clipped:
        print(
            "\nwarning: content did not fit the page box and was cropped:",
            file=sys.stderr,
        )
        for line in clipped:
            print(f"  - {line}", file=sys.stderr)
        print(
            "  Trim or split these slides in the HTML deck, then re-run.",
            file=sys.stderr,
        )

    return out


def merge(slides: list[tuple[bytes, str]], out_path: Path) -> None:
    """Merge one-page PDFs into a single document, one bookmark per slide."""
    writer = PdfWriter()
    for i, (pdf, title) in enumerate(slides):
        reader = PdfReader(io.BytesIO(pdf))
        if len(reader.pages) > 1:
            # Content overflowed the page box; extra pages are spillover, not slides.
            print(
                f"warning: slide {i + 1} produced {len(reader.pages)} pages — "
                "keeping the first, content may be clipped",
                file=sys.stderr,
            )
        writer.add_page(reader.pages[0])
        writer.add_outline_item(title or f"Slide {i + 1}", i)
    with out_path.open("wb") as fh:
        writer.write(fh)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert a workshop-slides HTML deck to a single PDF."
    )
    ap.add_argument("html", type=Path, help="input deck (.html)")
    ap.add_argument(
        "-o", "--output", type=Path, help="output PDF (default: <input>.pdf)"
    )
    ap.add_argument("--width", type=int, default=1280, help="slide width in px")
    ap.add_argument("--height", type=int, default=720, help="slide height in px")
    ap.add_argument(
        "--device-scale",
        type=float,
        default=2.0,
        help="browser device pixel ratio (default 2). Note: print-to-PDF output "
        "is resolution-independent — text is vector and images pass through at "
        "native resolution — so this does not change the PDF for typical decks. "
        "It only matters for content that branches on devicePixelRatio.",
    )
    ap.add_argument(
        "--keep-ui",
        action="store_true",
        help="keep on-screen chrome (navigator, theme/fullscreen toggles) in the PDF",
    )
    ap.add_argument(
        "--theme",
        choices=("as-is", "dark", "light"),
        default="as-is",
        help="force [data-theme] on decks with a dark/light toggle "
        "(default: as-is, which uses the deck's own default)",
    )
    ap.add_argument(
        "--timeout", type=int, default=30000, help="per-step timeout in ms"
    )
    ap.add_argument(
        "--browser-path",
        help="Chromium-family binary to drive, for when `playwright install "
        "chromium` is blocked. Also read from $SLIDES_TO_PDF_BROWSER or "
        "$PLAYWRIGHT_CHROMIUM_PATH; otherwise a Puppeteer cache and the usual "
        "Chrome/Chromium/Edge install paths are probed.",
    )
    args = ap.parse_args()

    if not args.html.is_file():
        sys.exit(f"not a file: {args.html}")

    out_path = args.output or args.html.with_suffix(".pdf")
    print(f"rendering {args.html.name} at {args.width}x{args.height} "
          f"@{args.device_scale:g}x", file=sys.stderr)

    slides = render_slides(
        args.html,
        args.width,
        args.height,
        args.device_scale,
        args.keep_ui,
        args.theme,
        args.timeout,
        find_browser(args.browser_path),
    )
    merge(slides, out_path)

    size_kb = out_path.stat().st_size / 1024
    print(f"wrote {out_path} — {len(slides)} pages, {size_kb:.0f} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
