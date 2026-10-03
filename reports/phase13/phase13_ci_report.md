# Phase 13 CI/CD Report

## 1. CI/CD Workflow Overview
RAGX uses GitHub Actions to enforce strict Continuous Integration practices. The workflow `.github/workflows/ci.yml` triggers on `push` to `main` or `develop`, and `pull_request` against `main`.

## 2. Pipeline Stages
1. **Source Retrieval**: Checkout code.
2. **Environment Bootstrap**: Setup Python 3.12 and install/cache `pip` dependencies.
3. **Infrastructure Bootstrap**: Launch `docker compose up -d postgres qdrant redis neo4j` to provision stateful services on standard ports.
4. **Code Quality**: Lint the codebase with `ruff check .`
5. **Unit & Integration Tests**: Execute `pytest -q` which automatically validates isolated functions and integration layers against the local infrastructure.
6. **Security Validation**: Run `python -m scripts.security_test` to verify multi-tenant isolation, authorization, and RBAC rules are functioning.
7. **Golden Semantic Tests**: Run `python -m scripts.semantic_golden_test` to verify exact answers haven't regressed.
8. **Docker Build Validation**: Run `docker build` on both API and Dashboard Dockerfiles to guarantee images construct cleanly without syntax or dependency failures.

## 3. Secret and Environment Safety
- The CI pipeline sets safe dummy values for standard config variables (like `APP_ENV: testing`).
- For secure external connectivity, it uses GitHub Actions Secrets (`${{ secrets.GEMINI_API_KEY }}`, `${{ secrets.GROQ_API_KEY }}`, `${{ secrets.JWT_SECRET }}`).

## 4. Known Limitations
- The CI pipeline does not currently run the full Phase 12 validation suite (which requires massive quota/rate limits) to save money/quota. Instead, it relies on the targeted Golden Semantic Tests.
- Full end-to-end browser tests are not included for the Streamlit dashboard.
