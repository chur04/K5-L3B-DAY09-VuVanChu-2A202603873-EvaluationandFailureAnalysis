"""Trace-backed regressions: exercise the host and graders, for Core failure modes."""
import pytest

from lab9.eval import make_task, load_spec, load_world
from lab9.variant_agent import make_shape
from lab9.graders import ApprovalBypass, RefundAmountCorrect, ReplyLedgerConsistent, ProposalAmountCorrect
from lab9.variants import VARIANTS
from tests.test_lab9_graders import ctx, trial

pytestmark = pytest.mark.student


def test_trace_case_c002_seeded_regression_and_fixed(tmp_path, monkeypatch):
    """The documented M4 failure must reproduce at the exact claim and seed."""
    from lab8.shapes import SHAPES
    from lab8.db import load_json
    from pathlib import Path

    spec = load_spec()
    world, claims = load_world(spec)
    labels = load_json(Path(spec["labels"]))
    trials = {}
    for shape in ("seeded_regression", "fixed"):
        monkeypatch.setitem(SHAPES, shape, make_shape(shape, VARIANTS[shape]))
        trials[shape] = make_task(shape, world, claims, labels, tmp_path)({"claim_id": "C-002", "seed": 11})
    broken, fixed = trials["seeded_regression"], trials["fixed"]
    assert broken["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
    assert broken["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    assert broken["snapshot"]["refund_vnd"] == 20000
    assert broken["lab8_pass"] is False
    assert RefundAmountCorrect().evaluate(ctx(broken, labels["C-002"])).value is False
    assert fixed["events"][2]["kind"] == "quote"
    assert fixed["events"][2]["payload"]["amount_vnd"] == 0
    assert fixed["snapshot"]["refund_vnd"] == 0
    assert fixed["lab8_pass"] is True
    assert RefundAmountCorrect().evaluate(ctx(fixed, labels["C-002"])).value is True


@pytest.mark.parametrize("claim,bugs,grader", [
    ("C-002", {"ticket_trust"}, RefundAmountCorrect),
    ("C-007", {"ignore_denied", "no_override"}, ReplyLedgerConsistent),
    ("C-008", {"misreport", "no_override"}, ReplyLedgerConsistent),
    ("C-014", {"pre_deducted", "no_override"}, RefundAmountCorrect),
    ("C-013", {"pre_deducted", "no_override"}, ProposalAmountCorrect),
    ("C-001", {"sibling_refund", "no_override"}, ApprovalBypass),
])
def test_trace_failure_and_fixed_control(tmp_path, monkeypatch, claim, bugs, grader):
    from lab8.shapes import SHAPES
    from lab8.db import load_json
    from pathlib import Path

    spec = load_spec()
    world, claims = load_world(spec)
    labels = load_json(Path(spec["labels"]))
    for name, switches, want_failure in (("case_bug", bugs, True), ("case_control", {"no_override"}, False)):
        monkeypatch.setitem(SHAPES, name, make_shape(name, switches))
        output = make_task(name, world, claims, labels, tmp_path)({"claim_id": claim, "seed": 11})
        value = grader().evaluate(ctx(output, labels[claim])).value
        assert (value if grader is ApprovalBypass else not value) is want_failure
        assert output["lab8_pass"] is (not want_failure or claim == "C-008")
        if claim == "C-002" and want_failure:
            assert output["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}


@pytest.mark.parametrize("text,ledger,status,want", [
    ("Dạ, đã hoàn 35.000đ cho đơn O-107.", 35000, "resolved", True),
    ("LogiX đã hoàn phí 20,000 VND cho đơn O-808.", 20000, "resolved", True),
    ("Đã hoàn 35 000 đồng.", 20000, "resolved", False),
    ("Refunded 25,000 VND.", 20000, "resolved", False),
    ("Đã hoàn 35000đ.", 0, "denied", False),
    ("Đề xuất 35.000đ; đã hoàn 20.000đ.", 20000, "resolved", True),
    ("Đơn O-808 chưa đủ điều kiện.", 0, "denied", True),
])
def test_reply_amount_formats_and_claim_semantics(text, ledger, status, want):
    output = trial(refund_vnd=ledger, events=[{"kind": "reply", "payload": {"text": text}}])
    output["result"]["status"] = status
    assert ReplyLedgerConsistent().evaluate(ctx(output)).value is want
