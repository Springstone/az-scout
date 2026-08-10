#!/usr/bin/env python3
"""Download third-party frontend assets into ``static/vendor/``.

az-scout ships every CDN-hosted CSS/JS/font file inside its own bundle so that
the web UI works with **no external network dependency** — identically for local
development, SaaS publishing (the files ride along in the wheel), and customers
self-hosting in air-gapped environments.

The committed files under ``src/az_scout/static/vendor/`` are the source of
truth. This script only needs to run when a pinned version is bumped:

    uv run python tools/vendor_assets.py            # download all
    uv run python tools/vendor_assets.py --check    # verify nothing is missing

No build tooling is added to the normal dev/install/publish flows — this is a
one-off maintenance helper, kept dependency-free (stdlib only).
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

# Root of the vendored asset tree (served at ``/static/vendor/...``).
VENDOR_DIR = Path(__file__).resolve().parent.parent / "src" / "az_scout" / "static" / "vendor"

# Pinned versions — bump here, then re-run this script and commit the result.
BOOTSTRAP = "5.3.8"
BOOTSTRAP_ICONS = "1.11.3"
SIMPLE_DATATABLES = "9.0.3"
HIGHLIGHT_JS = "11.11.1"
MARKED = "15.0.12"
D3 = "7"

# Mapping of ``local path (relative to VENDOR_DIR)`` -> ``source URL``.
#
# Sources are the canonical, version-pinned project repos/registries:
#   * Bootstrap / Bootstrap Icons -> tagged ``dist``/``font`` on GitHub (twbs)
#   * highlight.js                -> the official ``highlightjs/cdn-release`` repo
#   * marked / simple-datatables  -> the npm package via unpkg
#   * d3                          -> d3js.org
#
# NOTE: bootstrap-icons.min.css references its font files via a relative
# ``./fonts/`` URL, so the woff/woff2 files MUST live in a ``fonts/``
# subdirectory next to the CSS. Both highlight.js themes (dark + light) are
# vendored because app.js swaps between them at runtime.
ASSETS: dict[str, str] = {
    # Bootstrap
    "bootstrap/bootstrap.min.css": (
        f"https://raw.githubusercontent.com/twbs/bootstrap/v{BOOTSTRAP}/dist/css/bootstrap.min.css"
    ),
    "bootstrap/bootstrap.bundle.min.js": (
        f"https://raw.githubusercontent.com/twbs/bootstrap/v{BOOTSTRAP}"
        "/dist/js/bootstrap.bundle.min.js"
    ),
    # Bootstrap Icons (CSS + font files)
    "bootstrap-icons/bootstrap-icons.min.css": (
        f"https://raw.githubusercontent.com/twbs/icons/v{BOOTSTRAP_ICONS}"
        "/font/bootstrap-icons.min.css"
    ),
    "bootstrap-icons/fonts/bootstrap-icons.woff2": (
        f"https://raw.githubusercontent.com/twbs/icons/v{BOOTSTRAP_ICONS}"
        "/font/fonts/bootstrap-icons.woff2"
    ),
    "bootstrap-icons/fonts/bootstrap-icons.woff": (
        f"https://raw.githubusercontent.com/twbs/icons/v{BOOTSTRAP_ICONS}"
        "/font/fonts/bootstrap-icons.woff"
    ),
    # simple-datatables
    "simple-datatables/style.css": (
        f"https://unpkg.com/simple-datatables@{SIMPLE_DATATABLES}/dist/style.css"
    ),
    "simple-datatables/simple-datatables.js": (
        f"https://unpkg.com/simple-datatables@{SIMPLE_DATATABLES}/dist/umd/simple-datatables.js"
    ),
    # highlight.js (core + json language + both themes)
    "highlight/highlight.min.js": (
        f"https://raw.githubusercontent.com/highlightjs/cdn-release/{HIGHLIGHT_JS}"
        "/build/highlight.min.js"
    ),
    "highlight/languages/json.min.js": (
        f"https://raw.githubusercontent.com/highlightjs/cdn-release/{HIGHLIGHT_JS}"
        "/build/languages/json.min.js"
    ),
    "highlight/styles/atom-one-dark.min.css": (
        f"https://raw.githubusercontent.com/highlightjs/cdn-release/{HIGHLIGHT_JS}"
        "/build/styles/atom-one-dark.min.css"
    ),
    "highlight/styles/atom-one-light.min.css": (
        f"https://raw.githubusercontent.com/highlightjs/cdn-release/{HIGHLIGHT_JS}"
        "/build/styles/atom-one-light.min.css"
    ),
    # marked
    "marked/marked.min.js": f"https://unpkg.com/marked@{MARKED}/marked.min.js",
    # d3
    "d3/d3.v7.min.js": f"https://d3js.org/d3.v{D3}.min.js",
}


def _download(url: str, dest: Path) -> int:
    """Download ``url`` to ``dest``, returning the number of bytes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "az-scout-vendor-sync"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - trusted pinned CDN URLs
        data: bytes = resp.read()
    dest.write_bytes(data)
    return len(data)


def check() -> int:
    """Return the number of expected vendored files that are missing."""
    missing = [rel for rel in ASSETS if not (VENDOR_DIR / rel).is_file()]
    for rel in missing:
        print(f"MISSING: {rel}", file=sys.stderr)
    if missing:
        print(f"\n{len(missing)} vendored asset(s) missing. Run: python tools/vendor_assets.py")
    else:
        print(f"All {len(ASSETS)} vendored assets present.")
    return len(missing)


def sync() -> int:
    """Download every asset. Return 0 on success, 1 if any download failed."""
    failures = 0
    for rel, url in ASSETS.items():
        dest = VENDOR_DIR / rel
        try:
            size = _download(url, dest)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"FAIL  {rel}\n      {url}\n      {exc}", file=sys.stderr)
            failures += 1
            continue
        print(f"OK    {rel}  ({size:,} bytes)")
    if failures:
        print(f"\n{failures} download(s) failed.", file=sys.stderr)
    else:
        print(f"\nDownloaded {len(ASSETS)} assets into {VENDOR_DIR}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify that all vendored files exist (no download).",
    )
    args = parser.parse_args()
    if args.check:
        return 1 if check() else 0
    return sync()


if __name__ == "__main__":
    raise SystemExit(main())
