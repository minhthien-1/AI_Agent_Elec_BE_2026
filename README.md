# Elec-Agent Backend

Elec-Agent là backend hỗ trợ người dùng tham khảo và khắc phục các vấn đề thông thường của thiết bị điện gia dụng. Hệ thống sử dụng FastAPI, Ollama với model `qwen2.5:3b` và PostgreSQL/pgvector.

## 1. Yêu cầu hệ thống

Trước khi bắt đầu, cài đặt:

- Git
- Python 3.9 64-bit
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

- `api/`: FastAPI routers và request/response schemas.
- `agent/`: logic điều phối lượt chat.
- `llm/`: Ollama client.
- `db/`: SQLAlchemy database và models.
- `tools/`: TraceService.
- `alembic/`: database migrations.
- `tests/`: automated tests.
- `data/manuals/`: chỉ mục nguồn tài liệu và tài liệu tham khảo cục bộ.

## 5. Chạy kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Docker PostgreSQL và Ollama cần hoạt động đối với các integration test sử dụng dịch vụ thật.

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
