# fhir-adapter-service/crypto_service.py
"""
Module mã hóa dữ liệu y tế nhạy cảm (PHI/PII) theo chuẩn AES-256-GCM.
Tuân thủ yêu cầu bảo mật của QĐ-130/BYT và HIPAA.

Chiến lược: Field-level encryption — chỉ mã hóa các trường PII,
giữ nguyên cấu trúc FHIR resource để vẫn query được theo ID, resourceType.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from utils.logger import log

# Encryption key: 32 bytes = AES-256
# Production: dùng KMS (AWS KMS, HashiCorp Vault), KHÔNG hardcode
ENCRYPTION_KEY = os.getenv(
    "FHIR_ENCRYPTION_KEY",
    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
)

# Định nghĩa các trường PII cần mã hóa theo từng FHIR Resource Type
SENSITIVE_FIELDS = {
    "Patient": [
        "name",              # Họ tên bệnh nhân
        "identifier",        # CCCD, mã bệnh nhân
        "telecom",           # Số điện thoại
        "address",           # Địa chỉ
        "contact",           # Người liên hệ / người đưa trẻ đến
    ],
    "Practitioner": [
        "name",              # Họ tên bác sĩ
        "telecom",           # Số điện thoại
        "identifier",        # Mã bác sĩ
    ],
    "Encounter": [
        "diagnosis",         # Mã bệnh, tên bệnh (ICD-10)
    ],
    "MedicationRequest": [
        "dosageInstruction", # Liều dùng, đường dùng
    ],
    "Observation": [
        "valueString",       # Kết quả xét nghiệm
        "valueQuantity",     # Giá trị đo
        "note",              # Ghi chú lâm sàng
        "interpretation",    # Diễn giải kết quả
    ],
    "ClinicalImpression": [
        "summary",           # Diễn biến lâm sàng
        "note",              # Hội chẩn
        "finding",           # Phẫu thuật
    ],
    "Procedure": [
        # Procedure code/text giữ nguyên để thống kê
    ],
}

# Trường mã hóa khi gửi lên HAPI FHIR Server
# Chỉ encrypt giá trị nhạy cảm (value), giữ nguyên cấu trúc FHIR hợp lệ
HAPI_ENCRYPT_PATHS = {
    "Patient": {
        "identifier": ["value"],           # CCCD, mã BN — encrypt value, giữ system/type
        "name": ["text", "family", "given"],  # Họ tên
        "telecom": ["value"],              # SĐT
        "address": ["text", "line"],       # Địa chỉ
    },
    "Practitioner": {
        "identifier": ["value"],           # Mã bác sĩ
        "name": ["text", "family", "given"],
        "telecom": ["value"],
    },
}


class CryptoService:
    """
    Dịch vụ mã hóa/giải mã AES-256-GCM cho dữ liệu y tế nhạy cảm.
    
    AES-256-GCM cung cấp:
    - Confidentiality (bảo mật): AES-256 encryption
    - Integrity (toàn vẹn): GCM authentication tag
    - Nonce/IV duy nhất mỗi lần mã hóa → ciphertext khác nhau dù plaintext giống nhau
    """

    def __init__(self, key_hex: str = ENCRYPTION_KEY):
        key_bytes = bytes.fromhex(key_hex)
        if len(key_bytes) != 32:
            raise ValueError("FHIR_ENCRYPTION_KEY phải là 64 hex chars (32 bytes cho AES-256)")
        self.aesgcm = AESGCM(key_bytes)
        log.info("CryptoService: Khởi tạo AES-256-GCM thành công")

    def encrypt(self, plaintext: str) -> str:
        """
        Mã hóa chuỗi plaintext -> base64(nonce + ciphertext).
        Nonce 12 bytes được prepend vào ciphertext để giải mã sau.
        """
        nonce = os.urandom(12)  # 96-bit nonce (NIST recommended)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Format: base64(nonce || ciphertext || tag)
        encrypted = base64.b64encode(nonce + ciphertext).decode("utf-8")
        return f"ENC:{encrypted}"

    def decrypt(self, encrypted: str) -> str:
        """
        Giải mã chuỗi ENC:base64(...) -> plaintext gốc.
        """
        if not encrypted.startswith("ENC:"):
            return encrypted  # Không phải ciphertext, trả về nguyên bản

        raw = base64.b64decode(encrypted[4:])
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

    def encrypt_resource(self, resource_data: dict) -> dict:
        """
        Mã hóa các trường PII trong FHIR resource dict.
        Trả về bản copy đã mã hóa, giữ nguyên cấu trúc.
        """
        resource_type = resource_data.get("resourceType", "")
        fields_to_encrypt = SENSITIVE_FIELDS.get(resource_type, [])
        
        if not fields_to_encrypt:
            return resource_data
        
        import copy
        encrypted = copy.deepcopy(resource_data)
        
        encrypted_count = 0
        for field in fields_to_encrypt:
            if field in encrypted and encrypted[field] is not None:
                encrypted[field] = self._encrypt_value(encrypted[field])
                encrypted_count += 1
        
        if encrypted_count > 0:
            # Đánh dấu resource đã được mã hóa
            encrypted["_encrypted"] = True
            encrypted["_encrypted_fields"] = [f for f in fields_to_encrypt if f in resource_data]
            log.debug(f"Đã mã hóa {encrypted_count} trường PII trong {resource_type}")
        
        return encrypted

    def decrypt_resource(self, resource_data: dict) -> dict:
        """
        Giải mã các trường PII đã mã hóa trong FHIR resource dict.
        """
        if not resource_data.get("_encrypted"):
            return resource_data
        
        import copy
        decrypted = copy.deepcopy(resource_data)
        
        for field in decrypted.get("_encrypted_fields", []):
            if field in decrypted:
                decrypted[field] = self._decrypt_value(decrypted[field])
        
        del decrypted["_encrypted"]
        del decrypted["_encrypted_fields"]
        
        return decrypted

    def encrypt_for_hapi(self, resource_data: dict) -> dict:
        """
        Mã hóa chọn lọc cho HAPI FHIR Server.
        Chỉ encrypt giá trị nhạy cảm (identifier.value, name.text, ...),
        giữ nguyên cấu trúc FHIR hợp lệ (system, type, use...) để HAPI chấp nhận.
        """
        resource_type = resource_data.get("resourceType", "")
        paths = HAPI_ENCRYPT_PATHS.get(resource_type)

        if not paths:
            return resource_data

        import copy
        result = copy.deepcopy(resource_data)

        for field, subkeys in paths.items():
            if field not in result or result[field] is None:
                continue
            value = result[field]
            if isinstance(value, list):
                result[field] = [
                    self._encrypt_subkeys(item, subkeys) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[field] = self._encrypt_subkeys(value, subkeys)

        log.debug(f"HAPI encrypt: {resource_type} — encrypted fields: {list(paths.keys())}")
        return result

    def _encrypt_subkeys(self, obj: dict, subkeys: list) -> dict:
        """Mã hóa chỉ các subkey chỉ định bên trong dict, giữ nguyên structure."""
        for key in subkeys:
            if key not in obj or obj[key] is None:
                continue
            obj[key] = self._encrypt_value(obj[key])
        return obj

    def _encrypt_value(self, value):
        """Đệ quy mã hóa giá trị: string, list, hoặc dict."""
        if isinstance(value, str):
            return self.encrypt(value)
        elif isinstance(value, list):
            return [self._encrypt_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._encrypt_value(v) for k, v in value.items()}
        else:
            # Số, boolean, None -> giữ nguyên
            return value

    def _decrypt_value(self, value):
        """Đệ quy giải mã giá trị."""
        if isinstance(value, str):
            return self.decrypt(value)
        elif isinstance(value, list):
            return [self._decrypt_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._decrypt_value(v) for k, v in value.items()}
        else:
            return value


# Global instance
crypto_service = CryptoService()
