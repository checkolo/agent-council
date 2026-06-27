from __future__ import annotations

from pathlib import Path

# Ensure SPA mount works in CI/local pytest without a full UI build.
_web_dir = Path(__file__).resolve().parent.parent / "quorum" / "web"
_index = _web_dir / "index.html"
if not _index.exists():
    _web_dir.mkdir(parents=True, exist_ok=True)
    _index.write_text("<!doctype html><html><body>test</body></html>", encoding="utf-8")
