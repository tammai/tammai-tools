# tammai-tools

A **Claude Code plugin** by Tam Mai — workshop and presentation utilities built on the BigIn design system.

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

**Default brand:** dark slate (`#020617`) + orange accent (`#f97316`), Google Sans for headings and body, Fira Code for code only, BigIn watermark.

### `workshop-handbook`

Generates a complete, self-contained HTML handbook — the long-form, read-alone companion to a `workshop-slides` deck.

**Trigger phrases**

- "Write a handbook for this Docker workshop"
- "Make a participant guide for the onboarding session"
- "I need something people can read afterwards, not just slides"

**Output** — a single `.html` file: one scrolling document, a sidebar of bookmarks, no server, no dependencies.

**Handbook features**

| Feature | Detail |
|---|---|
| Bookmarks sidebar | Built at load from the headings — one flat list, no numbers, chapters and sections told apart by weight alone |
| Scrollspy + deep links | The bookmark for the section being read highlights itself; every heading gets a `#` anchor |
| Floating controls | Icon-only theme toggle, fixed top-right at every width; a drawer trigger, fixed top-left, appears only below 1080px — nothing lives in a header bar |
| Content types | Prose, lists (bullet / numbered / checklist), definition lists, four callout types, pull quotes, real `<pre>` code blocks with copy buttons, tabs, three table variants, card grids, step-by-step procedures, inline-SVG figures |
| Icons | Every control is genuine [Lucide](https://lucide.dev) markup — no icon font, no CDN |
| Branding | Shares `~/.workshop-slides-preset.json` with `workshop-slides` — configure once, both skills match |
| PDF | Cmd-P gives a contents page, then one chapter per page, forced to a light palette |

**Default brand:** same as `workshop-slides`.

### `slides-to-pdf`

Exports a generated HTML deck to a single multi-page PDF — one page per slide.

**Trigger phrases**

- "Convert my slides to PDF"
- "Export the deck as a PDF"
- "I need a PDF version to email the team"

| Property | Value |
|---|---|
| Page size | 1280 × 720 px → 960 × 540 pt → 13.333 × 7.5 in |
| Aspect ratio | 16:9 — same as PowerPoint / Keynote widescreen |
| Resolution | Resolution-independent — vector text (selectable & searchable), vector gradients, images at native resolution |
| Fidelity | Backgrounds, gradients, accent colors, webfonts and inline SVG preserved as-is |

**Requires** a local headless Chromium — `npx puppeteer browsers install chrome-headless-shell`. Nothing else: the exporter is Python standard library only.

Because the deck stacks every slide at `inset: 0` and reveals only the `.active` one, a plain `chromium --print-to-pdf` produces a single-page PDF. The exporter injects a print stylesheet into a copy of the deck, which returns every slide to the flow at 1280×720 with a page break after each — so one browser run produces the whole deck, with no per-slide loop and no merge step.

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

### `antv-infographic`

Renders data-storytelling infographics — stats, steps, comparisons, SWOT, quadrants, org trees, charts, wordclouds — through the open-source [AntV Infographic](https://github.com/antvis) engine (~54 templates) rather than hand-drawn SVG.

**Trigger phrases**

- "Make an infographic of these Q3 numbers"
- "Turn this into a SWOT graphic"
- "Chart the funnel as an infographic"

**Output** — a single `.html` file with a dark/light toggle and an SVG export button.

| Property | Detail |
|---|---|
| Engine | AntV Infographic, MIT-licensed, driven by a compact DSL |
| Theming | Dark/light re-renders the canvas from the DSL rather than restyling it |
| SVG export | Post-processed to a full sans-serif fallback chain, so a standalone file survives a failed webfont |
| Shell | Same header and button vocabulary as `soft-visuals` |

`soft-visuals` delegates here automatically when a request is data storytelling rather than a diagram.

### `doc-quality`

Enforces quality on any markdown, English or Vietnamese, in four passes: drafting rules, a deterministic lint, a measured compression, and an LLM-judge rubric. Two modes — `doc` and `social` — each with its own rubric and Vale config.

**Trigger phrases**

- "Lint this README"
- "Tighten this guide, it reads like AI slop"
- "Clean up this LinkedIn post before I publish"

**Output** — the edited document, plus one line of judge scores.

| Pass | Detail |
|---|---|
| 0 — Drafting rules | Applied while writing, not after: one idea in one place, no preamble, no summary that repeats the body, length budgets. Three rules invert in `social` mode |
| 1 — Lint (hard gate) | [Vale](https://vale.sh) with two bundled styles — `TamMai` (English slop words, filler phrases, substitutions, emoji) and `TamMaiVI` (Vietnamese fillers, marketing intensifiers). Both run on every file; the patterns are language-disjoint, so no path scoping |
| 2 — Compression | The cut is sized by measurement, not a quota: score redundancy and density first, then cut only the spans those scores cited. A document scoring 5 is shipped unchanged |
| 3 — Judge (soft gate) | `doc` scores redundancy, coherence, density and tone; `social` scores hook, single idea, concreteness and voice against a platform character limit. Any dimension below 4 is rewritten and re-scored once |

`social` mode exists because the two rubrics disagree by design: `rubric.md` scores rhetorical questions and rule-of-three as tone=1 and the `doc` Vale config bans emoji at error level, so a post linted as a document fails the hard gate on devices that are legitimate there. Slop words stay banned in both.

**Requires** Vale on `PATH` — `brew install vale`. Without it, Pass 1 degrades to a manual checklist and says so. `assets/selftest.py` runs before Pass 1 and asserts every rule still fires against the two bundled fixtures, because a broken Vale config reports zero findings and looks exactly like a clean document.

## Repository structure

```
.claude-plugin/plugin.json          — plugin metadata (name, version)
.claude-plugin/marketplace.json     — plugin marketplace metadata (owner, source, license, keywords)
skills/
  workshop-slides/
    SKILL.md                        — skill instructions (Claude reads this at invocation)
    assets/
      template.html                 — base HTML template for generated decks
      build.py                      — assembler: template + slide fragment → deck
      favicon.ico                   — browser tab icon
    demo.html                       — 15-slide reference deck; every slide is
                                      labelled with the components it demonstrates
  workshop-handbook/
    SKILL.md                        — skill instructions
    assets/
      template.html                 — viewer shell (sidebar bookmarks + flowing document)
      build.py                      — assembler: template + content fragment → handbook
      favicon.ico                   — browser tab icon
    demo.html                       — 6-chapter reference handbook; every chapter is
                                      labelled with the components it demonstrates
  slides-to-pdf/
    SKILL.md                        — skill instructions
    assets/
      export.py                     — deck-to-PDF exporter (stdlib; one headless-Chromium run)
  soft-visuals/
    SKILL.md                        — skill instructions
    assets/
      template.html                 — viewer shell (tokens + dark/light toggle)
      gallery.html                  — reference: every shape, connector and layout
    demo.html                       — worked example: all nine visual types on one
                                      product, each captioned with its prompt
  antv-infographic/
    SKILL.md                        — skill instructions; the HTML shell lives inline
                                      in its template block, extracted at generation time
  doc-quality/
    SKILL.md                        — skill instructions (3-pass doc quality workflow)
    assets/
      vale/                         — .vale.ini, .vale-social.ini, TamMai + TamMaiVI styles
      rubric.md                     — the doc-mode LLM-judge rubric
      rubric-social.md              — the social-mode rubric + platform character limits
      fixture.md                    — bilingual fixture; every rule has a planted hit
      fixture-social.md             — social fixture; emoji off, every other rule armed
      selftest.py                   — asserts each rule fires (stdlib; needs vale on PATH)
```

Skills are discovered automatically from the `skills/` directory.

## Installation

Add this repository as a plugin marketplace in Claude Code, then install `tammai-tools` from it:

```bash
claude plugin marketplace add tammai/tammai-tools
claude plugin install tammai-tools
```

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`).
2. Add static assets under `skills/<skill-name>/assets/`.
3. Reference them by relative path from `SKILL.md` (e.g. `assets/template.html`).

See [CLAUDE.md](CLAUDE.md) for full development guidance.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
