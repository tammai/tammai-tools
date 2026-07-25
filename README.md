# tammai-tools

A **Claude Cowork plugin** by Tam Mai — workshop and presentation utilities built on the BigIn design system.

## Skills

### `workshop-slides`

Generates a complete, self-contained HTML slide deck from a topic, outline, or detailed content brief.

**Trigger phrases**

- "Create slides for a Docker workshop"
- "Build a presentation about GraphQL for our backend team"
- "Make workshop slides for Intro to Figma — cover, components, variables, wrap-up"

**Output** — a single `.html` file you open directly in any browser. No server, no dependencies, no bundler.

**Slide features**

| Feature | Detail |
|---|---|
| Stage | Fixed 1280×720 (16:9) canvas that scales to any viewport — laptop, projector, or phone |
| Dark / light mode | Toggle button or press **T**; persisted in `localStorage` |
| Fullscreen | Toggle button or press **F** |
| Navigation | Keyboard (← → ↑ ↓ Space PageUp/Down), click navigator, and swipe on touch devices |
| Layouts | 1, 2, and 3-column body |
| Content types | Bullet lists, numbered lists, callouts (+ compact), code blocks, comparison tables, stat blocks, tag blocks, tags, inline-SVG diagrams |
| Slide variants | Cover, content, section-divider |
| Transitions | Smooth fade + slide |
| Branding | Fully themeable via CSS variables; presets saved to `~/.workshop-slides-preset.json` |
| PDF | `@media print` for Cmd-P, or the `slides-to-pdf` skill for a higher-fidelity export |

**Default brand:** dark slate (`#020617`) + orange accent (`#f97316`), Google Sans for headings and body, JetBrains Mono for code only, BigIn watermark.

### `slides-to-pdf`

Exports a generated HTML deck to a single multi-page PDF — one page per slide.

**Trigger phrases**

- "Convert my slides to PDF"
- "Export the deck as a PDF"
- "I need a PDF version to email the team"

**Output** — one PDF, one page per slide, with a bookmark per slide title.

| Property | Value |
|---|---|
| Page size | 1280 × 720 px → 960 × 540 pt → 13.333 × 7.5 in |
| Aspect ratio | 16:9 — same as PowerPoint / Keynote widescreen |
| Resolution | Resolution-independent — vector text (selectable & searchable), vector gradients, images at native resolution |
| Fidelity | Backgrounds, gradients, accent colors, and Google Fonts preserved as-is |

**Requires** `playwright` (+ Chromium) and `pypdf`. The skill checks for both and installs them if missing.

Because the deck stacks every slide at `inset: 0` and reveals only the `.active` one, a plain `chromium --print-to-pdf` produces a single-page PDF. The converter instead drives headless Chromium once per slide, then merges the results with pypdf.

### `soft-visuals`

Generates soft, flat, pastel visuals — the Whimsical-style look — as self-contained inline SVG.

**Trigger phrases**

- "Draw a diagram of our deploy flow"
- "Wireframe the settings screen"
- "Mindmap the Q3 roadmap"

**Output** — a single `.html` file with a dark/light toggle. No image files, no server.

| Type | Signature elements |
|---|---|
| Flowchart | `pill` start/end, `card` steps, `diamond` decisions with labelled edges |
| Architecture | dashed `group` boundaries, `cylinder` datastores, `cloud` third parties, `actor` users |
| Wireframe | device frame, placeholder bars, one accent action |
| Mindmap | accent centre, one hue per branch, curved stems, text-on-rule leaves |
| Org chart | rounded bus edges with no arrowheads, one hue per level |
| Sequence diagram | participant headers, dashed lifelines, activation bars, mint dashed returns |
| Timeline / Gantt | column time axis, bars sized in column units, `today` marker |
| Kanban board | surface columns, neutral cards, hue in the tags |
| User journey map | stage columns × lens rows, mood faces in the *Feeling* row |

**18 shapes**, **6 connector styles**, **22 wireframe components**, and **5 device frames**. `assets/gallery.html` renders every one of them as a copy-from reference — 14 figures, ~50 labelled swatches. `demo.html` is the worked example: all nine types describing one product, each captioned with the prompt that produced it.

The style is **flat — no shadows**: SVG filters force Chrome's print-to-PDF to rasterise, and faked offset shadows peek out under borders in light mode. Hue fills are translucent so one value works in both themes.

Because the `--dg-*` tokens are shared verbatim with `workshop-slides`, any generated `<svg>` pastes straight into a slide deck.

## Repository structure

```
.claude-plugin/plugin.json          — plugin metadata (name, version)
.claude-plugin/marketplace.json     — Claude Cowork marketplace config (categories, tags, pricing, icon)
skills/
  workshop-slides/
    SKILL.md                        — skill instructions (Claude reads this at invocation)
    assets/
      template.html                 — base HTML template for generated decks
      favicon.ico                   — browser tab icon
    demo.html                       — 15-slide reference deck; every slide is
                                      labelled with the components it demonstrates
  slides-to-pdf/
    SKILL.md                        — skill instructions
    assets/
      slides_to_pdf.py              — Playwright + pypdf deck-to-PDF converter
  soft-visuals/
    SKILL.md                        — skill instructions
    assets/
      template.html                 — viewer shell (tokens + dark/light toggle)
      gallery.html                  — reference: every shape, connector and layout
    demo.html                       — worked example: all nine visual types on one
                                      product, each captioned with its prompt
```

Skills are discovered automatically by Claude Cowork from the `skills/` directory. Each skill folder must contain a `SKILL.md` with YAML frontmatter (`name`, `description`, `triggers`).

## Installation

Open `tammai-tools.plugin` in Claude Cowork — a **Save plugin** button will appear. Click it to install.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with the required YAML frontmatter.
2. Add any static assets under `skills/<skill-name>/assets/`.
3. Reference assets by relative path from `SKILL.md` (e.g. `assets/template.html`).

See [CLAUDE.md](CLAUDE.md) for full development guidance.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
