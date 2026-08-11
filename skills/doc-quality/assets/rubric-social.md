# Social post rubric (LLM judge)

Score each dimension 1–5. For every score below 5, cite the offending
line numbers. A score without citations is invalid.

Language: judge the post in its own language (English or Vietnamese).
All four dimensions apply identically.

This rubric replaces `rubric.md` in `social` mode. It is not a relaxed
version of it — the dimensions are different, because a post fails in
different ways than a document does.

## 1. Hook
5 = the first line states a specific claim, number, or tension.
3 = generic opener that could head any post on the topic.
1 = throat-clearing; the point arrives in paragraph two or later.

## 2. Single idea
5 = one claim, developed once, landed.
3 = one claim plus a digression that dilutes it.
1 = unrelated observations stacked with no through-line.

## 3. Concreteness
5 = numbers, names, a real incident carry the post.
3 = one concrete detail surrounded by abstraction.
1 = true of any company in any year; nothing anchors it.

## 4. Voice
5 = a person talking. Contractions, one clear opinion, willing to be wrong.
3 = competent but anonymous; no one in particular wrote it.
1 = AI-default cadence — rule-of-three throughout, em-dash triplets,
    "It's not X. It's Y.", a closing rhetorical question.

## Deliberately not penalised

Emoji, rhetorical questions, sentence fragments and rule-of-three are
legitimate devices in social copy, and `rubric.md` scoring them as tone=1
is exactly why a post needs its own rubric. Vale's emoji rule is off in
this mode for the same reason.

Score them under **Voice** only when they read as generated rather than
chosen: three of them stacked in one post, a rhetorical question used as
a closer because posts tend to end that way, an emoji per bullet as
decoration rather than structure. One deliberate rhetorical question is
a voice; four is a cadence.

## Hard gate — character limit

Count **characters, not words**. Over the limit is a fail regardless of
every other score; cut to fit before scoring anything else.

| Platform | Limit |
|---|---|
| LinkedIn | 3000 |
| X | 280 (25 000 with premium) |
| Threads | 500 |
| Bluesky | 300 |

## Procedure
1. Read the whole post once before scoring.
2. Check the character limit first. Over → cut to fit, then score.
3. Score all four dimensions with line citations.
4. If any dimension < 4: rewrite only the cited lines, re-score once.
5. Output final scores as a single line, with the character count.
