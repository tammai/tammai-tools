#!/usr/bin/env python3
"""Assert both bundled Vale configs actually fire.

Run this before Pass 1, and after touching any .vale*.ini or styles/**/*.yml.

The failure mode this exists to catch is silence. Three real bugs shipped in
the first draft of this config, and every one reported "0 errors, 0 warnings" —
indistinguishable from a clean document:

  * `TokenIgnores` with a backtick-delimited pattern lost its outer backticks
    to Vale's INI parser and degraded into one matching every run of
    non-backtick characters, i.e. the whole file. Every rule was silenced.
  * Vale CONCATENATES successive `raw` entries instead of OR-ing them, so both
    TamMaiVI files compiled into a regex demanding all of their phrases in
    sequence. Neither had ever matched anything.
  * `in order to` sat in both Fillers and Substitutions and double-reported.

Two properties make the assertions non-obvious:

  * Counts are asserted PER RULE, not as a total. A rule can go dead while
    another over-fires and keeps the sum intact.
  * The social config asserts zero emoji hits AND that other rules still fire
    in the same run. Zero-emoji alone proves nothing — Vale ignores an
    unrecognised key like `TamMai.Emoji = NO` silently, and a wholly broken
    config also scores zero on every rule.

Exit 0 on pass, 1 on failure. Stdlib only.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Substrings that must never appear in a Match. The first two are the clean
# control lines present in both fixtures; the rest live in inline code or a
# fenced block, which Vale's default markdown scoping is supposed to skip.
FORBIDDEN_MATCHES = ("Ubuntu", "port 8080", "--seamlessly", "utilize thing")

CASES = [
    {
        "name": "doc",
        "config": HERE / "vale" / ".vale.ini",
        "fixture": HERE / "fixture.md",
        # Planted violations. Clean control lines and the code-scoping section
        # contribute nothing, so the total is exactly the sum below.
        "expected": {
            "TamMai.BannedWords": 2,
            "TamMai.Emoji": 1,
            "TamMai.Fillers": 1,
            "TamMai.Substitutions": 1,
            "TamMaiVI.Fillers": 5,
            "TamMaiVI.Intensifiers": 1,
        },
    },
    {
        "name": "social",
        "config": HERE / "vale" / ".vale-social.ini",
        "fixture": HERE / "fixture-social.md",
        # Emoji off; everything else armed. BannedWords and Intensifiers firing
        # here is what proves the config loaded rather than collapsed.
        "expected": {
            "TamMai.BannedWords": 1,
            "TamMaiVI.Intensifiers": 1,
        },
        # Must be absent entirely, not merely low.
        "silenced": ["TamMai.Emoji"],
    },
]


def run_vale(config: Path, fixture: Path) -> list | None:
    proc = subprocess.run(
        ["vale", "--config", str(config), "--no-exit", "--output=JSON", str(fixture)],
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        print(f"  vale did not emit JSON\n{proc.stdout}\n{proc.stderr}", file=sys.stderr)
        return None
    return [a for alerts in report.values() for a in alerts]


def check(case: dict) -> list[str]:
    for path in (case["config"], case["fixture"]):
        if not path.exists():
            return [f"missing {path}"]

    alerts = run_vale(case["config"], case["fixture"])
    if alerts is None:
        return ["vale produced no parseable output"]

    counts: dict[str, int] = {}
    for alert in alerts:
        counts[alert["Check"]] = counts.get(alert["Check"], 0) + 1

    failures = []
    expected = case["expected"]
    silenced = case.get("silenced", [])

    for rule, want in sorted(expected.items()):
        got = counts.get(rule, 0)
        if got != want:
            hint = "  <- rule is DEAD" if got == 0 else ""
            failures.append(f"{rule}: expected {want}, got {got}{hint}")

    for rule in silenced:
        if counts.get(rule, 0):
            failures.append(f"{rule}: expected 0 (switched off), got {counts[rule]}")

    for rule in sorted(set(counts) - set(expected) - set(silenced)):
        failures.append(f"{rule}: unexpected rule fired {counts[rule]}x")

    for alert in alerts:
        match = alert.get("Match", "")
        for needle in FORBIDDEN_MATCHES:
            if needle in match:
                failures.append(
                    f"false positive on line {alert['Line']}: "
                    f"{alert['Check']} matched {match!r}"
                )

    return failures


def main() -> int:
    if shutil.which("vale") is None:
        print("SKIP: vale not on PATH (brew install vale)", file=sys.stderr)
        return 0

    ok = True
    for case in CASES:
        failures = check(case)
        if failures:
            ok = False
            print(f"FAIL [{case['name']}]: config is not behaving as specified", file=sys.stderr)
            for line in failures:
                print(f"  {line}", file=sys.stderr)
        else:
            rules = len(case["expected"]) + len(case.get("silenced", []))
            total = sum(case["expected"].values())
            print(f"PASS [{case['name']}]: {rules} rules checked, {total} alerts, no false positives")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
