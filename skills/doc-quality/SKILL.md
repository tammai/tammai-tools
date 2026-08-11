---
name: doc-quality
description: >
  Enforce documentation quality on any markdown output (README, guides,
  playbooks, specs). Use whenever generating or editing docs, or when the
  user asks to lint, tighten, de-slop, or review a document. Runs three
  passes: deterministic lint (Vale + markdownlint), compression, and an
  LLM-judge rubric for redundancy/coherence.
---

# doc-quality

Applies to every markdown document this session produces or edits,
in English or Vietnamese. Project-agnostic: no assumptions about
stack, repo layout, or branding. Vale runs two styles on all files:
`TamMai` (English) and `TamMaiVI` (Vietnamese); patterns are
language-disjoint so no file scoping is required. Compression and
judge passes run in the document's own language.

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

## Pass 1 — Deterministic lint (hard gate)

Run Vale with the bundled config, plus markdownlint if available:

```bash
vale --config <skill-dir>/assets/vale/.vale.ini <files>
markdownlint <files>   # optional, skip if not installed
```

Fix every error-level finding, re-run until clean. If Vale is not
installed, apply `assets/vale/styles/TamMai/*.yml` manually as a checklist
(each rule file lists its banned tokens/swaps) and say so in the final
message.

## Pass 2 — Compression

Rewrite the full document once with a global view. If Pass 0 was
applied during drafting, this is a verification sweep, not a 40% cut —
target whatever redundancy survived. For pre-existing documents,
expect the full cut:

- Cut ~40% of words. Keep all technical facts, commands, and constraints.
- One idea in one place; replace restatements with links.
- Delete preamble, mini-conclusions, and any sentence whose removal
  loses no information.
- Prefer one example over three; a table over parallel prose.

## Pass 3 — Judge rubric (soft gate)

Score the document against `assets/rubric.md`. Any dimension below 4/5:
rewrite the cited lines and re-score once. Do not loop more than twice.
Report final scores in one line, e.g. `redundancy 5, coherence 4,
density 5, tone 5`.

## Output contract

- State which passes ran and what changed (one short paragraph, no
  per-edit narration).
- Never ship a document that skipped Pass 1 without flagging it.
