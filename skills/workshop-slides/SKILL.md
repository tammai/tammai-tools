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
| A | Use BigIn preset | Dark slate + orange accent, Google Sans / Space Grotesk, BigIn watermark. Ready now. |
| B | Create my own preset | Define your brand colors, fonts, and logo — saved for all future decks. |

**If a saved preset exists** (read the `name` field from the JSON):

| Option | Label | Description |
|---|---|---|
| A | Use BigIn preset | Dark slate + orange accent, Google Sans / Space Grotesk, BigIn watermark. |
| B | Use my "[name]" preset | Show the saved accent color and font names from the JSON file. |

Include a third option in the saved-preset case: **"Update my preset"** — re-collect all fields and overwrite the saved file.

### 3. Act on the choice

**BigIn preset** → proceed with template defaults, no CSS changes needed.

**Saved preset** → read values from `~/.workshop-slides-preset.json` and inject (see below).

**Create / Update preset** → collect these fields:

| Field | Example |
|---|---|
| Preset name | `My Company`, `ACME Corp` |
| Accent color | `#6366f1` (indigo), `#10b981` (emerald), `#e11d48` (rose) |
| Background color | `#0a0a0a`, `#1a1a2e`, `#0f0f23` |
| Heading font | `Inter`, `Poppins`, `Plus Jakarta Sans` |
| Body font | `DM Sans`, `Outfit`, `Nunito` |
| Code font | `Fira Code`, `Source Code Pro`, `Cascadia Code` |
| Logo | URL to SVG/PNG, or "none" |

After collecting, **save** to `~/.workshop-slides-preset.json`:

```json
{
  "name": "My Company",
  "accent": "#6366f1",
  "background": "#0a0a0a",
  "fontMain": "Inter",
  "fontBody": "DM Sans",
  "fontCode": "Fira Code",
  "googleFontsUrl": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=DM+Sans:wght@400;500;600&family=Fira+Code:wght@400;500&display=swap",
  "watermark": "<img src='https://example.com/logo.svg' alt='My Company'>"
}
```

Set `"watermark": ""` if the user chose no logo.

### 4. Inject branding into the template

When applying any non-BigIn preset, update the template:

**CSS** — replace the `BRAND CONFIGURATION` block:
```css
:root {
  --brand-accent:    #6366f1;
  --brand-bg:        #0a0a0a;
  --brand-font-main: 'Inter', system-ui, sans-serif;
  --brand-font-body: 'DM Sans', sans-serif;
  --brand-font-code: 'Fira Code', monospace;
}
```

**Google Fonts `<link>`** — replace `href` with the `googleFontsUrl` from the preset.

**Watermark** — replace the `<svg>` inside `<div id="watermark">` with the `watermark` value from the preset. If `watermark` is empty, remove the `<div id="watermark">` entirely.

## Step 2 — Read the template

Read the template from **`assets/template.html`** (in the same directory as this SKILL.md).

You will:
1. Keep the entire `<head>` (fonts, CSS variables, all style rules) **unchanged**
2. Keep the `#bg` background div, `#watermark`, `#navigator`, and `<script>` block **unchanged**
3. Replace only the contents of `<div id="deck">` with the user's slides
4. Save the resulting file to the outputs folder as `[kebab-case-title]-slides.html`

## Step 3 — Build slides

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
```

#### Code block
```html
<div class="code-block">
  <div class="code-lang">python</div>
  <span class="cmt"># comment</span>
  <span class="kw">def</span> <span class="fn">greet</span>(name):
      <span class="kw">return</span> <span class="str">f"Hello, {name}"</span>
</div>
```
Syntax classes: `.kw` (keyword, orange), `.fn` (function name, light), `.str` (string, muted), `.cmt` (comment, dim). Only wrap tokens you want highlighted — plain text renders in default slate-200.

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

#### Spacer — pushes subsequent content to the bottom of a column
```html
<div class="spacer"></div>
```

---

## Design tips

- Highlight 1–2 key words per title with `<span style="color:var(--brand-accent)">` for visual punch.
- Use section dividers to create breathing room before major topic shifts.
- Stats slides shine with exactly 3 columns and short, punchy numbers.
- Comparison slides (before/after): muted col-label left, orange col-label right.
- End with a closing slide: section divider or cover variant with a call-to-action.
- Aim for 6–12 slides total. More than 15 is usually too many for a workshop.

## Pre-save checklist

- [ ] First slide has `active` class; no other slide does
- [ ] Slide numbers are two-digit and sequential: `01`, `02`, `03` …
- [ ] No demo content from the template remains
- [ ] `<head>`, watermark, navigator, and `<script>` are byte-for-byte identical to the template
- [ ] File is saved to the outputs folder with a descriptive kebab-case name
