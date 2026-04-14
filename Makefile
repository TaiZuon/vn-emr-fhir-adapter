# Định nghĩa các lệnh tắt
up:
	docker compose up -d

down:
	docker compose down -v

# Lệnh "Xây lại từ đầu"
reset:
	docker compose down -v
	sudo rm -rf ./infrastructure/postgres_data/*
	sudo rm -rf ./infrastructure/mongo_data/*
	sudo rm -rf ./infrastructure/debezium_data/*
	docker compose up -d
	@echo "🔥 Đã dọn sạch và khởi động lại hệ thống!"

logs:
	docker compose logs -f

# HL7 FHIR Validator CLI
VALIDATOR_JAR = fhir-adapter-service/validator_cli.jar
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
	cd fhir-adapter-service && python3 validate_fhir_batch.py --compare --output validation_report.json

validate-pydantic:
	cd fhir-adapter-service && python3 validate_fhir_batch.py --pydantic-only

validate-hl7:
	cd fhir-adapter-service && python3 validate_fhir_batch.py --output validation_report.json
