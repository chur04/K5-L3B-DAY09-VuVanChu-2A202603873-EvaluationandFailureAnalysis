"""Regression for the Windows-generated baseline versus the Linux CI checkout."""
import hashlib
import json

import pytest

from lab9 import evalset, gate

pytestmark = pytest.mark.student


def test_eval_hash_matches_for_windows_and_linux_line_endings(tmp_path):
    content = b'{"item_id":"E-001","failure_modes":["FM-03"]}\n'
    linux, windows = tmp_path / "linux.jsonl", tmp_path / "windows.jsonl"
    linux.write_bytes(content)
    windows.write_bytes(content.replace(b"\n", b"\r\n"))
    assert linux.read_bytes() != windows.read_bytes()
    assert evalset.sha12(windows) == evalset.sha12(linux) == hashlib.sha256(content).hexdigest()[:12]


def test_changed_eval_content_still_blocks_the_gate(tmp_path):
    baseline, changed = tmp_path / "base.jsonl", tmp_path / "changed.jsonl"
    baseline.write_bytes(b'{"failure_modes":["FM-03"]}\n')
    changed.write_bytes(b'{"failure_modes":["FM-04"]}\r\n')
    base_sha, changed_sha = evalset.sha12(baseline), evalset.sha12(changed)
    assert base_sha != changed_sha
    blocked, _ = gate.check({"manifest": {"eval_set_sha": changed_sha}},
                            {"manifest": {"eval_set_sha": base_sha}}, {"metrics": []})
    assert blocked == ["eval_set_sha"]


def test_core_builder_writes_lf_for_items_and_labels(tmp_path, monkeypatch):
    source = tmp_path / "claims.jsonl"
    source.write_text(json.dumps({"claim_id": "C-001", "matrix_id": "T01",
                                  "expected": {"refund_vnd": 35000}}) + "\n", encoding="utf-8")
    items, labels = tmp_path / "items.jsonl", tmp_path / "labels.json"
    monkeypatch.setattr(evalset, "ITEMS", items)
    monkeypatch.setattr(evalset, "LABELS", labels)
    assert evalset.build(source) == (1, 1)
    for path in (items, labels):
        assert b"\n" in path.read_bytes()
        assert b"\r\n" not in path.read_bytes()
