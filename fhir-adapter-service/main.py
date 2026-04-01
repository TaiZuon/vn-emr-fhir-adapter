import pika
import json
import time
import sys
from dag_compiler import DAGCompiler
from fhir.resources import get_fhir_model_class
from reference_manager import ref_manager
from validator import FHIRValidator
from database_mongo import fhir_store
from utils.metrics import monitor_adapter, start_metrics_server
from utils.logger import log
from prehandle_module import DataPreHandler

# Khởi tạo Engine ánh xạ bằng DAG
compiler = DAGCompiler("transform_rules.json")
dag = compiler.compile()

# Khởi tạo PreHandler để micro-batching
prehandler = DataPreHandler(batch_size=50, timeout_seconds=5.0)

def process_batch(channel, batch, delivery_tags):
    """
    Xử lý một lô dữ liệu đã được PreHandle: Transform -> Validate -> Store
    """
    if not batch:
        return
    
    try:
        for item in batch:
            table = item.get("source", {}).get("table")
            data = item.get("after")
            
            # FIX: Gắn routing key (table) vào payload để kích hoạt DAG Condition
            data['_table'] = table
            
            # 2. Transform Module: Sử dụng DAG Engine
            fhir_dict = dag.execute(data)
            if not fhir_dict or "resourceType" not in fhir_dict:
                continue

            res_type = fhir_dict["resourceType"]
            try:
                # FIX: Chuyển đổi Dictionary sang Pydantic Model của FHIR
                ModelClass = get_fhir_model_class(res_type)
                fhir_resource = ModelClass(**fhir_dict)
            except Exception as e:
                log.error(f"Khởi tạo model Pydantic thất bại cho {res_type}: {e}")
                continue

            # 3. & 5. Validation Module
            is_valid, error_msg = FHIRValidator.validate(fhir_resource)
            if not is_valid:
                log.error(f"Validation failed for {res_type}: {error_msg}")
                continue
                
            log.debug(f"Validation thành công cho {res_type}")

            # 4. Store Module
            mongo_id = fhir_store.save_resource(fhir_resource)

            if mongo_id:
                ref_manager.add_mapping(res_type, data['id'], mongo_id)
                log.info(f"Đã lưu {res_type} vào MongoDB với ID: {mongo_id}")
                
        # Tất cả resource trong batch đã được process thành công, ta tiến hành ACK
        for tag in delivery_tags:
            channel.basic_ack(delivery_tag=tag)
            
        log.info(f" Đã xử lý và ACK thành công {len(delivery_tags)} sự kiện.")
        
    except Exception as e:
        log.error(f"Lỗi hệ thống khi xử lý batch: {e}")
        # Không Ack để tin nhắn chờ xử lý lại nếu lỗi hạ tầng
        for tag in delivery_tags:
            channel.basic_nack(delivery_tag=tag, requeue=True)
        time.sleep(2)

@monitor_adapter
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
            # Dữ liệu hỏng hoặc không có bảng -> ACK để drop
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Nạp event vào buffer, nếu trả về batch thì đem xử lý
        batch, tags = prehandler.add_event(message, method.delivery_tag)
        if batch:
            process_batch(ch, batch, tags)

    except Exception as e:
        log.error(f"Lỗi khi tiếp nhận tin nhắn: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_adapter():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='emr_events', durable=True)
        channel.queue_bind(queue='emr_events', exchange='amq.topic', routing_key='emr_events')
        
        # Prefetch larger than 1 to allow accumulation
        channel.basic_qos(prefetch_count=prehandler.batch_size)
    
        def heartbeat_flush():
            """
            Background async heartbeat check. Forcibly flushes trailing messages
            in the buffer if they've sat longer than timeout_seconds.
            """
            current_time = time.time()
            if prehandler.buffer and (current_time - prehandler.last_flush_time) >= prehandler.timeout_seconds:
                log.info(f" Heartbeat timeout reached. Bắt đầu flush thủ công {len(prehandler.buffer)} messages.")
                batch, tags = prehandler.flush()
                # We are safely on the main Pika loop thread here, so we can process and ACK
                process_batch(channel, batch, tags)
                
            # Schedule self again
            connection.call_later(1.0, heartbeat_flush)

        log.info('FHIR ADAPTER đang chạy. Đợi dữ liệu từ EMR...')
        
        # Bắt đầu vòng lặp Heartbeat không đồng bộ (1s/lần)
        connection.call_later(1.0, heartbeat_flush)
        
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
