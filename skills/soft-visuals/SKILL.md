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

## Ten visual types

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
| **Infographic** | Data storytelling, stats, steps, comparisons, SWOT | Rendered with the **AntV Infographic** engine — see the Infographic section below |

If the request spans two (e.g. "show the architecture and the deploy flow"), produce
**one file with two `.figure` blocks** rather than two files.

## Step 1 — Decide the type and gather content

| Field | Required | Notes |
|---|---|---|
| Visual type | Yes | Infer it; only ask if genuinely ambiguous |
| Title | Yes | Goes in the header |
| Nodes / screens / branches / rows | Yes | If the user gave prose, extract the entities yourself |
| The one thing to emphasise | Optional | Becomes the single accent-coloured element |

If the user gave only a topic, build something sensible and complete rather than asking a
list of questions. Prefer **5–9 nodes**; past that a diagram stops explaining and starts
documenting.

## Infographic (AntV engine) — different workflow

When the visual is an **infographic** (data storytelling: stats, steps, comparisons, SWOT,
quadrants, org trees, charts, wordclouds), do **NOT** hand-draw SVG. Use the AntV
Infographic engine instead — it ships ~54 polished templates and renders them from a tiny
DSL to SVG in the browser:

1. Load the **`antv-infographic`** skill (`skill_view(name='antv-infographic')`) — it holds
   the full template list, DSL syntax rules, HTML shell with Google Sans + Export SVG
   button, and the SSR verification script.
2. Pick the template category by content:
   - Steps / phases / roadmap → `sequence-*` (timeline, funnel, pyramid, snake, 3D stairs)
   - Multi-role interaction → `sequence-interaction-*` (swimlanes + relations)
   - Parallel points → `list-row-*` / `list-column-*` / `list-grid-*` / `list-waterfall-*`
   - Two-sided comparison → `compare-binary-*`; SWOT → `compare-swot`; quadrants → `compare-quadrant-*`
   - Tree / org → `hierarchy-tree-*`; brainstorm → `hierarchy-mindmap-*`
   - Trend line → `chart-line-plain-text`; bars → `chart-bar-plain-text` / `chart-column-simple`; share → `chart-pie-*`; words → `chart-wordcloud`
   - Node relations → `relation-*`
3. Write the DSL (first line `infographic <template-name>`, then `data` + `theme` blocks),
   always adding icons to main items and `theme.base.text.font-family Google Sans`.
4. Generate the HTML, verify via SSR (`renderToString` from `@antv/infographic/ssr`),
   save to `~/infographic-demo/` and `open` it.
5. Theming: keep the `--dg-*` pastel palette by passing the hex values into the DSL
   `palette` (bare hexes, space-separated) — e.g. `palette #a5b4fc #a7f3d0 #fcd34d` for the
   soft look.

Same deliverable contract as the rest of this skill: one self-contained HTML file the user
opens in a browser, content in the user's language, editable on request.

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

`class="figure narrow"` caps at 400px (phone and watch frames), `medium` at 760px. A plain `.figure` is 1160px.

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

<!-- rounded elbow: run, Q corner, turn, Q corner, run (corner radius 12–16) -->
<path d="M230 176 V194 Q230 206 218 206 H79 Q67 206 67 218 V240" fill="none"
      stroke="var(--dg-line)" stroke-width="1.75" stroke-linecap="round"
      stroke-linejoin="round" marker-end="url(#aFlow)"/>
```

- **Dashed** (`stroke-dasharray="7 6"`) = async, optional, or planned.
- **Curved** (`C`) = mindmap branches and soft flows.
- **Labelled** = a chip filled with `var(--brand-bg)` sitting on the line.
- **Annotation leader** = dashed, thin, **no arrowhead**.
- **Org chart edges** = no arrowheads at all.

### 22 wireframe components

`button` · `button, outline` · `text input` · `textarea` · `dropdown` · `checkbox` ·
`radio button` · `toggle` · `slider` · `progress bar` · `tabs` · `tabs, vertical` ·
`tabs, mobile` · `tooltip` · `overlay` (dimmed screen + modal) · `stars` · `tag` ·
`video` · `map` · `image` · `avatar` · `text, block`

**5 frames:** `plain` · `window` (desktop browser) · `phone` · `tablet` · `watch`

All of them are in the gallery.

### Layout rules

**Draw connectors first, shapes second.** Shapes then paint over the line ends.

**Stop every connector 6px short of the target's edge**, so the arrowhead sits in the gap
instead of crossing the border.

**Start every connector at its source's edge too.** A line that begins in the gap beside
its source belongs to nothing.

**Keep labels off other geometry.** Move labels clear or start connectors below them.

Per type:
- **Flowchart** — one dominant axis (usually top-down). Branch sideways at the `diamond` only.
- **Architecture** — layer it: clients on top, then edge, then services, then data.
- **Wireframe** — **drop the hues.** `--dg-surface` / `--dg-border` greys with a single accent.
- **Mindmap** — accent centre. Each branch owns one hue.
- **Org chart** — **no arrowheads**. One hue per level, accent on the root.
- **Sequence diagram** — participant headers in a row, dashed lifelines down. Requests solid, returns dashed and mint.
- **Timeline / Gantt** — column grid is the time axis. One hue per workstream.
- **Kanban** — `--dg-surface` columns, cards on `--brand-bg`. Hue lives in the tags.
- **User journey map** — stages are columns, lenses are rows. Use mood faces in the *Feeling* row.

## Step 4 — Save and verify

Save as `[kebab-case-title]-visual.html`.

Then check:
1. **Nothing outside the viewBox.** Content past `viewBox` width/height is simply invisible.
2. **Marker ids unique per document.** Two `<svg>` blocks must not both define `id="aFlow"`. Suffix them.
3. **Export SVG buttons appear automatically.** `assets/template.html` attaches an
   **Export SVG** button (top-right of each `.figure`) via JS — no per-figure markup needed.
   The export resolves `var(--dg-*)` to computed colours and inlines the Google Fonts
   `@font-face`, so the downloaded `.svg` keeps the pastel look standalone. Filename derives
   from the `.figure-label` (or `visual`). The button is hidden in print. No action needed
   from you beyond using `assets/template.html` as the shell.

## Reusing a visual in a slide deck

The `--dg-*` tokens are defined **identically** in `workshop-slides`, so an `<svg>` lifts straight into a slide:

```html
<div class="slide-body cols-2">
  <div class="col"><svg class="diagram" viewBox="…">…</svg></div>
  <div class="col">…</div>
</div>
```

Add `class="diagram"` for the deck's sizing.

## Hard rules

- **No shadows. No `filter:`, no `feDropShadow`.** The style is flat.
- **One stroke width (`1.75`) and one corner radius (`12`)** across every shape.
- **Translucent `*-fill` tokens, never solid colours.**
- **At most one accent element per visual.** Two focal points means none.
- **Hue carries meaning.** Same hue = same kind of thing.
- `var()` works in SVG presentation attributes.
- Keep `role="img"` and a real `aria-label` — a sentence, not "diagram".
