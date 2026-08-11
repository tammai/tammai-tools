# Doc quality rubric (LLM judge)

Score each dimension 1–5. For every score below 5, cite the offending
line numbers. A score without citations is invalid.

Language: judge the document in its own language (English or
Vietnamese). All four dimensions apply identically. For Vietnamese,
"tone 5" means the register of an internal engineering wiki — trực
tiếp, không rào đón, không văn marketing — not translated-English
corporate prose.

## 1. Redundancy
5 = every idea appears exactly once; cross-references use links.
3 = 1–2 restatements of earlier content.
1 = sections repeat each other; summary restates body.

## 2. Coherence
5 = linear read; each section assumes exactly what came before, no more.
3 = minor ordering issues or one orphaned section.
1 = sections readable in any order because each re-explains context.

## 3. Information density
5 = no sentence survives deletion without information loss.
3 = scattered filler sentences or over-explained trivial steps.
1 = padding throughout; examples outnumber facts.

## 4. Tone
5 = reads like a senior engineer's internal wiki page; facts only.
3 = occasional selling adjectives or fake emphasis (bold mid-sentence).
1 = product-landing-page voice; enthusiasm, rule-of-three, rhetorical
    questions.

## Procedure
1. Read the whole document once before scoring.
2. Score all four dimensions with line citations.
3. If any dimension < 4: rewrite only the cited lines, re-score once.
4. Output final scores as a single line.
