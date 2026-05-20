"""
Push saved benchmark JSON result to Prometheus Pushgateway.
Usage:
    python3 push_results.py results/benchmark_20260519_134600.json
    python3 push_results.py          # auto-picks the latest file in results/
"""
import sys
import json
import glob
import os

from benchmark import push_results_to_prometheus

def latest_result(results_dir="results"):
    files = glob.glob(os.path.join(results_dir, "*.json"))
    if not files:
        print(f"No JSON files found in {results_dir}/")
        sys.exit(1)
    return max(files, key=os.path.getmtime)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        # If path doesn't exist as-is, try resolving relative to script dir
        if not os.path.exists(path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt = os.path.join(script_dir, os.path.basename(path))
            if os.path.exists(alt):
                path = alt
    else:
        path = latest_result()
    print(f"Loading: {path}")
    with open(path) as f:
        data = json.load(f)
    push_results_to_prometheus(data)
    print("Done — open Grafana at http://localhost:3000")
