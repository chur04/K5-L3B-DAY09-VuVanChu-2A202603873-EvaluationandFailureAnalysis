# Bàn giao — Core M1–M4

Phạm vi bài nộp là **Core M1–M4 (60 điểm theo rubric)**. Bản Core đã được commit/push; bản sửa lỗi SHA khác nhau giữa Windows và Linux hiện chưa commit/push. Evidence Core đã được sinh lại. Điểm thực tế do giảng viên chấm, GitHub CI cần xác nhận sau lần push bản sửa này.

## Đối chiếu đầy đủ yêu cầu Core

| Mục | Tiêu chí đề | Bằng chứng / trạng thái |
|---|---|---|
| M1 | ≥5 FM có định nghĩa, layer, trace/claim, grader; phân tích bước sai đầu tiên | [Taxonomy](docs/failure_taxonomy.md) có 8 FM, 8 probe và đối chứng, coding sheet có event cụ thể. Key riêng giảng viên chưa có để đối chiếu trước điểm. |
| M1 | 14 item có failure_modes, provenance; nhãn tách riêng; checker sạch | Eval set v1 SHA 8fd87e07c356, `evalset --check`: 0 problem. |
| M2 | Confusion, precision/recall, kappa, Rogan–Gladen đúng | Test stats Core pass; tone κ=0.757/P=0.857/R=0.800; helpful κ=0.375/R=0.300, bị loại. |
| M2 | Audit ≥5 bất đồng, ai đúng và sửa rubric | [Judge audit](docs/judge_audit.md) có 15 trường hợp, gồm lỗi nhãn người có thể sai; không sửa CSV gốc để nâng điểm. |
| M3 | ApprovalBypass và RefundAmountCorrect đúng | Test gốc và regression Core pass; tiền/approval chấm bằng code. |
| M3 | Detection ≥80%, false alarm ≤10% | **20/20 lỗi phát hiện (100%)**, **0/70 fixed báo nhầm (0%)**, lệnh mutation --detect exit 0. |
| M3 | Metric FM-08 hoạt động | ReplyLedgerConsistent blocking min 1.0 bắt C-008 nói 35.000 trong khi ledger 20.000; Lab 8 vẫn pass nên metric mới có tác dụng riêng. |
| M4 | Paired bootstrap khớp tham chiếu ±0.01 | Δ pass_rate −0.271429, CI [−0.500000; −0.057143]. |
| M4 | Swarm/fixed qua; seeded_regression bị chặn ở pass_rate | Ba lệnh CLI có exit 0/0/1 đúng; cùng spec và baseline. |
| M4 | Baseline đúng swarm; có eval trong harness_map | `ci_check` kiểm với swarm chạy lại độc lập, exit 0; harness_map version 1.2 có section eval. |
| Tài liệu | Trace case có regression test | [Trace case](docs/trace_case.md) và test `test_trace_case_c002_seeded_regression_and_fixed` chạy đúng C-002@11. |
| Tài liệu | Eval card + PRD có run_id và giới hạn | [Eval card](docs/eval_card.md), [PRD v1.1](docs/PRD_v1.1.md), số liệu khớp report; nêu MockLLM, 14 item, judge replay. |
| CI/nộp bài | Job eval-gate xanh, PR trong fork, merge main, nộp LMS | **Bạn thực hiện tay sau commit/push**; chưa thể gọi là đã có GitHub CI xanh. |

Kết quả test local: **57 test host + 28 test Core** pass. [verification.txt](src/reports/verification.txt) ghi lệnh, output, actual/expected exit code; [analysis_core.json](src/reports/analysis_core.json) có diagnostic, judge, gate, bootstrap và payload trace.

## Phần nâng cao đã gỡ

Đã xóa dữ liệu v2 sinh thêm, các report v2/A/A/trap, test nâng cao tự thêm và job CI v2; bỏ triển khai pass_at_k/pass_hat_k, slice gate và integrity/ratchet. Cấu hình/hàm/template nâng cao có sẵn trong đề được trả về trạng thái gốc. Không xóa/sửa variants, traps, bộ chấm hay test gốc của đề. Quy trình bài nộp và script evidence hiện chỉ chạy Core.

## Sửa lỗi CI do xuống dòng

CI đọc eval set LF (SHA 8fd87e07c356), trong khi baseline cũ được sinh trên Windows CRLF. Nội dung item không đổi. Hàm sha12 hiện chuẩn hóa CRLF thành LF trước khi băm; .gitattributes và bộ sinh v1 ghi LF để checkout/build tái lập giữa Windows và Linux. Thay đổi nội dung thật vẫn đổi SHA và bị gate chặn. Ba test hồi quy kiểm các trường hợp này; mọi report đã được sinh lại bằng script với SHA 8fd87e07c356.

## Các bước bạn làm tay

Chạy từng dòng từ thư mục gốc project. Các report bị `.gitignore` bỏ qua nên cần `git add -f`:

```powershell
git status
git add -A
git add -f src/reports/baseline_v1.json src/reports/eval_fixed.json src/reports/eval_seeded_regression.json
git add -f src/reports/eval_pr.json src/reports/analysis_core.json src/reports/verification.txt
git diff --cached --stat
git commit -m "fix: stabilize eval hashes across Windows and Linux"
git push origin starter/d09
```

Sau đó:

1. Bật workflow trong tab Actions của fork nếu chưa bật.
2. PR hiện có sẽ tự nhận commit mới sau khi push. Nếu chưa có PR, mở `starter/d09` → `main` trong fork **chur04/K5-L3B-DAY09-VuVanChu-2A202603873-EvaluationandFailureAnalysis**; kiểm tra base repository đúng fork của bạn.
3. Tiêu đề gợi ý: `Complete Core M1-M4 evaluation and failure analysis`.
4. Dán [PR_DESCRIPTION.md](PR_DESCRIPTION.md) vào mô tả PR; đã có output regression exit 1 theo đề.
5. Chờ job **eval-gate** xanh, rồi tự merge vào main.
6. Kiểm tra main có đủ report và tài liệu, nộp link repo fork lên LMS theo hạn của ca.

[Trang mở PR cho starter/d09](https://github.com/chur04/K5-L3B-DAY09-VuVanChu-2A202603873-EvaluationandFailureAnalysis/pull/new/starter/d09).

## Tái lập Core

Từ thư mục gốc, dùng venv Python 3.12 hiện có, không cần activate PowerShell:

```powershell
cd src
.\.venv\Scripts\python.exe -m lab9.evalset --build --check
.\.venv\Scripts\python.exe -m lab9.evidence --verify
```

Lệnh evidence sinh lại baseline/swarm/fixed/regression, tám probe taxonomy, judge calibration, báo cáo phân tích và log kiểm tra Core. Không sửa JSON trong reports bằng tay. Manifest hiện ghi commit cha và working_tree_dirty=true vì code chưa commit; source_sha256 ghi chính nội dung đã chạy.

Không cần hoàn thiện workflow/single/orchestrator của Day 8; bài Core dùng swarm và variant Lab 9. Giữ nguyên src/lab8 theo quy định đề.
