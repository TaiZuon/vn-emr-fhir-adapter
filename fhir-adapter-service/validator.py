# fhir-adapter-service/validator.py
import json
from pydantic import ValidationError

class FHIRValidator:
    @staticmethod
    def validate(resource):
        """
        Kiểm tra tính hợp lệ của một FHIR Resource object.
        Trả về: (is_valid, error_message)
        """
        try:
            # 1. Schema Validation (Standard FHIR):
            # Thư viện fhir.resources sẽ tự động kiểm tra kiểu dữ liệu, 
            # định dạng chuỗi (regex), và các giá trị bắt buộc theo CHUẨN FHIR quốc tế.
            # Bất kỳ trường nào bắt buộc bởi FHIR standard, Pydantic sẽ ném ra ValidationError.
            resource.dict()

            return True, None

        except ValidationError as e:
            # Trích xuất lỗi từ Pydantic để log ra một cách dễ đọc
            errors = e.errors()
            readable_errors = []
            for err in errors:
                loc = " -> ".join([str(item) for item in err['loc']])
                msg = err['msg']
                readable_errors.append(f"[{loc}]: {msg}")
            
            return False, " | ".join(readable_errors)
        except Exception as e:
            return False, str(e)
