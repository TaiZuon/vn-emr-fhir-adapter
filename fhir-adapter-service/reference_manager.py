# fhir-adapter-service/reference_manager.py

class ReferenceManager:
    def __init__(self):
        # Cache đơn giản: { "Patient:1": "mongodb_id_xyz" }
        self._cache = {}

    def add_mapping(self, resource_type, local_id, fhir_id):
        key = f"{resource_type}:{local_id}"
        self._cache[key] = fhir_id

    def resolve(self, resource_type, local_id):
        key = f"{resource_type}:{local_id}"
        fhir_id = self._cache.get(key)
        return f"{resource_type}/{fhir_id}" if fhir_id else None

# Khởi tạo một instance dùng chung
ref_manager = ReferenceManager()
