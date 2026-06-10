# Deloitte CI/CD Demo

A production-style demonstration of continuous integration and delivery for a containerised Python Flask API. The project models how an enterprise team ships software: automated tests gate every change, Docker images are built and published to a registry, and deployments are validated with smoke tests before release.

## Overview

| Area | What this project demonstrates |
|------|--------------------------------|
| **CI/CD** | Multi-job GitHub Actions pipeline with dependency chains, secrets, and conditional deploy logic |
| **Containers** | Docker image with non-root user, layer caching, and health checks |
| **Registry** | Automated builds, SHA-based tags, and push to Docker Hub |
| **Quality** | Shift-left testing — deployment is blocked if tests fail |
| **Local dev** | Docker Compose for reproducible environments |
| **Governance** | Branch protection and required status checks on pull requests |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Developer  │────▶│  GitHub (main)   │────▶│  Docker Hub     │
│  PR / push  │     │  Actions CI/CD   │     │  deloitte-demo  │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ test          │  pytest (unit tests)
                    │      ↓        │
                    │ build-and-push│  Docker build + push
                    │      ↓        │
                    │ deploy        │  pull, run, smoke test (main only)
                    └───────────────┘
```

### Pipeline stages

1. **Test** — Runs on every push and pull request to `main`. Installs dependencies and executes `pytest`. Failure stops the pipeline.
2. **Build and push** — Runs only after tests pass (`needs: test`). Logs into Docker Hub, builds the image with Buildx and GHA layer caching, tags with commit SHA and `latest`, then pushes to the registry.
3. **Deploy (simulated)** — Runs only on pushes to `main` (`if: github.ref == 'refs/heads/main'`). Pulls the latest image, starts a container, runs a smoke test against `/health`, then tears down.

## Project structure

```
deloitte-cicd-demo/
├── app/
│   ├── app.py              # Flask application
│   └── requirements.txt    # Python dependencies
├── tests/
│   └── test_app.py         # Unit tests (pytest)
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # CI/CD pipeline definition
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Local development stack
├── .gitignore
└── README.md
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check (used by smoke tests and Docker healthcheck) |
| `GET` | `/version` | Application version |

Example:

```bash
curl http://localhost:5002/health
# {"service":"deloitte-demo","status":"healthy"}
```

## Prerequisites

- **Python 3.12+** (for local development and tests)
- **Docker Desktop** (for building and running containers)
- **Docker Compose** (included with Docker Desktop)
- **Git** and a **GitHub** account (for CI/CD and branch workflow)
- **Docker Hub** account (for registry push in CI — optional for local-only work)

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/hertheyhermee/deloitte-cicd-demo.git
cd deloitte-cicd-demo
```

### 2. Python virtual environment (recommended)

macOS often does not provide a `python` command; use `python3` or a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
```

### 3. Run tests

```bash
python -m pytest tests/ -v
```

All tests must pass before a change is merged — the same gate runs in CI.

### 4. Run the app locally (without Docker)

```bash
cd app
python app.py
```

The app listens on port **5000**. On macOS, port 5000 may be used by AirPlay Receiver; disable it in **System Settings → General → AirDrop & Handoff → AirPlay Receiver**, or use Docker Compose (port **5002**) instead.

### 5. Run with Docker Compose (recommended for local dev)

```bash
docker compose up --build
```

| Setting | Value |
|---------|-------|
| URL | http://localhost:5002 |
| Health check | `curl -f http://localhost:5002/health` |
| Port mapping | Host `5002` → container `5000` |

Docker Compose configures a production-like environment with health checks, restart policy, and `FLASK_ENV=production`.

### 6. Build and run with Docker directly

```bash
docker build -t deloitte-demo:local .
docker run -p 5001:5000 deloitte-demo:local
```

Use **5001** (or another free host port) if port 5000 is already in use on your machine.

## Branching and pull request workflow

This repository follows a **trunk-based** workflow aligned with enterprise practice:

| Branch | Purpose |
|--------|---------|
| `main` | Protected default branch; only merged, reviewed code lands here |
| `feature/*` | Short-lived branches for new work (e.g. `feature/add-version-endpoint`) |

### Typical workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```
2. Make changes, run tests locally:
   ```bash
   python -m pytest tests/ -v
   ```
3. Commit and push:
   ```bash
   git add .
   git commit -m "Add your feature"
   git push -u origin feature/your-feature-name
   ```
4. Open a **pull request** into `main` on GitHub.
5. Wait for the **CI pipeline** to pass (required status check).
6. Request review and merge after approval.

Direct pushes to `main` trigger the full pipeline including deploy; feature branches and PRs run **test** and **build-and-push** but not **deploy**.

## Branch protection (GitHub)

Configure these settings under **Settings → Branches → Branch protection rules** for `main`:

- [x] Require a pull request before merging
- [x] Require status checks to pass before merging
  - Required check: **Run Tests** (and optionally **Build and Push Docker Image**)
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

This enforces that no code reaches `main` without passing automated tests — modelling how enterprise teams gate production releases.

## CI/CD configuration

### GitHub Actions secrets

Add these under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not your account password) |

Create a token at [Docker Hub → Account Settings → Security](https://hub.docker.com/settings/security).

### Image tagging

Images are published as:

- `DOCKERHUB_USERNAME/deloitte-demo:latest` — latest build from `main`
- `DOCKERHUB_USERNAME/deloitte-demo:sha-<commit>` — immutable tag per commit

### Docker production practices

The `Dockerfile` applies several production conventions:

- **Slim base image** (`python:3.12-slim`) for a smaller attack surface
- **Layer caching** — `requirements.txt` is copied and installed before application code so dependency layers are reused across builds
- **Non-root user** — application runs as `appuser`, not root
- **Explicit port** — `EXPOSE 5000` documents the service port

`docker-compose.yml` adds a **health check** that polls `/health` every 10 seconds.

## Smoke testing

After deployment (in CI or manually), validate the running container:

```bash
curl --fail http://localhost:5000/health
```

The CI **deploy** job automates this: pull image → run container → `curl --fail` on `/health` → stop and remove container. A non-200 response fails the job and blocks the release.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `python: command not found` | Use `python3` or activate the `.venv` |
| `docker build` requires 1 argument | Add build context: `docker build -t deloitte-demo:local .` |
| `docker build` EOF error | Start Docker Desktop and wait until the daemon is running |
| Port 5000 already in use (macOS) | Use `docker run -p 5001:5000` or Docker Compose on port 5002 |
| GHA cache export error | Ensure `docker/setup-buildx-action@v3` is present before `build-push-action` |

## Tech stack

- **Runtime:** Python 3.12, Flask 3.0
- **Testing:** pytest
- **Containers:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (checkout, setup-python, login-action, setup-buildx, metadata-action, build-push-action)
- **Registry:** Docker Hub

## License

This project is provided as a demonstration for CI/CD and DevOps learning purposes.
