from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def export_cassette(run_data: dict[str, Any], output_path: Path) -> Path:
    """Export a run to a .cassette zip file."""
    output_path = output_path.with_suffix(".cassette")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({
            "version": "0.1",
            "exported_at": datetime.now(UTC).isoformat(),
            "run_id": run_data.get("run_id", ""),
            "template": run_data.get("template", ""),
        }, indent=2))
        zf.writestr("run.json", json.dumps(run_data, indent=2, default=str))
    return output_path


def import_cassette(cassette_path: Path) -> dict[str, Any]:
    """Import a .cassette zip file and return run data."""
    with zipfile.ZipFile(cassette_path, "r") as zf:
        if "run.json" in zf.namelist():
            return json.loads(zf.read("run.json"))
        raise ValueError("Invalid cassette: missing run.json")


def load_cassette_dir(cassette_dir: Path) -> list[dict[str, Any]]:
    """Load all sample cassettes from a directory."""
    results = []
    for path in sorted(cassette_dir.glob("*.cassette")):
        try:
            results.append(import_cassette(path))
        except (zipfile.BadZipFile, ValueError):
            continue
    return results
