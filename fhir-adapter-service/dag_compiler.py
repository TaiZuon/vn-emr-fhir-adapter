import json
import re
import datetime
from typing import Dict, Any, Callable, List
from dag_engine import RuleNode, TransformMap
from reference_manager import ref_manager
from terminology_service import terminology_service

def set_nested(d: dict, path: str, val: Any) -> dict:
    """
    Helper function to dynamically build nested dictionaries/lists based on 
    a string path like 'identifier[0].value'.
    """
    parts = re.findall(r'[^.\[\]]+', path)
    curr = d
    for i, part in enumerate(parts[:-1]):
        next_part = parts[i+1]
        
        is_list_index = part.isdigit()
        if is_list_index:
            part = int(part)
            while len(curr) <= part: 
                curr.append([] if next_part.isdigit() else {})
            if curr[part] is None:
                curr[part] = [] if next_part.isdigit() else {}
        else:
            if part not in curr or curr[part] is None:
                curr[part] = [] if next_part.isdigit() else {}
                
        curr = curr[part]
        
    last = parts[-1]
    if last.isdigit():
        last = int(last)
        while len(curr) <= last: curr.append(None)
        curr[last] = val
    else:
        curr[last] = val
    return d

def recursive_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merges dict2 into dict1."""
    for key, val in dict2.items():
        if isinstance(val, dict) and key in dict1 and isinstance(dict1[key], dict):
            recursive_merge(dict1[key], val)
        elif isinstance(val, list) and key in dict1 and isinstance(dict1[key], list):
            # Pad list1 if list2 is longer
            while len(dict1[key]) < len(val):
                dict1[key].append(None)
            # Merge elements
            for i, item in enumerate(val):
                if isinstance(item, dict) and dict1[key][i] is not None and isinstance(dict1[key][i], dict):
                    recursive_merge(dict1[key][i], item)
                elif item is not None:
                    dict1[key][i] = item
        else:
            dict1[key] = val
    return dict1

class DAGCompiler:
    """
    Module 3: The DAG Compiler.
    Reads declarative configuration (transform_rules.json) and compiles it
    into a functional Directed Acyclic Graph (TransformMap) of RuleNodes.
    """
    def __init__(self, rules_path: str):
        self.rules_path = rules_path
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    def _create_action(self, rule: dict) -> Callable:
        source = rule.get("source")
        target = rule.get("target")
        action_type = rule.get("action")
        
        def action_func(data: dict, child_results: dict) -> dict:
            val = data.get(source)
            if val is None:
                return {}
                
            final_val = val
            
            if action_type == "direct":
                # Ensure FHIR ID is strictly cast to safe string
                if target == "id":
                    id_str = str(val)
                    # HAPI FHIR yêu cầu ID chứa ít nhất 1 ký tự không phải số
                    if id_str.isdigit():
                        id_str = f"emr-{id_str}"
                    final_val = id_str
                else:
                    final_val = val
            elif action_type == "float":
                try:
                    final_val = float(val)
                except Exception:
                    if isinstance(val, dict) and "value" in val and "scale" in val:
                        import base64
                        raw_bytes = base64.b64decode(val["value"])
                        unscaled = int.from_bytes(raw_bytes, byteorder="big", signed=True)
                        final_val = float(unscaled) / (10 ** val["scale"])
            elif action_type == "date":
                if hasattr(val, 'isoformat'):
                    final_val = val.isoformat()
                elif isinstance(val, int):
                    if val > 1000000000:
                        final_val = datetime.datetime.fromtimestamp(val / 1000000.0).isoformat() + "Z"
                    else:
                        final_val = (datetime.date(1970, 1, 1) + datetime.timedelta(days=val)).isoformat()
            elif action_type == "reference":
                ref_type = rule.get("ref_type")
                resolved = ref_manager.resolve(ref_type, val)
                if not resolved:
                    return {} # Cache miss and Mongo miss, skip referencing
                # EncounterPatient là mapping ảo để resolve Patient từ dot_dieu_tri_id
                # Kết quả trả về dạng "EncounterPatient/emr-182" -> đổi thành "Patient/emr-182"
                if ref_type == "EncounterPatient":
                    resolved = "Patient/" + resolved.split("/")[-1]
                final_val = resolved
            elif action_type == "lookup":
                system = rule.get("system")
                if system:
                    translated = terminology_service.translate_code(system, str(val))
                    final_val = translated.get("code", val)
                else:
                    # Fallback to inline map if no system specified
                    rule_map = rule.get("map", {})
                    final_val = rule_map.get(str(val), val)
            elif action_type == "terminology_lookup":
                # Full terminology translation: returns {code, display, system} object
                system = rule.get("system", "")
                translated = terminology_service.translate_code(system, str(val))
                final_val = {
                    "code": translated.get("code", str(val)),
                    "display": translated.get("display", ""),
                    "system": translated.get("system", "")
                }
                    
            res = {}
            set_nested(res, target, final_val)
            return res
            
        return action_func

    def compile(self) -> TransformMap:
        root_nodes = []
        
        for table_name, table_config in self.config.items():
            resource_type = table_config["resource_type"]
            
            # Root action adds ResourceType and FHIR defaults (child results are merged by the engine)
            def make_root_action(res_type):
                def root_action_func(data: dict, child_results: dict) -> dict:
                    merged = {"resourceType": res_type}
                    
                    # FHIR R4 constraint defaults
                    if res_type == "Observation":
                        merged["status"] = "final"
                    elif res_type in ["Patient", "Practitioner"]:
                        merged["active"] = True
                    elif res_type == "MedicationRequest":
                        merged["status"] = "active"
                        merged["intent"] = "order"
                        if "subject" not in child_results:
                            merged["subject"] = {"display": "Unknown"}
                    elif res_type == "Procedure":
                        merged["status"] = "completed"
                        if "subject" not in child_results:
                            merged["subject"] = {"display": "Unknown"}
                    elif res_type == "ClinicalImpression":
                        merged["status"] = "completed"
                        # subject is required - fallback if no reference resolved
                        if "subject" not in child_results:
                            merged["subject"] = {"display": "Unknown"}
                        
                    # For Encounter, 'status' comes from child_results if mapped, else 'unknown'
                    if res_type == "Encounter" and "status" not in child_results:
                        merged["status"] = "unknown"
                        
                    return merged
                return root_action_func
                
            # Define condition to only run this root node if the table name matches!
            def make_condition(expected_table):
                return lambda data: data.get('_table') == expected_table

            root_node = RuleNode(
                id=f"root_{table_name}",
                action=make_root_action(resource_type),
                condition=make_condition(table_name),
                precedence=100
            )
            
            # Construct child RuleNodes from rules array
            for index, rule in enumerate(table_config.get("rules", [])):
                child_node = RuleNode(
                    id=f"{table_name}_rule_{index}",
                    action=self._create_action(rule),
                    precedence=50 - index
                )
                root_node.children.append(child_node)
                
            root_nodes.append(root_node)
            
        print(f" [Compiler] Compiled DAG with {len(root_nodes)} root mappings.")
        return TransformMap(root_nodes)

if __name__ == "__main__":
    compiler = DAGCompiler("transform_rules.json")
    dag = compiler.compile()
    
    mock_patient_data = {
        "_table": "benh_nhan",
        "id": 12345,
        "ma_bn": "BN-2026-001",
        "ho_ten": "Nguyen Van A",
        "gioi_tinh": 1,
        "ngay_sinh": "1990-01-01"
    }
    
    print("Executing Compiled DAG for a Patient record...")
    result = dag.execute(mock_patient_data)
    print(json.dumps(result, indent=2))
