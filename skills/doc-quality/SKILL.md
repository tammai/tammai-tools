---
name: doc-quality
description: >
  Enforce documentation quality on any markdown output (README, guides,
  playbooks, specs) or social copy (LinkedIn, X, Threads, Bluesky posts,
  launch announcements, release blurbs). Use whenever generating or editing
  docs or posts, or when the user asks to lint, tighten, de-slop, or review
  one. Runs four passes: drafting rules, deterministic lint (Vale +
  markdownlint), measurement-driven compression, and an LLM-judge rubric.
  Two modes — `doc` and `social` — each with its own rubric and Vale config.
---

# doc-quality

Applies to every markdown document or social post this session produces
or edits, in English or Vietnamese. Project-agnostic: no assumptions about
stack, repo layout, or branding. Vale runs two styles on all files:
`TamMai` (English) and `TamMaiVI` (Vietnamese); patterns are
language-disjoint so no file scoping is required. Compression and
judge passes run in the document's own language.

## Mode

Pick one before drafting. Mode selects the rubric, the Vale config, and
the Pass 0 rules.

| Mode | Rubric | Vale config | Hard gate |
|---|---|---|---|
| `doc` (default) | `assets/rubric.md` | `assets/vale/.vale.ini` | Vale clean |
| `social` | `assets/rubric-social.md` | `assets/vale/.vale-social.ini` | Vale clean + platform limit |

Infer from the artifact: README, guide, spec, playbook, runbook → `doc`.
LinkedIn / X / Threads post, launch announcement, release blurb →
`social`. Ask only if genuinely ambiguous.

The two are not strict/relaxed variants of each other. `rubric.md` scores
rhetorical questions and rule-of-three as tone=1 and the `doc` Vale config
bans emoji at error level, so a social post run in `doc` mode fails the
Pass 1 hard gate on devices that are legitimate there. Slop words stay
banned in both.

## Pass 0 — Writing rules (apply while drafting, not after)

When this skill is active and you are WRITING or restructuring a
document (not just linting an existing one), draft under these
constraints from the first token:

- One idea appears in exactly one place. Cross-reference with a
  link; never restate.
- No preamble ("This document describes..."), no summary section
  that repeats the body, no concluding remarks.
- Headings carry the meaning; the first sentence under a heading
  must not repeat it.
- Prefer one example over three; a table over parallel prose.
- Budgets: README ≤ 150 lines, guide section ≤ 40 lines. If a
  budget breaks, split into linked docs — only when content
  genuinely differs.
- Outline section structure BEFORE writing prose. Check the
  outline for overlap between sections; merge overlaps first.
  Compression (Pass 2) cannot fix a wrong structure.
- Tone: internal engineering wiki. Facts only, in the document's
  language (English or Vietnamese).

In `social` mode, three of these invert:

- The first line is a hook, not a heading restatement. Lead with the
  claim, not the setup.
- No document budgets — the platform character limit replaces them.
- "No preamble" still holds, and binds harder: cut everything before
  the first concrete claim.

## Pass 1 — Deterministic lint (hard gate)

Run the self-test first, then Vale with the mode's config, plus
markdownlint if available:

```bash
python3 <skill-dir>/assets/selftest.py                      # must print PASS
vale --config <skill-dir>/assets/vale/.vale.ini <files>     # doc mode
vale --config <skill-dir>/assets/vale/.vale-social.ini <files>   # social mode
markdownlint <files>   # optional, skip if not installed
```

**The self-test is not optional polish.** This bug class fails silently:
a broken Vale config and a clean document both report `0 errors`, and
three separate defects shipped that way. A clean Vale run means nothing
until `selftest.py` prints PASS.

Fix every error-level finding, re-run until clean. If Vale is not
installed, apply `assets/vale/styles/TamMai/*.yml` manually as a checklist
(each rule file lists its banned tokens/swaps) and say so in the final
message.

## Pass 2 — Compression (target set by measurement, not by quota)

Do not cut to a fixed percentage. Score redundancy and information
density against the active rubric FIRST, with line citations, then cut
to the target those scores imply:

| Lower of redundancy / density | Cut |
|---|---|
| 5 | none — verify only, ship as-is |
| 4 | the cited spans only (typically 5–15%) |
| 3 | ~25% |
| ≤ 2 | 40%+ |

Rules:

- The cut is bounded by the citations. Delete only what the score cited
  as redundant or padded. If nothing is cited, nothing is cut — report
  that outcome. Never manufacture a cut to reach a number.
- Never trade a fact for a word count. Tables, commands, version
  numbers, limits and constraints survive every cut.
- One idea in one place; replace restatements with links.
- Prefer one example over three; a table over parallel prose.

### In `social` mode

`rubric-social.md` scores neither redundancy nor density, so the table
above has no input. Use the social dimensions that measure the same
thing — text not earning its place:

| Lower of hook / single idea | Cut |
|---|---|
| 5 | none — the character limit is the only bound |
| 4 | the cited spans only |
| 3 | ~25% |
| ≤ 2 | 40%+ |

A low **hook** score cites throat-clearing before the first claim; a low
**single idea** score cites the digressions. Both are cuttable, and both
name the spans to cut.

The platform character limit is a hard bound applied FIRST — an
over-limit post cannot ship at any score. Cut to fit, then apply the
table to whatever slack remains.

**Concreteness and voice are never cut signals.** A post scoring low on
concreteness needs specifics added, not prose removed, and the rewrite
may legitimately *grow* — bounded only by the character limit. Measured
on a real draft scoring `hook 2, single idea 2, concreteness 1, voice 1`:
the correct rewrite removed every slop phrase and still came out 10%
longer, because what it lacked was numbers and a named failure. A quota
would have scored that a failed pass.

Calibration, not a target: unedited LLM or marketing prose usually
loses 30–50%; a document drafted under Pass 0 usually loses under 10%.
If a Pass 0 draft scores 3 or below, Pass 0 is not working — say so
rather than quietly compressing around it.

## Pass 3 — Judge rubric (soft gate)

Score against the mode's rubric — `assets/rubric.md` for `doc`,
`assets/rubric-social.md` for `social`. Any dimension below 4/5: rewrite
the cited lines and re-score once. Do not loop more than twice.

Report final scores in one line:

- `doc` — `redundancy 5, coherence 4, density 5, tone 5`
- `social` — `hook 5, single idea 4, concreteness 5, voice 4, 1,847 chars`

Pass 2 already produced the redundancy and density citations in `doc`
mode, and the character count in `social`; reuse them rather than
re-deriving.

## Output contract

- State the mode, which passes ran, and what changed (one short
  paragraph, no per-edit narration).
- Report the Pass 2 target the scores implied and what was actually cut.
  "Scored 4/4, cut the three cited spans, 6%" is the shape. A cut with no
  citation behind it is a bug, not a tighter document.
- Never ship a document that skipped Pass 1 without flagging it, and
  never treat a clean Vale run as meaningful if `selftest.py` did not pass.
