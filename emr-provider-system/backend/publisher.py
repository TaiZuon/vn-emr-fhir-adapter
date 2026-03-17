import pika
import json
import datetime
import time
from constants import RABBITMQ_HOST, RABBITMQ_QUEUE_NAME, RABBITMQ_DELIVERY_MODE

def publish_event(operation: str, table_name: str, data_snapshot: dict):
    """
    Publish sự kiện theo định dạng chuẩn của Debezium (CDC).
    - operation: 'c' (create), 'u' (update), 'd' (delete)
    - table_name: Tên bảng trong SQL (vd: 'patients', 'observations')
    - data_snapshot: Toàn bộ dữ liệu của bản ghi sau khi thay đổi (Fat Message)
    """
    
    # Đóng gói Envelope chuẩn
    message = {
        "op": operation,
        "ts_ms": int(time.time() * 1000), # Timestamp dạng mili-giây
        "source": {
            "db": "emr_legacy_db",
            "table": table_name
        },
        "after": data_snapshot
    }

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()

        # Khai báo hàng đợi (Queue)
        channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)

        # Publish tin nhắn vào hàng đợi
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=RABBITMQ_DELIVERY_MODE, # 2 = Persistent
                content_type="application/json"
            ),
        )
        
        print(f" [📤] Đã gửi sự kiện '{operation.upper()}' của bảng '{table_name}' lên RabbitMQ")
        connection.close()

    except Exception as e:
        print(f" [❌] Lỗi khi gửi sự kiện: {e}")