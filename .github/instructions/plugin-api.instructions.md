---
description: "az-scout plugin protocol, discovery, manager. USE WHEN editing the core plugin contract — plugin_api.py, plugins.py, plugin_manager/, or related docs."
applyTo: "src/az_scout/plugin_api.py,src/az_scout/plugins.py,src/az_scout/plugin_manager/**,docs/plugin-scaffold/**"
---

# Plugin API (core side)

Audience: **core maintainers** changing the plugin contract.
For plugin authors implementing a plugin, see `plugin-author.instructions.md`.

## Compatibility

- `PLUGIN_API_VERSION` lives in `azure_api/__init__.py`. **Bump it** for any breaking change to the protocol, dataclasses, or shared helpers.
- The plugin manager guard refuses to load plugins declaring an incompatible major version — keep the guard in sync.
- Document every bump in `CHANGELOG.md` under `### Changed` with a migration note.


## Plugin protocol

```python
from az_scout.plugin_api import AzScoutPlugin, TabDefinition, ChatMode, NavbarAction

class MyPlugin:
    name = "my-plugin"       # unique identifier
    version = "0.1.0"

    def get_router(self) -> APIRouter | None: ...
    def get_mcp_tools(self) -> list[Callable] | None: ...
    def get_static_dir(self) -> Path | None: ...
    def get_tabs(self) -> list[TabDefinition] | None: ...
    def get_chat_modes(self) -> list[ChatMode] | None: ...
    def get_navbar_actions(self) -> list[NavbarAction] | None: ...
```

All methods optional — return `None` to skip.

## Conventions

- **Package layout:** src-layout (`src/az_scout_myplugin/`) with hatchling
- **Naming:** Package `az-scout-plugin-{name}`, module `az_scout_{name}`
- **Entry point:** `[project.entry-points."az_scout.plugins"]`
- **Lazy imports:** Inside methods to avoid circular imports at discovery time
- **Static dir:** `Path(__file__).parent / "static"` at module level

## AI completion helpers

```python
from az_scout.plugin_api import is_ai_enabled, plugin_ai_complete

if is_ai_enabled():
    result = await plugin_ai_complete(
        "Analyse this data...",
        system_prompt="You are an expert.",
        region="eastus",
        cache_ttl=600,  # 10 min cache, 0 to bypass
    )
    # result = {"content": "...", "tool_calls": [...]}
```

JS: `if (aiEnabled) { const r = await aiComplete("...", {cacheTtl: 600}); }`

## Isolation rules

- Fully self-contained — no global state mutation
- No circular imports — use lazy imports
- No heavy imports at module import time
- Respect core authentication and context model
- Never override built-in routes

## Content-Security-Policy & plugin assets

The core serves a strict `'self'`-only CSP (`script-src`/`style-src`/`font-src`/`connect-src` in
`app.py:_CSP_POLICY`) and ships zero external CDN at runtime. Plugin static dirs are mounted
**same-origin** (`/plugins/{name}/static`, `/internal/{name}/static`), so plugin-vendored assets
are allowed automatically — **but any plugin that links an external CDN is blocked by the CSP.**

- When changing `_CSP_POLICY`, keep it `'self'`-only. Do **not** re-add CDN hosts to accommodate a
  plugin; the convention is that plugins **vendor** their extra third-party assets into their own
  package (see `plugin-author.instructions.md` → *Third-party / vendored assets*).
- If a genuine cross-origin need arises (e.g. an image host), scope it as narrowly as possible and
  document it in `CHANGELOG.md`.
- The core already vendors Bootstrap (+ Icons), D3, marked, highlight.js and simple-datatables;
  plugins should reuse these rather than re-vendor.

## Testing

- Use `pytest` + `httpx` with `TestClient`
- Mock `discover_plugins()` to inject test plugin instances
- Mock Azure API calls — never require live Azure in tests
