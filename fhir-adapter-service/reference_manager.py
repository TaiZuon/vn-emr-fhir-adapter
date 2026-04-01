# fhir-adapter-service/reference_manager.py
from pymongo import MongoClient
import os

class ReferenceManager:
    def __init__(self, uri=None, db_name="fhir_db"):
        # Lấy URI từ biến môi trường hoặc dùng default (localhost)
        # Trong Docker-compose, service mongo tên là 'fhir-store'
        mongo_uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        # Tạo một collection riêng để lưu mapping ID
        self.collection = self.db["id_mappings"]
        
        # Đảm bảo index cho tốc độ truy vấn cao
        self.collection.create_index([("_id", 1)])
        print(f" [connected] ReferenceManager: Đã kết nối MongoDB mapping tại {db_name}")

    def add_mapping(self, resource_type: str, local_id: str, fhir_id: str):
        """
        Lưu hoặc cập nhật ánh xạ ID.
        Key (_id): "Patient:1"
        Value: "fhir_mongo_id_abc"
        """
        mapping_id = f"{resource_type}:{local_id}"
        try:
            self.collection.replace_one(
                {"_id": mapping_id},
                {
                    "_id": mapping_id,
                    "resource_type": resource_type,
                    "local_id": str(local_id),
                    "fhir_id": fhir_id
                },
                upsert=True
            )
        except Exception as e:
            print(f" [❌] ReferenceManager Error (Add): {e}")

    def resolve(self, resource_type: str, local_id: str) -> str:
        """
        Tìm kiếm FHIR ID dựa trên ResourceType và LocalID.
        Trả về chuỗi FHIR Reference: "Patient/fhir_mongo_id_abc"
        """
        mapping_id = f"{resource_type}:{local_id}"
        try:
            mapping = self.collection.find_one({"_id": mapping_id})
            if mapping:
                return f"{resource_type}/{mapping['fhir_id']}"
            return None
        except Exception as e:
            print(f" [❌] ReferenceManager Error (Resolve): {e}")
            return None

# Khởi tạo instance duy nhất để các module khác import và dùng chung
ref_manager = ReferenceManager()
