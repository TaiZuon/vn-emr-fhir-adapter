import pika
import json
import time
import sys
from transform_engine import TransformEngine
from reference_manager import ref_manager
from validator import FHIRValidator
from database_mongo import fhir_store
from utils.metrics import monitor_adapter, start_metrics_server
from utils.logger import log

# Khởi tạo Engine ánh xạ
engine = TransformEngine("transform_rules.json")

@monitor_adapter
def process_event(ch, method, properties, body):
    """
    Quy trình 5 bước theo nghiên cứu MDPI:
    PreHandle -> Transform -> Reference -> [Validation] -> Store
    """
    try:
        log.info(f"[DEBUG] Received message with routing key: {method.routing_key}")
        # 1. PreHandle: Giải mã tin nhắn chuẩn (op, after, source)
        message = json.loads(body)
        op = message.get("op") # 'c' (create), 'u' (update)
        data = message.get("after")
        table = message.get("source", {}).get("table")

        if not data or not table:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        log.debug(f"Bắt sự kiện: {op.upper()} trên bảng '{table}'")

        # 2. Transform Module: Sử dụng Rule Engine
        fhir_resource = engine.convert(table, data)

        # print(f"[DEBUG] {fhir_resource}")

        if fhir_resource:
            # 3. Reference & Store Module (Task 3.4 sẽ kết nối MongoDB thật)
            is_valid, error_msg = FHIRValidator.validate(fhir_resource)
            res_type = fhir_resource.__class__.__name__
            if not is_valid:
                log.error(f"Validation failed: {error_msg}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            log.debug(f"Validation thành công cho {res_type}")

            # fhir_id = f"fhir_id_mock_{data['id']}" 
            mongo_id = fhir_store.save_resource(fhir_resource)

            if mongo_id:
            # Lưu vào cache tham chiếu để dùng cho các bản ghi liên quan sau này
                ref_manager.add_mapping(res_type, data['id'], mongo_id)

                log.info(f"Đã lưu {res_type} vào MongoDB với ID: {mongo_id}")

            # In thử JSON chuẩn FHIR để kiểm tra
            log.debug(f"FHIR Resource JSON:\n{fhir_resource.json(indent=2)}")

        # Xác nhận xử lý xong
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        log.error(f"Lỗi hệ thống: {e}")
        # Không Ack để tin nhắn chờ xử lý lại nếu lỗi hạ tầng
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        time.sleep(2)

def start_adapter():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='emr_events', durable=True)
        channel.queue_bind(queue='emr_events', exchange='amq.topic', routing_key='emr_events')
        channel.basic_qos(prefetch_count=1)

        log.info('FHIR ADAPTER đang chạy. Đợi dữ liệu từ EMR...')
        channel.basic_consume(queue='emr_events', on_message_callback=process_event)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        log.warning("RabbitMQ chưa sẵn sàng, thử lại sau 5s...")
        time.sleep(5)
        start_adapter()

if __name__ == '__main__':
    try:
        start_metrics_server(port=8008)
        start_adapter()
    except KeyboardInterrupt:
        log.info('Dừng Adapter.')
        sys.exit(0)
