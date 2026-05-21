#!/usr/bin/env python3
"""
validate_fhir_batch.py — Công cụ batch validation FHIR resources bằng HL7 Validator CLI.

Đọc FHIR resources từ MongoDB, validate bằng HL7 Validator CLI chính thức,
tạo báo cáo chất lượng dữ liệu.

Sử dụng:
    python3 validate_fhir_batch.py                     # Validate tất cả
    python3 validate_fhir_batch.py --type Patient       # Chỉ validate Patient
    python3 validate_fhir_batch.py --limit 50           # Giới hạn 50 resources
    python3 validate_fhir_batch.py --output report.json # Xuất báo cáo JSON
    python3 validate_fhir_batch.py --compare            # So sánh Pydantic vs HL7 CLI
"""
import argparse
import json
import sys
import time
from pymongo import MongoClient
from validator import FHIRValidator, HL7ValidatorCLI
from utils.logger import log

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "fhir_db"

FHIR_RESOURCE_TYPES = [
    "Patient", "Practitioner", "Encounter",
    "MedicationRequest", "Procedure", "Observation",
    "ClinicalImpression"
]


def fetch_resources(resource_type: str = None, limit: int = 100) -> list:
    """Lấy FHIR resources từ MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    resources = []

    types = [resource_type] if resource_type else FHIR_RESOURCE_TYPES
    
    for rt in types:
        collection = db[rt]
        count = collection.count_documents({})
        if count == 0:
            continue
        
        cursor = collection.find({}).limit(limit)
        for doc in cursor:
            doc.pop("_id", None)  # Xóa MongoDB _id
            resources.append(doc)
    
    client.close()
    log.info(f"Đã lấy {len(resources)} resources từ MongoDB")
    return resources


def run_pydantic_validation(resources: list) -> list:
    """Validate bằng Pydantic (Level 1) — đo thời gian."""
    from fhir.resources import get_fhir_model_class
    
    results = []
    for res in resources:
        rt = res.get("resourceType", "Unknown")
        start = time.time()
        
        try:
            ModelClass = get_fhir_model_class(rt)
            obj = ModelClass(**res)
            is_valid, error_msg = FHIRValidator.validate(obj)
            duration_ms = (time.time() - start) * 1000
            
            results.append({
                "resourceType": rt,
                "resourceId": res.get("id", "Unknown"),
                "valid": is_valid,
                "errors": [{"severity": "error", "message": error_msg, "location": ""}] if not is_valid else [],
                "warnings": [],
                "info": [],
                "duration_ms": duration_ms
            })
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            results.append({
                "resourceType": rt,
                "resourceId": res.get("id", "Unknown"),
                "valid": False,
                "errors": [{"severity": "error", "message": str(e), "location": ""}],
                "warnings": [],
                "info": [],
                "duration_ms": duration_ms
            })
    
    return results


def compare_validators(resources: list) -> dict:
    """
    So sánh Pydantic (Level 1) vs HL7 CLI (Level 2).
    Output hữu ích cho thesis.
    """
    print("\n" + "="*60)
    print("  SO SÁNH: Pydantic Validation vs HL7 FHIR Validator CLI")
    print("="*60)

    # Pydantic
    print(f"\n[1/2] Đang validate {len(resources)} resources bằng Pydantic...")
    pydantic_start = time.time()
    pydantic_results = run_pydantic_validation(resources)
    pydantic_total = (time.time() - pydantic_start) * 1000

    # HL7 CLI
    print(f"[2/2] Đang validate {len(resources)} resources bằng HL7 Validator CLI...")
    hl7 = HL7ValidatorCLI()
    hl7_start = time.time()
    hl7_results = hl7.validate_batch(resources)
    hl7_total = (time.time() - hl7_start) * 1000

    # Tổng hợp
    pydantic_valid = sum(1 for r in pydantic_results if r["valid"])
    hl7_valid = sum(1 for r in hl7_results if r["valid"])
    pydantic_avg = sum(r["duration_ms"] for r in pydantic_results) / len(pydantic_results) if pydantic_results else 0
    hl7_avg = sum(r["duration_ms"] for r in hl7_results) / len(hl7_results) if hl7_results else 0

    comparison = {
        "total_resources": len(resources),
        "pydantic": {
            "valid": pydantic_valid,
            "invalid": len(resources) - pydantic_valid,
            "validity_rate": f"{pydantic_valid/len(resources)*100:.1f}%",
            "total_time_ms": round(pydantic_total, 2),
            "avg_time_per_resource_ms": round(pydantic_avg, 2)
        },
        "hl7_cli": {
            "valid": hl7_valid,
            "invalid": len(resources) - hl7_valid,
            "validity_rate": f"{hl7_valid/len(resources)*100:.1f}%",
            "total_time_ms": round(hl7_total, 2),
            "avg_time_per_resource_ms": round(hl7_avg, 2)
        },
        "speedup_factor": round(hl7_total / pydantic_total, 1) if pydantic_total > 0 else "N/A"
    }

    # In kết quả
    print("\n" + "-"*60)
    print(f"{'Metric':<35} {'Pydantic':>10} {'HL7 CLI':>10}")
    print("-"*60)
    print(f"{'Resources valid':<35} {pydantic_valid:>10} {hl7_valid:>10}")
    print(f"{'Resources invalid':<35} {len(resources)-pydantic_valid:>10} {len(resources)-hl7_valid:>10}")
    print(f"{'Validity rate':<35} {comparison['pydantic']['validity_rate']:>10} {comparison['hl7_cli']['validity_rate']:>10}")
    print(f"{'Total time (ms)':<35} {pydantic_total:>10.1f} {hl7_total:>10.1f}")
    print(f"{'Avg per resource (ms)':<35} {pydantic_avg:>10.2f} {hl7_avg:>10.2f}")
    print(f"{'Speed ratio':<35} {'1x':>10} {comparison['speedup_factor']}x")
    print("-"*60)

    # Tìm differences (HL7 phát hiện lỗi mà Pydantic không)
    differences = []
    for p, h in zip(pydantic_results, hl7_results):
        if p["valid"] and not h["valid"]:
            differences.append({
                "resourceType": h["resourceType"],
                "resourceId": h["resourceId"],
                "pydantic": "PASS",
                "hl7": "FAIL",
                "hl7_errors": h["errors"]
            })
    
    if differences:
        print(f"\n⚠ {len(differences)} resources passed Pydantic but FAILED HL7 CLI:")
        for d in differences[:5]:
            print(f"  - {d['resourceType']}/{d['resourceId']}: {d['hl7_errors'][0]['message'][:80]}")
    
    comparison["differences"] = differences
    return comparison


def main():
    parser = argparse.ArgumentParser(description="FHIR Batch Validator — HL7 Validator CLI")
    parser.add_argument("--type", type=str, help="Resource type to validate (e.g. Patient)")
    parser.add_argument("--limit", type=int, default=100, help="Max resources per type (default: 100)")
    parser.add_argument("--output", type=str, help="Output JSON report file path")
    parser.add_argument("--compare", action="store_true", help="Compare Pydantic vs HL7 CLI")
    parser.add_argument("--pydantic-only", action="store_true", help="Only use Pydantic validation")
    args = parser.parse_args()

    # Lấy resources từ MongoDB
    resources = fetch_resources(resource_type=args.type, limit=args.limit)
    if not resources:
        print("Không tìm thấy FHIR resources trong MongoDB.")
        sys.exit(0)

    if args.compare:
        report = compare_validators(resources)
    elif args.pydantic_only:
        results = run_pydantic_validation(resources)
        validator = HL7ValidatorCLI()  # just for report generation
        report = validator.generate_report(results)
        print(f"\n[Pydantic] Valid: {report['summary']['valid']}/{report['summary']['total_resources']} "
              f"({report['summary']['validity_rate']})")
    else:
        hl7 = HL7ValidatorCLI()
        if not hl7.is_available():
            print("HL7 Validator CLI không khả dụng. Chạy: make download-validator")
            sys.exit(1)
        
        results = hl7.validate_batch(resources)
        report = hl7.generate_report(results)

        print(f"\n{'='*50}")
        print(f"  HL7 FHIR Validation Report")
        print(f"{'='*50}")
        s = report["summary"]
        print(f"  Total:    {s['total_resources']}")
        print(f"  Valid:    {s['valid']} ({s['validity_rate']})")
        print(f"  Invalid:  {s['invalid']}")
        print(f"  Errors:   {s['total_errors']}")
        print(f"  Warnings: {s['total_warnings']}")
        print(f"  Avg time: {s['avg_validation_time_ms']}ms/resource")
        print(f"{'='*50}")

        if report["by_resource_type"]:
            print("\n  By Resource Type:")
            for rt, stats in report["by_resource_type"].items():
                print(f"    {rt}: {stats['valid']}/{stats['total']} valid")

    # Xuất báo cáo JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nBáo cáo đã xuất: {args.output}")


if __name__ == "__main__":
    main()
