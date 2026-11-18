## Hoàn thành Core M1–M4

Bổ sung bộ đánh giá Core cho refund agent: taxonomy FM-01–FM-08 có trace và đối chứng, tag/provenance cho 14 item và nhãn tách riêng, calibration/audit judge, grader trajectory, paired bootstrap và release gate. Giữ nguyên mã Lab 8, variant, trap và bộ test gốc của đề. Phạm vi bài nộp chỉ gồm Core.

## M1 — Taxonomy và eval set

- Tám FM có định nghĩa, layer, claim@seed, bước sai đầu tiên, grader và metric.
- Eval set v1 SHA **da402347cdae**, 14 item × 5 seed, checker **0 problem**.
- Provenance có source/matrix/trace/generator/label_by/checked_by; nhãn nằm riêng trong labels_v1.json.
- Trace case C-002@11: event 3 model_override thay delay DB 2 bằng ticket 5; regression test chạy đúng seeded_regression và fixed.

## M2 — Judge calibration và audit

| Judge | κ | Precision | Recall | Quyết định |
|---|---|---|---|---|
| tone | 0.757 | 0.857 | 0.800 | PASS floors |
| helpful | 0.375 | 1.000 | 0.300 | FAIL; loại khỏi gate |

Audit 15 bất đồng có kết luận và hành động sửa rubric. Helpful bỏ sót 21/30 lỗi, nên precision cao không đủ để dùng làm gate. Giữ nguyên CSV nhãn gốc; tone hiện chỉ được calibration trên replay, chưa chạy judge cho từng trial.

## M3 — Grader và metric FM-08

ApprovalBypass kiểm tiền không có approval hợp lệ hoặc ledger row ngoài claim; RefundAmountCorrect đọc ledger. Metric riêng `reply_ledger_consistent` là capability blocking, min 1.0, phát hiện C-008 reply 35.000đ trong khi ledger 20.000đ dù Lab 8 vẫn pass. ProposalAmountCorrect giúp chẩn đoán C-013 khi proposal sai nhưng ledger 0 đúng.

```text
detection 100.00% (target >=80%) · false alarms 0.00% (target <=10%)
```

Có 20/20 trial lỗi được grader chẩn đoán, 0/70 false alarm trên fixed.

## M4 — Baseline, bootstrap và gate

- Baseline `E-swarm-20261118-da40`: pass_rate 0.9857.
- Swarm chạy lại độc lập: cùng số liệu baseline, gate exit 0, ci_check exit 0.
- Fixed `E-fixed-20261118-da40`: pass_rate 1.0, gate exit 0.
- Seeded regression `E-seeded_regression-20261118-da40`: pass_rate 0.7143.
- Bootstrap paired theo item, 1.000 resample percentile, RNG 2027, confidence 95%; sai số so tham chiếu <0.01.

Output gate seeded_regression (trích):

```text
refund_amount_correct  0.8571  Δ -0.129 CI [-0.315, +0.000] BLOCK
pass_rate              0.7143  Δ -0.271 CI [-0.500, -0.057] BLOCK
reply_ledger_consistent 0.7857 BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_ledger_consistent
```

Cả swarm/fixed/seeded_regression dùng chung spec và baseline. Harness map có section eval. Workflow eval-gate kiểm host/Core, eval set, detection, baseline sanity và kết quả ba gate.

## Validation và tài liệu

- **57 test host + 25 test Core** pass.
- Tái lập: từ src/ chạy `python -m lab9.evalset --build --check`, rồi `python -m lab9.evidence --verify`.
- Report cần nộp: baseline_v1.json, eval_fixed.json, eval_seeded_regression.json; thêm eval_pr.json, analysis_core.json, verification.txt để kiểm chứng.
- docs/: failure_taxonomy.md, trace_case.md, judge_audit.md, eval_card.md, PRD_v1.1.md đã điền bằng số liệu report.

Giới hạn: MockLLM, chỉ 14 item, CSV judge replay công khai, chưa có dữ liệu người dùng thật hoặc key chấm riêng của giảng viên. Swarm không có reply event nên baseline FM-08 không đại diện độ phủ ngôn ngữ. GitHub CI được xác nhận qua job của PR này, không suy từ local test.
