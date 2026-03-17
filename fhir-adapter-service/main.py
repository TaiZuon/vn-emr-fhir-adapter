import pika
import json
import time
import sys
from transform_engine import TransformEngine
from reference_manager import ref_manager
from validator import FHIRValidator

# Khởi tạo Engine ánh xạ
engine = TransformEngine("transform_rules.json")

def process_event(ch, method, properties, body):
    """
    Quy trình 5 bước theo nghiên cứu MDPI:
    PreHandle -> Transform -> Reference -> [Validation] -> Store
    """
    try:
        # 1. PreHandle: Giải mã tin nhắn chuẩn (op, after, source)
        message = json.loads(body)
        op = message.get("op") # 'c' (create), 'u' (update)
        data = message.get("after")
        table = message.get("source", {}).get("table")

        if not data or not table:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"\n{'='*50}")

        print(f" [⚡] {time.strftime('%H:%M:%S')} | Bắt sự kiện: {op.upper()} trên bảng '{table}'")

        # 2. Transform Module: Sử dụng Rule Engine
        fhir_resource = engine.convert(table, data)

        # print(f"[DEBUG] {fhir_resource}")

        if fhir_resource:
            # 3. Reference & Store Module (Task 3.4 sẽ kết nối MongoDB thật)
            # Hiện tại giả lập ID MongoDB trả về
            is_valid, error_msg = FHIRValidator.validate(fhir_resource)

            if not is_valid:
                print(f" [❌] Validation failed: {error_msg}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            fhir_id = f"fhir_id_mock_{data['id']}" 
            
            print(f" [✅] Validation thành công cho {fhir_resource.__class__.__name__} với ID: {fhir_id}")

            # Lưu vào cache tham chiếu để dùng cho các bản ghi liên quan sau này
            res_type = fhir_resource.__class__.__name__
            ref_manager.add_mapping(res_type, data['id'], fhir_id)

            print(f" [✅] Chuyển đổi thành công {res_type}")
            # In thử JSON chuẩn FHIR để kiểm tra
            print(fhir_resource.json(indent=2))

        # Xác nhận xử lý xong
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [❌] Lỗi hệ thống: {e}")
        # Không Ack để tin nhắn chờ xử lý lại nếu lỗi hạ tầng
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        time.sleep(2)

def start_adapter():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='emr_events', durable=True)
        channel.basic_qos(prefetch_count=1)

        print(' [*] FHIR ADAPTER đang chạy. Đợi dữ liệu từ EMR...')
        channel.basic_consume(queue='emr_events', on_message_callback=process_event)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print(" [!] RabbitMQ chưa sẵn sàng, thử lại sau 5s...")
        time.sleep(5)
        start_adapter()

if __name__ == '__main__':
    try:
        start_adapter()
    except KeyboardInterrupt:
        print('Dừng Adapter.')
        sys.exit(0)
