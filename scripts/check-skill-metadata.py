#!/usr/bin/env python3
"""Assert every SKILL.md carries frontmatter the plugin installer will accept.

Run before tagging a release, and after editing any SKILL.md frontmatter.

The failure this exists to catch is an install that refuses the whole plugin
over one field in one skill. `description` has a hard 1024-character limit;
past it the install fails rather than warning, and the error does not name the
offending skill. Two descriptions were over when this was written —
`soft-visuals` at 1287 and `workshop-handbook` at 1147 — and nothing in the
repo measured them, so the only symptom was a plugin that would not install.

Three things about it that are easy to get wrong:

  * The limit applies to the FOLDED value, not the raw block. These are `>`
    block scalars, so YAML joins the lines with single spaces and drops the
    2-space indents. Counting the raw frontmatter text overcounts by roughly
    2 chars per line, which reports a passing description as failing.
  * A description near the limit is a latent failure. Adding one trigger
    phrase tips it over, and the next person to hit it sees only a failed
    install. Anything inside NARROW of the ceiling warns.
  * `name` must match the directory. The directory is what the loader keys on,
    so a mismatch loads a skill under a name nothing references.

Exit 0 on pass (warnings included), 1 on failure. Stdlib only — no pyyaml.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

MAX_DESCRIPTION = 1024
# Headroom below which a description warns. One extra trigger phrase is
# roughly this long, which is exactly the edit that tips a passing file over.
NARROW = 64


def fold(raw: str, style: str) -> str:
    """Resolve a YAML block scalar the way the loader will.

    `>` folds line breaks to single spaces and a blank line to a newline;
    `|` keeps every line break. Both strip the block's common indent.
    """
    lines = [line.strip() for line in raw.splitlines()]
    if style == "|":
        return "\n".join(lines).strip()
    out: list[str] = []
    for line in lines:
        if not line:
            out.append("\n")
        elif out and out[-1] != "\n":
            out.append(" " + line)
        else:
            out.append(line)
    return "".join(out).strip()


def frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return None

    fields: dict[str, str] = {}
    block = match.group(1)
    for key in ("name", "description"):
        # Block scalar: `key: >` followed by indented lines.
        scalar = re.search(
            rf"^{key}:[ \t]*(>|\|)[-+]?[ \t]*\n((?:(?:[ \t]+.*)?\n?)*)", block, re.M
        )
        if scalar:
            fields[key] = fold(scalar.group(2), scalar.group(1))
            continue
        inline = re.search(rf"^{key}:[ \t]*(.*)$", block, re.M)
        if inline:
            fields[key] = inline.group(1).strip().strip("'\"")
    return fields


def check(path: Path) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []

    fields = frontmatter(path)
    if fields is None:
        return ["no YAML frontmatter — the skill will not load"], [], 0

    name = fields.get("name")
    if not name:
        errors.append("frontmatter has no `name`")
    elif name != path.parent.name:
        errors.append(f"`name: {name}` does not match directory {path.parent.name!r}")

    description = fields.get("description")
    if not description:
        errors.append("frontmatter has no `description` — nothing routes to this skill")
        return errors, warnings, 0

    size = len(description)
    if size > MAX_DESCRIPTION:
        errors.append(
            f"description is {size} chars, {size - MAX_DESCRIPTION} over the "
            f"{MAX_DESCRIPTION} limit — this fails the plugin install"
        )
    elif MAX_DESCRIPTION - size < NARROW:
        warnings.append(
            f"description is {size} chars, only {MAX_DESCRIPTION - size} under "
            f"the limit — one more trigger phrase tips it over"
        )
    return errors, warnings, size


def main() -> int:
    paths = sorted(SKILLS.glob("*/SKILL.md"))
    if not paths:
        print(f"FAIL: no SKILL.md found under {SKILLS}", file=sys.stderr)
        return 1

    failed = False
    warned = 0
    for path in paths:
        errors, warnings, size = check(path)
        label = path.parent.name
        if errors:
            failed = True
            for line in errors:
                print(f"FAIL [{label}]: {line}", file=sys.stderr)
        for line in warnings:
            warned += 1
            print(f"WARN [{label}]: {line}", file=sys.stderr)
        if not errors and not warnings:
            print(f"ok   [{label}]: description {size}/{MAX_DESCRIPTION}")

    if failed:
        return 1
    print(f"PASS: {len(paths)} skills checked, {warned} near the limit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
