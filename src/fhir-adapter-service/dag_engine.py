import json
import concurrent.futures
from typing import List, Callable, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

class RuleNode(BaseModel):
    """
    Represents a single node in the Transformation DAG.
    """
    id: str
    condition: Optional[Callable] = None 
    action: Optional[Callable] = None
    precedence: int = 0
    cardinality: str = "0..1"
    children: List['RuleNode'] = Field(default_factory=list)
    heavy: bool = False
    is_array: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merges dict2 into dict1, merging list elements by index."""
    for key, val in dict2.items():
        if isinstance(val, dict) and key in dict1 and isinstance(dict1[key], dict):
            deep_merge(dict1[key], val)
        elif isinstance(val, list) and key in dict1 and isinstance(dict1[key], list):
            # Merge by index (pad if needed)
            while len(dict1[key]) < len(val):
                dict1[key].append(None)
            for i, item in enumerate(val):
                if item is None:
                    continue
                if isinstance(item, dict) and dict1[key][i] is not None and isinstance(dict1[key][i], dict):
                    deep_merge(dict1[key][i], item)
                else:
                    dict1[key][i] = item
        else:
            dict1[key] = val
    return dict1

class TransformMap:
    """
    Manages the Directed Acyclic Graph (DAG) for FHIR transformation.
    Executes rules using Depth-First Search (DFS) and ThreadPoolExecutor.
    """
    def __init__(self, root_nodes: List[RuleNode]):
        # Sort root nodes by precedence descending
        self.root_nodes = sorted(root_nodes, key=lambda n: n.precedence, reverse=True)

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the DAG using DFS and Divide-and-Conquer strategy.
        Parallelizes the execution of sub-nodes.
        """
        final_result = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit root nodes
            futures = [executor.submit(self._dfs_evaluate, node, data, executor) for node in self.root_nodes]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        final_result.update(result)
                except Exception as e:
                    print(f"Error executing root node: {e}")
                    
        return final_result

    def _dfs_evaluate(self, node: RuleNode, data: Dict[str, Any], executor: concurrent.futures.ThreadPoolExecutor) -> Dict[str, Any]:
        """
        Recursive DFS evaluation. Evaluate children, then apply the current node's action.
        Uses ThreadPoolExecutor only for heavy nodes or deeply nested subtrees.
        """
        # 1. Evaluate condition (if defined and returns False, skip this node and children)
        if node.condition and not node.condition(data):
            return {}

        # 2. Divide: Process children inline or in parallel based on heavy flag / nesting
        child_results = {}
        if node.children:
            # Sort children by precedence
            sorted_children = sorted(node.children, key=lambda n: n.precedence, reverse=True)
            futures = []
            
            for child in sorted_children:
                # Priority 5: Thread Tuning. Only dispatch heavy nodes or subtrees.
                if child.heavy or len(child.children) > 0:
                    futures.append(executor.submit(self._dfs_evaluate, child, data, executor))
                else:
                    # Execute simple scalar updates synchronously on the main thread
                    try:
                        res = self._dfs_evaluate(child, data, executor)
                        if res:
                            deep_merge(child_results, res)
                    except Exception as e:
                        print(f"Error executing inline child node {child.id} in {node.id}: {e}")
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        deep_merge(child_results, res)
                except Exception as e:
                    print(f"Error executing async child node in {node.id}: {e}")

        # 3. Conquer: Execute current node's action, integrating child results
        current_result = {}
        if node.action:
            try:
                # Priority 4: Array Support. Iterate over merged_records for 1:N mapping
                if node.is_array and "merged_records" in data:
                    for record in data["merged_records"]:
                        res = node.action(record, child_results)
                        if res:
                            deep_merge(current_result, res)
                else:
                    current_result = node.action(data, child_results)
            except Exception as e:
                print(f"Action error in node {node.id}: {e}")

        # Merge child results with current node's results
        return deep_merge(child_results, current_result)

# ==========================================
# MOCK DAG TESTING
# ==========================================
def mock_action_patient_name(data: dict, child_results: dict):
    return {"name": [{"text": data.get("ho_ten")}]}

def mock_action_patient_id(data: dict, child_results: dict):
    return {"id": str(data.get("id"))}

def mock_action_patient_root(data: dict, child_results: dict):
    # Root action aggregates children and adds ResourceType
    return {
        "resourceType": "Patient",
        **child_results
    }

def run_mock_test():
    # Define leaf nodes
    name_node = RuleNode(
        id="patient_name",
        action=mock_action_patient_name,
        precedence=1
    )
    id_node = RuleNode(
        id="patient_id",
        action=mock_action_patient_id,
        precedence=10 # Higher precedence
    )

    # Define root node
    root_node = RuleNode(
        id="patient_root",
        action=mock_action_patient_root,
        precedence=100,
        children=[id_node, name_node]
    )

    dag = TransformMap([root_node])
    
    mock_data = {
        "id": 12345,
        "ho_ten": "Nguyen Van A",
        "gioi_tinh": 1
    }
    
    print("Executing Mock DAG...")
    result = dag.execute(mock_data)
    print("DAG Execution Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_mock_test()
