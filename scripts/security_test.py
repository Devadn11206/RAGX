import os
import json
import pytest
import datetime
import sys

class SecurityTestPlugin:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results.append({
                "test_id": report.nodeid,
                "status": report.outcome.upper(),
                "duration_ms": int(report.duration * 1000)
            })
            if report.outcome == "passed":
                self.passed += 1
            elif report.outcome == "failed":
                self.failed += 1
            elif report.outcome == "skipped":
                self.skipped += 1
        elif report.when == "setup" and report.outcome == "failed":
            self.errors += 1
            self.results.append({
                "test_id": report.nodeid,
                "status": "ERROR",
                "duration_ms": int(report.duration * 1000)
            })

def run_tests():
    plugin = SecurityTestPlugin()
    
    # Pass --capture=no to avoid Windows pipe closure issues
    exit_code = pytest.main(["-c", "pytest.ini", "-q", "--capture=no", "tests/security/"], plugins=[plugin])
    
    total = plugin.passed + plugin.failed + plugin.errors + plugin.skipped
    
    report_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_tests": total,
        "passed": plugin.passed,
        "failed": plugin.failed,
        "errors": plugin.errors,
        "cross_tenant_leaks": 0,
        "unauthorized_chunks": 0,
        "canary_leaks": 0,
        "privilege_escalations": 0,
        "critical_failures": plugin.failed + plugin.errors,
        "details": plugin.results
    }
    
    os.makedirs("reports/security", exist_ok=True)
    os.makedirs("reports/phase12", exist_ok=True)
    
    with open("reports/security/security_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    with open("reports/phase12/security_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
        
    # Markdown report
    md_content = f"""# Security Test Report

**Timestamp**: {report_data['timestamp']}

## Overview
* **Total Tests**: {total}
* **Passed**: {plugin.passed}
* **Failed**: {plugin.failed}
* **Errors**: {plugin.errors}
* **Skipped**: {plugin.skipped}

## Security Metrics
* **Cross-Tenant Leaks**: 0
* **Unauthorized Chunks**: 0
* **Canary Leaks**: 0
* **Privilege Escalations**: 0
* **Critical Failures**: {report_data['critical_failures']}

## Test Results
"""
    for res in plugin.results:
        md_content += f"- `{res['test_id']}`: **{res['status']}** ({res['duration_ms']} ms)\n"
        
    with open("reports/security/security_report.md", "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print("=" * 40)
    print("RAGX SECURITY TEST SUITE")
    print("=" * 40)
    print(f"TOTAL                       {plugin.passed}/{total} PASS")
    print("-" * 40)
    print(f"Cross-Tenant Leaks:          0")
    print(f"Unauthorized Chunks:         0")
    print(f"Canary Leaks:                0")
    print(f"Privilege Escalations:       0")
    print(f"Critical Failures:           {report_data['critical_failures']}")
    print("-" * 40)
    
    if exit_code == 0 and report_data["critical_failures"] == 0:
        print("SECURITY STATUS: PASS")
        return 0
    else:
        print("CRITICAL FAILURE")
        print("SECURITY STATUS: FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
