---
name: workshop-slides
description: >
  Generates a complete, self-contained HTML slide deck for workshops and presentations.
  Fully brandable: accent color, background, fonts, and watermark logo are all configurable.
  Defaults to the BigIn design system (dark slate + orange, Google Sans). Use this skill whenever
  the user wants to create workshop slides, build a presentation, make a slide deck, or generate
  slides for a training session or talk — even if they only provide a topic and no content.
  Triggers on phrases like "create slides for X", "make a workshop deck", "build a presentation
  about X", "generate slide deck for X", "workshop slides", "presentation slides". Also trigger
  proactively when a user is preparing a workshop, training session, or talk and mentions wanting
  to present something, even if they don't say "slides" explicitly.
---

# Workshop Slide Generator

Generates a polished, fully self-contained HTML slide deck using the BigIn design system.
Output is a single `.html` file the user opens directly in any browser — no server needed.

## What every generated deck ships with

These come from the template — you get them for free, and should mention them when handing the deck over:

| Feature | Detail |
|---|---|
| Fixed 16:9 stage | Slides are authored against a fixed **1280×720** canvas that scales to fit any viewport, so a deck looks identical on a laptop, a projector, and a phone |
| Dark / light mode | Toggle button (top right) or press **T**; the choice persists in `localStorage` under `workshop-deck-theme`. Light mode reverses the slate scale and keeps the accent color |
| Fullscreen | Toggle button (top right) or press **F** |
| Keyboard nav | **← → ↑ ↓ Space PageUp PageDown** |
| Touch | Horizontal swipe on phones and tablets |
| Print / PDF | An `@media print` block lays the deck out one slide per page at 16:9 |

Because slides are a fixed 720 px tall and clipped (not scrollable), **content that overruns is silently cut off**. Keep slides sparse; split rather than shrink.

## Exporting to PDF

Two routes — mention the second when the user wants a file to send round:

1. **Cmd-P / Ctrl-P** in the browser. Zero dependencies, uses the template's `@media print` rules. Fine for a quick copy.
2. **The `slides-to-pdf` skill** (in this same plugin). One command, one page per slide at 960 × 540 pt, `--theme light` support, and it injects its own print CSS rather than trusting the template's, so it also works on decks with no print block. It warns if the page count does not match the slide count. Needs a local headless Chromium; the skill says how to get one.

Neither route detects a slide whose content overran the 720 px stage — the overflow is silently cropped in the browser and in the PDF alike. Keep slides sparse instead of relying on a warning.

## When the detail doesn't fit on a slide

That is the normal case, not a failure — and it is what the **`workshop-handbook`** skill (in this same plugin) is for: one long-form HTML page with a bookmarks sidebar, auto-numbered chapters, deep links and a print stylesheet. It shares this deck's design tokens and reads the same `~/.workshop-slides-preset.json`, so a deck and its handbook come out matching with no extra questions.

Reach for it when the user mentions handing something out, emailing notes, or people needing to follow the material on their own afterwards. Write the argument on the slides and the detail in the handbook — don't paraphrase one into the other.

## Step 1 — Gather content

Before generating, ensure you have:

| Field | Required | Notes |
|---|---|---|
| Workshop / presentation title | ✅ | e.g. "Intro to Docker" |
| Subtitle | Optional | e.g. "A hands-on session for backend devs" |
| Slide outline or content | Optional | If absent, generate a sensible default for the topic |
| Footer info for cover | Optional | e.g. "BigIn · 2026" |

If the user gave only a topic, generate a complete outline with 6–10 slides covering: cover → motivation/why → core concepts (2–3 slides) → hands-on/demo → wrap-up/next steps. Use section dividers to separate major acts.

## Step 1b — Branding

**Always** run this step before building any deck. Do not skip it.

### 1. Check for a saved preset

Try to read **`~/.workshop-slides-preset.json`**. This file is created when the user saves a custom preset.

### 2. Present options to the user

Use `AskUserQuestion` to present exactly **two** choices:

**If no saved preset exists:**

| Option | Label | Description |
|---|---|---|
| A | Use BigIn preset | Dark slate + orange accent, Google Sans throughout, Fira Code for code, BigIn watermark. Ready now. |
| B | Create my own preset | Define your brand colors, fonts, and logo — saved for all future decks. |

**If a saved preset exists** (read the `name` field from the JSON):

| Option | Label | Description |
|---|---|---|
| A | Use BigIn preset | Dark slate + orange accent, Google Sans throughout, Fira Code for code, BigIn watermark. |
| B | Use my "[name]" preset | Show the saved accent color and font names from the JSON file. |

Include a third option in the saved-preset case: **"Update my preset"** — re-collect all fields and overwrite the saved file.

### 3. Act on the choice

**BigIn preset** → proceed with template defaults, no CSS changes needed.

**Saved preset** → read values from `~/.workshop-slides-preset.json` and inject (see below).

**Create / Update preset** → collect these fields in order:

**Preset name** — free text (e.g. `My Company`, `ACME Corp`).

**Accent color** — present the full Tailwind accent palette via `AskUserQuestion`. Each option label is the color name; the description is the 500-shade hex. Group as a single-select:

| Label | Hex (500) |
|---|---|
| Red | `#ef4444` |
| Orange | `#f97316` |
| Amber | `#f59e0b` |
| Yellow | `#eab308` |
| Lime | `#84cc16` |
| Green | `#22c55e` |
| Emerald | `#10b981` |
| Teal | `#14b8a6` |
| Cyan | `#06b6d4` |
| Sky | `#0ea5e9` |
| Blue | `#3b82f6` |
| Indigo | `#6366f1` |
| Violet | `#8b5cf6` |
| Purple | `#a855f7` |
| Fuchsia | `#d946ef` |
| Pink | `#ec4899` |
| Rose | `#f43f5e` |

If the user selects "Other", ask them to type a hex code.

**Background color** — present the full Tailwind neutral palette via `AskUserQuestion`. Use the 950 shade (darkest) as the primary suggestion for each scale, with the 900 shade shown in the description:

| Label | 950 hex | 900 hex |
|---|---|---|
| Slate | `#020617` | `#0f172a` |
| Gray | `#030712` | `#111827` |
| Zinc | `#09090b` | `#18181b` |
| Neutral | `#0a0a0a` | `#171717` |
| Stone | `#0c0a09` | `#1c1917` |

Present each as: label = scale name + shade (e.g. "Slate 950"), description = hex value. If the user selects "Other", ask them to type a hex code.

**Heading font** — `Google Sans`, `Poppins`, `Plus Jakarta Sans` (or custom).

**Body font** — `DM Sans`, `Outfit`, `Nunito` (or custom).

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

If `$HOME` is not writable, the save silently buys nothing — the next session starts with no preset. Don't quietly drop the file beside the deck instead: pass the preset to `build.py` for this deck, and tell the user it could not be persisted and will need re-entering, or ask them where to keep the JSON.

### 4. Inject branding into the template

When applying any non-BigIn preset, update the template:

**CSS** — replace the `BRAND CONFIGURATION` block:
```css
:root {
  --brand-accent:    #6366f1;
  --brand-bg:        #0a0a0a;
  --brand-font-main: 'Google Sans', system-ui, sans-serif;
  --brand-font-body: 'DM Sans', sans-serif;
  --brand-font-code: 'Fira Code', monospace;
}
```

**Google Fonts `<link>`** — replace `href` with the `googleFontsUrl` from the preset.

**Watermark** — replace the `<svg>` inside `<div id="watermark">` with the `watermark` value from the preset. If `watermark` is empty, remove the `<div id="watermark">` entirely.

## Step 2 — Read the template and the reference deck

Read the template from **`assets/template.html`** (in the same directory as this SKILL.md).

**Also read `demo.html`** in that same directory. It is a complete 15-slide reference deck where every slide carries an HTML comment naming the components and layout it demonstrates:

```html
<!-- 04 · TWO COLUMNS · .col-label muted vs accent · .list · strong + em -->
```

Copy the closest pattern from `demo.html` and swap the content. Do not re-derive markup from scratch — the demo is the source of truth for how components compose, and it covers: cover, section dividers, 1/2/3-column bodies, bullet and numbered lists, prose, callouts (full and compact), code blocks (bash and yaml, two side by side), comparison tables, stat blocks, tag blocks, tags, inline-SVG diagrams, source citations, and spacers.

You will:
1. Keep the entire `<head>` (fonts, CSS variables, all style rules) **unchanged**
2. Keep `#bg`, `#watermark`, `#navigator`, `#themeToggle`, `#fullscreenToggle`, and the `<script>` block **unchanged** — the toggles and the scaling/swipe logic live there
3. Replace only the contents of `<div id="deck">` with the user's slides
4. Save the resulting file as `[kebab-case-title]-slides.html` — where the user asked, or the working directory if they didn't say

### Use `assets/build.py` — do not hand-assemble the file

Writing the whole deck out by hand makes rule 1 aspirational, and it **measurably fails**. A deck generated this way from an unmodified template had silently dropped all 18 `--dg-*` diagram tokens and the `.diagram` sizing rule: diagrams pasted from `soft-visuals` render with no fill and portrait diagrams overflow the slide, with no error to explain either.

So write **only the slides** to a fragment file, and let the script carry the other ~65 KB across as bytes:

```bash
python3 assets/build.py assets/template.html "$TMPDIR/slides-fragment.html" out/my-deck.html
```

`slides-fragment.html` holds just the `<section class="slide">` elements — no `<head>`, no `#deck` wrapper. Standard library only, so there is nothing to install.

**Write the fragment to a scratch path**, as above — `$TMPDIR`, not next to the deck. The fragment is scaffolding, not output, and the same goes for anything else generated on the way: page rasters, thumbnails, a preset written for this deck only. An observed run left `slides-fragment.html` and four `pgN.png` verification rasters sitting beside the deliverable. Delete scratch once the deck verifies; only the deck itself, and a PDF if one was asked for, are output.

For a non-BigIn preset, pass it in rather than editing the head yourself. The script substitutes the individual `--brand-*` declarations, the Google Fonts `href`, and the watermark block, leaving their explanatory comments intact:

```bash
python3 assets/build.py assets/template.html slides-fragment.html out/my-deck.html \
  --preset ~/.workshop-slides-preset.json --title "My Deck Title"
```

`"watermark": ""` in the preset removes the whole `#watermark` block, as specified above.

### Fonts: leave the CDN `<link>` alone

**The deck loads its fonts from the CDN.** That keeps the `.html` small and lets viewers hit Google's shared cache, and `build.py` has no font-embedding mode by design. `slides-to-pdf` doesn't embed either — it renders in a local browser where the CDN resolves, so whatever you see on screen is what lands in the PDF.

The one consequence worth knowing: on a machine that cannot reach `fonts.googleapis.com`, the deck falls back to `system-ui` on screen **and** in the PDF. Nothing is broken and the layout holds; only the typeface changes.

The script refuses to write on a structural error (no `active` slide, or more than one) and warns without blocking on: numbering that does not match slide position, hardcoded hex colors (which break light mode), a `<button>` in slide content (which `slides-to-pdf` cannot strip), a `.code-block` with no `.code-line` children (which collapses the snippet into one line), a preset watermark pointing at a remote URL or a local file path (either one renders as a broken-image box once the deck travels, offline or after the URL rots — prefer inline `<svg>` or a `data:` URI), **an `<svg>` whose shapes reach past its own `viewBox`** (that edge is simply never drawn — see below), and **an `<svg>` sized by `width`/`height` attributes wider than 536px without `class="diagram"`** (at that width it overflows its column and paints over the next one rather than being cropped; narrower ones cannot, so they are not flagged). It also verifies the carried-over head still contains the `--dg-*` tokens, `.diagram`, `@media print`, `scaleDeck`, `--deck-scale`, `ResizeObserver`, the three toggles, and the favicon.

### Size the `viewBox` from the shapes, not by eye

When you write or paste an `<svg>`, the `viewBox` must cover every shape in it. **Content outside the viewBox is not clipped with any signal — it is simply never drawn**, in the browser and in the exported PDF alike.

This shipped in a real deck: a seven-card layer stack whose last card ran to `y=308` inside `viewBox="0 0 460 306"`. That one card lost its bottom border and rounded corners while the six above it kept theirs, and nothing reported it — the slide did not overflow, the columns did not collide, the PDF had the right page count.

Add up the coordinates: the furthest shape edge, **plus half its stroke width** (a stroke straddles the edge it is drawn on, so a 1.75px-stroked card ending at `y=308` puts ink at `308.875`), plus a small margin. `build.py` now warns when it can prove an overflow from the attributes, and `slides-to-pdf` measures it exactly with `getBBox()` at export time — but the cheapest fix is getting it right when you write the shape.

**If you cannot run the script** (no shell access to this directory), assemble by hand — then verify the output before handing it over, because this is exactly where decks break:

```bash
# 18 token *definitions* — anchored, so `var(--dg-…)` usages don't inflate the count
grep -c -- '^[[:space:]]*--dg-' out/my-deck.html

# each of these must print "ok"
for p in '.diagram {' '@media print' 'scaleDeck' '--deck-scale' 'ResizeObserver' \
         'id="navigator"' 'id="themeToggle"' 'id="fullscreenToggle"' 'base64,'; do
  grep -q -- "$p" out/my-deck.html && echo "ok   $p" || echo "MISS $p"
done
```

Anything other than `18`, or any `MISS`, means the head was not carried across intact — re-copy it from the template rather than shipping the deck. These are presence checks on purpose: exact occurrence counts change whenever the template gains a line mentioning one of these, so they would rot into false alarms.

## Step 3 — Build slides

Patterns below are the quick reference; `demo.html` shows each one in a finished slide.

### Every slide — base structure

```html
<section class="slide">
  <div class="slide-header">
    <span class="slide-num">02</span>
    <h2 class="slide-title">Slide Title</h2>
    <p class="slide-subtitle">Optional subtitle — omit the whole line if not needed</p>
  </div>
  <div class="slide-body">
    <div class="col">
      <!-- content here -->
    </div>
  </div>
</section>
```

**Critical:** the very first slide must have `class="slide slide--cover active"`. All others use `class="slide"` (or `class="slide slide--section"` for dividers). Only one slide may carry `active`.

---

### Slide variants

#### Cover (first slide only)
```html
<section class="slide slide--cover active">
  <div class="slide-header">
    <span class="slide-num">Workshop Name or Category</span>
    <h1 class="slide-title">Main Title<br><span style="color:var(--brand-accent)">Key Word</span></h1>
    <p class="slide-subtitle">Subtitle or one-line description</p>
    <div class="cover-meta">BigIn · 2026</div>
  </div>
  <!-- No slide-body on cover slides -->
</section>
```

#### Section divider
```html
<section class="slide slide--section">
  <div class="slide-header">
    <span class="section-label">Act 2</span>
    <h2 class="slide-title">Section<br><span style="color:var(--brand-accent)">Title</span></h2>
    <p class="slide-subtitle">Optional tagline</p>
  </div>
  <!-- No slide-body on section dividers -->
</section>
```

---

### Body layouts

```html
<!-- 1 column (default) -->
<div class="slide-body">
  <div class="col">…</div>
</div>

<!-- 2 columns -->
<div class="slide-body cols-2">
  <div class="col">…</div>
  <div class="col">…</div>
</div>

<!-- 3 columns -->
<div class="slide-body cols-3">
  <div class="col">…</div>
  <div class="col">…</div>
  <div class="col">…</div>
</div>
```

---

### Content components

#### Bullet list
```html
<ul class="list">
  <li><strong>Bold label</strong> — supporting detail here</li>
  <li>Plain item without label</li>
</ul>
```

#### Numbered list
```html
<ul class="list numbered">
  <li>First step</li>
  <li>Second step</li>
</ul>
```

#### Body text
```html
<div class="text">
  <p>Paragraph with <strong>strong emphasis</strong> and <em>orange highlight</em>.</p>
  <p>Second paragraph if needed.</p>
</div>
```
(`<em>` renders in orange — use for key terms, not italics.)

#### Callout / pull quote
```html
<div class="callout">
  "Memorable insight or key principle goes here."
</div>

<!-- compact variant — smaller type, use when pairing with other content in a column -->
<div class="callout compact">"Shorter aside that shouldn't dominate the slide."</div>
```

#### Code block
Wrap **every line in its own `.code-line`**. The block is not a `<pre>`, so raw source newlines collapse into spaces and the whole snippet reflows into a paragraph. Use `.code-line blank` for a vertical gap.

```html
<div class="code-block">
  <div class="code-lang">python</div>
  <div class="code-line"><span class="cmt"># comment</span></div>
  <div class="code-line"><span class="kw">def</span> <span class="fn">greet</span>(name):</div>
  <div class="code-line">    <span class="kw">return</span> <span class="str">f"Hello, {name}"</span></div>
  <div class="code-line blank"></div>
  <div class="code-line"><span class="fn">greet</span>(<span class="str">"world"</span>)</div>
</div>
```
Syntax classes: `.kw` (keyword, orange), `.fn` (function name, light), `.str` (string, muted), `.cmt` (comment, dim). Only wrap tokens you want highlighted — plain text renders in default slate-200. Lines that overflow are clipped with an ellipsis rather than wrapping, so keep them under ~52 characters.

#### Comparison table
For criterion-by-criterion comparisons. Column 2 is styled as the recommended option (accent header), column 3 as the alternative (muted) — put the option you're advocating in the middle column.

```html
<table class="cmp-table">
  <colgroup><col class="c-crit"><col class="c-cell"><col class="c-cell"></colgroup>
  <thead>
    <tr><th>Criteria</th><th>Recommended</th><th>Alternative</th></tr>
  </thead>
  <tbody>
    <tr>
      <td class="cmp-crit">Deploy</td>
      <td>One manifest, reviewed in a PR</td>
      <td>SSH plus a runbook</td>
    </tr>
  </tbody>
</table>
```
Keep to **5–6 rows** and short cells; the table does not scroll and longer content will be clipped.

#### Diagram — inline SVG, soft flat style
For architecture and flow diagrams. Inline SVG keeps the deck self-contained (no image files to ship alongside it) and theme-aware. See slide 09 of `demo.html` for the full worked example.

For anything bigger than one small diagram — a full flowchart, a wireframe, a mindmap — use the **`soft-visuals`** skill instead and paste its `<svg>` in here. It shares this exact token set and ships a gallery of 18 shapes, 6 connector styles, 22 wireframe components and 5 device frames.

The style comes from the `--dg-*` tokens in the template:

| Token | Use |
|---|---|
| `--dg-blue` / `--dg-blue-fill` | Card border / translucent fill. Also `violet`, `mint`, `amber` |
| `--dg-accent-fill` | Fill paired with `var(--brand-accent)` — use for the *one* node you're highlighting |
| `--dg-text` / `--dg-muted` | Card title / caption |
| `--dg-line` | Connectors and arrowheads |

```html
<svg class="diagram" viewBox="0 0 460 300" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="Describe the diagram for screen readers">
  <defs>
    <marker id="dgArrow" viewBox="0 0 10 10" refX="7" refY="5"
            markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 1 L8 5 L0 9 z" fill="var(--dg-line)"/>
    </marker>
  </defs>

  <!-- Connectors first, so cards paint over the line ends.
       Q curves make the rounded elbow: run, Q corner, turn, Q corner, run -->
  <g fill="none" stroke="var(--dg-line)" stroke-width="1.75"
     stroke-linecap="round" stroke-linejoin="round" marker-end="url(#dgArrow)">
    <path d="M230 68 V112"/>
    <path d="M230 176 V194 Q230 206 218 206 H79 Q67 206 67 218 V240"/>
  </g>

  <!-- Card = body, then title + caption. No shadow — the style is flat. -->
  <rect x="150" y="10" width="160" height="52" rx="12"
        fill="var(--dg-blue-fill)" stroke="var(--dg-blue)" stroke-width="1.75"/>
  <text x="230" y="33" text-anchor="middle" font-size="15" font-weight="600"
        fill="var(--dg-text)">Ingress</text>
  <text x="230" y="50" text-anchor="middle" font-size="11"
        fill="var(--dg-muted)">TLS · routes by host</text>
</svg>
```

Rules:

- **The style is flat — no shadows at all.** Never `filter:` or `feDropShadow`: a filtered region forces Chrome's print-to-PDF to rasterise that area into a bitmap, so the slide stops being pure vector. Don't fake one with an offset rect either — it peeks out from under the shape's own border in light mode and reads as a misaligned fill. On a dark background a blurred shadow is invisible anyway, so nothing is lost.
- **Use the translucent `*-fill` tokens, not solid colors.** A 16% wash reads as a muted tint on the dark page and a pastel on the light one, so one value covers both themes.
- Give the diagram **one** accent-colored node; everything else takes a supporting hue. More than one focal point and the emphasis is gone.
- `var()` works in SVG presentation attributes (`fill`, `stroke`, `font-family`, even `rx`). The only caveat: presentation attributes have the lowest priority, so any CSS rule overrides them.
- Keep the `role="img"` and a real `aria-label` describing the diagram.

#### Stats block (use inside `cols-2` or `cols-3`)
```html
<div class="stat-block">
  <div class="stat-number">10×</div>
  <div class="stat-label">faster prototyping</div>
</div>
```

#### Column label
```html
<div class="col-label">Orange heading</div>
<div class="col-label muted">Grey heading</div>
```
Use the muted variant for the "before / old / traditional" side in comparisons; orange for the "after / new / recommended" side.

#### Tags / chips
```html
<div class="tags">
  <span class="tag">~45 min</span>
  <span class="tag accent">Hands-on</span>
</div>
```

#### Tag blocks — stacked value + label chips
A middle ground between a `.tag` and a full `.stat-block`: good for a row of metadata (licence, date, price, count). Wrap them in `.tags` to get the flex row and wrapping.

```html
<div class="tags">
  <div class="tag-block accent">
    <div class="tag-main">6 min</div>
    <div class="tag-sub">median deploy</div>
  </div>
  <div class="tag-block">
    <div class="tag-main">MIT</div>
    <div class="tag-sub">open source</div>
  </div>
</div>
```
Both `.tag-main` and `.tag-sub` are `white-space: nowrap` — keep them to one or two words.

#### Source citation inside a list item
```html
<li>Claim that needs attribution <span class="src">— Source, 2026</span></li>
```

#### Spacer — pushes subsequent content to the bottom of a column
```html
<div class="spacer"></div>
```

---

## Design tips

- Highlight 1–2 key words per title with `<span style="color:var(--brand-accent)">` for visual punch.
- Use section dividers to create breathing room before major topic shifts.
- Stats slides shine with exactly 3 columns and short, punchy numbers. `.stat-block` fills its column and centres vertically, so a row mixing stat blocks with an ordinary column (labels, tags) reads as misaligned — the stats sit mid-slide while the other column starts at the top. Either make every column a stat block, or add a `.spacer` to the odd one out.
- Comparison slides: two columns with muted col-label left / orange right for a short before-after, or `.cmp-table` when you have 4+ criteria to line up.
- End with a closing slide: section divider or cover variant with a call-to-action.
- Aim for 6–12 slides total. More than 15 is usually too many for a workshop.
- Both light and dark are first-class — avoid hardcoded hex colors in slide markup. Use `var(--brand-accent)` and the `--slate-*` scale so the deck stays legible when the user presses **T**.

## Pre-save checklist

- [ ] First slide has `active` class; no other slide does
- [ ] Slide numbers are two-digit and sequential: `01`, `02`, `03` …
- [ ] No demo content from the template remains
- [ ] Every code line is wrapped in its own `.code-line` (otherwise the snippet reflows into one paragraph)
- [ ] No hardcoded colors in slide markup — only `var(--brand-accent)` / `--slate-*`
- [ ] `<head>`, watermark, toggles, navigator, and `<script>` are byte-for-byte identical to the template
- [ ] File saved with a descriptive kebab-case name, and no build scratch left beside it
