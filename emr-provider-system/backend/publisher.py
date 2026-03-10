import pika
import json
from constants import RABBITMQ_HOST, RABBITMQ_QUEUE_NAME, RABBITMQ_DELIVERY_MODE


def publish_event(routing_key, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Khai báo hàng đợi (Queue)
    channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE_NAME,
        body=json.dumps(message),
        # Đảm bảo tin nhắn không mất khi server crash
        properties=pika.BasicProperties(delivery_mode=RABBITMQ_DELIVERY_MODE),
    )
    connection.close()
