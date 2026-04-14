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

# ========== Cấu hình Dead Letter Queue (DLQ) ==========
DLQ_EXCHANGE = 'emr_events.dlx'        # Dead Letter Exchange
DLQ_QUEUE = 'emr_events.dlq'           # Dead Letter Queue
DLQ_ROUTING_KEY = 'emr_events.dead'    # Routing key cho DLQ
MAX_RETRY_COUNT = 3                     # Số lần retry tối đa trước khi chuyển vào DLQ

# Khởi tạo Engine ánh xạ bằng DAG
compiler = DAGCompiler("transform_rules.json")
dag = compiler.compile()

# Khởi tạo PreHandler để micro-batching
prehandler = DataPreHandler(batch_size=50, timeout_seconds=5.0)

# Parallel list theo dõi properties của từng message trong buffer
_properties_buffer = []

def get_retry_count(properties):
    """Lấy số lần retry từ message headers."""
    if properties and properties.headers:
        return properties.headers.get('x-retry-count', 0)
    return 0

def publish_to_dlq(channel, body, properties, reason):
    """Đẩy message lỗi vào Dead Letter Queue kèm metadata debug."""
    headers = dict(properties.headers) if properties and properties.headers else {}
    headers['x-dlq-reason'] = str(reason)[:500]
    headers['x-dlq-timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    headers['x-retry-count'] = headers.get('x-retry-count', 0)

    dlq_properties = pika.BasicProperties(
        delivery_mode=2,  # persistent
        headers=headers
    )
    channel.basic_publish(
        exchange=DLQ_EXCHANGE,
        routing_key=DLQ_ROUTING_KEY,
        body=body,
        properties=dlq_properties
    )
    log.warning(f"Message chuyển vào DLQ. Lý do: {str(reason)[:200]}")

def process_batch(channel, batch, delivery_tags, batch_properties=None):
    """
    Xử lý một lô dữ liệu đã được PreHandle: Transform -> Validate -> Store
    Nếu lỗi từng item -> DLQ. Nếu lỗi hệ thống -> requeue hoặc DLQ tùy retry count.
    """
    if not batch:
        return
    
    try:
        for idx, item in enumerate(batch):
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
                # Lỗi transform -> đẩy vào DLQ
                props = batch_properties[idx] if batch_properties and idx < len(batch_properties) else None
                publish_to_dlq(channel, json.dumps(item).encode(), 
                             props or pika.BasicProperties(), 
                             f"Pydantic model error ({res_type}): {e}")
                continue

            # 3. & 5. Validation Module
            is_valid, error_msg = FHIRValidator.validate(fhir_resource)
            if not is_valid:
                log.error(f"Validation failed for {res_type}: {error_msg}")
                # Lỗi validation -> đẩy vào DLQ
                props = batch_properties[idx] if batch_properties and idx < len(batch_properties) else None
                publish_to_dlq(channel, json.dumps(item).encode(),
                             props or pika.BasicProperties(),
                             f"FHIR validation failed ({res_type}): {error_msg}")
                continue
                
            log.debug(f"Validation thành công cho {res_type}")

            # 4. Store Module
            mongo_id = fhir_store.save_resource(fhir_resource)

            if mongo_id:
                # Lấy EMR key: ưu tiên ma_lk (dot_dieu_tri), rồi id (các bảng khác)
                emr_key = data.get('ma_lk', data.get('id'))
                ref_manager.add_mapping(res_type, emr_key, mongo_id)
                
                # Khi lưu Encounter, tạo thêm mapping ngược EncounterPatient
                # để các resource con (MedicationRequest, Procedure...) resolve được Patient từ dot_dieu_tri_id
                if res_type == 'Encounter' and data.get('benh_nhan_id'):
                    patient_ref = ref_manager.resolve('Patient', data['benh_nhan_id'])
                    if patient_ref:
                        # patient_ref = "Patient/emr-182" -> lấy "emr-182"
                        patient_id = patient_ref.split('/')[-1]
                        ref_manager.add_mapping('EncounterPatient', emr_key, patient_id)
                
                log.info(f"Đã lưu {res_type} vào MongoDB với ID: {mongo_id}")
                
        # Tất cả resource trong batch đã được process thành công, ta tiến hành ACK
        for tag in delivery_tags:
            channel.basic_ack(delivery_tag=tag)
            
        log.info(f" Đã xử lý và ACK thành công {len(delivery_tags)} sự kiện.")
        
    except Exception as e:
        log.error(f"Lỗi hệ thống khi xử lý batch: {e}")
        # Lỗi hệ thống (DB down, network...) -> kiểm tra retry count
        for i, tag in enumerate(delivery_tags):
            props = batch_properties[i] if batch_properties and i < len(batch_properties) else None
            retry_count = get_retry_count(props)
            if retry_count >= MAX_RETRY_COUNT:
                # Đã retry quá nhiều lần -> DLQ
                channel.basic_ack(delivery_tag=tag)
                item_body = json.dumps(batch[i]).encode() if i < len(batch) else b'{}'
                publish_to_dlq(channel, item_body, 
                             props or pika.BasicProperties(),
                             f"Max retries ({MAX_RETRY_COUNT}) exceeded. Last error: {e}")
            else:
                # Còn lượt retry -> requeue
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
        _properties_buffer.append(properties)
        batch, tags = prehandler.add_event(message, method.delivery_tag)
        if batch:
            props_snapshot = _properties_buffer.copy()
            _properties_buffer.clear()
            process_batch(ch, batch, tags, batch_properties=props_snapshot)

    except json.JSONDecodeError as e:
        log.error(f"Message không phải JSON hợp lệ: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        publish_to_dlq(ch, body, properties, f"Invalid JSON: {e}")
    except Exception as e:
        log.error(f"Lỗi khi tiếp nhận tin nhắn: {e}")
        retry_count = get_retry_count(properties)
        if retry_count >= MAX_RETRY_COUNT:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            publish_to_dlq(ch, body, properties, f"Max retries exceeded: {e}")
        else:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def setup_dlq(channel):
    """
    Khai báo Dead Letter Exchange + Dead Letter Queue.
    Messages bị reject/expire từ emr_events sẽ tự động route vào đây.
    """
    # 1. Khai báo DLX (Dead Letter Exchange) — fanout để đảm bảo mọi message đều vào DLQ
    channel.exchange_declare(
        exchange=DLQ_EXCHANGE,
        exchange_type='fanout',
        durable=True
    )

    # 2. Khai báo DLQ (Dead Letter Queue) — persistent, không TTL
    channel.queue_declare(
        queue=DLQ_QUEUE,
        durable=True,
        arguments={
            'x-queue-type': 'classic'
        }
    )

    # 3. Bind DLQ vào DLX
    channel.queue_bind(
        queue=DLQ_QUEUE,
        exchange=DLQ_EXCHANGE,
        routing_key=DLQ_ROUTING_KEY
    )

    log.info(f"DLQ đã sẵn sàng: {DLQ_EXCHANGE} -> {DLQ_QUEUE}")

def start_adapter():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        # Khai báo DLQ trước
        setup_dlq(channel)

        # Khai báo queue chính với DLX policy
        # Lưu ý: Nếu queue đã tồn tại mà không có DLX, cần xóa queue cũ trước
        # hoặc thêm DLX policy qua RabbitMQ Management UI
        try:
            channel.queue_declare(
                queue='emr_events',
                durable=True,
                arguments={
                    'x-dead-letter-exchange': DLQ_EXCHANGE,
                    'x-dead-letter-routing-key': DLQ_ROUTING_KEY
                }
            )
        except pika.exceptions.ChannelClosedByBroker:
            # Queue đã tồn tại với arguments khác -> dùng queue hiện có
            log.warning("Queue 'emr_events' đã tồn tại. Sử dụng queue hiện có (DLQ sẽ hoạt động qua publish thủ công).")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
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
                props_snapshot = _properties_buffer.copy()
                _properties_buffer.clear()
                # We are safely on the main Pika loop thread here, so we can process and ACK
                process_batch(channel, batch, tags, batch_properties=props_snapshot)
                
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
