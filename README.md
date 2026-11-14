# Day 7 — Agentic RAG

## Bài làm — Hoàng Lam Minh (2A202603566)

Agent Gemini (`gemini-3.5-flash-lite`, function calling) tìm bằng chứng trong kho Day 6: 2 báo cáo World Bank *Taking Stock* 12/2017 và 06/2018 (CC BY 3.0 IGO), 618 chunk, Chroma, MiniLM 384 chiều. Agent trả lời kèm citation hoặc từ chối.

- 4 phương pháp retrieval: dense trên Chroma Day 6, BM25, hybrid RRF, hybrid + cross-encoder rerank.
- Benchmark 24 câu: dev 15+2, test 5+2; thêm test2 độc lập 5+2, viết sau khi chốt cấu hình.
- Báo cáo: [report/individual/2A202603566_HoangLamMinh.md](report/individual/2A202603566_HoangLamMinh.md).

**Ghi nguồn dữ liệu:** World Bank. 2017. *Taking Stock, December 2017* (https://hdl.handle.net/10986/29032) và World Bank. 2018. *Taking Stock, June 2018* (https://hdl.handle.net/10986/29959). License: CC BY 3.0 IGO. `data/chunks.json` là text trích xuất đã chuẩn hóa từ Day 6, không phải bản chính thức của World Bank.

### Cài đặt

1. Cần repo Day 6 (https://github.com/laminh-h/K5-L3A-DAY06-HoangLamMinh-2A202603566-DataIngestion), clone cạnh repo này. Kho Chroma `starter/chroma_db` **không** nằm trong git, nên phải tạo lại: trong `starter/` của Day 6, cài `requirements.txt` vào `.venv`, rồi chạy `python -m src.run ingest` (PDF đã có sẵn trong `data/raw/`; Day 6 tạo index A/B với cùng ID, vì vậy `day7.export_day6` sẽ cho đúng 618 chunk). Nếu Day 6 đặt chỗ khác, khai báo đường dẫn bằng biến `DAY6_ROOT`.
2. Dùng venv của Day 6 (đã có chromadb, sentence-transformers và `requests`). Không cần cài thêm gì.
3. `cp .env.example .env`, rồi điền `GEMINI_API_KEY` (lấy key free ở https://aistudio.google.com/apikey). Không commit `.env`.

### Chạy (từ thư mục gốc repo này)

```bash
PY=../K5-L3A-DAY06-HoangLamMinh-2A202603566-DataIngestion/starter/.venv/Scripts/python.exe   # Linux/macOS: .venv/bin/python
$PY -X utf8 -m unittest discover -s tests                 # 23 test offline (mock; không phải benchmark)
$PY -X utf8 -m day7.export_day6                           # Chroma Day 6 -> data/chunks.json
$PY -X utf8 -m day7.build_benchmark                       # data/questions.json, data/cases.json
$PY -X utf8 -m day7.eval_retrieval --split dev            # R1..R6 -> results/retrieval/dev/
$PY -X utf8 -m day7.run_agent_bench --config A1_dense --split dev    # cũng: A2_hybrid_rerank_adj, A3_hybrid_rerank_adj_steps
$PY -X utf8 -m day7.review_sheet --split dev --config A1_dense       # bảng đọc để chấm tay
# sau khi chốt configs/selected.json:
$PY -X utf8 -m day7.eval_retrieval --split test           # chỉ cho phép R1 và R4
$PY -X utf8 -m day7.run_agent_bench --config A3_hybrid_rerank_adj_steps --split test
# test2 = bộ test độc lập viết sau khi chốt cấu hình (thay --split test bằng --split test2 ở 3 lệnh trên)
$PY -X utf8 starter/agent_metrics.py --cases data/cases.json --traces results/agent/test/A3_hybrid_rerank_adj_steps/traces.json --reviews results/agent/test/A3_hybrid_rerank_adj_steps/reviews.json --split test --output results/agent/test/A3_hybrid_rerank_adj_steps/summary.json
```

| Đường dẫn | Nội dung |
|---|---|
| `day7/` | config (kết nối Day 6), retrievers, context, gemini client, agent, các script benchmark |
| `configs/` | `retrieval.json` (R1–R6), `agent.json` (A1–A3), `selected.json` (cấu hình chốt trước test) |
| `data/` | chunks, questions (gold + `absence_check`), cases, báo cáo build benchmark |
| `results/retrieval/<split>/` | metric và trace top-10 cho từng cấu hình |
| `results/agent/<split>/<config>/` | `traces.json`, `auto_summary.json`, `review_sheet.md`, `reviews.json`, `summary.json` |
| `results/logs/` | log chạy agent |

---

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
