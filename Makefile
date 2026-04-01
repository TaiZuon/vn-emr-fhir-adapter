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
