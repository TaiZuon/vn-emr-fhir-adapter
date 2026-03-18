# fhir-adapter-service/database_mongo.py
from pymongo import MongoClient
import json

class FHIRStore:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="fhir_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f" [connected] Đã kết nối MongoDB: {db_name}")

    def save_resource(self, resource_obj):
        """
        Lưu FHIR Resource vào Collection tương ứng dựa trên resourceType.
        """
        try:
            # 1. Lấy tên Resource (Patient, Observation, ...)
            resource_type = resource_obj.__class__.__name__
            collection = self.db[resource_type]

            # # 2. Chuyển đổi Resource Object sang Dictionary
            # # Sử dụng .dict() của pydantic (lõi của fhir.resources)
            # resource_data = resource_obj.dict()

            # Dùng .json() để format ngày tháng thành String trước khi nạp vào Mongo
            # Cách này giúp tránh lỗi datetime.date của PyMongo
            resource_data = json.loads(resource_obj.json())

            # 3. Sử dụng FHIR ID làm MongoDB _id để tránh trùng lặp
            if 'id' in resource_data:
                resource_data['_id'] = resource_data['id']

            # 4. Lưu vào Database (Upsert: Nếu trùng ID thì cập nhật, chưa có thì thêm mới)
            result = collection.replace_one(
                {'_id': resource_data['_id']},
                resource_data,
                upsert=True
            )
            
            inserted_id = resource_data['_id']
            print(f" [💾] MongoDB: Đã lưu {resource_type} với ID: {inserted_id}")
            return inserted_id

        except Exception as e:
            print(f" [❌] Lỗi lưu trữ MongoDB: {e}")
            return None

# Khởi tạo instance dùng chung
fhir_store = FHIRStore()
