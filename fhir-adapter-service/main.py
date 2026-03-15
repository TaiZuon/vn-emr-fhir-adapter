import pika
import json
import time
import sys


def process_event(ch, method, properties, body):
    """
    Hàm callback xử lý tin nhắn khi nhận được từ RabbitMQ
    """
    try:
        # Giải mã tin nhắn
        event = json.loads(body)
        event_type = event.get("event_type")
        resource_id = event.get("id")

        print(f" [⚡] Đã nhận sự kiện: {event_type} | ID gốc: {resource_id}")

        # Giả lập thời gian xử lý (Mapping sẽ viết ở Task 3.2)
        print(
            f" [🔄] Đang chuẩn bị chuyển đổi Resource {event.get('resource_type')}..."
        )
        time.sleep(1)

        print(f" [✅] Xử lý xong sự kiện ID: {resource_id}")

        # Xác nhận đã xử lý xong (Ack)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [❌] Lỗi xử lý sự kiện: {e}")
        # Nếu lỗi, có thể chọn không Ack để tin nhắn quay lại hàng đợi (Nack)
        # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_worker():
    try:
        # Kết nối tới RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost")
        )
        channel = connection.channel()

        # Khai báo hàng đợi
        channel.queue_declare(queue="emr_events", durable=True)

        # Cấu hình QoS: Mỗi lần chỉ nhận 1 tin nhắn (Tránh quá tải)
        channel.basic_qos(prefetch_count=1)

        print(" [*] Worker đang đợi tin nhắn từ HIS. Nhấn CTRL+C để thoát.")

        # Đăng ký hàm callback
        channel.basic_consume(queue="emr_events", on_message_callback=process_event)

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print(" [!] Không thể kết nối RabbitMQ. Đang thử lại sau 5 giây...")
        time.sleep(5)
        start_worker()


if __name__ == "__main__":
    try:
        start_worker()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
