import time
from collections import defaultdict
from typing import List, Dict, Any, Tuple

class DataPreHandler:
    """
    Micro-batching processor that buffers, merges, and sorts incoming EMR events 
    before triggering transformation.
    """
    def __init__(self, batch_size: int = 50, timeout_seconds: float = 5.0):
        self.buffer = []
        self.delivery_tags = []
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        self.last_flush_time = time.time()
        
        # FHIR Resource Creation Priority (Lower number = Created first)
        # e.g. Patients/Practitioners must exist before Encounters, which must exist before detail tables
        self.priority_map = {
            'benh_nhan': 1,
            'nhan_vien_y_te': 2,
            'dot_dieu_tri': 3,
            'chi_tiet_thuoc': 4,
            'dich_vu_ky_thuat': 5,
            'can_lam_sang': 6,
            'dien_bien_lam_sang': 7
        }

    def add_event(self, event: Dict[str, Any], delivery_tag: int) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Adds an incoming event to the buffer.
        Returns a tuple of (processed_batch, delivery_tags) if the buffer is full or timeout is reached, else ([], []).
        """
        self.buffer.append(event)
        self.delivery_tags.append(delivery_tag)
        current_time = time.time()
        
        if len(self.buffer) >= self.batch_size or (current_time - self.last_flush_time) >= self.timeout_seconds:
            return self.flush()
            
        return [], []

    def flush(self) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Forcibly processes the current buffer.
        """
        if not self.buffer:
            return [], []
            
        raw_batch = self.buffer.copy()
        raw_tags = self.delivery_tags.copy()
        self.buffer.clear()
        self.delivery_tags.clear()
        self.last_flush_time = time.time()
        
        # 1. Merge N:1 records
        merged_batch = self.merge_data(raw_batch)
        
        # 2. Sort by dependency priority
        sorted_batch = self.sort_data(merged_batch)
        
        return sorted_batch, raw_tags

    def sort_data(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reorders data creation based on standard HL7 FHIR workflow priorities.
        """
        def get_priority(event: Dict[str, Any]) -> int:
            table = event.get("source", {}).get("table", "unknown")
            return self.priority_map.get(table, 99) # 99 for lowest priority/unknown
            
        return sorted(batch, key=get_priority)

    def merge_data(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combines multiple rows of EMR data into a single dataset.
        Prevents duplicate resources by merging them under a specific cache/merge key.
        """
        merged_events = {}
        
        for event in batch:
            table = event.get("source", {}).get("table")
            data = event.get("after")
            
            if not table or not data:
                continue
                
            # Define merge key strategy. 
            # Merge by the target entity ID: benh_nhan_id for patient-level, dot_dieu_tri_id for encounter-level details
            merge_identifier = data.get("benh_nhan_id", data.get("dot_dieu_tri_id", data.get("ma_lk", data.get("id"))))
            merge_key = f"{table}_{merge_identifier}"
            
            if merge_key not in merged_events:
                # Initialize the base event with a list to hold sub-records
                event["after"]["merged_records"] = [data.copy()]
                merged_events[merge_key] = event
            else:
                # N:1 Mapping -> Accumulate into the existing event
                # This combines rows (e.g. multiple immunizations) into the `merged_records` array
                existing_data = merged_events[merge_key]["after"]
                existing_data["merged_records"].append(data.copy())
                
                # Optionally update top-level fields with the latest event data
                for k, v in data.items():
                    if k not in existing_data or existing_data[k] is None:
                        existing_data[k] = v
                        
        return list(merged_events.values())

# Mock testing
if __name__ == "__main__":
    pre_handler = DataPreHandler(batch_size=5)
    
    mock_events = [
        ({"source": {"table": "can_lam_sang"}, "after": {"id": 101, "dot_dieu_tri_id": "DT001", "ten_chi_so": "Đường huyết"}}, 1),
        ({"source": {"table": "benh_nhan"}, "after": {"id": "P1", "ho_ten": "Nguyễn Văn A"}}, 2),  # Should go first despite appending second
        ({"source": {"table": "can_lam_sang"}, "after": {"id": 102, "dot_dieu_tri_id": "DT001", "ten_chi_so": "Nhịp tim"}}, 3)
    ]
    
    for evt, tag in mock_events:
        pre_handler.add_event(evt, tag)
        
    print("Processing Mock Batch...")
    processed, tags = pre_handler.flush()
    import json
    print("Tags to ACK:", tags)
    print(json.dumps(processed, indent=2))
