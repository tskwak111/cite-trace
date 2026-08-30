"""Contract test: atomic JSONL write in adjudicate.

The adjudicate.py `_write_jsonl` writes through a sibling
temporary file and renames atomically so a partial write
cannot leave the merged file half-written. This test
asserts that:

  - the merged file exists after adjudication;
  - the .tmp sibling does not leak (the rename moved it);
  - the merged file is parseable JSONL (no half-written
    lines).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "adjudicate.py"
PILOT_DIR = REPO_ROOT / "eval" / "pilot_annotation"


def _load_module():
    spec = importlib.util.spec_from_file_location("adjudicate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_jsonl_is_atomic(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "merged.jsonl"
    rows = [{"case_id": f"c{i}", "ok": True} for i in range(3)]
    module._write_jsonl(target, rows)
    assert target.exists()
    assert not target.with_suffix(target.suffix + ".tmp").exists(), (
        "the .tmp sibling should be renamed into place; "
        "its presence means the atomic rename did not run"
    )
    lines = [
        line for line in target.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    parsed = [json.loads(line) for line in lines]
    assert parsed == rows


def test_write_jsonl_cleans_up_tmp_on_error(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "merged.jsonl"

    def _explode(*_args, **_kwargs):
        raise OSError("synthetic write failure")

    original_open = module.Path.open
    module.Path.open = _explode  # type: ignore[assignment]
    try:
        with pytest.raises(OSError):
            module._write_jsonl(target, [{"case_id": "c1"}])
    finally:
        module.Path.open = original_open  # type: ignore[assignment]
    assert not target.with_suffix(target.suffix + ".tmp").exists(), (
        "the .tmp sibling must be removed on failure so a "
        "stale half-written file does not leak across runs"
    )


def test_end_to_end_adjudicate_uses_atomic_write(tmp_path: Path) -> None:
    """Running the full script must produce a merged file
    with no .tmp sibling left behind. This pins the
    behaviour across the end-to-end pipeline, not just
    the helper."""
    out = tmp_path / "merged.jsonl"
    ties = tmp_path / "ties.jsonl"
    subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--a", str(PILOT_DIR / "annotator_a.jsonl"),
            "--b", str(PILOT_DIR / "annotator_b.jsonl"),
            "--adjudicator", str(PILOT_DIR / "adjudicator.jsonl"),
            "--output", str(out),
            "--ties", str(ties),
        ],
        check=True,
        capture_output=True,
    )
    assert out.exists()
    assert not out.with_suffix(out.suffix + ".tmp").exists()
    assert not ties.with_suffix(ties.suffix + ".tmp").exists()
