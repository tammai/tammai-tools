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
| Navigation | Keyboard (← → Space) + bottom-right click navigator |
| Layouts | 1, 2, and 3-column body |
| Content types | Bullet lists, numbered lists, callouts, code blocks, stat blocks, tags |
| Slide variants | Cover, content, section-divider |
| Transitions | Smooth fade + slide |
| Branding | Fully themeable via CSS variables; presets saved to `~/.workshop-slides-preset.json` |

**Default brand:** dark slate (`#020617`) + orange accent (`#f97316`), Google Sans / Space Grotesk / JetBrains Mono, BigIn watermark.

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
    demo.html                       — live demo of all slide components
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
