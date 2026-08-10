# Vendored third-party assets

az-scout ships **no external CDN at runtime** and enforces a strict `'self'`-only
Content-Security-Policy. Plugin static files are served **same-origin**, so anything committed in
this package is allowed — but linking to a CDN is **blocked by the CSP** and breaks offline /
air-gapped self-hosting.

## Do you actually need to vendor anything?

Reuse the core's already-vendored libraries first. These are loaded on the page or exposed as JS
globals, so you don't ship them yourself:

- **Bootstrap** + **Bootstrap Icons** (CSS classes such as `bi bi-puzzle`)
- **D3** (`d3` global)
- **marked** (`renderMarkdown(md)` global)
- **highlight.js**
- **simple-datatables**

Plus helpers: `apiFetch`, `apiPost`, `aiComplete`, `aiEnabled`, `escapeHtml`, `tenantQS`,
`subscriptions`, `regions`.

## Vendoring an extra library

If your plugin needs an *additional* third-party JS/CSS/font, drop the pinned file(s) in this
directory and reference them from your own static prefix:

```html
<!-- vendored, same-origin — allowed by the CSP -->
<link rel="stylesheet" href="/plugins/example/static/vendor/chart/chart.min.css">
<script src="/plugins/example/static/vendor/chart/chart.min.js"></script>

<!-- external CDN — blocked by the CSP, breaks air-gapped self-hosting; do NOT do this -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

If a CSS file references fonts by relative URL (e.g. `url("fonts/...")`), keep those fonts in a
sibling `fonts/` folder next to the CSS so the relative path resolves.

Your `static/` directory ships in the wheel automatically, so vendored files behave identically
across local dev, SaaS publishing, and customer self-hosting — no per-mode configuration.

## Keeping vendored files up to date (optional)

Mirror the core: add a small dependency-free (stdlib `urllib` only) `tools/vendor_assets.py`
script that pins versions and re-downloads into this folder on a bump. The committed files remain
the source of truth, so **no npm, bundler, or build step** is introduced.
