up:
	docker compose up -d

down:
	docker compose down -v

# Lệnh "Xây lại từ đầu"
# Khởi động theo thứ tự để tránh I/O spike trên ổ USB gây kernel panic
reset:
	docker compose down -v
	find ./src/infrastructure/postgres_data -mindepth 1 -delete 2>/dev/null || true
	find ./src/infrastructure/mongo_data -mindepth 1 -delete 2>/dev/null || true
	find ./src/infrastructure/debezium_data -mindepth 1 -delete 2>/dev/null || true
	docker compose up -d emr-db rabbitmq fhir-store
	@echo "Chờ DB khởi động ổn định trước khi bật các service còn lại..."
	sleep 15
	docker compose up -d
	@echo "Đã dọn sạch và khởi động lại hệ thống!"

logs:
	docker compose logs -f

# HL7 FHIR Validator CLI
VALIDATOR_JAR = src/fhir-adapter-service/validator_cli.jar
VALIDATOR_VERSION = 6.4.0
VALIDATOR_URL = https://github.com/hapifhir/org.hl7.fhir.core/releases/download/$(VALIDATOR_VERSION)/validator_cli.jar

download-validator:
	@if [ -f $(VALIDATOR_JAR) ]; then \
		echo "validator_cli.jar already exists"; \
	else \
		echo "Downloading HL7 FHIR Validator CLI v$(VALIDATOR_VERSION)..."; \
		curl -L -o $(VALIDATOR_JAR) $(VALIDATOR_URL); \
		echo "Downloaded to $(VALIDATOR_JAR)"; \
	fi

validate:
	cd src/fhir-adapter-service && python3 validate_fhir_batch.py --compare --output validation_report.json

validate-pydantic:
	cd src/fhir-adapter-service && python3 validate_fhir_batch.py --pydantic-only

validate-hl7:
	cd src/fhir-adapter-service && python3 validate_fhir_batch.py --output validation_report.json

# HAPI FHIR Server
hapi-ui:
	@echo "HAPI FHIR UI: http://localhost:8080"
	@echo "FHIR API:     http://localhost:8080/fhir"
	@echo "Metadata:     http://localhost:8080/fhir/metadata"

# Benchmark
benchmark:
	cd src/fhir-adapter-service && python3 benchmark.py --output results/ --push

benchmark-1:
	cd src/fhir-adapter-service && python3 benchmark.py -e 1 --output results/ --push

benchmark-2:
	cd src/fhir-adapter-service && python3 benchmark.py -e 2 --output results/ --push

benchmark-3:
	cd src/fhir-adapter-service && python3 benchmark.py -e 3 --output results/ --push

benchmark-4:
	cd src/fhir-adapter-service && python3 benchmark.py -e 4 --output results/ --push

benchmark-5:
	cd src/fhir-adapter-service && python3 benchmark.py -e 5 --output results/ --push

# Grafana
grafana:
	@echo "Grafana:      http://localhost:3000  (admin/admin)"
	@echo "Pushgateway:  http://localhost:9091"
	@echo "Prometheus:   http://localhost:9090"

# Push kết quả benchmark cũ lên Grafana
# Dùng: make push-results FILE=src/fhir-adapter-service/results/benchmark_xxx.json
# Hoặc: make push-latest  (tự chọn file mới nhất)
push-results:
	cd src/fhir-adapter-service && python3 push_results.py $(if $(FILE),$(CURDIR)/$(FILE),)

push-latest:
	cd src/fhir-adapter-service && python3 push_results.py
