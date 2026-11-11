# Elec-Agent Backend

Elec-Agent là backend hỗ trợ người dùng tham khảo và khắc phục các vấn đề thông thường của thiết bị điện gia dụng. Hệ thống sử dụng FastAPI, Ollama với model `qwen2.5:3b` và PostgreSQL/pgvector.

## 1. Yêu cầu hệ thống

Trước khi bắt đầu, cài đặt:

- Git
- Python 3.11 64-bit
- Docker Desktop, đang chạy Docker Engine
- Ollama, đã mở ứng dụng để API hoạt động

Model AI sử dụng: `qwen2.5:3b`.

## 2. Chạy nhanh trên Windows

Các lệnh bên dưới dành cho PowerShell. Thay `<REPO_URL>` bằng URL repository Git thực tế.

### Lệnh 1 — Clone repository

```powershell
git clone https://github.com/minhthien-1/AI_Agent_Elec_BE_2026.git
```

### Lệnh 2 — Vào thư mục project

```powershell
cd AI_Agent_Elec_BE_2026
```

### Lệnh 3 — Cài dependency và chuẩn bị database

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Lệnh này tạo `.venv`, cài dependency, tạo `.env` nếu cần, khởi động PostgreSQL, bật pgvector, bảo đảm model Ollama tồn tại và chạy migration Alembic.

Không commit `.env` lên Git. Cấu hình local mặc định chỉ dành cho phát triển.

### Lệnh 4 — Khởi động API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

API mặc định chạy tại:

`http://127.0.0.1:8000`

Swagger UI:

`http://127.0.0.1:8000/docs`

### Lệnh 5 — Gửi thử request

Mở terminal PowerShell thứ hai:

```powershell
$body = '{"message":"Máy giặt không lên nguồn thì tôi nên kiểm tra gì?"}'

$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/chat" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $bodyBytes
```

Response thành công gồm `answer`, `trace_id` và `duration_ms`.

## 3. API

### GET /health

Kiểm tra API có hoạt động hay không.

### POST /chat

Nhận câu hỏi, gọi LLM, ghi Trace/TraceStep vào PostgreSQL và trả lời người dùng.

Request mẫu:

```json
{
  "message": "Tủ lạnh không lạnh"
}
```

## 4. Cấu trúc project

```text
api/                         # HTTP endpoints, schemas, dependency wiring
application/                 # Chat use case, ports, application result
domain/                      # Business policies and domain concepts
infrastructure/
  llm/                       # Ollama adapter/client
  persistence/               # PostgreSQL, SQLAlchemy models, trace storage
  rag/                       # Retrieval, embeddings, ingestion command
  document_processing/       # Document readers, cleaning, chunking, indexing
alembic/                     # Database migrations
tests/                       # Tests arranged by layer
```

- `api/`: FastAPI routers, HTTP schemas và composition root/dependency wiring.
- `application/`: use case chat và các port trừu tượng, không phụ thuộc FastAPI/SQLAlchemy/Ollama.
- `domain/`: khái niệm và chính sách nghiệp vụ độc lập với framework.
- `infrastructure/`: adapter và tích hợp bên ngoài như PostgreSQL, Ollama, RAG, xử lý tài liệu.
- `alembic/`: database migrations.
- `tests/`: automated tests.
- `data/manuals/`: chỉ mục nguồn tài liệu và tài liệu tham khảo cục bộ.

API là điểm khởi tạo adapter; `application` chỉ phụ thuộc `domain` và các port.
`infrastructure` hiện thực các port đó.

### P3-1 — Trạng thái hội thoại

`domain.conversation.ConversationState` là một bản tóm tắt bất biến theo từng thời điểm,
không phải lịch sử các tin nhắn. State gồm thiết bị, triệu chứng, mức rủi ro,
câu hỏi đã hỏi và giai đoạn:

- `clarifying`: đang thu thập thông tin còn thiếu.
- `safety_warning`: đã nhận diện rủi ro cao; ưu tiên cảnh báo an toàn.
- `guidance`: đã có đủ thông tin để đưa ra hướng dẫn phù hợp.
- `completed`: lượt tư vấn đã kết thúc.

`transition_conversation` nhận state hiện tại cùng thông tin mới và trả về state mới;
state cũ không bị sửa. Ở P3-1, caller cung cấp các thông tin đã được nhận diện,
bao gồm giai đoạn tiếp theo. Mức rủi ro `high` luôn đưa state sang `safety_warning`.

P3-1 chưa lưu state vào database. API hiện chưa có `conversation_id` để liên kết
nhiều request thành một cuộc hội thoại; việc lưu bền vững cần đi cùng chức năng
định danh và khôi phục cuộc hội thoại ở bước sau.

### P3-2 — Định tuyến bằng luật

`domain.routing.choose_route` chọn một trong bốn nhánh theo thứ tự ưu tiên:

1. `emergency`: dấu hiệu nguy hiểm rõ ràng hoặc state đã có rủi ro cao; trả cảnh báo
   cố định, không gọi LLM hay RAG.
2. `ask_clarification`: câu mơ hồ/thiếu ngữ cảnh; hỏi người dùng bổ sung thông tin.
3. `retrieve_documents`: câu hỏi về hướng dẫn, bảo hành, model, lỗi hoặc khắc phục;
   tìm tài liệu trước khi gọi LLM. Nếu không có tài liệu, yêu cầu hãng/model thay vì đoán.
4. `direct_answer`: câu hỏi phổ thông, rõ nghĩa; gọi LLM trực tiếp.

Đây là bộ luật từ khóa ban đầu, không phải bộ phân loại ngôn ngữ hoàn chỉnh.
Request chat hiện chưa nhận `ConversationState`, nên nhánh kiểm tra state rủi ro cao
có thể được dùng qua domain API nhưng chưa duy trì trạng thái giữa các request.

### P3-3 — Giao diện Tool chung

`application.tools.AgentTool` là hợp đồng chung: mỗi tool có `name`, `description`,
`parameters_schema` theo JSON Schema và `run(arguments)`. `ToolRegistry` đăng ký,
liệt kê metadata và thực thi tool theo tên; mỗi tool kiểm tra tham số cụ thể của nó.
`infrastructure.tools.SearchManualTool` là tool mẫu, bọc cổng truy xuất tài liệu hiện có.

Khi P3-2 chọn nhánh `retrieve_documents`, `ChatService` gọi `search_manual` qua registry,
nhận kết quả chuẩn `ToolResult`, rồi đưa tài liệu đó vào prompt. Trace ghi lại tên và
tham số tool để có thể kiểm tra nhánh nào đã chạy. Các comment trong Python dùng `#`,
đây là cú pháp comment hợp lệ của Python (`//` không phải comment Python).

P3-3 chuẩn hóa giao diện và cách gọi tool; hiện tại rule router vẫn chọn khi nào gọi
`search_manual`. Agent/LLM tự chọn tool dựa trên `parameters_schema` là phần mở rộng sau,
chưa được bật ở bước này.

### P3-4 — Hai tool đầu tiên

Tool đầu tiên `search_manual` tra tài liệu như mô tả ở P3-3. Tool thứ hai,
`ask_clarification`, nhận `missing_fields` và tạo câu hỏi theo mẫu mà không gọi LLM.
Khi thiếu thiết bị và triệu chứng, tool hỏi cả hai; nếu tên thiết bị đã nhận diện
được từ request thì chỉ hỏi triệu chứng. Vì `ConversationState` chưa được truyền qua API,
đây mới là nhận diện thiết bị theo một số từ khóa, chưa phải theo dõi các lượt chat trước.

### P4-1 — Bộ luật an toàn cứng

Luật tại `domain.routing` ưu tiên các tín hiệu điện giật/rò điện, mùi khét, khói/cháy,
tia lửa, nước vào ổ điện hoặc thiết bị đang cắm, và sửa chữa khi chưa ngắt nguồn.
Khi khớp, hệ thống trả cảnh báo cố định, không gọi LLM hoặc RAG. Bộ nhận diện kiểm tra
phủ định gần tín hiệu và bỏ qua một số ngữ cảnh giả định/trích dẫn; đây là bộ luật từ khóa
ban đầu, không thay thế đánh giá của người có chuyên môn.

### P4-2 — Bộ kiểm duyệt độc lập

P4-1 chặn ở **đầu vào** (câu hỏi). P4-2 thêm lớp chặn ở **đầu ra**: `domain.answer_review`
kiểm tra câu trả lời SAU khi đã sinh, trước khi trả cho người dùng. Nếu phát hiện chỉ dẫn
thao tác điện nguy hiểm, toàn bộ câu trả lời bị thay bằng `UNSAFE_ANSWER_RESPONSE`
(cảnh báo về thao tác, khác với `EMERGENCY_RESPONSE` dành cho tình huống khẩn cấp).

- **Tách hẳn module, không nằm trong prompt**: reviewer là luật thuần Python, không gọi
  Ollama, nên độc lập với model sinh câu trả lời, cho kết quả ổn định và test được.
  `ChatService` chỉ biết port `application.ports.AnswerReviewer`; hiện thực mặc định là
  `RuleBasedAnswerReviewer`, được gắn trong `api/dependencies.py`.
- **Nhóm luật luôn cấm** (bị chặn kể cả khi câu trả lời có nhắc "ngắt nguồn trước"):
  `live_work` (chạm/đo/sửa khi còn điện), `bypass_protection` (nối tắt cầu chì, bỏ CB,
  bỏ tiếp địa), `high_energy_component` (xả/thay tụ, magnetron, bo nguồn, máy nén),
  `refrigerant_gas` (xả/nạp gas), `mains_wiring` (tự đấu nối điện lưới),
  `open_enclosure` (tháo vỏ máy). Bảo dưỡng thông thường như rút phích rồi vệ sinh lưới
  lọc không nằm trong luật.
- **Phủ định**: luật xét theo từng câu/dòng. Lời cấm như "không được", "không nên",
  "đừng", "tránh", "tuyệt đối không" đứng trước thao tác thì cho qua; nhưng nếu sau lời
  cấm có "hãy", "sau đó", "rồi"... thì vẫn chặn (ví dụ "Đừng lo, hãy xả tụ").
- **Một cửa kiểm duyệt duy nhất**: bước review đặt sau mọi nhánh route. Mặc định mọi câu
  trả lời (LLM, output tool) đều bị kiểm; chỉ các câu cố định trong `domain/`
  (`EMERGENCY_RESPONSE`, `NO_DOCUMENTS_RESPONSE`) được bỏ qua để reviewer không thể chặn
  nhầm cảnh báo khẩn cấp. Test `test_fixed_templates_pass_reviewer` bảo đảm các câu cố định
  vẫn qua được luật nếu sau này luật thay đổi.
- **Fail-closed**: nếu reviewer ném lỗi, hệ thống trả `UNSAFE_ANSWER_RESPONSE` thay vì
  câu chưa được kiểm; request vẫn thành công và lỗi được ghi trong trace.
- **Trace**: thêm step `answer_review` (`step_order=2`) với `status`
  (`allowed`/`blocked`/`skipped`/`error`), `reason`, `matched_rules`, `final_answer`, và
  `blocked_answer` (câu gốc bị chặn) để rà soát chặn nhầm. Step 1 vẫn lưu câu trả lời do
  nhánh route tạo ra.
- **API không đổi**: response vẫn gồm `answer`, `trace_id`, `duration_ms`.

Đây là bộ luật từ khóa/regex ban đầu: có thể chặn nhầm hoặc bỏ sót cách diễn đạt chưa có
trong luật; khi gặp, bổ sung mẫu vào `_UNSAFE_RULES` kèm test tương ứng.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\domain\test_answer_review.py tests\application\test_chat_service.py -q
```

### Xử lý tài liệu

Module `infrastructure.document_processing` đọc PDF, DOCX, HTML và TXT, giữ văn bản thô,
chuẩn hóa thận trọng các ký tự điều khiển và loại dòng lặp ở lề PDF. Kết quả
được ghi thành cặp `.txt`/`.json` theo thư mục nguồn; file gốc không bị sửa.
Lệnh trích xuất này chưa thực hiện OCR, chia chunk hoặc embedding. Hãy rà soát các cảnh báo
`OCR_REQUIRED`, `HIGH_TEXT_REDUCTION`, `CLEANED_TEXT_EMPTY` và `LOW_TEXT_VOLUME`
trước khi đưa tài liệu vào bước tiếp theo.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\infrastructure\document_processing -q
.\.venv\Scripts\python.exe -m infrastructure.document_processing.cli `
    --input .\data\manuals\files `
    --output .\data\processed\extracted
```

### Nạp dữ liệu vào RAG

Sau khi Docker PostgreSQL đã chạy và migration đã hoàn tất, nạp toàn bộ tài liệu
vào pgvector bằng một lệnh từ thư mục gốc project:

```powershell
.\.venv\Scripts\python.exe -m infrastructure.rag.ingest data/manuals
```

Lệnh quét đệ quy các định dạng được hỗ trợ, làm sạch và chia văn bản thành các
chunk, tạo embedding trên CPU, rồi upsert các chunk vào bảng `chunks`. Dòng JSON
cuối cùng có `files`, `chunks`, và `duration_seconds`; với bộ dữ liệu hiện tại,
`files` phải là `30`. Có thể giảm/tăng số chunk mỗi lô bằng `--batch-size 16`.

Mỗi chunk được lưu kèm metadata chuẩn hoá `device` và `brand`. Retriever tự nhận
diện các cụm như `nồi cơm điện`, `máy giặt`, `tủ lạnh` và các hãng được hỗ trợ
trong câu hỏi; điều kiện metadata được áp dụng trước khi xếp hạng cosine. Caller
có thể truyền chính xác hơn qua `retrieve(..., device="rice_cooker",
brand="panasonic")`. Khi không nhận diện được, retriever không lọc để tránh làm
mất kết quả của câu hỏi chung chung.

## 5. Chạy kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Docker PostgreSQL và Ollama cần hoạt động đối với các integration test sử dụng dịch vụ thật.
Các test này được đánh dấu `@pytest.mark.integration` (đăng ký trong `pytest.ini`).
Chỉ chạy unit test (nhanh, không cần Docker/Ollama):

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not integration" -q
```

### CI trên GitHub

`.github/workflows/ci.yml` chạy tự động khi push lên `main` hoặc mở Pull Request vào `main`:
cài Python 3.11, torch bản CPU, `requirements.txt`, rồi chạy `pytest -m "not integration"`.
Kết quả xem ở tab **Actions** của repository. Test mới cần PostgreSQL/Ollama thật phải thêm
`pytestmark = pytest.mark.integration`, nếu không CI sẽ fail vì không có các dịch vụ đó.

`requirements.txt` phải được lưu ở UTF-8. Khi thêm thư viện, hãy thêm dòng mới bằng editor;
tránh `pip freeze > requirements.txt` trong Windows PowerShell 5.1 vì lệnh này tạo file UTF-16
(GitHub hiển thị file như dữ liệu nhị phân và không xem được diff).

## 6. Database

PostgreSQL được chạy qua Docker Compose. Database local mặc định là `elec_agent`.

Các bảng Trace và TraceStep được tạo bởi Alembic:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Không cần chạy lại `alembic init` khi repository đã có cấu hình và migration.

## 7. Lưu ý

- `.env` là cấu hình riêng của máy, không được commit.
- `.env.example` là file mẫu cần được duy trì trong repository.
- Không sử dụng credential mặc định cho môi trường production.
- Không đưa dữ liệu cá nhân hoặc thông tin nhạy cảm vào các request thử nghiệm.
- Tài liệu của bên thứ ba cần ghi nguồn và tuân thủ điều kiện sử dụng/redistribution tương ứng.
