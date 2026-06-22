# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Cowork plugin** (`tammai-tools`) by Tam Mai — a collection of skills (slash commands) for workshop and presentation tooling, built on the BigIn design system. The plugin is distributed as a `.plugin` file (git-ignored) bundled from this directory.

There is no build system, package manager, or test suite. All assets are plain files consumed directly by Claude Code at runtime.

## Structure

```
.claude-plugin/plugin.json     — plugin metadata (name, version, description)
.claude-plugin/marketplace.json — Claude Cowork marketplace config (categories, tags, pricing, icon)
skills/
  workshop-slides/
    SKILL.md                   — the skill's instruction document (Claude reads this at invocation)
    assets/template.html       — the base HTML template for generated slide decks
```

Skills are discovered automatically by Claude Cowork from the `skills/` directory. Each skill folder must contain a `SKILL.md` with YAML frontmatter (`name`, `description`, `triggers`).

## workshop-slides skill

The skill generates self-contained HTML slide decks. Key design constraints:

- **Output is a single `.html` file** — no server, no JS bundler, no external runtime dependencies at view-time (fonts load from Google Fonts CDN when online).
- **Template is read at generation time** — the skill reads `assets/template.html`, replaces only the `<div id="deck">` contents, and saves the result. The `<head>`, `#bg`, `#watermark`, `#navigator`, and `<script>` blocks are preserved byte-for-byte.
- **Branding via CSS variables** — the `BRAND CONFIGURATION` `:root` block in the template controls accent color, background, and fonts. Custom presets are saved to `~/.workshop-slides-preset.json` and injected at generation time.
- **BigIn defaults**: dark slate (`#020617`) + orange accent (`#f97316`), Google Sans / Space Grotesk / JetBrains Mono.

### Slide HTML rules

- First slide: `class="slide slide--cover active"` — no `slide-body`
- Section dividers: `class="slide slide--section"` — no `slide-body`
- All other slides: `class="slide"`
- Slide numbers are zero-padded two digits: `01`, `02`, …
- Only one slide may carry the `active` class

### Syntax highlight classes (inside `.code-block`)

`.kw` = keyword (orange), `.fn` = function name (light), `.str` = string (muted), `.cmt` = comment (dim)

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with the required YAML frontmatter.
2. Add any static assets under `skills/<skill-name>/assets/`.
3. Reference assets by relative path from `SKILL.md` (e.g. `assets/template.html`).
