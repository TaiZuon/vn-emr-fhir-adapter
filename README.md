# vn-emr-fhir-adapter

Hệ thống middleware chuyển đổi và liên thông dữ liệu bệnh án điện tử (EMR) Việt Nam sang tiêu chuẩn HL7 FHIR R5, sử dụng kiến trúc hướng sự kiện (CDC → RabbitMQ → Transform → Validate → Encrypt → Dual-write).

## Cấu trúc Repository

```
/
├── src/                          # Toàn bộ mã nguồn
│   ├── emr-provider-system/      # Hệ thống EMR nguồn (FastAPI + PostgreSQL)
│   │   ├── backend/              # API server (FastAPI)
│   │   └── database/             # SQL schema khởi tạo
│   ├── fhir-adapter-service/     # Dịch vụ adapter chính
│   │   ├── main.py               # Consumer RabbitMQ + pipeline chính
│   │   ├── dag_engine.py         # DAG transform engine
│   │   ├── dag_compiler.py       # Biên dịch transform_rules.json → DAG
│   │   ├── transform_rules.json  # Khai báo ánh xạ EMR → FHIR
│   │   ├── crypto_service.py     # Mã hóa AES-256-GCM
│   │   ├── validator.py          # Xác thực Pydantic + HL7 CLI
│   │   ├── fhir_client.py        # Ghi vào HAPI FHIR Server
│   │   ├── database_mongo.py     # Ghi vào MongoDB
│   │   ├── terminology/          # Bảng ánh xạ thuật ngữ y tế
│   │   ├── results/              # Kết quả benchmark
│   │   └── benchmark.py          # Bộ thí nghiệm đánh giá (TN1–TN5)
│   └── infrastructure/           # Cấu hình hạ tầng
│       ├── debezium_conf/        # Cấu hình Debezium CDC
│       ├── grafana/              # Dashboard Grafana
│       └── prometheus.yml        # Cấu hình Prometheus
├── references/                   # Tài liệu tham khảo (PDF, bài báo)
├── docker-compose.yml            # Khởi động toàn bộ hệ thống
├── Makefile                      # Lệnh tắt tiện ích
├── requirements.txt              # Python dependencies
└── README.md
```

## Yêu cầu hệ thống

- **Docker** ≥ 24.0 và **Docker Compose** ≥ 2.20
- **Python** ≥ 3.10 (để chạy adapter và benchmark trực tiếp)
- **Java** ≥ 11 (để chạy HL7 FHIR Validator CLI)
- RAM tối thiểu: 4 GB (khuyến nghị 8 GB để chạy đầy đủ stack)

## Cài đặt môi trường

### 1. Clone repository

```bash
git clone <repo-url>
cd vn-emr-fhir-adapter
```

### 2. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc (hoặc chỉnh sửa file `.env` có sẵn):

```env
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

MONGO_URI=mongodb://localhost:27017
MONGO_DB=fhir_store

HAPI_FHIR_BASE=http://localhost:8080/fhir

ENCRYPT_KEY=<32-byte hex key cho AES-256-GCM>
```

### 3. Tạo môi trường ảo Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Tải HL7 FHIR Validator CLI

```bash
make download-validator
```

Lệnh này tải `validator_cli.jar` (~300 MB) vào `src/fhir-adapter-service/`.

## Cách chạy hệ thống

### Khởi động toàn bộ hạ tầng (Docker)

```bash
make up
# hoặc
docker compose up -d
```

Dịch vụ sẽ khởi động:

| Dịch vụ | URL | Mô tả |
|---|---|---|
| EMR PostgreSQL | `localhost:5432` | Database nguồn EMR |
| RabbitMQ | `localhost:15672` | Message broker (UI: guest/guest) |
| MongoDB | `localhost:27017` | FHIR Store |
| HAPI FHIR Server | `localhost:8080/fhir` | FHIR REST API (R5) |
| Mongo Express | `localhost:8081` | MongoDB UI |
| Prometheus | `localhost:9090` | Metrics |
| Grafana | `localhost:3000` | Dashboard (admin/admin) |
| Pushgateway | `localhost:9091` | Nhận metrics từ benchmark |

### Chạy EMR Provider (API nguồn)

```bash
source venv/bin/activate
cd src/emr-provider-system/backend
uvicorn main:app --reload --port 8000
```

API docs tại: `http://localhost:8000/docs`

### Chạy FHIR Adapter Service

```bash
source venv/bin/activate
cd src/fhir-adapter-service
python main.py
```

Adapter sẽ lắng nghe queue RabbitMQ, transform và ghi dữ liệu FHIR vào MongoDB + HAPI server.

### Reset hệ thống (xóa toàn bộ dữ liệu)

```bash
make reset
```

## Chạy Benchmark (TN1–TN5)

```bash
# Tất cả thí nghiệm
make benchmark

# Từng thí nghiệm riêng
make benchmark-1   # TN1: Tính đúng đắn chuyển đổi
make benchmark-2   # TN2: Hiệu năng & khả năng mở rộng
make benchmark-3   # TN3: Chi phí mã hóa AES-256-GCM
make benchmark-4   # TN4: Phân tích bottleneck pipeline
make benchmark-5   # TN5: Hiệu quả song song hóa DAG
```

Kết quả JSON được lưu vào `src/fhir-adapter-service/results/`.

## Xác thực FHIR

```bash
# Xác thực cả Pydantic và HL7 CLI
make validate

# Chỉ Pydantic
make validate-pydantic

# Chỉ HL7 CLI
make validate-hl7
```

## Giám sát

```bash
make grafana
# → Grafana:     http://localhost:3000  (admin/admin)
# → Pushgateway: http://localhost:9091
# → Prometheus:  http://localhost:9090
```

Dashboard `Benchmark Results` trong Grafana hiển thị kết quả TN1–TN5 theo thời gian thực.

## Ghi chú

- `src/infrastructure/` bị loại khỏi git tracking (chứa dữ liệu runtime của PostgreSQL, MongoDB, Debezium). Cấu hình tĩnh trong `debezium_conf/` và `grafana/` vẫn được track.
- `validator_cli.jar` (~300 MB) bị loại khỏi git tracking — cần tải lại bằng `make download-validator`.
- Thư mục `references/` dùng để lưu tài liệu tham khảo (PDF, bài báo khoa học).
