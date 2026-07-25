---
name: soft-visuals
description: >
  Generates soft, flat, pastel visuals — the Whimsical-style look — as self-contained
  inline SVG: flowcharts, architecture diagrams, wireframes (desktop and mobile), mindmaps,
  org charts, sequence diagrams, Gantt timelines, kanban boards, and user journey maps.
  Rounded cards with translucent hue fills, one even stroke weight, rounded elbow
  connectors, no shadows. Output is a single .html file with a built-in dark/light toggle,
  and every <svg> can be pasted straight into a workshop-slides deck. Use this skill
  whenever the user wants to draw, diagram, map, mock up, chart, or visualise something.
  Triggers on phrases like "draw a diagram", "diagram this", "make a flowchart", "chart
  this flow", "architecture diagram", "system diagram", "visualise this", "wireframe
  this", "mock up a screen", "UI mockup", "mindmap", "mind map this", "org chart", "team
  structure", "sequence diagram", "show the request flow", "timeline", "gantt chart",
  "roadmap view", "kanban board", "user journey map", "whimsical style diagram", "sketch
  the flow". Also trigger proactively when a user is explaining a system, flow, hierarchy,
  schedule, or screen layout and a picture would carry it better than prose. Do NOT use
  for data charts — bar/line/pie charts of a dataset are a charting job, not this skill.
---

# Soft Visuals

Generates diagrams, wireframes, and board layouts as inline SVG in a soft, flat, pastel
style. Output is a single self-contained `.html` file the user opens in any browser —
dark/light toggle built in, no server, no image files.

## Nine visual types

| Type | Use for | Signature elements |
|---|---|---|
| **Flowchart** | Processes, decisions, CI pipelines | `pill` start/end, `card` steps, `diamond` decisions with labelled edges |
| **Architecture** | Systems, services, data flow | `group` boundaries, `cylinder` datastores, `cloud` third parties, `actor` users |
| **Wireframe** | Screen layouts, UI structure | Device frame, placeholder bars, one accent action |
| **Mindmap** | Hierarchies, brainstorms, topic breakdowns | Accent centre, hue-per-branch, curved stems, text-on-rule leaves |
| **Org chart** | Team structure, reporting lines, sitemaps | Rounded bus edges with **no arrowheads**, one hue per level |
| **Sequence diagram** | Request flows, protocols, service interactions | Participant headers, dashed lifelines, activation bars, mint dashed returns |
| **Timeline / Gantt** | Schedules, roadmaps, phased plans | Column time axis, bars sized in column units, `today` marker |
| **Kanban board** | Work state, sprint boards, pipelines | `--dg-surface` columns, neutral cards on `--brand-bg`, hue in the tags |
| **User journey map** | Experience across stages, research synthesis | Stage columns × lens rows, mood faces in the *Feeling* row |

If the request spans two (e.g. "show the architecture and the deploy flow"), produce
**one file with two `.figure` blocks** rather than two files.

## Step 1 — Decide the type and gather content

| Field | Required | Notes |
|---|---|---|
| Visual type | ✅ | Infer it; only ask if genuinely ambiguous |
| Title | ✅ | Goes in the header |
| Nodes / screens / branches / rows | ✅ | If the user gave prose, extract the entities yourself |
| The one thing to emphasise | Optional | Becomes the single accent-coloured element |

If the user gave only a topic, build something sensible and complete rather than asking a
list of questions. Prefer **5–9 nodes**; past that a diagram stops explaining and starts
documenting.

## Step 2 — Read the template and the gallery

1. Read **`assets/template.html`** — the viewer shell. Keep `<head>`, the token block,
   `#themeToggle`, and the `<script>` **unchanged**. Replace the `<header id="head">`
   text and the contents of `<main id="canvas">`.
2. Read **`assets/gallery.html`** — the reference. It renders **every** shape, connector,
   component, and layout this skill supports, each with a caption naming it.

**Copy the closest pattern from `gallery.html` and change the coordinates and labels. Do
not author SVG from scratch** — the fiddly paths (cylinder, cloud, note fold, doc wave,
bracket, tooltip tail, org-chart bus, mood faces) are already correct there.

## Step 3 — Build

### Structure

```html
<div class="figure">
  <div class="figure-label">Optional small label</div>
  <svg viewBox="0 0 720 420" xmlns="http://www.w3.org/2000/svg"
       role="img" aria-label="A real sentence describing the visual">
    <defs>
      <marker id="aFlow" viewBox="0 0 10 10" refX="7" refY="5"
              markerWidth="5" markerHeight="5" orient="auto-start-reverse">
        <path d="M0 1 L8 5 L0 9 z" fill="var(--dg-line)"/>
      </marker>
    </defs>
    <!-- connectors first, then shapes on top -->
  </svg>
  <p class="figure-note">Optional caption under the visual.</p>
</div>
```

`class="figure narrow"` caps a visual at 400px (phone and watch frames), `medium` at
760px. A plain `.figure` is 1160px.

### Tokens

Never hardcode a colour. Every value comes from a token — that is what makes the visual
work in both themes and match the deck.

| Token | Use |
|---|---|
| `--dg-blue` `--dg-violet` `--dg-mint` `--dg-amber` `--dg-rose` `--dg-cyan` | Shape border / stroke |
| `--dg-<hue>-fill` | Matching translucent fill |
| `--brand-accent` + `--dg-accent-fill` | The **one** emphasised element |
| `--dg-surface` / `--dg-border` | Neutral shape, wireframe chrome, board columns |
| `--dg-text` / `--dg-muted` | Shape title / caption and placeholder bars |
| `--dg-line` | Connectors and arrow markers |

### 18 shapes

| Shape | Meaning |
|---|---|
| `card` (rounded rect) | Step, service, component — the default |
| `pill` (`rx = h/2`) | Start / end terminator |
| `diamond` | Decision — always label the outgoing edges |
| `cylinder` | Datastore, queue, bucket |
| `hexagon` | Preparation or config step |
| `parallelogram` / `parallelogram, flipped` | Input / output — pair them |
| `trapezoid` | Manual operation |
| `triangle` | Warning, or a hierarchy apex |
| `circle` | Step number or junction |
| `doc` | Document or generated artifact |
| `note` | Sticky annotation (folded corner) — sits *near* something |
| `annotation` | Callout with a pointer tail — points *at* something |
| `bracket` | Curly brace annotating a span of rows |
| `actor` | A person or external role |
| `sequence actor` | Participant header over a dashed lifeline |
| `cloud` | External or third-party system |
| `group` (dashed) | Trust or network boundary |

### Connectors

```html
<!-- straight -->
<path d="M115 62 V84" fill="none" stroke="var(--dg-line)" stroke-width="1.75"
      stroke-linecap="round" marker-end="url(#aFlow)"/>

<!-- rounded elbow: run, Q corner, turn, Q corner, run (corner radius 12) -->
<path d="M230 176 V194 Q230 206 218 206 H79 Q67 206 67 218 V240" fill="none"
      stroke="var(--dg-line)" stroke-width="1.75" stroke-linecap="round"
      stroke-linejoin="round" marker-end="url(#aFlow)"/>
```

- **Dashed** (`stroke-dasharray="7 6"`) = async, optional, or planned.
- **Curved** (`C`) = mindmap branches and soft flows.
- **Labelled** = a chip filled with `var(--brand-bg)` sitting on the line. Any label that
  crosses another line or lifeline **needs** that chip, or the line reads through the text.
- **Annotation leader** = dashed, thin, **no arrowhead**. An arrow means flow; a note is
  not a step.
- **Org chart edges** = no arrowheads at all.

### 22 wireframe components

`button` · `button, outline` · `text input` · `textarea` · `dropdown` · `checkbox` ·
`radio button` · `toggle` · `slider` · `progress bar` · `tabs` · `tabs, vertical` ·
`tabs, mobile` · `tooltip` · `overlay` (dimmed screen + modal) · `stars` · `tag` ·
`video` · `map` · `image` · `avatar` · `text, block`

**5 frames:** `plain` · `window` (desktop browser) · `phone` · `tablet` · `watch`

All of them are in the gallery's *Wireframe components* and *Wireframe frames* grids.

### Layout rules

**Draw connectors first, shapes second.** Shapes then paint over the line ends and any
tiny overshoot is hidden.

**Stop every connector 6px short of the target's edge**, so the arrowhead sits in the gap
instead of crossing the border. Derive the number from the shape's real geometry — a card
at `y=90 height=64` has edges at 90 and 154, so an arrow into its top ends at `84` and one
leaving its bottom starts at `154`. Getting this wrong puts arrowheads *inside* shapes,
which is the most common way these look sloppy. Watch the shapes whose edge is not their
bounding box: a `cylinder` drawn from `y=309` with `ry=9` has its visible top at **300**, so
an arrow into it ends at `294`.

**Start every connector at its source's edge too.** A line that begins in the gap beside
its source belongs to nothing — the reader cannot tell what it leaves. An arrow out of the
right side of a card at `x=200 width=200` starts at `400`, not wherever the label happens
to sit.

**Keep labels off other geometry.** A bar label that a `today` marker crosses, or a shape
label that its own outgoing connector runs through, reads as a rendering bug. Either move
the label clear or start the connector below it.

Per type:

- **Flowchart** — one dominant axis (usually top-down). Branch sideways at the `diamond`
  only. Failure paths take `--dg-rose`; the happy path stays neutral.
- **Architecture** — layer it: clients on top, then edge, then services, then data. Dashed
  `group` around the trust boundary, `cloud` outside it, all datastores one shared hue. Give
  the `cloud` a hue of its own — sharing one with internal compute says the third party *is*
  your compute. Remember the `actor` label sits below the figure, so an arrow leaving an
  actor starts below that label, not at the shape.
- **Wireframe** — **drop the hues.** `--dg-surface` / `--dg-border` greys with a single
  accent for the primary action or active tab, never both. Copy stays as placeholder bars,
  never real sentences — real words make reviewers argue about the words.
- **Mindmap** — accent centre. Each branch owns one hue and its stems and leaf rules
  inherit it. Balance branches left and right. Leaves are text on a tinted rule, not
  boxes — boxing every leaf turns a mindmap into an org chart.
- **Org chart** — **no arrowheads**; reporting is a relationship, not a flow. One hue per
  level so depth reads at a glance, accent on the root. The bus is one path per parent: up
  from the leftmost child, `Q` corner, along, `Q` corner, down to the rightmost; middle
  children get their own short drop.
- **Sequence diagram** — participant headers in a row, dashed lifelines down. Requests
  solid and neutral, **returns dashed and mint**, so round trips read without following
  labels. Draw activation bars *before* the arrows so arrowheads land on top. Self-calls
  go out-down-back.
- **Timeline / Gantt** — a column grid is the time axis and every bar is positioned and
  sized in **column units** (`x = GX + cw * start`), never by eye. One hue per workstream;
  the only accent is the `today` marker.
- **Kanban** — `--dg-surface` columns, cards on `--brand-bg` so they read as lifted with
  no shadow. **Hue lives in the tags**, not the cards; four columns of coloured cards is
  noise. Leave 6px between a card's tag and its bottom border.
- **User journey map** — stages are columns, lenses are rows. Use **mood faces** in the
  *Feeling* row rather than words: the emotional dip is the point of the artifact and it
  should be visible without reading. Opportunities take a hue by sentiment — mint for a
  clear win, rose where the journey is losing people.

## Step 4 — Save and verify

Save to the outputs folder as `[kebab-case-title]-visual.html`.

Then check the two things that silently break a visual:

1. **Nothing outside the viewBox.** Content past `viewBox` width/height is simply
   invisible — no error, no warning. Add up your coordinates; the furthest shape edge plus
   a small margin is your viewBox size. Watch for labels and chips hanging below the last
   row.
2. **Marker ids unique per document.** Two `<svg>` blocks in one file must not both define
   `id="aFlow"`; duplicate ids are invalid and both references resolve to the first.
   Suffix them (`aFlow`, `aArch`, `aSeqRet`).

Paste this in DevTools to check both at once:

```js
document.querySelectorAll('svg').forEach((s, i) => {
  const vb = s.viewBox.baseVal, b = s.getBBox();
  if (vb.width && (b.x < -1 || b.y < -1 ||
      b.x + b.width > vb.width + 1 || b.y + b.height > vb.height + 1))
    console.warn('overflows viewBox', i, [b.x, b.y, b.width, b.height], [vb.width, vb.height]);
});
const seen = {};
document.querySelectorAll('[id]').forEach(e => seen[e.id] = (seen[e.id] || 0) + 1);
Object.entries(seen).filter(([, n]) => n > 1).forEach(d => console.warn('duplicate id', d));
```

## Reusing a visual in a slide deck

The `--dg-*` tokens are defined **identically** here and in
`workshop-slides/assets/template.html`, so an `<svg>` lifts straight into a slide:

```html
<div class="slide-body cols-2">
  <div class="col"><svg class="diagram" viewBox="…">…</svg></div>
  <div class="col">…</div>
</div>
```

Add `class="diagram"` for the deck's sizing. If you add a **new** token here, add it there
too — a token the deck doesn't define renders as no fill, silently.

## Hard rules

- **No shadows. No `filter:`, no `feDropShadow`.** Both measured: a filtered region forces
  Chrome's print-to-PDF to rasterise that area into a bitmap (so a deck exported to PDF
  stops being vector), and a faked offset-rect shadow peeks out from under the shape's own
  border in light mode and reads as a misaligned fill. The style is flat.
- **One stroke width (`1.75`) and one corner radius (`12`)** across every shape. That
  evenness is most of the look.
- **Translucent `*-fill` tokens, never solid colours.** A 16% wash reads as a muted tint
  on the dark page and a pastel on the light one, so one value covers both themes.
- **At most one accent element per visual.** Two focal points means none. Some types carry
  their whole meaning in hue and take **no** accent — a kanban board (hue is in the tags) and
  a user journey map (hue is sentiment). Don't bolt one on to satisfy the rule.
- **Hue carries meaning.** Same hue = same kind of thing, and the same thing keeps its hue
  across every figure in the file. Don't rotate hues for variety — and don't let two
  different kinds collide, e.g. internal workers and a third-party `cloud` sharing cyan.
- `var()` works in SVG presentation attributes (`fill`, `stroke`, `font-family`, `rx`).
  The only caveat: presentation attributes lose to any CSS rule, having lowest priority.
- Keep `role="img"` and a real `aria-label` — a sentence, not "diagram".

## Pre-save checklist

- [ ] Connectors drawn before shapes, each stopping ~6px short of the target edge
- [ ] No arrowhead landing inside a shape; org-chart edges have no arrowheads at all
- [ ] All content inside the `viewBox` (run the snippet above)
- [ ] Marker ids unique across the whole file
- [ ] No `filter`, no `feDropShadow`, no shadow rects
- [ ] Every colour a `--dg-*` / `--brand-accent` token, no hardcoded hex
- [ ] At most one accent element (none for kanban and journey maps)
- [ ] No two different kinds of thing sharing a hue; recurring things keep theirs
- [ ] Labels that cross a line or lifeline sit on a `--brand-bg` chip
- [ ] Checked in **both** themes (press **T**)
- [ ] Portrait visuals use `.figure.narrow`
- [ ] `role="img"` + a descriptive `aria-label` on every `<svg>`
