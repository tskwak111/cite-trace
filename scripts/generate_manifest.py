#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "PACKAGE_MANIFEST.txt"
EXCLUDED = {OUTPUT.name, "CHECKSUMS.sha256"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    files = [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.is_file()
        and path.name not in EXCLUDED
        and not any(part in {".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__", "node_modules", ".next"} for part in path.parts)
    ]
    lines = [
        "CiteTrace AAA Development Package v1.0",
        "Generated: 2026-08-28",
        f"File count: {len(files)}",
        "",
    ]
    lines.extend(
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in files
    )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
