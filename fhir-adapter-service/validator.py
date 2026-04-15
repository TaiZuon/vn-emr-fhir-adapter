# fhir-adapter-service/validator.py
import json
import os
import subprocess
import tempfile
import time
from pydantic import ValidationError
from utils.logger import log

# ========== Cấu hình HL7 Validator CLI ==========
VALIDATOR_JAR = os.path.join(os.path.dirname(__file__), "validator_cli.jar")
FHIR_VERSION = "5.0.0"


class FHIRValidator:
    """
    Level 1: Pydantic-based validation (real-time, inline trong pipeline).
    Dùng fhir.resources library để kiểm tra schema FHIR cơ bản.
    """
    @staticmethod
    def validate(resource):
        """
        Kiểm tra tính hợp lệ của một FHIR Resource object.
        Trả về: (is_valid, error_message)
        """
        try:
            resource.dict()
            return True, None

        except ValidationError as e:
            errors = e.errors()
            readable_errors = []
            for err in errors:
                loc = " -> ".join([str(item) for item in err['loc']])
                msg = err['msg']
                readable_errors.append(f"[{loc}]: {msg}")
            
            return False, " | ".join(readable_errors)
        except Exception as e:
            return False, str(e)


class HL7ValidatorCLI:
    """
    Level 2: HL7 FHIR Validator CLI (deep validation, batch/audit mode).
    Sử dụng validator_cli.jar chính thức từ HL7 để validate theo 
    StructureDefinition, cardinality, terminology binding, v.v.
    
    Không dùng inline trong pipeline (JVM startup ~3-5s).
    Dùng cho: batch audit, thesis comparison, quality report.
    """

    def __init__(self, jar_path: str = None):
        self.jar_path = jar_path or VALIDATOR_JAR
        self._available = None

    def is_available(self) -> bool:
        """Kiểm tra validator JAR và Java có sẵn không."""
        if self._available is not None:
            return self._available
        
        if not os.path.isfile(self.jar_path):
            log.warning(f"HL7 Validator JAR không tìm thấy: {self.jar_path}")
            self._available = False
            return False
        
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True, text=True, timeout=10
            )
            self._available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._available = False
        
        return self._available

    def validate_resource(self, fhir_json: dict) -> dict:
        """
        Validate một FHIR resource dict bằng HL7 Validator CLI.
        
        Returns:
            {
                "valid": bool,
                "errors": [{"severity": str, "message": str, "location": str}],
                "warnings": [...],
                "info": [...],
                "duration_ms": float
            }
        """
        if not self.is_available():
            return {
                "valid": False,
                "errors": [{"severity": "fatal", "message": "HL7 Validator CLI không khả dụng", "location": ""}],
                "warnings": [], "info": [], "duration_ms": 0
            }

        start_time = time.time()
        
        # Ghi resource ra file tạm
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, prefix='fhir_validate_'
        ) as tmp:
            json.dump(fhir_json, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            cmd = [
                "java", "-jar", self.jar_path,
                tmp_path,
                "-version", FHIR_VERSION,
                "-output-style", "json",
                "-tx", "n/a",
                "-extension", "any"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60s timeout
            )

            duration_ms = (time.time() - start_time) * 1000
            return self._parse_output(result.stdout, result.stderr, result.returncode, duration_ms)

        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "valid": False,
                "errors": [{"severity": "fatal", "message": "Validator timeout (>60s)", "location": ""}],
                "warnings": [], "info": [], "duration_ms": duration_ms
            }
        finally:
            os.unlink(tmp_path)

    def validate_batch(self, resources: list) -> list:
        """
        Validate nhiều FHIR resources. Trả về list kết quả.
        """
        results = []
        for i, res in enumerate(resources):
            log.info(f"HL7 Validating resource {i+1}/{len(resources)}: {res.get('resourceType', 'Unknown')}")
            result = self.validate_resource(res)
            result["resourceType"] = res.get("resourceType", "Unknown")
            result["resourceId"] = res.get("id", "Unknown")
            results.append(result)
        return results

    def _parse_output(self, stdout: str, stderr: str, returncode: int, duration_ms: float) -> dict:
        """Parse output từ HL7 Validator CLI."""
        errors = []
        warnings = []
        info = []

        # Thử parse JSON output trước
        try:
            # HL7 Validator trả OperationOutcome JSON
            oo = json.loads(stdout)
            if oo.get("resourceType") == "OperationOutcome":
                for issue in oo.get("issue", []):
                    entry = {
                        "severity": issue.get("severity", "unknown"),
                        "message": issue.get("diagnostics", issue.get("details", {}).get("text", "")),
                        "location": ", ".join(issue.get("expression", issue.get("location", [])))
                    }
                    if issue.get("severity") in ("fatal", "error"):
                        errors.append(entry)
                    elif issue.get("severity") == "warning":
                        warnings.append(entry)
                    else:
                        info.append(entry)
                
                return {
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings,
                    "info": info,
                    "duration_ms": duration_ms
                }
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: parse text output
        combined = stdout + "\n" + stderr
        for line in combined.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "Error" in line or "FAILURE" in line:
                errors.append({"severity": "error", "message": line, "location": ""})
            elif "Warning" in line:
                warnings.append({"severity": "warning", "message": line, "location": ""})
            elif "Information" in line or "Success" in line:
                info.append({"severity": "information", "message": line, "location": ""})

        return {
            "valid": returncode == 0 and len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "duration_ms": duration_ms
        }

    def generate_report(self, results: list) -> dict:
        """
        Tạo báo cáo tổng hợp từ batch validation results.
        Hữu ích cho thesis: so sánh tỷ lệ valid, loại lỗi phổ biến, thời gian.
        """
        total = len(results)
        valid_count = sum(1 for r in results if r["valid"])
        total_errors = sum(len(r["errors"]) for r in results)
        total_warnings = sum(len(r["warnings"]) for r in results)
        avg_duration = sum(r["duration_ms"] for r in results) / total if total > 0 else 0

        # Thống kê lỗi theo resource type
        errors_by_type = {}
        for r in results:
            rt = r.get("resourceType", "Unknown")
            if rt not in errors_by_type:
                errors_by_type[rt] = {"total": 0, "valid": 0, "invalid": 0}
            errors_by_type[rt]["total"] += 1
            if r["valid"]:
                errors_by_type[rt]["valid"] += 1
            else:
                errors_by_type[rt]["invalid"] += 1

        return {
            "summary": {
                "total_resources": total,
                "valid": valid_count,
                "invalid": total - valid_count,
                "validity_rate": f"{(valid_count / total * 100):.1f}%" if total > 0 else "N/A",
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "avg_validation_time_ms": round(avg_duration, 2)
            },
            "by_resource_type": errors_by_type,
            "details": results
        }
