import pytest
import sys
import os
import io
import time
import json

class CustomPlugin:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
        self.results = []
        self.start_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            if report.passed:
                self.passed += 1
                self.results.append({"nodeid": report.nodeid, "outcome": "passed", "duration": report.duration})
            elif report.failed:
                self.failed += 1
                self.results.append({"nodeid": report.nodeid, "outcome": "failed", "duration": report.duration, "longrepr": str(report.longrepr)})
            elif report.skipped:
                self.skipped += 1
                self.results.append({"nodeid": report.nodeid, "outcome": "skipped", "duration": report.duration})
        elif report.failed: # setup/teardown failures
            self.errors += 1
            self.results.append({"nodeid": report.nodeid, "outcome": "error", "duration": report.duration, "longrepr": str(report.longrepr)})

def main():
    plugin = CustomPlugin()
    # Suppress capture plugins that write to closed handles
    args = [
        "-q",
        "--capture=no",
        "-p", "no:sugar",
        "tests"
    ]
    
    print("Starting pytest test suite...")
    start_time = time.time()
    try:
        ret = pytest.main(args, plugins=[plugin])
    except Exception as e:
        print(f"Pytest run exception: {e}")
        ret = 1
        
    duration = round(time.time() - start_time, 2)
    total = plugin.passed + plugin.failed + plugin.skipped + plugin.errors
    
    summary = {
        "total": total,
        "passed": plugin.passed,
        "failed": plugin.failed,
        "skipped": plugin.skipped,
        "errors": plugin.errors,
        "duration_seconds": duration,
        "exit_code": int(ret),
        "results": plugin.results
    }
    
    print("\n" + "="*50)
    print(f"PYTEST SUMMARY:")
    print(f"Total:   {total}")
    print(f"Passed:  {plugin.passed}")
    print(f"Failed:  {plugin.failed}")
    print(f"Skipped: {plugin.skipped}")
    print(f"Errors:  {plugin.errors}")
    print(f"Duration: {duration}s")
    print("="*50)
    
    os.makedirs("reports/phase12", exist_ok=True)
    with open("reports/phase12/pytest_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    return ret

if __name__ == "__main__":
    sys.exit(main())
