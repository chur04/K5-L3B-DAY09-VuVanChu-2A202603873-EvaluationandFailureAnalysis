"""Reproduce the Core M1-M4 evidence without editing reports by hand.

Run from src/: python -m lab9.evidence
Add --verify to run the Core tests and command-line checks and save verification.txt.
This script does not commit, push, or call GitHub.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic_evals.evaluators import EvaluatorContext

from lab8.console import utf8_stdio
from lab8.shapes import SHAPES
from lab9 import ci_check, evalset, gate, judge, variants
from lab9.eval import load_spec, load_world, make_task, per_item, run_eval, source_revision
from lab9.graders import GRADERS
from lab9.stats import paired_bootstrap
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape

OUT = Path("reports")
PROBES = [
    ("FM-01", "C-010", {"leaky_trace", "no_override"}),
    ("FM-02", "C-007", {"ignore_denied", "no_override"}),
    ("FM-03", "C-002", {"ticket_trust"}),
    ("FM-04", "C-014", {"sum_parts", "no_override"}),
    ("FM-05", "C-014", {"pre_deducted", "no_override"}),
    ("FM-06", "C-006", {"stale_clause", "no_override"}),
    ("FM-07", "C-001", {"sibling_refund", "no_override"}),
    ("FM-08", "C-008", {"misreport", "no_override"}),
]


def write(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def evaluate(shape: str, spec: dict, filename: str) -> dict:
    path = OUT / filename
    report = run_eval(shape, spec)
    if report["evaluator_failures"]:
        raise RuntimeError(report["evaluator_failures"])
    write(path, report)
    print(f"wrote {path}: {report['run_id']}", flush=True)
    return report


def decision(pr: dict, base: dict, spec: dict) -> dict:
    blocked, lines = gate.check(pr, base, spec)
    return {"pr_run_id": pr["run_id"], "baseline_run_id": base["run_id"],
            "exit_code": int(bool(blocked)), "blocked": blocked, "lines": lines}


def diagnostic_rates(broken: dict, fixed: dict, spec: dict) -> dict:
    bad_value = {m["id"]: "max" in m.get("threshold", {}) for m in spec["metrics"]
                 if m["id"] in GRADERS and m["id"] != "pass_rate"}
    def flagged(row):
        return any(row.get(mid) is bad for mid, bad in bad_value.items())
    failures = [r for r in broken["rows"] if r["pass_rate"] is False]
    detected = sum(flagged(r) for r in failures)
    alarms = sum(flagged(r) for r in fixed["rows"])
    return {"failing_trials": len(failures), "detected_trials": detected,
            "detection_rate": detected / len(failures) if failures else 0,
            "fixed_trials": len(fixed["rows"]), "false_alarms": alarms,
            "false_alarm_rate": alarms / len(fixed["rows"])}


def trace_controls(spec: dict) -> dict:
    world, claims = load_world(spec)
    labels = json.loads(Path(spec["labels"]).read_text(encoding="utf-8"))
    output = {}
    with tempfile.TemporaryDirectory(prefix="lab9-evidence-", ignore_cleanup_errors=True) as tmp:
        for mode, cid, bugs in PROBES:
            pair = {}
            for role, switches in (("probe", bugs), ("control", {"no_override"})):
                name = f"evidence_{mode.replace('-', '')}_{role}"
                previous = SHAPES.get(name)
                SHAPES[name] = make_shape(name, switches)
                try:
                    trial = make_task(name, world, claims, labels, Path(tmp))({"claim_id": cid, "seed": 11})
                finally:
                    if previous is None:
                        SHAPES.pop(name, None)
                    else:
                        SHAPES[name] = previous
                context = EvaluatorContext(name=name, inputs={"claim_id": cid, "seed": 11}, metadata=None,
                                           expected_output=labels[cid], output=trial, duration=0,
                                           _span_tree=None, attributes={}, metrics={})
                grades = {}
                for mid, grader in GRADERS.items():
                    result = grader().evaluate(context)
                    grades[mid] = {"value": result.value, "reason": result.reason}
                pair[role] = {"switches": sorted(switches), "result": trial["result"],
                              "snapshot": trial["snapshot"], "unexpected_rows": trial["unexpected_rows"],
                              "events": trial["events"], "grades": grades}
            output[mode] = {"claim_id": cid, "seed": 11, "label": labels[cid], **pair}
    return output


def verify_core() -> bool:
    """Check real CLI exits, including the expected rejection of helpful and regression."""
    checks = [
        (["-m", "lab9.smoke"], 0, "M0 PASS"),
        (["-m", "pytest", "-q"], 0, "passed"),
        (["-m", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9 and not advanced"], 0, "passed"),
        (["-m", "lab9.evalset", "--check"], 0, "0 problem(s)"),
        (["-m", "lab9.judge", "--csv", "data/eval/judge_tone_public.csv", "--audit", "5"], 0, "PASS floors"),
        (["-m", "lab9.judge", "--csv", "data/eval/judge_helpful_public.csv", "--audit", "5"], 1, "FAIL floors"),
        (["-m", "lab9.ci_check", "--pr", "reports/eval_pr.json", "--baseline", "reports/baseline_v1.json"], 0, "exit 0"),
        (["-m", "lab9.mutation", "--detect"], 0, "detection 100.00%"),
    ]
    for filename, expected, text in (("eval_pr.json", 0, "exit 0"), ("eval_fixed.json", 0, "exit 0"),
                                     ("eval_seeded_regression.json", 1, "exit 1 — blocked:")):
        checks.append((["-m", "lab9.gate", "--pr", f"reports/{filename}",
                        "--baseline", "reports/baseline_v1.json"], expected, text))
    lines = ["Core M1-M4 verification " + datetime.now(timezone(timedelta(hours=7))).isoformat()]
    ok = True
    for argv, expected, required_text in checks:
        result = subprocess.run([sys.executable, *argv], capture_output=True, text=True, encoding="utf-8",
                                env={**os.environ, "PYTHONUTF8": "1"})
        output = result.stdout + result.stderr
        passed = result.returncode == expected and required_text in output
        if "eval_seeded_regression.json" in argv:
            passed &= any(line.startswith("exit 1 — blocked:") and "pass_rate" in line
                          for line in output.splitlines())
        ok &= passed
        lines.extend(["", "> python " + " ".join(argv), output.rstrip(),
                      f"actual exit {result.returncode}; expected {expected}; {'PASS' if passed else 'FAIL'}"])
        print(f"{'PASS' if passed else 'FAIL'} {' '.join(argv)} (exit {result.returncode})", flush=True)
    lines.append("\nCore verification PASS" if ok else "\nCore verification FAIL")
    (OUT / "verification.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ok


def main(argv=None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    variants.register()
    problems = evalset.check()
    if problems:
        raise ValueError(problems)
    v1 = load_spec()
    if v1["eval_set_version"] != "v1" or v1.get("slices") or v1.get("pass_k"):
        raise ValueError("Core evidence requires the v1 spec without optional advanced metrics")
    b1 = evaluate("swarm", v1, "baseline_v1.json")
    core = {shape: evaluate(shape, v1, f"eval_{shape}.json")
            for shape in ("fixed", "seeded_regression")}
    pr = evaluate("swarm", v1, "eval_pr.json")
    a, b = per_item(core["seeded_regression"], "pass_rate"), per_item(b1, "pass_rate")
    keys = sorted(a)
    diagnostic = diagnostic_rates(core["seeded_regression"], core["fixed"], v1)
    summary = {"generator": "python -m lab9.evidence", "revision": source_revision(),
               "run_id": f"A-core-{b1['run_id']}", "scope": "M1-M4",
               "core": {shape: decision(rep, b1, v1) for shape, rep in {"swarm": pr, **core}.items()},
               "baseline_self_gate": decision(b1, b1, v1),
               "ci_sanity_problems": ci_check.check(pr, b1, v1),
               "pass_rate_delta_ci": paired_bootstrap([a[k] for k in keys], [b[k] for k in keys]),
               "diagnostic_rates": diagnostic,
               "judge": {name: judge.calibrate(Path(f"data/eval/judge_{name}_public.csv"))
                         for name in ("tone", "helpful")},
               "trace_controls": trace_controls(v1),
               "trace_case": {shape: investigate(shape, "C-002", 11) for shape in ("seeded_regression", "fixed")}}
    write(OUT / "analysis_core.json", summary)
    ok = (not summary["core"]["fixed"]["exit_code"] and "pass_rate" in summary["core"]["seeded_regression"]["blocked"]
          and not summary["ci_sanity_problems"] and diagnostic["detection_rate"] >= 0.8
          and diagnostic["false_alarm_rate"] <= 0.1 and not summary["baseline_self_gate"]["exit_code"]
          and not summary["core"]["swarm"]["exit_code"]
          and summary["judge"]["tone"]["passed"] and not summary["judge"]["helpful"]["passed"]
          and all(abs(actual - reference) <= 0.01 for actual, reference in
                  zip(summary["pass_rate_delta_ci"], (-0.271429, -0.5, -0.057143))))
    if args.verify:
        ok = verify_core() and ok
    print(f"Core evidence {'PASS' if ok else 'FAIL'} · diagnostic {diagnostic}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
