#!/usr/bin/env python3
"""Audit raster figure integrity, pixel size and declared DPI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

SUPPORTED = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def audit(path: Path, min_dpi: float, min_width: int, min_height: int) -> dict:
    result = {"path": str(path), "status": "PASS", "warnings": []}
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            dpi_value = image.info.get("dpi")
            dpi = min(dpi_value) if isinstance(dpi_value, tuple) else dpi_value
            result.update({"width": width, "height": height, "dpi": dpi})
            if width < min_width or height < min_height:
                result["warnings"].append(f"pixel dimensions below {min_width}x{min_height}")
            if dpi is None:
                result["warnings"].append("DPI metadata missing; verify effective DPI at insertion size")
            elif dpi + 0.5 < min_dpi:
                result["warnings"].append(f"declared DPI below {min_dpi:g}")
    except Exception as exc:
        result["status"] = "FAIL"
        result["error"] = str(exc)
        return result
    if result["warnings"]:
        result["status"] = "WARN"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="image file or directory")
    parser.add_argument("--min-dpi", type=float, default=300.0)
    parser.add_argument("--min-width", type=int, default=1200)
    parser.add_argument("--min-height", type=int, default=800)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    if not args.source.exists():
        parser.error(f"source does not exist: {args.source}")
    paths = [args.source] if args.source.is_file() else sorted(
        p for p in args.source.rglob("*") if p.suffix.lower() in SUPPORTED
    )
    results = [audit(p, args.min_dpi, args.min_width, args.min_height) for p in paths]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            detail = f"{item.get('width', '?')}x{item.get('height', '?')}, dpi={item.get('dpi', '?')}"
            print(f"[{item['status']}] {item['path']} ({detail})")
            for warning in item.get("warnings", []):
                print(f"  - {warning}")
            if "error" in item:
                print(f"  - {item['error']}")
    return 1 if any(item["status"] == "FAIL" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
