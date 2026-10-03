# Security Policy

## Secrets Management

RAGX strictly prohibits the inclusion of any sensitive information within the source code.

- **.env usage**: All environment-specific configurations and secrets must be placed in a local `.env` file, which is ignored by Git (`.gitignore`). Do not commit this file. A template is provided in `.env.example`.
- **GitHub Actions Secrets**: For CI/CD, all secrets (`GEMINI_API_KEY`, `GROQ_API_KEY`, `JWT_SECRET`, database passwords) must be stored in GitHub Secrets. They are securely injected into the workflow at runtime and automatically masked in logs.
- **Production Secret Handling**: In production deployments, it is recommended to use a secure secret manager (e.g., AWS Secrets Manager, HashiCorp Vault) or orchestrator-native secret provisioning (e.g., Kubernetes Secrets, Docker Swarm Secrets) instead of plain `.env` files.
