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
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
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
  if (!el) return { title: '', overflowY: 0, overflowX: 0, overlap: null };

  // Two separate lookups, not one selector list: on section dividers the
  // .section-label sits *before* the .slide-title, and querySelector returns
  // whichever comes first in the document, not first in the selector list.
  const t = el.querySelector('.slide-title') || el.querySelector('.section-label');
  // innerText, not textContent: titles wrap words in <br>, which textContent
  // would splice into "Beautiful DecksInstantly".
  const title = t ? (t.innerText || t.textContent).trim().replace(/\\s+/g, ' ') : '';

  // A child wider than its column is NOT caught above: `.col` is
  // `overflow: visible`, so an oversized child paints over its neighbour
  // instead of growing the slide's scroll box. Measured case: an <svg> carrying
  // width="700" height="660" in a 568px column reaches 132px into the next
  // column — slide scrollWidth unchanged, nothing cropped, slide visually
  // broken. `class="diagram"` is what prevents it; this catches the omission.
  let overlap = null;
  for (const col of el.querySelectorAll('.col')) {
    const cb = col.getBoundingClientRect();
    if (cb.width === 0) continue;
    for (const child of col.children) {
      const cs = getComputedStyle(child);
      // Absolutely-positioned decoration is placed deliberately; a hidden child
      // has no visible geometry to collide with anything.
      if (cs.position === 'absolute' || cs.position === 'fixed') continue;
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const rb = child.getBoundingClientRect();
      // 2px of slack: subpixel layout rounding is not an overlap.
      const past = Math.max(rb.right - cb.right, cb.left - rb.left);
      if (past > 2 && (!overlap || past > overlap.px)) {
        const cls = (child.getAttribute('class') || '').trim().split(/\\s+/)[0];
        overlap = {
          px: Math.round(past),
          el: child.tagName.toLowerCase() + (cls ? '.' + cls : ''),
        };
      }
    }
  }

  // A third, independent failure: content outside an <svg>'s own viewBox is
  // not clipped with any signal — it is simply never drawn. A deck shipped on
  // 2026-07-25 had a seven-card stack running to y=308 inside
  // viewBox="0 0 460 306", so exactly one card lost its bottom border and
  // rounded corners while the six above kept theirs. Invisible in the browser,
  // invisible in the PDF, and neither measurement above can see it: the slide
  // does not overflow and the column does not overlap. getBBox() is exact here,
  // including curves, transforms and text runs that no static check can size.
  // Note getBBox() excludes stroke width, so a 2.9px overflow of a 1.75px
  // stroked edge measures as 2.0 — the tolerance stays low for that reason.
  let svgClip = null;
  for (const s of el.querySelectorAll('svg[viewBox]')) {
    const vb = s.viewBox.baseVal;
    if (!vb || !vb.width || !vb.height) continue;
    let b;
    try { b = s.getBBox(); } catch (e) { continue; }
    if (!b.width && !b.height) continue;
    const worst = Math.max(
      b.x + b.width - (vb.x + vb.width),
      b.y + b.height - (vb.y + vb.height),
      vb.x - b.x,
      vb.y - b.y,
    );
    if (worst > 1 && (!svgClip || worst > svgClip.px)) {
      svgClip = {
        px: Math.round(worst * 10) / 10,
        vb: Math.round(vb.width) + 'x' + Math.round(vb.height),
      };
    }
  }

  // The slide is pinned to the page box inside an overflow:hidden body, so
  // content that does not fit is silently cropped rather than pushed onto a
  // second PDF page. Measure it instead of trusting the page count.
  return {
    title,
    overlap,
    svgClip,
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


# ─────────────────────────────────────────────────────────────────────────────
# Font embedding — make the PDF independent of the font CDN.
#
# The deck deliberately keeps its Google Fonts <link>: as an interactive page it
# should stay a small file and pick up the CDN's own caching. A PDF cannot do
# that. It is a snapshot of whatever rendered at export time, so a blocked or
# slow CDN is baked in permanently and silently — the PDF simply *is* the
# fallback font, with nothing to re-try later.
#
# So the export self-hosts the same families for the duration of the render:
# fetch the woff2 from npm's @fontsource* packages (npm stays reachable in
# sandboxes that block fonts.googleapis.com), inject them as data: URIs, and let
# the page re-layout before any page.pdf() call. Nothing is written to the deck —
# same contract as every other override here.
#
# Two traps that produce a silently wrong result:
#   * The variable packages name the family `'<Family> Variable'`. Injected
#     verbatim, `--brand-font-main: 'Google Sans'` matches nothing and the page
#     falls back while *looking* correctly wired. The family is forced back to
#     the name the deck actually asks for.
#   * They ship `format('woff2-variations')`, long deprecated. An engine that
#     does not recognise the format string skips that `src` entirely, so it is
#     normalised to `format('woff2')` — universally accepted, and correct for
#     variable fonts too.
# ─────────────────────────────────────────────────────────────────────────────

# `vietnamese` is not optional for this plugin's audience: without it the
# diacritics alone fall out of the embedded face and the browser substitutes a
# system font for those glyphs only, so a slide renders in two typefaces at once.
DEFAULT_SUBSETS = ("latin", "latin-ext", "vietnamese")

FACE_RE = re.compile(r"@font-face\s*\{[^}]*\}", re.DOTALL)

# The families the deck actually asks for, read off the live page rather than
# regexed out of the file — a preset may have rewritten them.
FAMILIES_JS = """() => {
  const cs = getComputedStyle(document.documentElement);
  const out = [];
  for (const v of ['--brand-font-main', '--brand-font-body', '--brand-font-code']) {
    const m = cs.getPropertyValue(v).trim().match(/^\\s*['"]?([^'",]+)/);
    if (m && !out.includes(m[1].trim())) out.push(m[1].trim());
  }
  return out;
}"""


def _slug(family: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def _npm_pack(pkg: str, dest: Path) -> Path | None:
    """Fetch a package tarball with `npm pack`. None if unavailable."""
    try:
        r = subprocess.run(
            ["npm", "pack", pkg, "--pack-destination", str(dest), "--silent"],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    for line in reversed((r.stdout or "").strip().splitlines()):
        cand = dest / line.strip()
        if cand.is_file():
            return cand
    tgz = sorted(dest.glob("*.tgz"))
    return tgz[-1] if tgz else None


def _find_tgz(pkg: str, cache: Path) -> Path | None:
    """A pre-fetched tarball in the cache dir, else fetch it with npm."""
    stem = pkg.lstrip("@").replace("/", "-")
    for cand in sorted(cache.glob(stem + "-*.tgz")):
        # `fontsource-google-sans-*` cannot match `fontsource-variable-google-…`:
        # the variable package's stem carries the extra token.
        return cand
    return _npm_pack(pkg, cache)


def _read_pkg(tgz: Path) -> tuple[dict[str, str], dict[str, bytes]]:
    """Return ({css name: text}, {woff2 basename: bytes}) from a package tarball."""
    css: dict[str, str] = {}
    woff2: dict[str, bytes] = {}
    with tarfile.open(tgz) as t:
        for m in t.getmembers():
            if not m.isfile():
                continue
            name = m.name.split("package/", 1)[-1]
            f = t.extractfile(m)
            if f is None:
                continue
            if name.endswith(".css"):
                css[name] = f.read().decode("utf-8", "replace")
            elif name.endswith(".woff2"):
                woff2[name.split("files/", 1)[-1]] = f.read()
    return css, woff2


def _faces(
    css_text: str,
    family: str,
    slug: str,
    woff2: dict[str, bytes],
    subsets: tuple[str, ...],
) -> list[tuple[str, str, int]]:
    """Rewrite @font-face blocks to embed their woff2 as data: URIs."""
    out: list[tuple[str, str, int]] = []
    # Longest first, so `latin-ext` is not swallowed by `latin`.
    ordered = sorted(subsets, key=len, reverse=True)
    for block in FACE_RE.findall(css_text):
        m = re.search(r"url\(\./files/([^)]+\.woff2)\)", block)
        if not m:
            continue
        fname = m.group(1)
        rest = fname[len(slug) + 1 :] if fname.startswith(slug + "-") else fname
        subset = next((s for s in ordered if rest.startswith(s + "-")), None)
        if subset is None:
            continue
        data = woff2.get(fname)
        if not data:
            continue
        uri = "data:font/woff2;base64," + base64.b64encode(data).decode("ascii")
        b = re.sub(
            r"src:\s*url\([^)]*\)\s*format\([^)]*\)",
            "src: url({}) format('woff2')".format(uri),
            block,
        )
        b = re.sub(r"font-family:\s*['\"][^'\"]*['\"]", "font-family: '{}'".format(family), b)
        out.append((fname, b, len(data)))
    return out


def _family_faces(
    family: str, subsets: tuple[str, ...], cache: Path
) -> tuple[list[str], int, str | None]:
    """Return (css blocks, embedded bytes, error). Prefers the variable package.

    A variable package ships several CSS files covering the *same* glyphs by a
    different axis (`wght.css`, `standard.css`, `full.css`). They are
    alternatives, not additions — taking more than one embeds the family twice.
    Static packages are the opposite case: each weight file is a distinct face
    and all of them are wanted.
    """
    slug = _slug(family)

    tgz = _find_tgz("@fontsource-variable/" + slug, cache)
    if tgz:
        css, woff2 = _read_pkg(tgz)
        for upright, italic in (
            ("wght.css", "wght-italic.css"),
            ("standard.css", "standard-italic.css"),
            ("full.css", "full-italic.css"),
            ("index.css", None),
        ):
            if upright not in css:
                continue
            blocks = _faces(css[upright], family, slug, woff2, subsets)
            if italic and italic in css:
                blocks += _faces(css[italic], family, slug, woff2, subsets)
            if blocks:
                return [b for _f, b, _n in blocks], sum(n for _f, _b, n in blocks), None

    tgz = _find_tgz("@fontsource/" + slug, cache)
    if tgz:
        css, woff2 = _read_pkg(tgz)
        seen: set[str] = set()
        blocks: list[tuple[str, str, int]] = []
        for name in ("400.css", "500.css", "600.css", "700.css",
                     "400-italic.css", "700-italic.css"):
            if name not in css:
                continue
            for f, b, n in _faces(css[name], family, slug, woff2, subsets):
                if f not in seen:
                    seen.add(f)
                    blocks.append((f, b, n))
        if blocks:
            return [b for _f, b, _n in blocks], sum(n for _f, _b, n in blocks), None

    return [], 0, "no Fontsource package for {!r} (tried @fontsource-variable/{} and " \
                  "@fontsource/{})".format(family, slug, slug)


def font_face_css(
    families: list[str], subsets: tuple[str, ...], font_dir: Path | None
) -> str:
    """@font-face rules embedding `families`, or "" if none could be fetched."""
    # Without this, a missing npm reports as "no Fontsource package for 'Google
    # Sans'" once per family — which reads as a wrong family name and sends the
    # reader off checking spellings instead of installing node.
    if font_dir is None and shutil.which("npm") is None:
        print(
            "warning: npm not found, so the deck's fonts cannot be self-hosted — "
            "the PDF will use whatever the page loaded (the CDN, if reachable). "
            "Either install node, or fetch the tarballs elsewhere with "
            "`npm pack @fontsource-variable/<family>` and pass --font-dir. "
            "--no-embed-fonts skips this step silently.",
            file=sys.stderr,
        )
        return ""

    blocks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="s2pfonts-") as tmp:
        cache = font_dir if font_dir else Path(tmp)
        for fam in families:
            got, size, err = _family_faces(fam, subsets, cache)
            if err:
                print("warning: {} — it will use whatever the page loaded".format(err),
                      file=sys.stderr)
                continue
            blocks += got
            print("embedded {} ({} face(s), {:.0f} KB)".format(fam, len(got), size / 1024),
                  file=sys.stderr)
    return "\n".join(blocks)


def render_slides(
    html: Path,
    width: int,
    height: int,
    device_scale: float,
    keep_ui: bool,
    theme: str,
    timeout_ms: int,
    browser_path: str | None = None,
    embed_fonts: bool = True,
    subsets: tuple[str, ...] = DEFAULT_SUBSETS,
    font_dir: Path | None = None,
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

        # Self-host the deck's own families before anything is rendered, so the
        # PDF does not depend on the CDN having answered. Injected after the
        # deck's own <link>, so these faces win where both exist — same glyphs
        # either way, since it is the same family from the same upstream.
        if embed_fonts:
            faces = font_face_css(page.evaluate(FAMILIES_JS), subsets, font_dir)
            if faces:
                page.add_style_tag(content=faces)

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
        overlapping: list[str] = []
        svg_clipped: list[str] = []

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

            # Distinct from clipping: nothing is cropped, the element just
            # collides with whatever sits in the next column.
            ov = info.get("overlap")
            if ov:
                note += f"  ← OVERLAP ({ov['el']} {ov['px']}px past its column)"
                overlapping.append(
                    "slide {} ({}): {} reaches {}px past its column".format(
                        i + 1, title or "untitled", ov["el"], ov["px"]
                    )
                )
            # Nothing cropped at the slide level, nothing overlapping — the
            # loss is inside the SVG's own coordinate system.
            sc = info.get("svgClip")
            if sc:
                note += f"  ← SVG OUTSIDE VIEWBOX ({sc['px']:g}px, viewBox {sc['vb']})"
                svg_clipped.append(
                    "slide {} ({}): content reaches {:g}px outside a viewBox {}".format(
                        i + 1, title or "untitled", sc["px"], sc["vb"]
                    )
                )
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

    if overlapping:
        print(
            "\nwarning: content overlaps the next column — not cropped, but it "
            "paints over its neighbour:",
            file=sys.stderr,
        )
        for line in overlapping:
            print(f"  - {line}", file=sys.stderr)
        print(
            '  Usually an <svg> with width/height attributes and no class="diagram";'
            "\n  adding that class constrains it to the column.",
            file=sys.stderr,
        )

    if svg_clipped:
        print(
            "\nwarning: an <svg> draws outside its own viewBox — that part is not "
            "rendered at all, in the deck or the PDF:",
            file=sys.stderr,
        )
        for line in svg_clipped:
            print(f"  - {line}", file=sys.stderr)
        print(
            "  Grow the viewBox to cover the shapes (mind that a stroke straddles\n"
            "  the edge it sits on, so it needs ~half the stroke width beyond them),\n"
            "  or move the content inside. Typical symptom: the last row of cards\n"
            "  loses its bottom border while the rows above keep theirs.",
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
    ap.add_argument(
        "--no-embed-fonts",
        dest="embed_fonts",
        action="store_false",
        help="do not self-host the deck's fonts; use whatever the page loads "
        "from the CDN (the PDF then depends on that CDN being reachable)",
    )
    ap.add_argument(
        "--font-subsets",
        default=",".join(DEFAULT_SUBSETS),
        help="comma-separated subsets to embed (default: %(default)s)",
    )
    ap.add_argument(
        "--font-dir",
        type=Path,
        help="directory of pre-fetched @fontsource *.tgz tarballs, for a host "
        "with no npm registry access",
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
        args.embed_fonts,
        tuple(s.strip() for s in args.font_subsets.split(",") if s.strip()),
        args.font_dir,
    )
    merge(slides, out_path)

    size_kb = out_path.stat().st_size / 1024
    print(f"wrote {out_path} — {len(slides)} pages, {size_kb:.0f} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
