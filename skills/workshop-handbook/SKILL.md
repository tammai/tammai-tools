---
name: workshop-handbook
description: >
  Generates a complete, self-contained HTML handbook — a single long-form page with a sidebar of
  bookmarks, deep links, dark/light mode and a print stylesheet. Detailed reference reading, the
  written companion to a slide deck. Brandable from the same preset the workshop-slides skill uses;
  defaults to the BigIn design system (dark slate + orange, Google Sans). Use this skill whenever the
  user wants a handbook, manual, guide, playbook, workbook, participant notes, leave-behind, onboarding
  doc, runbook or written reference — even if they only provide a topic and no content. Triggers on
  phrases like "write a handbook for X", "make a guide about X", "workshop handbook", "participant
  notes", "training manual", "onboarding guide", "a long-form version of these slides", "something
  people can read afterwards". Also trigger proactively right
  after generating a deck with workshop-slides if the user mentions handing something out, emailing
  notes, or people needing the detail that would not fit on a slide.
---

# Workshop Handbook Generator

Generates a polished, fully self-contained HTML handbook using the BigIn design system.
Output is a single `.html` file the user opens directly in any browser — no server needed.

**This is the long-form counterpart to `workshop-slides`, not a variant of it.** A deck is a
fixed 1280×720 stage read *with* a presenter, where anything that overruns is silently cropped.
A handbook flows: length is free, and the job is to write down the detail that would not fit on
a slide. If the user wants something to present, use `workshop-slides`. If they want something to
hand out, read alone, and search under pressure — this skill.

## What every generated handbook ships with

These come from the template — you get them for free, and should mention them when handing it over:

| Feature | Detail |
|---|---|
| Bookmarks sidebar | Built at load from the headings. Every `<h2>` and every direct-child `<h3>` becomes a row in **one flat list** — no numbers, no nesting, no rules or fills; the two levels are told apart by weight alone |
| Scrollspy | The bookmark for the section being read turns accent-coloured and scrolls itself into view |
| Deep links | Every heading gets an `id` and a `#` anchor on hover, so any section can be linked to directly |
| Reading progress | A 2px accent bar across the top |
| Floating controls | One icon-only theme toggle, fixed top-right, at every viewport width — press **T** — plus a drawer trigger, fixed top-left, that only appears below 1080px. Nothing lives in a bar; both float above the content on scroll |
| Copy buttons | Every code block gets one in its header bar — always visible, with a `file://`-safe fallback |
| Tabs | Per-platform or per-variant instructions, with every panel printed on paper |
| Responsive | Below 1080px the sidebar becomes an off-canvas drawer — the floating trigger, **C**, or **Esc** to close, plus a close button and a tappable backdrop. There is no separate mobile header bar |
| Figure numbers | `<figcaption>` counts itself — the only auto-numbered thing in the document |
| Print / PDF | Cmd-P gives a contents page, then chapters one per page, forced to a light palette |
| Icons | Every control uses genuine [Lucide](https://lucide.dev) icon markup (24×24, stroke-width 2) — no icon font, no CDN, just inline `<svg>` |

**Headings are deliberately unnumbered.** No `1.`, no `4.2.1`, in the page or in the sidebar. Emphasis comes from accenting a key word inside the title with `<em>`, which reads better in a contents list than a numeral and removes a whole class of drift between the two.

**Nothing is cropped and nothing is hidden.** All content is in the DOM and visible, so the
browser's own Ctrl-F works across the whole document — which is why the skill does not build a
search box, and why no content is ever collapsed behind a toggle.

## Exporting to PDF

**Cmd-P / Ctrl-P in the browser is the whole export path.** The `@media print` block lays out a
contents page, then each chapter starting on a new page, in a forced light palette with callouts,
code blocks, figures and table rows kept off page boundaries.

Do **not** reach for `slides-to-pdf` here — it exists to give a deck a fixed 960×540 page per slide
and injects print CSS that assumes a slide stage. A handbook paginates by content length instead.

## Step 1 — Gather content

Before generating, ensure you have:

| Field | Required | Notes |
|---|---|---|
| Handbook title | Yes | e.g. "Docker for Backend Devs" |
| Subtitle / lede | Optional | One sentence on who it is for and what they will be able to do |
| Chapter outline or content | Optional | If absent, generate a sensible outline for the topic |
| Footer info for the cover | Optional | e.g. "BigIn · 2026" |

If the user gave only a topic, generate a complete outline of **4–8 chapters**: orientation and
prerequisites → core concepts → the main procedure, step by step → troubleshooting → an appendix
or glossary. Give each chapter 2–5 sections.

**Write for someone reading alone, under time pressure, who arrived from a search.** That means:
state the prerequisite before the step that needs it, show the actual command and its actual
output, name the error message someone will paste into a search box, and put a troubleshooting
chapter in. Where a slide says "three commands", the handbook lists all three and explains each.

If this handbook accompanies a deck, **do not paraphrase the slides**. The deck carries the
argument; the handbook carries the detail the argument skipped.

## Step 1b — Branding

**Always** run this step before building. Do not skip it.

The handbook reads and writes the **same preset file as `workshop-slides`** —
`~/.workshop-slides-preset.json`, same schema, same keys. A handbook is normally handed out
alongside a deck, so one brand means one file. If the user already made a preset for their slides,
it applies here with no further questions.

### 1. Check for a saved preset

Try to read **`~/.workshop-slides-preset.json`**.

### 2. Present options to the user

Use `AskUserQuestion` to present exactly **two** choices:

**If no saved preset exists:**

| Option | Label | Description |
|---|---|---|
| A | Use BigIn preset | Dark slate + orange accent, Google Sans throughout, Fira Code for code, BigIn watermark. Ready now. |
| B | Create my own preset | Define your brand colors, fonts, and logo — saved for all future handbooks *and* decks. |

**If a saved preset exists** (read the `name` field from the JSON):

| Option | Label | Description |
|---|---|---|
| A | Use BigIn preset | Dark slate + orange accent, Google Sans throughout, Fira Code for code. |
| B | Use my "[name]" preset | Show the saved accent color and font names from the JSON file. |

Include a third option in the saved-preset case: **"Update my preset"** — re-collect all fields and
overwrite the saved file. Say plainly that this also changes future slide decks, since the file is
shared.

### 3. Act on the choice

**BigIn preset** → proceed with template defaults, no CSS changes needed.

**Saved preset** → pass the file to `build.py` with `--preset`.

**Create / Update preset** → collect these fields in order:

**Preset name** — free text (e.g. `My Company`, `ACME Corp`).

**Accent color** — present the full Tailwind accent palette via `AskUserQuestion`. Each option
label is the color name; the description is the 500-shade hex:

| Label | Hex (500) | | Label | Hex (500) |
|---|---|---|---|---|
| Red | `#ef4444` | | Teal | `#14b8a6` |
| Orange | `#f97316` | | Cyan | `#06b6d4` |
| Amber | `#f59e0b` | | Sky | `#0ea5e9` |
| Yellow | `#eab308` | | Blue | `#3b82f6` |
| Lime | `#84cc16` | | Indigo | `#6366f1` |
| Green | `#22c55e` | | Violet | `#8b5cf6` |
| Emerald | `#10b981` | | Purple | `#a855f7` |
| Fuchsia | `#d946ef` | | Pink | `#ec4899` |
| Rose | `#f43f5e` | | | |

If the user selects "Other", ask them to type a hex code.

**Background color** — present the Tailwind neutral palette. Label = scale name + shade
(e.g. "Slate 950"), description = hex:

| Label | 950 hex | 900 hex |
|---|---|---|
| Slate | `#020617` | `#0f172a` |
| Gray | `#030712` | `#111827` |
| Zinc | `#09090b` | `#18181b` |
| Neutral | `#0a0a0a` | `#171717` |
| Stone | `#0c0a09` | `#1c1917` |

**Heading font** — `Google Sans`, `Poppins`, `Plus Jakarta Sans` (or custom).

**Body font** — `DM Sans`, `Outfit`, `Nunito` (or custom). For a handbook this is the font
carrying thousands of words, so favour a face with a generous x-height.

**Code font** — `Fira Code`, `Source Code Pro`, `Cascadia Code` (or custom).

**Logo** — URL to SVG/PNG, or "none".

After collecting, **save** to `~/.workshop-slides-preset.json`:

```json
{
  "name": "My Company",
  "accent": "#6366f1",
  "background": "#0a0a0a",
  "fontMain": "Google Sans",
  "fontBody": "DM Sans",
  "fontCode": "Fira Code",
  "googleFontsUrl": "https://fonts.googleapis.com/css2?family=Google+Sans:ital,opsz,wght@0,17..18,400..700;1,17..18,400..700&family=DM+Sans:wght@400;500;600&family=Fira+Code:wght@400&display=swap",
  "watermark": "<img src='https://example.com/logo.svg' alt='My Company'>"
}
```

Set `"watermark": ""` if the user chose no logo.

If `$HOME` is not writable, the save buys nothing — the next session starts with no preset. Don't
quietly drop the file beside the handbook instead: pass the preset to `build.py` for this document,
and tell the user it could not be persisted, or ask where to keep the JSON.

## Step 2 — Read the template and the reference handbook

Read the template from **`assets/template.html`** (in the same directory as this SKILL.md).

**Also read `demo.html`** in that same directory. It is a complete 6-chapter reference document
where every chapter carries an HTML comment naming the components it demonstrates:

```html
<!-- 03 · CODE · .code-path · <pre> block with syntax classes · .wrap variant · steps -->
```

Copy the closest pattern from `demo.html` and swap the content. Do not re-derive markup from
scratch — the demo is the source of truth for how components compose, and it covers: cover block,
chapter ledes, bullet / nested / numbered / checklist lists, definition lists, all four callout
types, pull quotes, code blocks with syntax highlighting, file paths, step procedures, three table
shapes, card grids, stats, tags, an inline-SVG figure, cross-references, and an unnumbered appendix.

### Use `assets/build.py` — do not hand-assemble the file

Writing the whole document out by hand makes the "keep the head unchanged" rule aspirational, and
it **measurably fails**. A deck generated that way in this repo from an unmodified template had
silently dropped all 18 `--dg-*` diagram tokens and the `.diagram` sizing rule — diagrams rendering
with no fill, with no error to explain it.

So write **only the content** to a fragment file, and let the script carry the other ~80 KB across
as bytes:

```bash
python3 assets/build.py assets/template.html "$TMPDIR/content.html" out/my-handbook.html
```

`content.html` holds just the `.cover` block and the `<section class="chapter">` elements — no
`<head>`, no sidebar, no `<main>` wrapper. Standard library only, so there is nothing to install.

**Write the fragment to a scratch path**, as above — `$TMPDIR`, not next to the handbook. The
fragment is scaffolding, not output, and so is anything else generated on the way: page rasters,
a preset written for this document only. Delete scratch once the handbook verifies; only the
handbook itself is output.

For a non-BigIn preset, pass it in rather than editing the head yourself:

```bash
python3 assets/build.py assets/template.html "$TMPDIR/content.html" out/my-handbook.html \
  --preset ~/.workshop-slides-preset.json \
  --title "Docker for Backend Devs" --subtitle "Workshop handbook · 2026"
```

`--title` sets both the browser tab and the sidebar title; `--subtitle` sets the line beneath it.
`"watermark": ""` in the preset removes the whole `#watermark` block.

### What the script refuses, and what it merely warns about

It **refuses to write** on a structural error: no `<section class="chapter">` at all, or a chapter
with no `<h2>` (which loses its bookmark *and* pushes every later sidebar number out of step with
the page, because the CSS counter still increments).

It **warns without blocking** on: a duplicate `id`, a cross-reference pointing at an id nothing
produces, a heading level skipped, an `<h1>` inside a chapter, an `<h3>` nested too deep to become
a bookmark, a CSS counter set by the content, hardcoded hex colors, a `.code-block` with no `<pre>`,
a preset watermark pointing at a remote URL or local path, an `<svg>` whose shapes reach past its
own `viewBox`, an attribute-sized `<svg>` wider than the 820px text column without `class="diagram"`,
and **any `workshop-slides` class that has no rule in this stylesheet** — `.slide-body`, `.cols-2`,
`.code-line`, `.cmp-table`, `.stat-block` and friends render as unstyled prose with no visual cue
that anything was meant to be there, and reaching for them out of habit is the single most likely
mistake when moving between the two skills.

All of those scans skip the inside of `<pre>` and `<code>`, so a handbook that *documents* markup
does not get flagged for the markup it is documenting.

It also verifies the carried-over head still contains the `--dg-*` tokens, `.diagram`,
`@media print`, `--content-width`, `buildToc`, the scrollspy, the sidebar, the theme toggle, the
progress bar, the copy buttons, the counters and the favicon.

**If you cannot run the script** (no shell access), assemble by hand — then verify before handing
it over:

```bash
grep -c -- '^[[:space:]]*--dg-' out/my-handbook.html   # must print 18
for p in '.diagram {' '@media print' '--content-width' 'buildToc' 'READING_LINE' \
         'id="toc"' 'id="sidebar"' 'id="themeToggle"' 'copy-btn' 'base64,'; do
  grep -q -- "$p" out/my-handbook.html && echo "ok   $p" || echo "MISS $p"
done
```

Anything other than `18`, or any `MISS`, means the head was not carried across intact.

## Step 3 — Write the content

Patterns below are the quick reference; `demo.html` shows each one in a finished document.

### Never type a number

Headings carry no numerals, and neither does the sidebar. Typing `1.2` into an `<h2>` both
reintroduces the numbering this template dropped **and** puts the digits in the bookmark, because
`buildToc()` takes the heading's own text. `build.py` warns when it sees one.

Figures and steps *are* CSS counters, so don't set `counter-reset` in your content either.

### Hero — once, at the top

```html
<div class="cover">
  <div class="cover-kicker">BigIn · Hands-on Handbook</div>
  <h1>WordPress on your laptop,<br><em>powered by Docker</em></h1>
  <p class="cover-lede">One sentence on who this is for and what they will be able to do.</p>
  <div class="tags">
    <span class="tag accent">~45 minutes</span>
    <span class="tag">Windows + macOS</span>
  </div>
  <div class="cover-meta">BigIn · 2026</div>
</div>
```

This holds the document's **only** `<h1>`. Put the accented run in an `<em>`, usually on its own
line after a `<br>`.

### Chapter — the unit of everything

```html
<section class="chapter" id="getting-started">
  <div class="part-label">Part 1 · Setup</div>
  <h2>Getting <em>started</em></h2>
  <p class="h-sub">One line of framing, so a reader can tell from the top whether this is the chapter they want.</p>

  <h3>Install the toolchain</h3>
  <p>Prose…</p>

  <h4>On macOS</h4>
  <p>A sub-point. Does not appear in the sidebar.</p>
</section>
```

- `.part-label` is optional — a small chip marking the start of a new act. Use it on the first
  chapter of each part, not on every chapter.
- Accent **one** word or short phrase in the `<h2>` with `<em>`. Never the whole title.
- `.h-sub` is the one-line framing under the title. Use it on every chapter.
- The `id` is optional — omit it and one is slugified from the heading. **Set one when a link to
  this section needs to outlive the wording of its title.**
- `<h3>` must be a **direct child** of `.chapter` to become a bookmark.
- `<h4>` is not bookmarked. Do not go deeper than `<h4>`.
- An appendix or glossary is just another chapter — there is no numbering to opt out of.

### Prose

```html
<p>Text with <strong>strong emphasis</strong>, an <em>accented key term</em>,
   some <code>inline_code()</code>, a <kbd>⌘K</kbd> shortcut, and a
   <a href="#other-chapter">cross-reference</a>.</p>
```

`<em>` renders in the accent color, not italics — the same rule as the deck. Use `<i>` or `<cite>`
when you actually want italics.

### Lists

```html
<ul class="list">
  <li><strong>Bold label</strong> — supporting detail
    <ul class="list"><li>One level of nesting, muted dots</li></ul>
  </li>
</ul>

<ul class="list numbered">
  <li>First point</li>
</ul>

<ul class="list check">
  <li class="done">Already handled</li>
  <li>Still to do</li>
</ul>
```

### Callouts — four types

```html
<div class="callout note">
  <span class="callout-label">Note</span>
  Background a careful reader wants and a hurried one can skip.
</div>
```

| Class | Hue | Use for |
|---|---|---|
| `note` | blue | Background, context, an aside |
| `tip` | mint | A shortcut or a better way round |
| `warn` | amber | A trap with real consequences — data loss, a silent failure |
| `key` | accent | The one sentence worth carrying into the next chapter |
| `info` | slate | A neutral remark that needs setting apart without claiming urgency |

Spend `warn` and `key` sparingly — at most one or two per chapter, or they stop registering.

```html
<blockquote class="quote">
  The line worth remembering.
  <cite>— attribution</cite>
</blockquote>
```

### Code

**This is a real `<pre>`, unlike the deck's one-div-per-line block.** Write real newlines and real
indentation; do not use `.code-line`.

```html
<div class="code-block">
  <div class="code-head">
    <span class="code-lang">python</span>
    <span class="code-path">src/config.py</span>
  </div>
  <pre><code><span class="cmt"># comment</span>
<span class="kw">def</span> <span class="fn">greet</span>(name):
    <span class="kw">return</span> <span class="str">f"Hello, {name}"</span></code></pre>
</div>
```

The `.code-head` bar carries the language, an optional file path, and the copy button (added by
the script). Both spans are optional; omit the whole bar and one is created for the button.

- Syntax classes: `.kw` keyword (accent), `.fn` function name (light), `.str` string, `.cmt` comment.
- **Escape `<`, `>` and `&`** inside the block — it is real HTML, so `<div>` must be written
  `&lt;div&gt;`.
- Do not indent the `<pre>` contents to match the surrounding HTML: whitespace is preserved and
  that indentation will show up in the output and in whatever the reader copies.
- Long lines scroll horizontally. Add `class="code-block wrap"` for a single long command that
  should soft-wrap instead — wrong for a listing where indentation carries meaning.

### Tabs — the same step on two platforms

```html
<div class="tabs">
  <div class="tab-bar">
    <button class="tab-btn active" type="button">macOS</button>
    <button class="tab-btn" type="button">Windows</button>
  </div>
  <div class="tab-panel active">…first panel…</div>
  <div class="tab-panel">…second panel…</div>
</div>
```

Buttons and panels pair up **by position**, so keep the counts equal and the order matching.
Marking one `active` in the markup sets the opening tab; if none is marked the script opens the
first. On paper the bar is hidden and every panel prints, so nothing is lost in the PDF.

### Steps — a procedure with room to breathe

```html
<div class="steps">
  <div class="step">
    <h4>Install the CLI</h4>
    <p>Explanation, and a code block if the step needs one.</p>
  </div>
</div>
```

Numbered circles joined by a rail. Use this over `.list.numbered` when each step needs more than
one line.

### Tables

Always wrap in `.table-wrap` so a wide table scrolls rather than breaking the layout.

```html
<div class="table-wrap">
  <table class="keyed">          <!-- first column reads as the row's label -->
    <thead><tr><th>Flag</th><th>Default</th><th>What it does</th></tr></thead>
    <tbody><tr><td>--preset</td><td>none</td><td>Reads brand values from JSON</td></tr></tbody>
  </table>
</div>
```

Three modifiers:

| Class | Effect |
|---|---|
| `keyed` | First column is the row's label — semibold, unwrapped. For options and settings |
| `cmd` | First-column `<code>` renders accented and unwrapped. For a command reference |
| `cmp` | Column 2 is the recommended option, column 3 the alternative — put the one you are advocating in the middle, same convention as the deck |

```html
<dl class="deflist">
  <dt>Term</dt>
  <dd>Meaning. Lighter than a table when there are only two columns.</dd>
</dl>
```

### Cards, stats and tags

```html
<div class="cards">
  <div class="card accent">          <!-- at most one accent card per grid -->
    <div class="card-title">Start here</div>
    <p>Short description.</p>
  </div>
  <div class="card">
    <div class="stat-number">10×</div>
    <div class="stat-label">faster</div>
  </div>
</div>

<div class="tags">
  <span class="tag accent">Hands-on</span>
  <span class="tag">~45 min</span>
</div>
```

The grid is `auto-fit, minmax(220px, 1fr)` — it reflows on its own, so do not try to control the
column count.

### Figures and diagrams

```html
<figure>
  <svg class="diagram" viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg"
       role="img" aria-label="Describe the diagram for screen readers">…</svg>
  <figcaption>Caption. The "Fig. n ·" prefix is added and numbered automatically.</figcaption>
</figure>
```

Add `class="figure plain"` to drop the figure number.

For anything bigger than one small diagram — a flowchart, a wireframe, a mindmap — use the
**`soft-visuals`** skill and paste its `<svg>` in here. It shares this exact `--dg-*` token set, so
it needs no edits. The same tokens and the same rules as the deck apply:

| Token | Use |
|---|---|
| `--dg-blue` / `--dg-blue-fill` | Card border / translucent fill. Also `violet`, `mint`, `amber`, `rose`, `cyan` |
| `--dg-accent-fill` | Fill paired with `var(--brand-accent)` — for the *one* node you're highlighting |
| `--dg-text` / `--dg-muted` | Card title / caption |
| `--dg-line` | Connectors and arrowheads |

- **Flat by design — no shadows, and never `filter:`/`feDropShadow`.** A filtered region forces
  Chrome's print path to rasterise that area into a bitmap, so the page stops being pure vector.
- **Use the translucent `*-fill` tokens, not solid colors** — a 16% wash reads correctly over both
  the dark and the light page.
- **Size the `viewBox` from the shapes.** Content outside it is not clipped with any signal — it is
  simply never drawn, on screen and in print alike. Add up the furthest shape edge, plus half its
  stroke width, plus a small margin. `build.py` warns when it can prove an overflow from the
  attributes, but getting it right when you write the shape is cheaper.
- **Marker ids must be unique per document.** Several `<svg>` blocks in one handbook each need their
  own suffixed marker id, or every arrowhead resolves to the first one.

## Design tips

- **Length is free, but attention is not.** 4–8 chapters, 2–5 sections each. If a chapter passes
  ~8 sections it is two chapters.
- Open every chapter with an `.h-sub`. It is what a reader scanning the sidebar lands on to decide
  whether this is the chapter they want.
- **Accent exactly one run per heading** with `<em>` — the verb or the noun that makes the chapter
  distinct, not the generic half. "Code and *procedures*", not "*Code and procedures*".
- Write headings that read well stripped of context: they become the sidebar rows verbatim, with
  no number in front to lean on. "Install Docker Desktop" beats "Installation".
- Cross-reference other chapters by anchor rather than repeating yourself — `build.py` checks
  that every `#target` resolves.
- End the handbook with an appendix or glossary, and a `<footer>` in the last chapter.
- Both light and dark are first-class — never hardcode a hex in content. Use `var(--brand-accent)`
  and the `--slate-*` scale, or the handbook breaks when the reader presses **T**.

## Pre-save checklist

- [ ] Exactly one `<h1>`, inside the `.cover`
- [ ] Every chapter has an `<h2>` with exactly one `<em>` run; every `<h3>` is a direct child of its `.chapter`
- [ ] No numbers typed into headings, and no `counter-reset` in the content
- [ ] Every `.tabs` group has equal, matching-order `.tab-btn` and `.tab-panel` counts
- [ ] Code blocks use `<pre><code>` with `<`, `>`, `&` escaped — no `.code-line`
- [ ] No `workshop-slides` classes carried over
- [ ] Every cross-reference resolves; no duplicate `id`s
- [ ] No hardcoded colors — only `var(--brand-accent)` / `--slate-*`
- [ ] Built through `build.py`, and every warning read
- [ ] Opened once: clicked three bookmarks, toggled the theme, printed to PDF to check pagination
- [ ] File saved with a descriptive kebab-case name, and no build scratch left beside it
