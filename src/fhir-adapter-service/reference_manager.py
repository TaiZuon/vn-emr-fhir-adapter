# fhir-adapter-service/reference_manager.py
from pymongo import MongoClient
import os
from typing import Optional

from collections import OrderedDict

class ReferenceCache:
    """
    Abstract/Interface layer for caching references.
    Uses an in-memory OrderedDict for O(1) lookups and LRU (Least Recently Used) eviction.
    Prevents Out-of-Memory (OOM) issues bounded by maxsize.
    """
    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self._cache = OrderedDict()

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: str):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

class ReferenceManager:
    def __init__(self, uri=None, db_name="fhir_db"):
        # Lấy URI từ biến môi trường hoặc dùng default (localhost)
        mongo_uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["id_mappings"]
        self.collection.create_index([("_id", 1)])
        
        # Initialize the caching layer
        self.cache = ReferenceCache()
        
        print(f" [connected] ReferenceManager: Đã kết nối MongoDB mapping tại {db_name} và khởi tạo Local Cache")

    def store_reference(self, resource_type: str, emr_key: str, fhir_id: str):
        """
        Lưu ánh xạ ID vào Cache (O(1)) và MongoDB (Persistent).
        """
        mapping_id = f"{resource_type}:{emr_key}"
        
        # 1. Lưu vào cache ngay lập tức
        self.cache.set(mapping_id, fhir_id)
        
        # 2. Xử lý lưu MongoDB (Persistent)
        try:
            self.collection.replace_one(
                {"_id": mapping_id},
                {
                    "_id": mapping_id,
                    "resource_type": resource_type,
                    "local_id": str(emr_key),
                    "fhir_id": fhir_id
                },
                upsert=True
            )
        except Exception as e:
            print(f" [❌] ReferenceManager Error (Add Mongo): {e}")

    def resolve_reference(self, resource_type: str, emr_key: str) -> Optional[str]:
        """
        Tìm kiếm FHIR ID với cơ chế Cache First, Fallback to DB.
        """
        mapping_id = f"{resource_type}:{emr_key}"
        
        # 1. Thử lấy từ Cache trước (O(1) lookup)
        cached_fhir_id = self.cache.get(mapping_id)
        if cached_fhir_id:
            return f"{resource_type}/{cached_fhir_id}"
            
        # 2. Cache Miss -> Truy vấn MongoDB (Fallback)
        try:
            from pymongo.errors import PyMongoError
            
            # Using serverSelectionTimeoutMS inside the MongoClient instantiation would be better,
            # but we catch any connectivity or logical errors here.
            mapping = self.collection.find_one({"_id": mapping_id})
            if mapping:
                fhir_id = mapping['fhir_id']
                # 3. Cập nhật lại Cache để lần sau O(1)
                self.cache.set(mapping_id, fhir_id)
                return f"{resource_type}/{fhir_id}"
            return None
        except PyMongoError as e:
            print(f" [❌] ReferenceManager Error (MongoDB Connection/Timeout): {e}")
            return None
        except Exception as e:
            print(f" [❌] ReferenceManager Error (Resolve Mongo Generic): {e}")
            return None

    # Backward compatibility with existing engine calls
    def add_mapping(self, resource_type: str, local_id: str, fhir_id: str):
        self.store_reference(resource_type, local_id, fhir_id)

    def resolve(self, resource_type: str, local_id: str) -> str:
        return self.resolve_reference(resource_type, local_id)

# Khởi tạo instance duy nhất để các module khác import và dùng chung
ref_manager = ReferenceManager()
