import json
from typing import Dict, Any, Optional

class TerminologyService:
    """
    Module 4: Translation Module.
    Handles mapping local hospital codes to standard international terminologies
    (e.g., ICD-10, LOINC, SNOMED-CT) using a ConceptMap.
    """
    def __init__(self, concept_map_path: Optional[str] = None):
        # Mock ConceptMap: System -> Local Code -> Standard Mapping
        self.concept_map = {
            "local-diagnosis": {
                "J00": {"code": "J00", "display": "Acute nasopharyngitis [common cold]", "system": "http://hl7.org/fhir/sid/icd-10"},
                "D01": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications", "system": "http://hl7.org/fhir/sid/icd-10"}
            },
            "local-lab": {
                "GLU01": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood", "system": "http://loinc.org"},
                "WBC01": {"code": "6690-2", "display": "Leukocytes [#/volume] in Blood by Automated count", "system": "http://loinc.org"}
            },
            "local-gender": {
                 "Nam": {"code": "male", "display": "Male", "system": "http://hl7.org/fhir/administrative-gender"},
                 "Nữ": {"code": "female", "display": "Female", "system": "http://hl7.org/fhir/administrative-gender"},
                 "Khác": {"code": "other", "display": "Other", "system": "http://hl7.org/fhir/administrative-gender"}
            },
            "local-encounter-status": {
                "COMPLETED": {"code": "finished", "display": "Finished", "system": "http://hl7.org/fhir/encounter-status"},
                "IN_PROGRESS": {"code": "in-progress", "display": "In Progress", "system": "http://hl7.org/fhir/encounter-status"},
                "PLANNED": {"code": "planned", "display": "Planned", "system": "http://hl7.org/fhir/encounter-status"}
            }
        }
        
        if concept_map_path:
            self.load_concept_map(concept_map_path)
            
    def load_concept_map(self, file_path: str):
        """
        Loads mappings from an external JSON file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                external_map = json.load(f)
                # Merge into existing concepts
                for sys_key, mappings in external_map.items():
                    if sys_key not in self.concept_map:
                        self.concept_map[sys_key] = {}
                    self.concept_map[sys_key].update(mappings)
            print(f" [Terminology] Loaded ConceptMap from {file_path}")
        except Exception as e:
            print(f" [!] Warning: Could not load ConceptMap from {file_path}: {e}")

    def translate_code(self, system: str, local_code: str) -> Dict[str, str]:
        """
        Translates a local code to a standard terminology code.
        Returns a dictionary containing 'code', 'display', and 'system'.
        Fallback: If code is not found, returns the original code with a local unmapped system flag.
        """
        if system in self.concept_map and local_code in self.concept_map[system]:
            return self.concept_map[system][local_code]
        
        # Graceful fallback for missing mappings
        return {
            "code": str(local_code),
            "display": f"Unknown {system} code: {local_code}",
            "system": f"http://hospital.vn/fhir/CodeSystem/{system}-unmapped"
        }

# Initialize global instance
terminology_service = TerminologyService()

# ==========================================
# MOCK TESTING
# ==========================================
if __name__ == "__main__":
    service = TerminologyService()
    
    print("1. Translating internal gender code 'Nam':")
    print(json.dumps(service.translate_code("local-gender", "Nam"), indent=2))
    
    print("\n2. Translating internal diagnosis code 'D01':")
    print(json.dumps(service.translate_code("local-diagnosis", "D01"), indent=2))
    
    print("\n3. Testing Fallback (Unknown Lab Code 'XYZ-99'):")
    print(json.dumps(service.translate_code("local-lab", "XYZ-99"), indent=2))
