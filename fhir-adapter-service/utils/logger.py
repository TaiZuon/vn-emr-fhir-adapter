# fhir-adapter-service/utils/logger.py
from loguru import logger
import sys
import os

# 1. Tạo thư mục chứa log nếu chưa có
os.makedirs("logs", exist_ok=True)

# 2. Xóa cấu hình mặc định của loguru
logger.remove()

# 3. Thêm Handler in ra màn hình (Console) - Để em nhìn lúc dev
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 4. Thêm Handler lưu vào File - Để sau này "bơm" lên Grafana Loki
logger.add(
    "logs/adapter.log",
    rotation="10 MB",    # File đủ 10MB thì tự đổi sang file mới
    retention="7 days",  # Chỉ giữ log trong vòng 7 ngày cho nhẹ máy
    compression="zip",   # Nén log cũ lại cho tiết kiệm dung lượng
    level="DEBUG",       # Lưu chi tiết hơn vào file để dễ "bắt bệnh"
    encoding="utf-8"
)

# Export ra để dùng ở các file khác
log = logger
