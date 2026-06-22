# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] — 2026-06-22

### Added
- `.claude-plugin/marketplace.json` — Claude Cowork marketplace metadata: categories, tags, pricing, icon, license, repository, and homepage

### Changed
- Navigator layout changed from vertical (column, 80 px wide) to horizontal (row, 48 px tall, width auto)
- Navigator chevron icons updated from up/down to left/right to match horizontal orientation

## [0.1.0] — 2026-06-22

### Added
- `workshop-slides` skill — generates self-contained HTML slide decks from a topic or outline
- Base HTML template (`assets/template.html`) with BigIn design system defaults:
  - Dark slate background (`#020617`) + orange accent (`#f97316`)
  - Google Sans / Space Grotesk / JetBrains Mono via Google Fonts
  - Slide variants: cover, content, section-divider
  - Body layouts: 1, 2, and 3-column
  - Content components: bullet lists, numbered lists, callouts, code blocks, stat blocks, tags, spacer
  - Keyboard navigation (← → Space PageUp PageDown)
  - Horizontal bottom-right navigator with page indicator
  - BigIn watermark (swappable)
  - Ambient radial-gradient background decoration
- Custom branding presets saved to `~/.workshop-slides-preset.json`
- Demo deck (`demo.html`) showcasing all slide components and layouts
- Plugin metadata (`.claude-plugin/plugin.json`) — name `tammai-tools`, version `0.1.0`
