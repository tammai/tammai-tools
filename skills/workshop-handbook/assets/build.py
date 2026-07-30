#!/usr/bin/env python3
"""Assemble a workshop handbook: template + content markup -> finished handbook.

Why this exists
---------------
Same reason as `workshop-slides/assets/build.py`, and the same measured
failure: when an agent produces the output by writing a whole new file, the
"keep the <head> unchanged" rule is aspirational. A deck generated that way
from an unmodified template had silently lost all 18 `--dg-*` diagram tokens
and the `.diagram` sizing rule — no error, just diagrams with no fill.

This script makes the guarantee mechanical: everything outside
`<main id="handbook">` is carried across as bytes, and branding is applied by
substituting known declarations rather than by retyping the block around them.

It also checks the invariants a handbook can break that a deck cannot — a
duplicate `id` silently sending a bookmark to the wrong place, a cross-reference
pointing at a heading that no longer exists, a chapter with no heading and so no
bookmark at all.

Usage
-----
    build.py TEMPLATE CONTENT OUTPUT [--preset PRESET.json] [--title TITLE]
                                     [--subtitle SUBTITLE]

TEMPLATE    assets/template.html
CONTENT     a fragment file: the .cover block plus <section class="chapter">s
OUTPUT      the handbook to write
--preset    ~/.workshop-slides-preset.json — the same file the deck uses
--title     replaces <title> and the sidebar title
--subtitle  replaces the sidebar subtitle line

Exits non-zero on a structural problem and writes nothing. Warnings are
advisory and do not block the write.

Standard library only — no install step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

MAIN_OPEN = '<main id="handbook">'
MAIN_CLOSE = '</main><!-- /#handbook -->'


def fail(msg: str) -> None:
    sys.exit("error: " + msg)


# ─────────────────────────────────────────────────────────────────────────────
# Branding — substitute individual declarations, never rewrite whole blocks.
# The BRAND CONFIGURATION block carries explanatory comments that a wholesale
# replacement would drop. Deliberately the same preset schema as the slides
# skill, read from the same ~/.workshop-slides-preset.json: a handbook is
# normally handed out alongside the deck, and one brand should mean one file.
# ─────────────────────────────────────────────────────────────────────────────


def apply_preset(html: str, preset: dict) -> tuple[str, list[str], list[str]]:
    """Return (html, notes, warnings). Only keys present in the preset apply."""
    notes: list[str] = []
    warnings: list[str] = []

    def set_var(text: str, name: str, value: str) -> str:
        """Replace the value of the first `--name: ...;` declaration.

        First only, deliberately: `--brand-bg` is declared three times here —
        `:root`, the `[data-theme="light"]` override, and the `@media print`
        block. The last two must stay light or light mode and every printed
        page render on a dark background.
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

    # `watermark` present but empty means "no logo" — drop the whole block.
    if "watermark" in preset:
        block = re.compile(r'<div id="watermark"[^>]*>.*?</div>\n?', re.DOTALL)
        if not block.search(html):
            fail('could not find the <div id="watermark"> block in the template')
        mark = preset["watermark"].strip()
        if mark:
            # A watermark that points off-machine breaks the handbook's core
            # promise of being self-contained: offline, or once the URL rots, it
            # renders as a broken-image box — silently, on screen and in print.
            ref = re.search(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', mark)
            if ref:
                url = ref.group(1)
                if url.startswith(("http://", "https://")):
                    warnings.append(
                        "watermark points at a remote URL ({}) — the handbook stops "
                        "being self-contained and renders a broken-image box offline "
                        "or if the URL breaks. Prefer inline <svg> or a data: URI"
                        .format(url[:60])
                    )
                elif not url.startswith("data:"):
                    warnings.append(
                        "watermark references a local path ({}) — it must travel with "
                        "the .html file or the logo will not render. Prefer inline "
                        "<svg> or a data: URI".format(url[:60])
                    )
            html = block.sub(
                '<div id="watermark" aria-hidden="true">\n' + mark + "\n</div>\n",
                html,
                count=1,
            )
            notes.append("watermark replaced")
        else:
            html = block.sub("", html, count=1)
            notes.append("watermark removed")

    return html, notes, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Bookmarks — the anchor ids the runtime will generate, computed here so a
# cross-reference can be checked before anyone clicks it.
# ─────────────────────────────────────────────────────────────────────────────


def slugify(text: str, fallback: str, used: set[str]) -> str:
    """Mirror of `slug()` in the template's buildToc(). Keep the two in step."""
    base = unicodedata.normalize("NFD", text.lower().strip())
    base = "".join(c for c in base if not unicodedata.combining(c))
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:60]
    if not base:
        base = fallback
    slug, n = base, 2
    while slug in used:
        slug = "{}-{}".format(base, n)
        n += 1
    used.add(slug)
    return slug


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def strip_code_samples(text: str) -> str:
    """Blank out comments and the inside of <pre>/<code>, keeping offsets stable.

    A handbook's whole job is often to *document* markup, so its code samples
    are full of `id="…"`, `class="slide-body"` and `href="#…"` that are text,
    not structure. Scanning them as markup is how a check earns a reputation
    for crying wolf — this very file's demo shows an escaped
    `<main id="handbook">` inside a <code>, and a snippet that shows the same
    `id=` twice would otherwise be reported as a duplicate id.

    Replacement is space-for-character so every offset a caller has already
    computed still points at the same place.
    """
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    text = re.sub(r"<!--.*?-->", blank, text, flags=re.DOTALL)
    text = re.sub(r"<pre\b.*?</pre>", blank, text, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"<code\b.*?</code>", blank, text, flags=re.DOTALL | re.IGNORECASE)


def split_chapters(content: str) -> list[tuple[str, str]]:
    """[(opening-tag-attributes, inner-html)] for each `<section class="chapter">`."""
    out = []
    for m in re.finditer(r'<section\b([^>]*\bclass\s*=\s*["\'][^"\']*\bchapter\b[^"\']*["\'][^>]*)>', content):
        # Sections do not nest in a handbook, so the next `<section` or the end
        # of the fragment bounds this one. A nested one would only truncate the
        # body, which under-reports — never a false alarm.
        nxt = content.find("<section", m.end())
        out.append((m.group(1), content[m.end(): nxt if nxt != -1 else len(content)]))
    return out


def collect_anchors(content: str) -> tuple[set[str], list[str]]:
    """Every id the finished page will have, plus warnings found on the way."""
    warnings: list[str] = []
    content = strip_code_samples(content)
    explicit = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', content)
    dupes = sorted({i for i in explicit if explicit.count(i) > 1})
    if dupes:
        warnings.append(
            "duplicate id(s) {} — a bookmark or cross-reference to one of these "
            "silently jumps to whichever comes first".format(", ".join(dupes[:4]))
        )

    used = set(explicit)
    for ci, (attrs, body) in enumerate(split_chapters(content), start=1):
        h2 = re.search(r"<h2\b[^>]*>(.*?)</h2>", body, re.DOTALL | re.IGNORECASE)
        if not h2:
            continue
        if not re.search(r'\bid\s*=\s*["\']', attrs):
            slugify(strip_tags(h2.group(1)), "chapter-{}".format(ci), used)
        for si, h3 in enumerate(
            re.finditer(r"<h3\b([^>]*)>(.*?)</h3>", body, re.DOTALL | re.IGNORECASE), start=1
        ):
            if not re.search(r'\bid\s*=\s*["\']', h3.group(1)):
                slugify(strip_tags(h3.group(2)), "sect-{}-{}".format(ci, si), used)
    return used, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Checks — each one a real failure mode, not a style opinion.
# ─────────────────────────────────────────────────────────────────────────────

# Deck classes with no handbook equivalent. An agent that has just read
# workshop-slides/SKILL.md reaches for these by reflex, and because the
# stylesheet simply has no rule for them they render as unstyled prose —
# no error, no visual cue that anything was meant to be there.
SLIDE_ISMS = {
    "slide-body": "wrap content in <section class=\"chapter\"> instead",
    "cols-2": "use .cards for a grid, or let prose run full measure",
    "cols-3": "use .cards for a grid, or let prose run full measure",
    "col-label": "use an <h4>",
    "code-line": "the handbook uses a real <pre><code>, one block, real newlines",
    "cmp-table": 'use <table class="cmp">',
    "stat-block": 'use <div class="card"> with .stat-number / .stat-label',
    "slide-num": "chapters are unnumbered — accent a word in the <h2> with <em>",
    "section-label": 'use <div class="part-label">',
    "tag-block": "use .tag, or a .card with .stat-number",
    "spacer": "not needed — the handbook flows",
}


def check_content(content: str) -> tuple[list[str], list[str], int]:
    """Return (errors, warnings, chapter_count) for the content fragment."""
    errors: list[str] = []
    warnings: list[str] = []

    chapters = split_chapters(content)
    if not chapters:
        errors.append(
            'no <section class="chapter"> elements found — the handbook would '
            "have no content and no bookmarks"
        )
        return errors, warnings, 0

    if not re.search(r'class\s*=\s*["\'][^"\']*\bcover\b', content):
        warnings.append('no .cover block — the handbook opens straight into chapter 1')

    for ci, (attrs, body) in enumerate(chapters, start=1):
        label = re.search(r'\bid\s*=\s*["\']([^"\']+)', attrs)
        who = label.group(1) if label else "#{}".format(ci)

        h2s = re.findall(r"<h2\b[^>]*>(.*?)</h2>", body, re.DOTALL | re.IGNORECASE)
        if not h2s:
            errors.append(
                "chapter {} has no <h2> — buildToc() skips it entirely, so the "
                "chapter is unreachable from the sidebar".format(who)
            )
        elif len(h2s) > 1:
            warnings.append(
                "chapter {} has {} <h2> elements — only the first becomes a "
                "bookmark; use <h3> for sections".format(who, len(h2s))
            )

        if re.search(r"<h1\b", body, re.IGNORECASE):
            warnings.append(
                "chapter {} contains an <h1> — the .cover owns the document's "
                "only h1; use <h2>".format(who)
            )

        # A heading level skipped is a hole in the outline, and the sidebar
        # renders an h4's content with no parent row to sit under.
        if re.search(r"<h4\b", body, re.IGNORECASE) and not re.search(r"<h3\b", body, re.IGNORECASE):
            warnings.append(
                "chapter {} jumps from <h2> to <h4> with no <h3> between "
                "them".format(who)
            )

        # buildToc() collects `:scope > h3`. One nested deeper renders as a
        # heading but never appears in the sidebar.
        for m in re.finditer(r"<h3\b[^>]*>(.*?)</h3>", body, re.DOTALL | re.IGNORECASE):
            before = body[: m.start()]
            if before.count("<div") - before.count("</div>") > 0 or \
               before.count("<figure") - before.count("</figure>") > 0:
                warnings.append(
                    "chapter {}: <h3>{}</h3> is nested inside another element — "
                    "only a direct child of .chapter becomes a bookmark".format(
                        who, strip_tags(m.group(1))[:40]
                    )
                )
                break

        # Headings are unnumbered by design — the accent comes from an <em>
        # inside the title. A hand-typed "1." or "2.3" both reintroduces the
        # numbering this template dropped and lands in the sidebar row, since
        # buildToc() takes the heading's own text.
        for tag in ("h2", "h3"):
            m = re.search(
                r"<{0}\b[^>]*>\s*(\d+(?:\.\d+)*)[.)]?\s".format(tag), body, re.IGNORECASE
            )
            if m:
                warnings.append(
                    "chapter {}: <{}> starts with a typed number ({!r}) — headings "
                    "are unnumbered in this template, and the digits show up in "
                    "the bookmark too. Accent a key word with <em> instead".format(
                        who, tag, m.group(1)
                    )
                )
                break

        # A tab group with no panels, or panels with no buttons, renders as a
        # bare button row over nothing (or an always-visible stack).
        #
        # Windowed to the next tab group rather than matched as a balanced
        # element: `.tabs` nests .tab-bar and .tab-panel divs, so a non-greedy
        # `<div class="tabs".*?</div>` stops at the tab bar's closing tag and
        # reports every well-formed group as "buttons but no panels".
        for chunk in re.split(r'<div class="tabs"', body)[1:]:
            tabs = re.split(r'</section|<div class="tabs"', chunk)[0]
            if ("tab-btn" in tabs) != ("tab-panel" in tabs):
                warnings.append(
                    "chapter {}: a .tabs group has {} — a tab group needs both "
                    ".tab-btn buttons and matching .tab-panel blocks".format(
                        who,
                        "buttons but no panels" if "tab-btn" in tabs else "panels but no buttons",
                    )
                )
                break

    # Everything below inspects *markup*, so code samples are blanked first —
    # a handbook documenting the slides skill legitimately prints `.slide-body`
    # and `#f97316` inside a <code>, and flagging those trains the reader to
    # ignore the whole warning list.
    prose = strip_code_samples(content)

    # Figure and step numbers are the template's counters. A fragment that
    # resets one renumbers everything after it with no way to notice by reading.
    if re.search(r"counter-(reset|increment)\s*:", prose):
        warnings.append(
            "the content sets a CSS counter — figure and step numbers come from "
            "the template's counters, and overriding one silently renumbers "
            "every figure or step after it"
        )

    # Light mode reverses the --slate-* scale, so a hardcoded hex breaks it.
    hexes = re.findall(r"(?:color|background|fill|stroke)\s*:\s*(#[0-9a-fA-F]{3,8})", prose)
    if hexes:
        warnings.append(
            "hardcoded color(s) {} — light mode reverses the slate scale, so use "
            "var(--brand-accent) / var(--slate-*)".format(", ".join(sorted(set(hexes))[:4]))
        )

    # The handbook's .code-block is a real <pre>, unlike the deck's.
    for block in re.split(r'<div class="code-block[^"]*"', content)[1:]:
        window = re.split(r"</section|<div class=\"code-block", block)[0]
        if "<pre" not in window:
            warnings.append(
                ".code-block with no <pre> — it renders with no padding and no "
                "monospace wrapping, and gets no copy button"
            )
            break

    for cls, fix in SLIDE_ISMS.items():
        if re.search(r'class\s*=\s*["\'][^"\']*\b' + re.escape(cls) + r'\b', prose):
            warnings.append(
                "`.{}` is a workshop-slides class with no rule in this "
                "stylesheet — it renders unstyled. {}".format(cls, fix)
            )

    return errors, warnings, len(chapters)


def check_links(content: str, anchors: set[str]) -> list[str]:
    """Warn on a cross-reference that lands nowhere."""
    warnings: list[str] = []
    broken = []
    for m in re.finditer(r'<a\b[^>]*\bhref\s*=\s*["\']#([^"\']+)["\']', strip_code_samples(content)):
        target = m.group(1)
        if target and target not in anchors and target not in broken:
            broken.append(target)
    if broken:
        warnings.append(
            "cross-reference(s) to {} — no heading or element produces "
            "{}, so the link does nothing when clicked".format(
                ", ".join("#" + b for b in broken[:4]),
                "those ids" if len(broken) > 1 else "that id",
            )
        )
    return warnings


# Own coordinate systems, or never rendered in place — their coordinates say
# nothing about the parent viewBox. A `<marker>` in particular carries its own
# `viewBox`, and missing this reads every arrowhead as a wild overflow.
SVG_ISOLATED_BLOCKS = ("defs", "marker", "clipPath", "pattern", "symbol", "mask")


def _svg_extent(body: str) -> tuple[float, float, str] | None:
    """Furthest right/bottom edge of the shapes whose geometry is exactly known.

    Deliberately partial. Anything whose extent cannot be computed from
    attributes alone — a transformed element, a relative or curved path, the
    *width* of a text run — is skipped rather than guessed at, because a check
    that cries wolf on the reference document gets ignored and then removed.
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
        # the shape's own box — a 1.75px stroke on a card at y+38 puts real ink
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


# `--content-width` in the template. An attribute-sized <svg> wider than this
# is laid out at that width and pushes the page into horizontal scroll, because
# nothing in the flow clamps it.
CONTENT_WIDTH = 820


def check_svg(content: str) -> list[str]:
    """Warn when an <svg> reaches past its viewBox, or past the text column.

    Content outside the viewBox is not clipped with a red flag — it is simply
    not drawn. A deck shipped on 2026-07-25 had a seven-card layer stack whose
    last card ran to y=308 inside `viewBox="0 0 460 306"`, so that one card lost
    its bottom border and rounded corners while the other six kept theirs. It
    rendered that way on screen and in the exported PDF, silently.
    """
    warnings: list[str] = []

    # Comments first. The template *mentions* `<svg>` in prose — inside a CSS
    # comment — and a naive `<svg…>(.*?)</svg>` pairs that prose opening with
    # the real diagram's closing tag, hiding the diagram inside another match's
    # body. That made an earlier version of this check in the slides skill
    # silently never fire on any deck built from the template.
    text = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    for m in re.finditer(r"<svg\b([^>]*)>", text, re.IGNORECASE):
        head = m.group(1)
        close = text.find("</svg>", m.end())
        body = text[m.end(): close if close != -1 else len(text)]

        w = re.search(r'\bwidth\s*=\s*["\'](\d+(?:\.\d+)?)(?:px)?["\']', head)
        if (
            w
            and float(w.group(1)) > CONTENT_WIDTH
            and re.search(r'\bheight\s*=\s*["\']\d', head)
            and not re.search(r'class\s*=\s*["\'][^"\']*\bdiagram\b', head)
        ):
            warnings.append(
                'an <svg width="{}"> has no class="diagram" — the text column is '
                "{}px, so it overflows into the margin and puts the page into "
                "horizontal scroll".format(w.group(1), CONTENT_WIDTH)
            )

        vb = re.search(
            r'viewBox\s*=\s*["\']\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)', head
        )
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
                "the viewBox is not drawn at all: that edge is silently missing on "
                "screen and in print. Grow the viewBox to {:g} {:g} (or move the "
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
        (".diagram {", "wide diagrams overflow the text column without it"),
        ("@media print", "the Cmd-P export path is gone — the only export this skill has"),
        ("transform: none !important", "the printed contents page comes out blank"),
        ("--content-width", "the reading measure is gone and prose runs edge to edge"),
        ("buildToc", "the bookmarks are gone — nothing builds the sidebar"),
        ("tocTargets", "scrollspy has nothing to track"),
        ("READING_LINE", "scrollspy is gone"),
        ('id="toc"', "the bookmark list has no container"),
        ('id="sidebar"', "the sidebar is gone"),
        ('id="scrim"', "the drawer has no backdrop"),
        ("drawer-open", "the open drawer renders underneath its own backdrop"),
        ('id="closeToc"', "the drawer cannot be dismissed by button"),
        ('id="menuToggle"', "the drawer cannot be opened on a narrow screen"),
        ('id="themeToggle"', "the dark/light toggle is gone"),
        ('id="progress"', "the reading progress bar is gone"),
        ("copy-btn", "code blocks lose their copy button"),
        ("tab-btn", "tab groups render as plain stacked panels"),
        ("counter-reset: figure", "figure numbering is gone"),
        ("base64,", "the favicon data URI is gone"),
    ):
        if needle in template and needle not in output:
            problems.append("lost {!r} — {}".format(needle, why))

    return problems


# ─────────────────────────────────────────────────────────────────────────────


def replace_once(html: str, pattern: str, repl: str, what: str) -> str:
    out, n = re.subn(pattern, lambda _m: repl, html, count=1, flags=re.DOTALL)
    if n != 1:
        fail("could not find {} in the template".format(what))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Assemble a workshop handbook from the template plus a "
        "content fragment, carrying the head/chrome/script across as bytes."
    )
    ap.add_argument("template", type=Path, help="assets/template.html")
    ap.add_argument("content", type=Path, help="fragment: .cover plus .chapter sections")
    ap.add_argument("output", type=Path, help="handbook to write")
    ap.add_argument("--preset", type=Path, help="~/.workshop-slides-preset.json")
    ap.add_argument("--title", help="replaces <title> and the sidebar title")
    ap.add_argument("--subtitle", help="replaces the sidebar subtitle line")
    ap.add_argument(
        "--force", action="store_true", help="write even if a check reports an error"
    )
    args = ap.parse_args()

    for p in (args.template, args.content):
        if not p.is_file():
            fail("not a file: {}".format(p))

    template = args.template.read_text(encoding="utf-8")
    content = args.content.read_text(encoding="utf-8").strip("\n")

    open_at = template.find(MAIN_OPEN)
    close_at = template.find(MAIN_CLOSE)
    if open_at < 0:
        fail("template has no {!r}".format(MAIN_OPEN))
    if close_at < 0:
        fail("template has no {!r}".format(MAIN_CLOSE))
    if close_at < open_at:
        fail("{!r} appears before {!r}".format(MAIN_CLOSE, MAIN_OPEN))

    errors, warnings, chapters = check_content(content)
    anchors, anchor_warnings = collect_anchors(content)
    warnings += anchor_warnings
    warnings += check_links(content, anchors)
    warnings += check_svg(content)

    head = template[: open_at + len(MAIN_OPEN)]
    tail = template[close_at:]
    output = head + "\n\n" + content + "\n\n" + tail

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
        output = replace_once(output, r"<title>.*?</title>",
                              "<title>{}</title>".format(args.title), "<title>")
        output = replace_once(
            output, r'<div id="sidebar-title">.*?</div>',
            '<div id="sidebar-title">{}</div>'.format(args.title), 'the sidebar title'
        )
    if args.subtitle:
        output = replace_once(
            output, r'<div id="sidebar-sub">.*?</div>',
            '<div id="sidebar-sub">{}</div>'.format(args.subtitle), 'the sidebar subtitle'
        )

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

    carried = len(template) - (close_at - open_at - len(MAIN_OPEN))
    bookmarks = len([a for a in anchors])
    print(
        "wrote {} — {} chapter(s), {} anchor(s), {} bytes of template carried "
        "across verbatim".format(args.output, chapters, bookmarks, carried)
    )
    for n in notes:
        print("  preset: {}".format(n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
