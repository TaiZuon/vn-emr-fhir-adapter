# fhir-adapter-service/metrics.py
import time
from functools import wraps
from prometheus_client import Counter, Histogram, start_http_server

# 1. Định nghĩa các chỉ số đo lường
# Đếm số lượng task (Thành công/Thất bại)
ADAPTER_TASKS_TOTAL = Counter(
    'fhir_adapter_tasks_total', 
    'Tổng số task xử lý bởi Adapter',
    ['operation', 'status']
)

# Đo thời gian xử lý (Latency)
ADAPTER_LATENCY = Histogram(
    'fhir_adapter_processing_seconds',
    'Thời gian xử lý một bản ghi (giây)',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0] # Các ngưỡng thời gian để theo dõi
)

def monitor_adapter(func):
    """Decorator để tự động đo lường hiệu năng và kết quả xử lý"""
    @wraps(func)
    def wrapper(ch, method, properties, body, *args, **kwargs):
        start_time = time.time()
        # Mặc định coi như thất bại trừ khi chạy hết hàm
        status = "system_error"
        
        try:
            # Thực hiện hàm logic chính (process_event)
            result = func(ch, method, properties, body, *args, **kwargs)
            status = "success"
            return result
        except Exception as e:
            # Nếu hàm ném ra lỗi, status sẽ là system_error
            status = "system_error"
            raise e
        finally:
            # Ghi nhận kết quả vào Prometheus
            duration = time.time() - start_time
            ADAPTER_LATENCY.observe(duration)
            # Lấy operation từ RabbitMQ method (ví dụ: 'c', 'u', 'd')
            # Ở đây ta giả định em có thể lấy op từ message body bên trong 
            # hoặc đơn giản để là 'process'
            ADAPTER_TASKS_TOTAL.labels(operation="process", status=status).inc()
            
    return wrapper

def start_metrics_server(port=8008):
    """Khởi động server để Prometheus vào kéo dữ liệu"""
    start_http_server(port)
    print(f" [📊] Metrics Server đang chạy tại: http://localhost:{port}/metrics")
