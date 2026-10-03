# Security Test Report

**Timestamp**: 2026-10-03T00:17:52.563927Z

## Overview
* **Total Tests**: 11
* **Passed**: 11
* **Failed**: 0
* **Errors**: 0
* **Skipped**: 0

## Security Metrics
* **Cross-Tenant Leaks**: 0
* **Unauthorized Chunks**: 0
* **Canary Leaks**: 0
* **Privilege Escalations**: 0
* **Critical Failures**: 0

## Test Results
- `tests/security/test_authentication.py::test_missing_auth_header`: **PASSED** (8 ms)
- `tests/security/test_authentication.py::test_malformed_jwt`: **PASSED** (6 ms)
- `tests/security/test_authentication.py::test_expired_jwt`: **PASSED** (9 ms)
- `tests/security/test_authentication.py::test_tampered_jwt`: **PASSED** (6 ms)
- `tests/security/test_authorization.py::test_unauthorized_role`: **PASSED** (218 ms)
- `tests/security/test_authorization.py::test_authorized_role`: **PASSED** (127 ms)
- `tests/security/test_prompt_injection.py::test_ignore_acl_prompt`: **PASSED** (123 ms)
- `tests/security/test_retrieval_leakage.py::test_canary_leak`: **PASSED** (84 ms)
- `tests/security/test_role_escalation.py::test_role_spoofing_in_body`: **PASSED** (60 ms)
- `tests/security/test_tenant_isolation.py::test_cross_tenant_query`: **PASSED** (57 ms)
- `tests/security/test_tenant_isolation.py::test_direct_cross_tenant_access`: **PASSED** (6 ms)
