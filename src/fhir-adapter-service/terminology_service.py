import json
import os
import glob
from typing import Dict, Any, Optional

class TerminologyService:
    """
    Module 4: Translation Module.
    Handles mapping local hospital codes to standard international terminologies
    (e.g., ICD-10, LOINC, SNOMED-CT) using FHIR ConceptMap resources.
    
    Loads all ConceptMap JSON files from the terminology/ directory at startup.
    Each file follows the FHIR ConceptMap structure and is flattened into a
    lookup dictionary keyed by ConceptMap ID.
    """
    def __init__(self, terminology_dir: Optional[str] = None):
        self.concept_map: Dict[str, Dict[str, Dict[str, str]]] = {}
        
        if terminology_dir is None:
            terminology_dir = os.path.join(os.path.dirname(__file__), "terminology")
        
        self._load_all_concept_maps(terminology_dir)

    def _load_all_concept_maps(self, directory: str):
        """
        Scans the terminology directory for *.json files and loads each
        as a FHIR ConceptMap resource.
        """
        if not os.path.isdir(directory):
            print(f" [!] Terminology directory not found: {directory}")
            return
        
        json_files = sorted(glob.glob(os.path.join(directory, "*.json")))
        for file_path in json_files:
            self._load_concept_map_file(file_path)

        print(f" [Terminology] Loaded {len(json_files)} ConceptMap file(s) from {directory}")
        print(f" [Terminology] Available systems: {list(self.concept_map.keys())}")

    def _load_concept_map_file(self, file_path: str):
        """
        Loads a single FHIR ConceptMap JSON file and flattens it into the
        internal concept_map dictionary.
        
        ConceptMap structure:
          { "id": "system-key", "group": [{ "element": [{ "code": "1", 
            "target": [{ "code": "male", "display": "Male" }] }] }] }
        
        Flattened to:
          concept_map["system-key"]["1"] = {"code": "male", "display": "Male", "system": "..."}
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cm = json.load(f)
            
            cm_id = cm.get("id")
            if not cm_id:
                print(f" [!] Skipping {file_path}: no 'id' field")
                return
            
            if cm_id not in self.concept_map:
                self.concept_map[cm_id] = {}
            
            for group in cm.get("group", []):
                target_system = group.get("target", "")
                for element in group.get("element", []):
                    source_code = element.get("code")
                    targets = element.get("target", [])
                    if source_code and targets:
                        t = targets[0]  # Take first target mapping
                        self.concept_map[cm_id][source_code] = {
                            "code": t.get("code", source_code),
                            "display": t.get("display", ""),
                            "system": target_system
                        }
            
            print(f" [Terminology] Loaded ConceptMap '{cm_id}' ({len(self.concept_map[cm_id])} codes) from {os.path.basename(file_path)}")
        except Exception as e:
            print(f" [!] Warning: Could not load ConceptMap from {file_path}: {e}")

    def translate_code(self, system: str, local_code: str) -> Dict[str, str]:
        """
        Translates a local code to a standard terminology code.
        
        Args:
            system: The ConceptMap ID (e.g., 'vn-emr-gender-map', 'vn-emr-icd10-map')
            local_code: The source code to translate
            
        Returns:
            Dictionary with 'code', 'display', and 'system' keys.
            Falls back gracefully if mapping is not found.
        """
        if system in self.concept_map and local_code in self.concept_map[system]:
            return self.concept_map[system][local_code]
        
        # Graceful fallback for missing mappings
        return {
            "code": str(local_code),
            "display": f"Unmapped ({system}): {local_code}",
            "system": f"http://hospital.vn/fhir/CodeSystem/{system}-unmapped"
        }

    def get_available_systems(self) -> list:
        """Returns list of all loaded ConceptMap IDs."""
        return list(self.concept_map.keys())
    
    def get_mapping_count(self, system: str) -> int:
        """Returns number of mappings for a given system."""
        return len(self.concept_map.get(system, {}))

# Initialize global instance
terminology_service = TerminologyService()

# ==========================================
# MOCK TESTING
# ==========================================
if __name__ == "__main__":
    service = TerminologyService()
    
    print("\n=== Available Systems ===")
    for sys_id in service.get_available_systems():
        print(f"  {sys_id}: {service.get_mapping_count(sys_id)} codes")
    
    print("\n1. Translating gender code '1' (Nam):")
    print(json.dumps(service.translate_code("vn-emr-gender-map", "1"), indent=2))
    
    print("\n2. Translating gender code '2' (Nữ):")
    print(json.dumps(service.translate_code("vn-emr-gender-map", "2"), indent=2))
    
    print("\n3. Translating encounter status '1' (Hoàn thành):")
    print(json.dumps(service.translate_code("vn-emr-encounter-status-map", "1"), indent=2))
    
    print("\n4. Translating ICD-10 code 'I10' (Tăng huyết áp):")
    print(json.dumps(service.translate_code("vn-emr-icd10-map", "I10"), indent=2))
    
    print("\n5. Translating LOINC code '2339-0' (Glucose):")
    print(json.dumps(service.translate_code("vn-emr-loinc-lab-map", "2339-0"), indent=2))
    
    print("\n6. Translating medication 'PARA500' (Paracetamol):")
    print(json.dumps(service.translate_code("vn-emr-medication-map", "PARA500"), indent=2))
    
    print("\n7. Translating procedure 'PT006' (X-quang):")
    print(json.dumps(service.translate_code("vn-emr-procedure-map", "PT006"), indent=2))
    
    print("\n8. Testing Fallback (Unknown code):")
    print(json.dumps(service.translate_code("vn-emr-loinc-lab-map", "XYZ-99"), indent=2))
