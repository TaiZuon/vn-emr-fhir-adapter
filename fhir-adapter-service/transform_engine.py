# fhir-adapter-service/transform_engine.py
import json
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from reference_manager import ref_manager

class TransformEngine:
    def __init__(self, rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def _set_nested_attr(self, obj, path, value):
        """Hàm helper để gán giá trị vào path phức tạp của FHIR"""
        try:
            if path == "id":
                obj.id = str(value)  # [QUAN TRỌNG] Ép kiểu int sang string cho FHIR ID
            elif path == "name[0].text":
                obj.name = [HumanName(text=value)]
            elif path == "identifier[0].value":
                obj.identifier = [Identifier(value=str(value), system="http://hospital.vn/id")]
            elif path == "code.coding[0].code":
                if not obj.code: obj.code = CodeableConcept()
                obj.code.coding = [Coding(code=str(value), system="http://loinc.org")]
            elif path == "code.coding[0].display":
                if obj.code and obj.code.coding:
                    obj.code.coding[0].display = str(value)
            elif path == "valueQuantity.value":
                if not obj.valueQuantity: obj.valueQuantity = Quantity()
                obj.valueQuantity.value = float(value)
            elif path == "valueQuantity.unit":
                if not obj.valueQuantity: obj.valueQuantity = Quantity()
                obj.valueQuantity.unit = str(value)
            elif path == "subject.reference":
                obj.subject = {"reference": str(value)}
            else:
                setattr(obj, path, value)
        except Exception as e:
            print(f" [!] Lỗi gán trường {path}: {e}")
            raise e

    def convert(self, table_name, data):
        table_config = self.config.get(table_name)
        if not table_config: return None

        # Khởi tạo đúng loại Resource
        res_type = table_config["resource_type"]
        if res_type == "Patient":
            resource = Patient()
            resource.active = True  # FHIR Patient dùng 'active' thay vì 'status'
        elif res_type == "Observation":
            resource = Observation()
            resource.status = "final" # Bắt buộc đối với Observation
        else:
            return None

        for rule in table_config["rules"]:
            val = data.get(rule["source"])
            if val is None: continue

            # Thực thi Action (Transform logic)
            final_val = val
            if rule["action"] == "lookup":
                # final_val = rule["map"].get(val, "unknown")
                final_val = rule["map"].get(val, val)
            elif rule["action"] == "float":
                final_val = float(val)
            elif rule["action"] == "reference":
                final_val = ref_manager.resolve(rule["ref_type"], val)
                if not final_val: continue # Bỏ qua nếu chưa có tham chiếu
            # Nếu là string định dạng ngày tháng ISO (từ EMR gửi qua), ta gán trực tiếp
            elif rule["action"] == "date" and hasattr(val, 'isoformat'):
                final_val = val.isoformat()

            self._set_nested_attr(resource, rule["target"], final_val)
        
        return resource
