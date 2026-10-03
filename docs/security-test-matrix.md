# Security Test Matrix

| Category         | Attack              | Expected     | Severity | Automated |
| ---------------- | ------------------- | ------------ | -------- | --------- |
| Authentication   | Missing JWT         | 401          | High     | ✓         |
| Authentication   | Expired JWT         | 401          | High     | ✓         |
| Authentication   | Malformed JWT       | 401          | High     | ✓         |
| Authentication   | Tampered JWT        | 401          | High     | ✓         |
| Tenant Isolation | Cross-tenant query  | No leak      | Critical | ✓         |
| Tenant Isolation | Cross-tenant list   | Only own     | Critical | ✓         |
| Authorization    | Role spoofing       | Denied       | Critical | ✓         |
| ACL              | Unauthorized role   | No retrieval | Critical | ✓         |
| ACL              | Authorized role     | Retrieved    | Critical | ✓         |
| Prompt Injection | Ignore ACL          | No leak      | Critical | ✓         |
| Information Leak | Canary query        | No leak      | Critical | ✓         |
| Revocation       | Access after revoke | Denied       | Critical | ✓         |
| Audit            | Tampering           | Denied       | High     | ✓         |
