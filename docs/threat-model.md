# Security Threat Model

## Assets
- Documents (Original textual knowledge)
- Chunks (Segmented document text used for vector search)
- Embeddings (Vector representation of chunks)
- Queries (User prompts, which could contain sensitive intent)
- Chat history (Conversational context over time)
- Tenant metadata (Organizational structures and settings)
- Audit logs (Proof of access and actions)

## Attackers
- **Malicious tenant user**: Tries to access data belonging to another tenant or unauthorized data in their own tenant.
- **Compromised account**: An attacker who has stolen a valid user's JWT.
- **Curious employee**: Attempts to access internal or restricted HR/Financial data they shouldn't see.
- **Prompt injection attacker**: Tries to subvert the LLM to ignore filtering constraints or leak sensitive context.
- **Malicious API client**: An attacker constructing raw HTTP requests trying to bypass the UI constraints, tamper with JWT payloads, or inject false identifiers.

## Attack Surfaces
- **Authentication**: JWT token issuance, validation, and parsing.
- **API (FastAPI)**: HTTP endpoints handling user inputs, parameters, and roles.
- **Retrieval Engine**: The vector search execution and metadata filtering logic.
- **Vector Database (Qdrant)**: Where embeddings and metadata are physically stored.
- **LLM Context Window**: The assembled text sent to the LLM (where data leakage actually occurs).
- **Documents**: Malicious text deliberately inserted into documents for indirect prompt injection.
- **Audit APIs**: Attempting to hide tracks by tampering with logs.
- **Dashboard**: The UI reflecting security metrics and data visibility.

## Security Assumptions
1. The `JWT_SECRET_KEY` is securely stored and only known to the RAGX authentication server.
2. The Postgres and Qdrant instances are not exposed to the public internet and are only accessible by the backend.
3. The LLM provider (Gemini/Groq) treats the prompts as isolated and does not use our prompts to train base models (standard enterprise contract assumption).
4. The Qdrant connection is trusted.
