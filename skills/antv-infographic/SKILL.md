---
name: antv-infographic
description: Use when creating infographics from content (信息图).
---

# AntV Infographic

Render high-quality infographics from a simple DSL. Backed by the open-source [AntV Infographic](https://github.com/antvis/infographic) engine (~54 built-in templates, MIT). Output is self-contained HTML that renders SVG in the browser; users can export SVG with a button.

## When to use

- User asks for an infographic (信息图) from text content: timelines, steps, comparisons, SWOT, org charts, stats, wordclouds.
- User needs a reusable template library for infographics.

## Template library (full list, grouped)

| Category | Templates |
|---|---|
| list (并列要点) | list-row-horizontal-icon-arrow, list-column-done-list, list-column-simple-vertical-arrow, list-column-vertical-icon-arrow, list-grid-badge-card, list-grid-candy-card-lite, list-grid-ribbon-card, list-sector-plain-text, list-waterfall-badge-card, list-waterfall-compact-card, list-zigzag-down-compact-card, list-zigzag-down-simple, list-zigzag-up-compact-card, list-zigzag-up-simple |
| sequence (步骤/阶段) | sequence-ascending-stairs-3d-underline-text, sequence-ascending-steps, sequence-circular-simple, sequence-color-snake-steps-horizontal-icon-line, sequence-cylinders-3d-simple, sequence-filter-mesh-simple, sequence-funnel-simple, sequence-horizontal-zigzag-underline-text, sequence-mountain-underline-text, sequence-pyramid-simple, sequence-roadmap-vertical-plain-text, sequence-roadmap-vertical-simple, sequence-snake-steps-compact-card, sequence-snake-steps-simple, sequence-snake-steps-underline-text, sequence-stairs-front-compact-card, sequence-stairs-front-pill-badge, sequence-timeline-rounded-rect-node, sequence-timeline-simple, sequence-zigzag-pucks-3d-simple, sequence-zigzag-steps-underline-text |
| sequence-interaction (泳道交互) | sequence-interaction-default-badge-card, sequence-interaction-default-animated-badge-card, sequence-interaction-default-compact-card, sequence-interaction-default-capsule-item, sequence-interaction-default-rounded-rect-node |
| compare (对比) | compare-binary-horizontal-badge-card-arrow, compare-binary-horizontal-simple-fold, compare-binary-horizontal-underline-text-vs, compare-hierarchy-left-right-circle-node-pill-badge, compare-quadrant-quarter-circular, compare-quadrant-quarter-simple-card, compare-swot |
| hierarchy (层级树) | hierarchy-mindmap-branch-gradient-capsule-item, hierarchy-mindmap-level-gradient-compact-card, hierarchy-structure, hierarchy-tree-curved-line-rounded-rect-node, hierarchy-tree-tech-style-badge-card, hierarchy-tree-tech-style-capsule-item |
| chart (图表) | chart-bar-plain-text, chart-column-simple, chart-line-plain-text, chart-pie-compact-card, chart-pie-donut-pill-badge, chart-pie-donut-plain-text, chart-pie-plain-text, chart-wordcloud |
| relation (关系流) | relation-dagre-flow-tb-animated-badge-card, relation-dagre-flow-tb-animated-simple-circle-node, relation-dagre-flow-tb-badge-card, relation-dagre-flow-tb-simple-circle-node |

## Template selection

- Strict order / steps / phases → `sequence-*`
- Multi-role or multi-system interaction → `sequence-interaction-*` (swimlanes)
- Parallel bullet points → `list-row-*` / `list-column-*` / `list-grid-*`
- Two-sided comparison / before-after → `compare-binary-*`
- SWOT → `compare-swot`
- Quadrant analysis → `compare-quadrant-*`
- Tree structure → `hierarchy-tree-*`; mindmap → `hierarchy-mindmap-*`
- Trend / single series → `chart-line-plain-text`; bar compare → `chart-bar-plain-text` / `chart-column-simple`; pie/donut → `chart-pie-*`; word frequency → `chart-wordcloud`
- Node relations / flow dependencies → `relation-*`

## DSL syntax rules (hard requirements)

- Line 1 MUST be `infographic <template-name>`.
- Blocks `data` / `theme`, 2-space indentation.
- `key value` pairs; object arrays use `- ` prefix.
- Main data field per template:
  - `list-*` → `lists`
  - `sequence-*` → `sequences` (optional `order asc|desc`)
  - `sequence-interaction-*` → `sequences` (swimlanes, each with `label`, `children` nodes with `label`, optional `id`/`icon`/`step`/`desc`/`value`; same `step` = same height) + `relations` (`nodeA - 关系名 -> nodeB`)
  - `compare-binary-*` / `compare-hierarchy-left-right-*` → `compares` with EXACTLY TWO root nodes, each with `children`
  - `compare-swot` → `compares` multiple roots, optional `children`
  - `compare-quadrant-*` → `compares` exactly 4 quadrant roots
  - `hierarchy-structure` → `items`; other `hierarchy-*` → single `root` with recursive `children`
  - `relation-*` → `nodes` + `relations`
  - `chart-*` → single ordered `values` (`label` = category, `value` = number)
  - fallback: `items`
- Give EVERY main data item a semantic `icon` keyword (e.g. `rocket launch`, `shield check`, `chart line`, `users`) unless pure numeric chart points or user explicitly wants minimal text. Never omit icons on list/sequence/node/compare items.
- `value` = pure number; units go in `label` or `desc`.
- `palette` = bare hex colors separated by spaces, NO quotes/commas, e.g. `palette #3b82f6 #8b5cf6 #f97316`.
- DEFAULT font is **Google Sans** — always append `theme.base.text.font-family Google Sans` to the DSL AND include the Google Fonts `<link>` in the HTML head (see HTML template). Other fonts via `theme.base.text.font-family`; `theme.stylize` for `rough` (hand-drawn), `pattern`, `linear-gradient`/`radial-gradient`.
- Keep output language = user's language (never auto-translate).

## Workflow

1. Parse user content into structure: title, desc, main data field, icons, palette.
2. Pick template from the list above.
3. Write DSL following the syntax rules.
4. Generate HTML (see template below), save as `<title>-infographic.html` in `~/infographic-demo/` (or user-specified dir). Fill the template placeholders:
   - `{title}` — infographic title (goes in `<title>` tag AND the `<h1>` header)
   - `{desc}` — one-line description for the `.lede` under the title (can be the DSL's `desc` value, or a short sentence)
   - `{syntax}` — the DSL
   - `{slug}` — kebab-case filename stem
5. Verify: run SSR check (see below) or open in browser. Then `open <file>` for the user.
6. Tell the user: file path, that the bottom-right download button exports the infographic as SVG, and that template/palette/content can be changed on request.

## HTML template (self-contained, CDN)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Infographic</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  /* ---------- Page shell (matches soft-visuals) ---------- */
  html, body { margin: 0; min-height: 100%; }
  body {
    min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
    padding: 56px 40px 72px; gap: 34px;
    background: var(--page-bg); color: var(--page-text);
    font-family: 'Google Sans', -apple-system, 'Segoe UI', sans-serif;
    -webkit-font-smoothing: antialiased;
    transition: background 0.25s ease, color 0.25s ease;
  }

  /* ---------- Header — title + desc, same structure as soft-visuals ---------- */
  #head { width: 100%; max-width: 1160px; flex-shrink: 0; }
  .kicker {
    display: block; font-size: 10px; font-weight: 600;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: #f97316; margin-bottom: 10px;
  }
  h1 {
    font-size: 2.1rem; font-weight: 700; line-height: 1.15;
    letter-spacing: -0.02em; color: var(--page-text);
    text-wrap: balance; margin: 0;
  }
  .lede {
    margin-top: 9px; font-size: 1rem; color: var(--page-muted);
    line-height: 1.55; max-width: 68ch; text-wrap: pretty;
  }
  #head::after {
    content: ''; display: block; width: 40px; height: 3px;
    border-radius: 2px; background: #f97316; margin-top: 18px;
  }

  /* ---------- Theme variables — dark mode restyles buttons & page ---------- */
  :root {
    --page-bg: #fafafa; --page-text: #18181b; --page-muted: #71717a;
    --btn-bg: #fff; --btn-border: #d4d4d8; --btn-text: #52525b;
    --btn-hover-bg: #f4f4f5; --btn-hover-text: #18181b; --btn-hover-border: #a1a1aa;
  }
  :root.dark {
    --page-bg: #1f1f1f; --page-text: #e4e4e7; --page-muted: #a1a1aa;
    --btn-bg: #27272a; --btn-border: #3f3f46; --btn-text: #a1a1aa;
    --btn-hover-bg: #3f3f46; --btn-hover-text: #e4e4e7; --btn-hover-border: #52525b;
  }

  /* ---------- Buttons — mirrored offsets: export bottom-right, toggle top-right ---------- */
  #toolbar { position: fixed; bottom: 24px; right: 32px; z-index: 10; }
  #toolbar button {
    height: 38px; padding: 0 12px;
    border: 1px solid var(--btn-border); background: var(--btn-bg); color: var(--btn-text);
    border-radius: 8px; cursor: pointer;
    display: inline-flex; align-items: center; gap: 7px;
    font-family: inherit; font-size: 12px; font-weight: 500; letter-spacing: 0.02em;
    box-shadow: 0 1px 2px rgba(0,0,0,.06);
    transition: background 0.15s, color 0.15s, border-color 0.15s;
  }
  #toolbar button:hover {
    background: var(--btn-hover-bg); color: var(--btn-hover-text); border-color: var(--btn-hover-border);
  }
  #toolbar svg { width: 16px; height: 16px; }

  #themeToggle {
    position: fixed; top: 24px; right: 32px; z-index: 10;
    width: 38px; height: 38px;
    border: 1px solid var(--btn-border); background: var(--btn-bg); color: var(--btn-text);
    border-radius: 8px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 2px rgba(0,0,0,.06);
    transition: background 0.15s, color 0.15s, border-color 0.15s;
  }
  #themeToggle:hover {
    background: var(--btn-hover-bg); color: #f97316; border-color: #f97316;
  }
  #themeToggle svg { width: 18px; height: 18px; }
  #themeToggle .icon-moon { display: none; }
  :root.dark #themeToggle .icon-sun { display: none; }
  :root.dark #themeToggle .icon-moon { display: flex; }
  #container { width: 100%; max-width: 1160px; flex: 1; }
</style>
</head>
<body>
<!-- Header — title + desc, same structure as soft-visuals -->
<header id="head">
  <span class="kicker">Infographic</span>
  <h1>{title}</h1>
  <p class="lede">{desc}</p>
</header>

<div id="toolbar">
  <button onclick="exportSvg()" title="Export SVG" aria-label="Export SVG">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
    <span>SVG Export</span>
  </button>
</div>
<button id="themeToggle" title="Toggle dark/light mode" aria-label="Toggle dark/light mode">
  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
  </svg>
  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"/>
  </svg>
</button>
<div id="container"></div>
<script src="https://unpkg.com/@antv/infographic@latest/dist/infographic.min.js"></script>
<script>
  const syntax = `{syntax}`;
  const infographic = new AntVInfographic.Infographic({
    container: '#container',
    width: '100%',
    height: '100%',
  });
  infographic.render(syntax);
  document.fonts?.ready.then(() => infographic.render(syntax)).catch(e => console.error(e));

  /* ================================================================
     DARK / LIGHT TOGGLE — re-renders with theme.type dark|light,
     restyles page & buttons via body.dark (CSS variables), remembers
     the choice, swaps the icon.
  ================================================================ */
  const themeToggle = document.getElementById('themeToggle');
  const root = document.documentElement;

  function setTheme(theme) {
    const isDark = theme === 'dark';
    root.classList.toggle('dark', isDark);           // CSS variables switch
    themeToggle.classList.toggle('dark', isDark);    // icon swap
    localStorage.setItem('infographic-theme', theme);
    applyTheme(theme);                               // re-render infographic
  }

  function applyTheme(theme) {
    let next;
    // 1. existing `type dark|light` line inside the theme block — swap it
    if (/^[ \t]*type\s+\w+[ \t]*$/m.test(syntax)) {
      next = syntax.replace(/^([ \t]*)type\s+\w+[ \t]*$/m, '$1type ' + theme);
    } else if (/^\s*theme\s*$/m.test(syntax)) {
      // 2. bare `theme` line — give it a type
      next = syntax.replace(/^\s*theme\s*$/m, 'theme\n  type ' + theme);
    } else if (/^\s*theme\n/m.test(syntax)) {
      // 3. theme block without a type — add as first key
      next = syntax.replace(/^\s*theme\n/, 'theme\n  type ' + theme + '\n');
    } else {
      // 4. no theme block — append one
      next = syntax + '\ntheme\n  type ' + theme;
    }
    try {
      infographic.render(next);
      document.fonts?.ready.then(() => infographic.render(next)).catch(() => {});
    } catch (e) { console.error('render failed:', e); }
  }

  if (themeToggle) {
    const saved = localStorage.getItem('infographic-theme');
    if (saved === 'dark') {
      root.classList.add('dark');
      themeToggle.classList.add('dark');
      applyTheme('dark');
    }
    themeToggle.addEventListener('click', () => {
      const isDark = !root.classList.contains('dark');
      setTheme(isDark ? 'dark' : 'light');
    });
  }

  // Sans-serif fallback so exported SVG text never renders as serif
  // when opened standalone without Google Sans available. AntV puts
  // text in <foreignObject> divs + a font-family on the root <svg>, so
  // every occurrence of "Google Sans" must gain a fallback chain.
  const FONT_CSS_URL = 'https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap';
  const FONT_FALLBACK = "'Google Sans', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif";
  let fontCss = '';

  async function ensureFonts() {
    if (fontCss !== '' || !navigator.onLine) return;
    try {
      const r = await fetch(FONT_CSS_URL, { mode: 'cors' });
      if (r.ok) fontCss = await r.text();
    } catch (e) { fontCss = ''; }
  }

  function applyFontFallback(svgEl) {
    const re = /font-family\s*:\s*["']?Google Sans["']?/gi;
    // 1. inline style attributes (foreignObject divs, etc.)
    svgEl.querySelectorAll('*').forEach(node => {
      const st = node.getAttribute('style');
      if (st && st.includes('font-family')) {
        node.setAttribute('style', st.replace(re, 'font-family: ' + FONT_FALLBACK));
      }
    });
    // 2. font-family presentation attributes on any element
    svgEl.querySelectorAll('*').forEach(node => {
      const ff = node.getAttribute('font-family');
      if (ff && ff.includes('Google Sans')) node.setAttribute('font-family', FONT_FALLBACK);
    });
    // 3. the root <svg> itself
    if (svgEl.getAttribute('font-family') && svgEl.getAttribute('font-family').includes('Google Sans')) {
      svgEl.setAttribute('font-family', FONT_FALLBACK);
    }
    // 4. bare <text>/<tspan> with no font-family at all
    svgEl.querySelectorAll('text, tspan').forEach(node => {
      if (!node.getAttribute('font-family')) node.setAttribute('font-family', FONT_FALLBACK);
    });
  }

  async function exportSvg() {
    try {
      await ensureFonts();
      let svgDataUrl = await infographic.toDataURL({ type: 'svg' });
      try {
        // Decode the data URL (base64 or percent-encoded)
        let svgText;
        if (svgDataUrl.includes('base64,')) {
          svgText = atob(svgDataUrl.split('base64,')[1]);
        } else {
          svgText = decodeURIComponent(svgDataUrl.split(',')[1]);
        }
        const doc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
        applyFontFallback(doc.documentElement);
        if (fontCss) {
          const style = doc.createElementNS('http://www.w3.org/2000/svg', 'style');
          style.textContent = fontCss;
          doc.documentElement.insertBefore(style, doc.documentElement.firstChild);
        }
        const xml = new XMLSerializer().serializeToString(doc);
        svgDataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
      } catch (e) {
        console.error('SVG post-process failed, exporting raw:', e);
      }
      const a = document.createElement('a');
      a.href = svgDataUrl;
      a.download = '{slug}-infographic.svg';
      a.click();
    } catch (e) {
      alert('Export failed: ' + e.message);
    }
  }
</script>
</body>
</html>
```

## Verify with SSR (no browser needed)

```bash
mkdir -p /tmp/info-test && cd /tmp/info-test
npm init -y >/dev/null && npm install @antv/infographic >/dev/null
node -e "
const { renderToString } = require('@antv/infographic/ssr');
(async () => {
  const svg = await renderToString(process.argv[1]);
  console.log(svg.includes('<svg') ? 'OK len=' + svg.length : 'EMPTY');
})().catch(e => console.log('FAIL', e.message));
" "$(cat syntax.txt)"
```

- `renderToString` returns a PROMISE (awaits fonts).
- Every template renders to a full `<svg>` document; any FAIL means the DSL is wrong — fix syntax before shipping.

## Pitfalls

- `renderToString` is async — must await.
- `compare-binary-*` REQUIRES exactly 2 root nodes in `compares`, each with `children` (even 1 item per side).
- `sequence-interaction-*` children nodes must be object entries with `label`; use `step` for time levels.
- Icons: semantic keyword phrases with spaces (`rocket launch`), NOT hyphens. Exact icon IDs also work (e.g. `mingcute/server-line`).
- Local npm SSR test can't load webfonts — "Font family not registered, using fallback" warnings are expected; the browser still renders the real Google Sans via the `<link>`.
- Unpkg `@latest` resolves to the latest version (currently 0.2.19); pin exact version if reproducibility matters.
- Local npm SSR test needs network for fonts; offline it may still render (fonts fall back).

## References

- Repo: https://github.com/antvis/infographic (clone depth 1; `skills/infographic-creator/SKILL.md` is the canonical spec, Chinese)
- Docs: https://infographic.antv.vision (learn/syntax, gallery of templates)
