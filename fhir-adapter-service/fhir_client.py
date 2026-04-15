# fhir-adapter-service/fhir_client.py
"""
HAPI FHIR Server REST Client.
Gửi FHIR resources lên HAPI FHIR Server qua REST API (PUT upsert).
"""
import json
import requests
from utils.logger import log

HAPI_BASE_URL = "http://localhost:8080/fhir"
TIMEOUT = 10  # seconds


class HAPIFHIRClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or HAPI_BASE_URL).rstrip("/")
        self._available = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        })

    def is_available(self) -> bool:
        """Kiểm tra HAPI FHIR Server có sẵn sàng không."""
        if self._available is True:
            return True
        try:
            resp = self.session.get(
                f"{self.base_url}/metadata",
                timeout=5
            )
            self._available = resp.status_code == 200
            if self._available:
                log.info(f"HAPI FHIR Server sẵn sàng: {self.base_url}")
            else:
                log.warning(f"HAPI FHIR Server trả về status {resp.status_code}")
        except requests.ConnectionError:
            log.warning(f"Không kết nối được HAPI FHIR Server: {self.base_url}")
            self._available = False
        return self._available

    def save_resource(self, resource_obj) -> str:
        """
        Lưu FHIR Resource lên HAPI Server bằng PUT (upsert).
        
        Args:
            resource_obj: Pydantic FHIR resource object (từ fhir.resources)
            
        Returns:
            FHIR ID nếu thành công, None nếu thất bại.
        """
        try:
            resource_type = resource_obj.__class__.__name__
            resource_json = json.loads(resource_obj.json())
            resource_id = resource_json.get("id")

            if resource_id:
                # PUT = upsert (tạo mới hoặc cập nhật theo ID)
                url = f"{self.base_url}/{resource_type}/{resource_id}"
                resp = self.session.put(url, json=resource_json, timeout=TIMEOUT)
            else:
                # POST = server tự sinh ID
                url = f"{self.base_url}/{resource_type}"
                resp = self.session.post(url, json=resource_json, timeout=TIMEOUT)

            if resp.status_code in (200, 201):
                result = resp.json()
                fhir_id = result.get("id", resource_id)
                log.info(f"HAPI: Đã lưu {resource_type}/{fhir_id} (HTTP {resp.status_code})")
                return fhir_id
            else:
                error_detail = ""
                try:
                    oo = resp.json()
                    if oo.get("resourceType") == "OperationOutcome":
                        issues = oo.get("issue", [])
                        error_detail = "; ".join(
                            i.get("diagnostics", i.get("details", {}).get("text", ""))
                            for i in issues
                        )
                except Exception:
                    error_detail = resp.text[:300]
                
                log.error(f"HAPI: Lỗi lưu {resource_type} (HTTP {resp.status_code}): {error_detail}")
                return None

        except requests.Timeout:
            log.error(f"HAPI: Timeout khi lưu {resource_type}")
            return None
        except requests.ConnectionError:
            log.error(f"HAPI: Mất kết nối đến server")
            self._available = False
            return None
        except Exception as e:
            log.error(f"HAPI: Lỗi không xác định: {e}")
            return None

    def get_resource(self, resource_type: str, resource_id: str) -> dict:
        """Đọc FHIR resource từ HAPI Server."""
        try:
            url = f"{self.base_url}/{resource_type}/{resource_id}"
            resp = self.session.get(url, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def search(self, resource_type: str, params: dict = None) -> list:
        """
        FHIR Search trên HAPI Server.
        Ví dụ: search("Patient", {"name": "Nguyen", "birthdate": "gt1990-01-01"})
        """
        try:
            url = f"{self.base_url}/{resource_type}"
            resp = self.session.get(url, params=params or {}, timeout=TIMEOUT)
            if resp.status_code == 200:
                bundle = resp.json()
                entries = bundle.get("entry", [])
                return [e.get("resource") for e in entries]
            return []
        except Exception:
            return []


# Global instance
hapi_client = HAPIFHIRClient()
