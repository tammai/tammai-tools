#!/usr/bin/env python3
"""Assemble a workshop-slides deck: template + slide markup -> finished deck.

Why this exists
---------------
SKILL.md asks the agent to keep the template's `<head>`, chrome and `<script>`
"unchanged" while replacing only the contents of `<div id="deck">`. When the
agent produces the output by writing a whole new file, that guarantee is
aspirational — and it measurably fails. A deck generated on 2026-07-24 from an
unmodified template had silently lost all 18 `--dg-*` diagram tokens and the
`.diagram` sizing rule: diagrams pasted from `soft-visuals` render with no fill,
with no error to explain why, and portrait diagrams overflow the slide.

This script makes the guarantee mechanical. Everything outside the deck region
is carried across as bytes; branding is applied by substituting known
declarations rather than by retyping the block that contains them.

Usage
-----
    build.py TEMPLATE SLIDES OUTPUT [--preset PRESET.json] [--title TITLE]

TEMPLATE  assets/template.html
SLIDES    a fragment file: just the <section class="slide"> elements
OUTPUT    the deck to write
--preset  ~/.workshop-slides-preset.json (see SKILL.md for the schema)
--title   replaces the <title>; defaults to the template's

Exits non-zero on a structural problem and writes nothing. Warnings (numbering,
hardcoded colors) are advisory and do not block the write.

Standard library only — no install step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DECK_OPEN = '<div id="deck">'
DECK_CLOSE = '</div><!-- /#deck -->'


def fail(msg: str) -> None:
    sys.exit("error: " + msg)


# ─────────────────────────────────────────────────────────────────────────────
# Branding — substitute individual declarations, never rewrite whole blocks.
# The BRAND CONFIGURATION block carries explanatory comments that a wholesale
# replacement would drop.
# ─────────────────────────────────────────────────────────────────────────────


def apply_preset(html: str, preset: dict) -> tuple[str, list[str], list[str]]:
    """Return (html, notes, warnings). Only keys present in the preset apply."""
    notes: list[str] = []
    warnings: list[str] = []

    def set_var(text: str, name: str, value: str) -> str:
        """Replace the value of the first `--name: ...;` declaration.

        First only, deliberately: `--brand-bg` is declared twice, and the second
        is the `:root[data-theme="light"]` override, which has to stay light or
        light mode renders a dark page. Same reasoning for any future override.
        """
        pattern = re.compile(r"(--" + re.escape(name) + r":\s*)([^;]*)(;)")
        new, n = pattern.subn(lambda m: m.group(1) + value + m.group(3), text, count=1)
        if n != 1:
            fail("could not find the --{} declaration in the template".format(name))
        notes.append("--{} -> {}".format(name, value))
        return new

    if preset.get("accent"):
        html = set_var(html, "brand-accent", preset["accent"])
    if preset.get("background"):
        html = set_var(html, "brand-bg", preset["background"])

    # A bare family name from the preset needs quoting plus a fallback stack;
    # the template's own values already carry both.
    for key, var, fallback in (
        ("fontMain", "brand-font-main", "system-ui, sans-serif"),
        ("fontBody", "brand-font-body", "sans-serif"),
        ("fontCode", "brand-font-code", "monospace"),
    ):
        if preset.get(key):
            fam = preset[key].strip()
            if not fam.startswith(("'", '"')):
                fam = "'{}'".format(fam)
            html = set_var(html, var, "{}, {}".format(fam, fallback))

    if preset.get("googleFontsUrl"):
        pattern = re.compile(
            r'(<link\s+href=")https://fonts\.googleapis\.com/css2[^"]*(")'
        )
        html, n = pattern.subn(
            lambda m: m.group(1) + preset["googleFontsUrl"] + m.group(2), html, count=1
        )
        if n != 1:
            fail("could not find the Google Fonts <link> in the template")
        notes.append("google fonts <link> replaced")

    # `watermark` present but empty means "no logo" — drop the whole block,
    # which is what SKILL.md specifies.
    if "watermark" in preset:
        block = re.compile(
            r'<div id="watermark"[^>]*>.*?</div>\n?', re.DOTALL
        )
        if not block.search(html):
            fail('could not find the <div id="watermark"> block in the template')
        mark = preset["watermark"].strip()
        if mark:
            # A watermark that points off-machine breaks the deck's core promise
            # of being self-contained: offline, or once the URL rots, it renders
            # as a broken-image box — silently, in the deck *and* in an exported
            # PDF. Measured with a logo at a non-existent https URL. SKILL.md
            # does offer "Remote URL" as an option, so this warns, not errors.
            ref = re.search(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', mark)
            if ref:
                url = ref.group(1)
                if url.startswith(("http://", "https://")):
                    warnings.append(
                        "watermark points at a remote URL ({}) — the deck stops "
                        "being self-contained and renders a broken-image box "
                        "offline or if the URL breaks. Prefer inline <svg> or a "
                        "data: URI".format(url[:60])
                    )
                elif not url.startswith("data:"):
                    warnings.append(
                        "watermark references a local path ({}) — it must travel "
                        "with the .html file or the logo will not render. Prefer "
                        "inline <svg> or a data: URI".format(url[:60])
                    )
            html = block.sub(
                '<div id="watermark" aria-hidden="true">\n  '
                + mark
                + "\n</div>\n",
                html,
                count=1,
            )
            notes.append("watermark replaced")
        else:
            html = block.sub("", html, count=1)
            notes.append("watermark removed")

    return html, notes, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Checks — invariants documented in CLAUDE.md, each one a real failure mode.
# ─────────────────────────────────────────────────────────────────────────────


def check_slides(slides: str) -> tuple[list[str], list[str], int]:
    """Return (errors, warnings, slide_count) for the slide fragment."""
    errors: list[str] = []
    warnings: list[str] = []

    # Capture each section with its body, so a check can tell which slide a
    # `slide-num` belongs to. A flat findall over the fragment cannot: the cover
    # puts kicker text in `.slide-num` and section dividers omit it entirely.
    parts = re.findall(
        r'<section\s+class="(slide[^"]*)"(.*?)(?=<section\s+class="slide|\Z)',
        slides,
        re.DOTALL,
    )
    sections = [cls for cls, _ in parts]
    count = len(sections)
    if count == 0:
        errors.append("no <section class=\"slide\"> elements found in the slides file")
        return errors, warnings, 0

    active = [s for s in sections if "active" in s]
    if len(active) == 0:
        errors.append("no slide carries the `active` class — the deck opens blank")
    elif len(active) > 1:
        errors.append(
            "{} slides carry the `active` class; exactly one may".format(len(active))
        )
    elif "active" not in sections[0]:
        warnings.append("the `active` slide is not the first one")

    if "slide--cover" not in sections[0]:
        warnings.append("first slide is not `slide--cover`")

    # A numeric slide-num is the slide's absolute position, zero-padded to two
    # digits, or the deck contradicts the navigator's "n / total". The cover
    # legitimately puts kicker text in `.slide-num` and dividers omit it, so
    # only digits are checked, and against the section's own position.
    for pos, (_cls, body) in enumerate(parts, start=1):
        m = re.search(r'class="slide-num">\s*([^<]*?)\s*<', body)
        if not m or not m.group(1).isdigit():
            continue
        raw = m.group(1)
        if int(raw) != pos:
            warnings.append(
                "slide {} has slide-num {!r} — numbering does not match position".format(
                    pos, raw
                )
            )
            break
        if len(raw) < 2:
            warnings.append("slide-num {!r} is not zero-padded to two digits".format(raw))
            break

    # Light mode reverses the --slate-* scale, so a hardcoded hex breaks it.
    hexes = re.findall(r"(?:color|background|fill|stroke)\s*:\s*(#[0-9a-fA-F]{3,8})", slides)
    if hexes:
        warnings.append(
            "hardcoded color(s) {} — light mode reverses the slate scale, so use "
            "var(--brand-accent) / var(--slate-*)".format(", ".join(sorted(set(hexes))[:4]))
        )

    # slides-to-pdf strips chrome with `button:not(#deck button)`, which relies
    # on slide content containing no buttons.
    if re.search(r"<button\b", slides):
        warnings.append(
            "slide content contains a <button> — slides-to-pdf hides chrome via "
            "`button:not(#deck button)`, so it will survive into the PDF"
        )

    # .code-block is not a <pre>; every line needs its own .code-line or raw
    # newlines collapse and the snippet reflows into a single paragraph. Scan to
    # the next code block or the end of the slide rather than to the first
    # `</div>` — a block's first child is usually `.code-lang`, which closes one.
    for block in re.split(r'<div class="code-block"', slides)[1:]:
        window = re.split(r'</section|<div class="code-block"', block)[0]
        if "code-line" not in window:
            warnings.append(
                ".code-block without .code-line children — raw newlines collapse "
                "and the snippet reflows into a single line"
            )
            break

    return errors, warnings, count


# Own coordinate systems, or never rendered in place — their coordinates say
# nothing about the parent viewBox. A `<marker>` in particular carries its own
# `viewBox`, and missing this reads every arrowhead as a wild overflow.
SVG_ISOLATED_BLOCKS = ("defs", "marker", "clipPath", "pattern", "symbol", "mask")


def _svg_extent(body: str) -> tuple[float, float, str] | None:
    """Furthest right/bottom edge of the shapes whose geometry is exactly known.

    Deliberately partial. Anything whose extent cannot be computed from
    attributes alone — a transformed element, a relative or curved path, the
    *width* of a text run — is skipped rather than guessed at, because a check
    that cries wolf on the reference deck gets ignored and then removed. What
    remains still catches the common authoring slip: a row of `<rect>` cards
    laid out past the bottom of the viewBox.
    """
    for block in SVG_ISOLATED_BLOCKS:
        body = re.sub(r"<{0}\b.*?</{0}>".format(block), "", body, flags=re.DOTALL | re.IGNORECASE)

    # A translated group shifts everything under it; without a transform stack
    # every child coordinate would be wrong. Bail out rather than mislead.
    if re.search(r"<g\b[^>]*\btransform\s*=", body, re.IGNORECASE):
        return None

    def attrs(tag: str) -> list[dict[str, str]]:
        out = []
        for m in re.finditer(r"<" + tag + r"\b([^>]*)>", body, re.IGNORECASE):
            raw = m.group(1)
            if re.search(r"\btransform\s*=", raw):
                continue
            out.append(dict(re.findall(r'([a-zA-Z-]+)\s*=\s*["\']([^"\']*)["\']', raw)))
        return out

    def num(d: dict[str, str], key: str, default: float = 0.0) -> float:
        try:
            return float(d.get(key, default))
        except (TypeError, ValueError):
            return default

    def pad(d: dict[str, str]) -> float:
        # A stroke straddles the edge it is drawn on, so half of it sits outside
        # the shape's own box — the 1.75px stroke on a card at y+38 puts real ink
        # at y+38.875. Ignoring it is how a "2px" overflow reads as none.
        if d.get("stroke", "none") in ("none", ""):
            return 0.0
        return num(d, "stroke-width", 1.0) / 2.0

    right = bottom = float("-inf")
    who = ""

    def bump(x: float, y: float, label: str) -> None:
        nonlocal right, bottom, who
        if x > right or y > bottom:
            if max(x - right, y - bottom) > 0:
                who = label
            right = max(right, x)
            bottom = max(bottom, y)

    for d in attrs("rect"):
        p = pad(d)
        bump(num(d, "x") + num(d, "width") + p, num(d, "y") + num(d, "height") + p, "<rect>")
    for d in attrs("circle"):
        p = pad(d) + num(d, "r")
        bump(num(d, "cx") + p, num(d, "cy") + p, "<circle>")
    for d in attrs("ellipse"):
        p = pad(d)
        bump(num(d, "cx") + num(d, "rx") + p, num(d, "cy") + num(d, "ry") + p, "<ellipse>")
    for d in attrs("line"):
        p = pad(d)
        bump(max(num(d, "x1"), num(d, "x2")) + p, max(num(d, "y1"), num(d, "y2")) + p, "<line>")
    for tag in ("polyline", "polygon"):
        for d in attrs(tag):
            pts = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d.get("points", ""))]
            if len(pts) >= 2:
                p = pad(d)
                bump(max(pts[0::2]) + p, max(pts[1::2]) + p, "<{}>".format(tag))
    for d in attrs("path"):
        dd = d.get("d", "")
        # Absolute straight-line paths only: M/L/Z give clean x,y pairs. A
        # relative or curved path needs a real path parser, and a wrong answer
        # here is worse than no answer.
        if not dd or re.search(r"[a-z]", dd) or re.search(r"[CSQTAHV]", dd):
            continue
        pts = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", dd)]
        if len(pts) >= 2:
            p = pad(d)
            bump(max(pts[0::2]) + p, max(pts[1::2]) + p, "<path>")

    if right == float("-inf"):
        return None
    return right, bottom, who


# Slide is 1280px wide with 72px padding each side, so a `.slide-body` is 1136px.
# `.col` splits that evenly and adds 32px of inner padding — dropped on the outer
# side of the first and last column, so a lone column keeps the full width.
SLIDE_BODY_WIDTH = 1280 - 72 * 2
COL_GUTTER = 32


def _column_width(text: str, pos: int) -> float:
    """Inner width of the column containing `pos`, from the nearest `.slide-body` above it."""
    body = None
    for m in re.finditer(r'<div[^>]*class\s*=\s*["\']([^"\']*\bslide-body\b[^"\']*)["\']', text):
        if m.start() > pos:
            break
        body = m.group(1)
    if body is None:
        return float(SLIDE_BODY_WIDTH)
    cols = 2 if "cols-2" in body else 3 if "cols-3" in body else 1
    if cols == 1:
        return float(SLIDE_BODY_WIDTH)
    return SLIDE_BODY_WIDTH / cols - COL_GUTTER


def check_svg_viewbox(slides: str) -> list[str]:
    """Warn when an <svg>'s own shapes reach past its viewBox.

    Content outside the viewBox is not clipped with a red flag — it is simply
    not drawn. A deck shipped on 2026-07-25 had a seven-card layer stack whose
    last card ran to y=308 inside `viewBox="0 0 460 306"`, so that one card lost
    its bottom border and rounded corners while the other six kept theirs. It
    rendered that way in the browser and in the exported PDF, silently. The
    `soft-visuals` skill has documented a DevTools snippet for this since v0.2 —
    which is exactly the problem: a check nobody runs catches nothing.
    """
    warnings: list[str] = []

    # Comments first. Both this template and the soft-visuals one *mention*
    # `<svg>` in prose — one inside a CSS comment, one inside an HTML comment —
    # and a naive `<svg…>(.*?)</svg>` pairs that prose opening with the real
    # diagram's closing tag, hiding the actual diagram inside another match's
    # body. That made an earlier version of this check silently never fire on any
    # deck built from the template: the worst kind of check.
    text = re.sub(r"<!--.*?-->", "", slides, flags=re.DOTALL)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # Each opening is resolved against the next `</svg>` independently, rather
    # than by one alternating pattern, so an unclosed or attribute-less <svg>
    # cannot consume the one after it. A nested <svg> only truncates the outer
    # body, which under-measures — safe, never a false alarm.
    for m in re.finditer(r"<svg\b([^>]*)>", text, re.IGNORECASE):
        head = m.group(1)
        close = text.find("</svg>", m.end())
        body = text[m.end() : close if close != -1 else len(text)]

        # A `width`/`height`-sized <svg> is laid out at that size, so one wider than
        # its column paints over the neighbour instead of being cropped — `.col` is
        # `overflow: visible`, so nothing reports it. Measured: width="700" in a
        # 568px column reaches 132px into the next. `class="diagram"` (width: 100%;
        # max-height: 100%) is what constrains it.
        #
        # The limit is the enclosing column's width, not a constant: a single column is
        # the full 1136px and has no neighbour to paint over, so flagging a wide diagram
        # there is a false alarm, while a cols-3 column is only ~347px and a 420px SVG
        # already overlaps. Both were measured against this stylesheet.
        w = re.search(r'\bwidth\s*=\s*["\'](\d+(?:\.\d+)?)(?:px)?["\']', head)
        if (
            w
            and float(w.group(1)) > _column_width(text, m.start())
            and re.search(r'\bheight\s*=\s*["\']\d', head)
            and not re.search(r'class\s*=\s*["\'][^"\']*\bdiagram\b', head)
        ):
            limit = _column_width(text, m.start())
            warnings.append(
                'an <svg width="{}"> has no class="diagram" — its column is only {:.0f}px '
                "wide, so it paints over the next one instead of being cropped, which "
                "nothing else reports".format(w.group(1), limit)
            )

        vb = re.search(r'viewBox\s*=\s*["\']\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)', head)
        if not vb:
            continue
        vx, vy, vw, vh = (float(vb.group(i)) for i in range(1, 5))
        if vw <= 0 or vh <= 0:
            continue
        ext = _svg_extent(body)
        if not ext:
            continue
        right, bottom, who = ext
        over_x, over_y = right - (vx + vw), bottom - (vy + vh)
        # 0.5 of slack: half-pixel rounding in generated coordinates is not a bug.
        if over_x > 0.5 or over_y > 0.5:
            parts = []
            if over_x > 0.5:
                parts.append("{:.3g}px past its right edge".format(over_x))
            if over_y > 0.5:
                parts.append("{:.3g}px below its bottom edge".format(over_y))
            warnings.append(
                'svg viewBox="{:g} {:g} {:g} {:g}" — {} reaches {}. Content outside '
                "the viewBox is not drawn at all: that edge is silently missing in "
                "the deck and in any PDF. Grow the viewBox to {:g} {:g} (or move the "
                "shape in)".format(
                    vx, vy, vw, vh, who or "content", " and ".join(parts),
                    vw + max(0.0, over_x) + 6, vh + max(0.0, over_y) + 6,
                )
            )
    return warnings


def check_carryover(template: str, output: str) -> list[str]:
    """Canary for head/chrome drift: anything here missing means the carry-over
    broke, which is exactly the failure this script exists to prevent."""
    problems: list[str] = []

    want = set(re.findall(r"--dg-[a-z0-9-]+(?=\s*:)", template))
    got = set(re.findall(r"--dg-[a-z0-9-]+(?=\s*:)", output))
    if want - got:
        problems.append(
            "lost {} of {} --dg-* diagram tokens ({}) — pasted soft-visuals SVGs "
            "would render with no fill".format(
                len(want - got), len(want), ", ".join(sorted(want - got)[:5])
            )
        )

    for needle, why in (
        (".diagram {", "portrait diagrams overflow the slide without it"),
        ("@media print", "the dependency-free Cmd-P export path is gone"),
        ("scaleDeck", "the 16:9 stage stops scaling to the viewport"),
        ("--deck-scale", "the CSS half of the 16:9 ratio lock is gone"),
        ("ResizeObserver", "a deck revealed from display:none never rescales"),
        ('id="navigator"', "slide navigation chrome is gone"),
        ('id="themeToggle"', "the dark/light toggle is gone"),
        ('id="fullscreenToggle"', "the fullscreen toggle is gone"),
        ("base64,", "the favicon data URI is gone"),
    ):
        if needle in template and needle not in output:
            problems.append("lost {!r} — {}".format(needle, why))

    return problems


# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Assemble a workshop-slides deck from the template plus a "
        "slide fragment, carrying the head/chrome/script across as bytes."
    )
    ap.add_argument("template", type=Path, help="assets/template.html")
    ap.add_argument("slides", type=Path, help="fragment of <section class=slide> elements")
    ap.add_argument("output", type=Path, help="deck to write")
    ap.add_argument("--preset", type=Path, help="~/.workshop-slides-preset.json")
    ap.add_argument("--title", help="replaces the <title> (default: the template's)")
    ap.add_argument(
        "--force", action="store_true", help="write even if a check reports an error"
    )
    args = ap.parse_args()

    for p in (args.template, args.slides):
        if not p.is_file():
            fail("not a file: {}".format(p))

    template = args.template.read_text(encoding="utf-8")
    slides = args.slides.read_text(encoding="utf-8").strip("\n")

    open_at = template.find(DECK_OPEN)
    close_at = template.find(DECK_CLOSE)
    if open_at < 0:
        fail("template has no {!r}".format(DECK_OPEN))
    if close_at < 0:
        fail("template has no {!r}".format(DECK_CLOSE))
    if close_at < open_at:
        fail("{!r} appears before {!r}".format(DECK_CLOSE, DECK_OPEN))

    errors, warnings, count = check_slides(slides)
    warnings += check_svg_viewbox(slides)

    head = template[: open_at + len(DECK_OPEN)]
    tail = template[close_at:]
    output = head + "\n\n" + slides + "\n\n" + tail

    notes: list[str] = []
    if args.preset:
        if not args.preset.is_file():
            fail("preset not found: {}".format(args.preset))
        try:
            preset = json.loads(args.preset.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail("preset is not valid JSON: {}".format(e))
        output, notes, preset_warnings = apply_preset(output, preset)
        warnings += preset_warnings

    if args.title:
        output, n = re.subn(
            r"<title>.*?</title>",
            "<title>{}</title>".format(args.title),
            output,
            count=1,
            flags=re.DOTALL,
        )
        if n != 1:
            fail("could not find <title> in the template")

    errors += check_carryover(template, output)

    for w in warnings:
        print("warning: {}".format(w), file=sys.stderr)
    for e in errors:
        print("error: {}".format(e), file=sys.stderr)

    if errors and not args.force:
        print("\nnothing written. re-run with --force to override.", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")

    carried = len(template) - (close_at - open_at - len(DECK_OPEN))
    print(
        "wrote {} — {} slide(s), {} bytes of template carried across verbatim".format(
            args.output, count, carried
        )
    )
    for n in notes:
        print("  preset: {}".format(n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
