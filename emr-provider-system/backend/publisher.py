import pika
import json
import datetime
from constants import RABBITMQ_HOST, RABBITMQ_QUEUE_NAME, RABBITMQ_DELIVERY_MODE


def publish_event(routing_key, message):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()

        # Khai báo hàng đợi (Queue)
        channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)

        # Timestamp cho sự kiện
        message['timestamp'] = datetime.datetime.now().isoformat()

        # Publish tin nhắn vào hàng đợi
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE_NAME,
            body=json.dumps(message),
            # Đảm bảo tin nhắn không mất khi server crash
            properties=pika.BasicProperties(
                delivery_mode=RABBITMQ_DELIVERY_MODE,
                content_type='application/json'),
        )
        # test a lil bit
        print(f"Published event to {RABBITMQ_QUEUE_NAME}: {message}")
        connection.close()
        
    except Exception as e:
        print(f"Error publishing event: {e}")
