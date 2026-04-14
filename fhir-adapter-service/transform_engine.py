# fhir-adapter-service/transform_engine.py
import json
import datetime
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.practitioner import Practitioner, PractitionerQualification
from fhir.resources.encounter import Encounter, EncounterParticipant, EncounterLocation
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.procedure import Procedure
from fhir.resources.clinicalimpression import ClinicalImpression
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.period import Period
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
                if not obj.code.coding: obj.code.coding = [Coding()]
                obj.code.coding[0].code = str(value)
                if not obj.code.coding[0].system: obj.code.coding[0].system = "http://loinc.org"
            elif path == "code.coding[0].display":
                if not obj.code: obj.code = CodeableConcept()
                if not obj.code.coding: obj.code.coding = [Coding()]
                obj.code.coding[0].display = str(value)
            elif path == "valueQuantity.value":
                if not obj.valueQuantity: obj.valueQuantity = Quantity()
                obj.valueQuantity.value = float(value)
            elif path == "valueQuantity.unit":
                if not obj.valueQuantity: obj.valueQuantity = Quantity()
                obj.valueQuantity.unit = str(value)
            elif path == "subject.reference":
                obj.subject = {"reference": str(value)}
            elif path == "encounter.reference":
                obj.encounter = {"reference": str(value)}
            elif path == "telecom[0].value":
                obj.telecom = [ContactPoint(system="phone", value=str(value))]
            elif path == "qualification[0].code.text":
                obj.qualification = [PractitionerQualification(code=CodeableConcept(text=str(value)))]
            elif path == "actualPeriod.start":
                if not obj.actualPeriod: obj.actualPeriod = Period()
                obj.actualPeriod.start = value
            elif path == "type[0].text":
                obj.type = [CodeableConcept(text=str(value))]
            elif path == "location[0].location.display":
                obj.location = [EncounterLocation(location={"display": str(value)})]
            elif path == "participant[0].actor.reference":
                obj.participant = [EncounterParticipant(actor={"reference": str(value)})]
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
            # Khởi tạo kèm các trường bắt buộc (mandatory fields) để Pydantic không báo lỗi ngay lập tức
            resource = Observation(status="final", code=CodeableConcept())
        elif res_type == "Practitioner":
            resource = Practitioner()
            resource.active = True
        elif res_type == "Encounter":
            resource = Encounter(status="unknown", class_fhir=[CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/v3-ActCode", code="AMB", display="ambulatory")])])
        elif res_type == "MedicationRequest":
            resource = MedicationRequest(status="active", intent="order")
        elif res_type == "Procedure":
            resource = Procedure(status="completed")
        elif res_type == "ClinicalImpression":
            resource = ClinicalImpression(status="completed")
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
                try:
                    final_val = float(val)
                except Exception as e:
                    if isinstance(val, dict):
                        # Debezium decimal format {"scale": 1, "value": "Base64"}
                        if "value" in val and "scale" in val:
                            import base64
                            raw_bytes = base64.b64decode(val["value"])
                            unscaled = int.from_bytes(raw_bytes, byteorder="big", signed=True)
                            final_val = float(unscaled) / (10 ** val["scale"])
                        else:
                            raise e
                    else:
                        raise e
            elif rule["action"] == "reference":
                final_val = ref_manager.resolve(rule["ref_type"], val)
                if not final_val: continue # Bỏ qua nếu chưa có tham chiếu
            # Nếu là string định dạng ngày tháng ISO (từ EMR gửi qua), ta gán trực tiếp
            elif rule["action"] == "date":
                if hasattr(val, 'isoformat'):
                    final_val = val.isoformat()
                elif isinstance(val, int):
                    if val > 1000000000:
                        # Debezium timestamp in microseconds
                        final_val = datetime.datetime.fromtimestamp(val / 1000000.0).isoformat() + "Z"
                    else:
                        # Debezium date in epoch days
                        final_val = (datetime.date(1970, 1, 1) + datetime.timedelta(days=val)).isoformat()
                elif isinstance(val, str):
                    final_val = val

            self._set_nested_attr(resource, rule["target"], final_val)
        
        return resource
