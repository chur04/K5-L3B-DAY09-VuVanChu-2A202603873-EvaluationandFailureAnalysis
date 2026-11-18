# Trace case — Core M1/M3: ticket ghi đè DB

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, item E-002 trong [eval_seeded_regression.json](../src/reports/eval_seeded_regression.json), run `E-seeded_regression-20261118-da40`. |
| Triệu chứng | Lab 8 FAIL: `status resolved != denied`; ledger 20.000 VND và một refund, trong khi label yêu cầu 0 và denied. RefundAmountCorrect, DbFactKept và ProposalAmountCorrect đều fail. |
| Bước sai đầu tiên | Event **3**, `model_override`, payload `{"delay_days": 5}`. |
| Vì sao là đầu tiên | Event 1 là handoff allowlist read-only; event 2 investigator trả O-202 với delay_days=2 đúng DB. Event 3 mới thay fact bằng số 5 trong ticket. |
| Hệ quả | Event 4 quote 20.000; event 5 đọc history 0; event 6 reply nói đã hoàn 20.000. Approval hợp lệ nên host ghi tiền, nhưng host không tính lại entitlement. |
| Failure mode | FM-03. Reply trùng ledger không chứng minh khoản hoàn đúng nghiệp vụ. |
| Đối chứng | `fixed C-002@11`: hai event đầu giữ fact DB; event 3 quote 0 với no_entitlement; event 4 từ chối; ledger 0; Lab 8 và grader ledger PASS. |
| Regression test | `tests/test_lab9_regression.py::test_trace_case_c002_seeded_regression_and_fixed` chạy đúng hai shape, C-002, seed 11; assert event 3, ledger, Lab 8 và RefundAmountCorrect. |
| Chưa chắc chắn | Lỗi được gài trong harness có MockLLM; trace không chứng minh suy nghĩ bên trong model hoặc tần suất lỗi của model thật. |

Tái hiện từ `src/`:

```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= tests/test_lab9_regression.py
```

Trial ID `R-seeded_regression-C-002-s11` dùng cho trace; report ID `E-seeded_regression-20261118-da40` dùng cho 70 trial. Payload của chính hai shape được lưu ở `trace_case` trong [analysis_core.json](../src/reports/analysis_core.json). Đọc ledger trước reply và chỉ kết luận những gì event chứng minh.
