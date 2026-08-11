#!/usr/bin/env python3
"""Assert the bundled Vale config actually fires.

Run this after touching .vale.ini or any styles/**/*.yml.

The failure mode this exists to catch is silence. Two real bugs shipped in
the first draft of this config, and both reported "0 errors, 0 warnings" —
indistinguishable from a clean document:

  * `TokenIgnores` with a backtick-delimited pattern lost its outer
    backticks to Vale's INI parser and degraded into one matching every
    run of non-backtick characters, i.e. the whole file. Every rule was
    silenced.
  * Vale CONCATENATES successive `raw` entries instead of OR-ing them, so
    both TamMaiVI files compiled into a regex demanding all of their
    phrases in sequence. Neither had ever matched anything.

Checking a total count is not enough — a rule can go dead while another
over-fires and keeps the sum intact. Counts are asserted per rule.

Exit 0 on pass, 1 on failure. Stdlib only.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "vale" / ".vale.ini"
FIXTURE = HERE / "fixture.md"

# Planted violations in fixture.md. Clean control lines and the code-scoping
# section must contribute nothing, so the total is exactly the sum below.
EXPECTED = {
    "TamMai.BannedWords": 2,
    "TamMai.Emoji": 1,
    "TamMai.Fillers": 1,
    "TamMai.Substitutions": 1,
    "TamMaiVI.Fillers": 5,
    "TamMaiVI.Intensifiers": 1,
}

# Substrings that must never appear in a Match. The first two are the clean
# control lines; the rest live in inline code or a fenced block, which Vale's
# default markdown scoping is supposed to skip.
FORBIDDEN_MATCHES = ("Ubuntu", "port 8080", "--seamlessly", "utilize thing")


def main() -> int:
    if shutil.which("vale") is None:
        print("SKIP: vale not on PATH (brew install vale)", file=sys.stderr)
        return 0
    for path in (CONFIG, FIXTURE):
        if not path.exists():
            print(f"FAIL: missing {path}", file=sys.stderr)
            return 1

    proc = subprocess.run(
        ["vale", "--config", str(CONFIG), "--no-exit", "--output=JSON", str(FIXTURE)],
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        print(f"FAIL: vale did not emit JSON\n{proc.stdout}\n{proc.stderr}", file=sys.stderr)
        return 1

    alerts = [a for file_alerts in report.values() for a in file_alerts]

    counts: dict[str, int] = {}
    for alert in alerts:
        counts[alert["Check"]] = counts.get(alert["Check"], 0) + 1

    failures = []
    for check, want in sorted(EXPECTED.items()):
        got = counts.get(check, 0)
        if got != want:
            hint = "  <- rule is DEAD" if got == 0 else ""
            failures.append(f"  {check}: expected {want}, got {got}{hint}")

    for check in sorted(set(counts) - set(EXPECTED)):
        failures.append(f"  {check}: unexpected rule fired {counts[check]}x")

    for alert in alerts:
        match = alert.get("Match", "")
        for needle in FORBIDDEN_MATCHES:
            if needle in match:
                failures.append(
                    f"  false positive on line {alert['Line']}: "
                    f"{alert['Check']} matched {match!r}"
                )

    if failures:
        print("FAIL: Vale config is not behaving as specified", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    total = sum(EXPECTED.values())
    print(f"PASS: {len(EXPECTED)} rules fired, {total} alerts, no false positives")
    return 0


if __name__ == "__main__":
    sys.exit(main())
