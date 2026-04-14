# fhir-adapter-service/database_mongo.py
from pymongo import MongoClient
from fhir_client import hapi_client
import json

class FHIRStore:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="fhir_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.hapi_enabled = hapi_client.is_available()
        print(f" [connected] Đã kết nối MongoDB: {db_name}")
        if self.hapi_enabled:
            print(f" [connected] HAPI FHIR Server sẵn sàng (dual-write mode)")
        else:
            print(f" [info] HAPI FHIR Server không khả dụng (MongoDB-only mode)")

    def save_resource(self, resource_obj):
        """
        Lưu FHIR Resource — dual-write strategy:
          1. MongoDB (luôn luôn) — backup + ID mapping
          2. HAPI FHIR Server (nếu available) — chuẩn FHIR REST API
        """
        try:
            resource_type = resource_obj.__class__.__name__
            collection = self.db[resource_type]

            resource_data = json.loads(resource_obj.json())

            if 'id' in resource_data:
                resource_data['_id'] = resource_data['id']

            # 1. Luôn lưu vào MongoDB
            collection.replace_one(
                {'_id': resource_data['_id']},
                resource_data,
                upsert=True
            )
            
            inserted_id = resource_data['_id']
            print(f" [💾] MongoDB: Đã lưu {resource_type} với ID: {inserted_id}")

            # 2. Gửi lên HAPI FHIR Server (nếu available)
            if self.hapi_enabled:
                hapi_id = hapi_client.save_resource(resource_obj)
                if hapi_id:
                    print(f" [🏥] HAPI: Đã lưu {resource_type}/{hapi_id}")
                else:
                    # HAPI lỗi nhưng MongoDB đã lưu OK -> không fatal
                    print(f" [⚠] HAPI: Lưu {resource_type} thất bại (MongoDB vẫn OK)")

            return inserted_id

        except Exception as e:
            print(f" [❌] Lỗi lưu trữ: {e}")
            return None

# Khởi tạo instance dùng chung
fhir_store = FHIRStore()
