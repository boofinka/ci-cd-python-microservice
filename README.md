# CI/CD Python Microservice (FastAPI + Docker + GitHub Actions + Kubernetes)

A production‑style Python FastAPI microservice with a complete CI/CD pipeline using:

- FastAPI for the application  
- Docker for containerization  
- GitHub Actions for CI/CD  
- GitHub Container Registry (GHCR) for image storage  
- Kubernetes for deployment  
- Health checks, tests, and autoscaling‑ready manifests  

This project demonstrates real‑world DevOps practices end‑to‑end.

---

## Project Structure

```text
ci-cd-python-microservice/
│
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
│       └── test_health.py
│
├── Dockerfile
│
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
│
└── .github/
    └── workflows/
        └── ci-cd.yaml
```

---

## Features

- FastAPI microservice with health endpoint  
- Automated tests with Pytest  
- Docker multi‑stage build  
- CI pipeline: test → build → push image  
- CD pipeline: deploy to Kubernetes  
- Kubernetes Deployment, Service, Ingress  
- Readiness and liveness probes  
- GHCR integration  
- Clean, modular repository structure  

---

## Application Overview

The service exposes:

- `GET /` — returns a welcome message  
- `GET /health` — used for Kubernetes probes  

### Run locally

```bash
pip install -r app/requirements.txt
uvicorn app.main:app --reload
```

Visit:

<http://localhost:8000>

---

## Docker

### Build the image

```bash
docker build -t python-microservice .
```

### Run the container

```bash
docker run -p 8000:8000 python-microservice
```

---

## CI/CD Pipeline (GitHub Actions)

The pipeline performs:

1. Install dependencies
2. Run tests
3. Build Docker image
4. Push image to GHCR
5. Deploy it to an Oracle VM over SSH

The workflow file is located at:

`.github/workflows/ci-cd.yaml`

### Required GitHub secrets

Create these repository secrets in GitHub:

- `ORACLE_VM_HOST` — public IP or hostname of the VM
- `ORACLE_VM_USER` — SSH username (commonly `ubuntu` or `opc`)
- `ORACLE_VM_SSH_KEY` — private SSH key for the VM

The deployment step will:

- log in to GHCR
- pull the latest image
- stop any existing container named `python-microservice`
- start a new container on port `80`

---

## Oracle VM deployment notes

On the VM, ensure Docker is installed and the firewall allows TCP port `80`.

Example:

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

After the first deployment, the app should be reachable at:

```text
http://<your-vm-ip>/health
```

---

## Health Checks

Kubernetes uses:

- Liveness probe — ensures the container is healthy  
- Readiness probe — ensures the application is ready to receive traffic  

Both use the `/health` endpoint.

---

## Testing

Tests are located in:

`app/tests/`

Run tests:

```bash
pytest app/tests
```

---

## Container Registry (GHCR)

Images are pushed to:

```text
ghcr.io/<your-username>/<repo-name>:<sha>
```

Pull the latest image:

```bash
docker pull ghcr.io/<your-username>/<repo-name>:latest
```

---

## Roadmap / Possible Enhancements

- Add Helm chart  
- Add Horizontal Pod Autoscaler (HPA)  
- Add Prometheus metrics  
- Add ArgoCD GitOps pipeline  
- Add Terraform to provision the cluster  

---

## Summary

This project demonstrates a complete DevOps workflow:

Python → Docker → CI → CD → Kubernetes

It is designed to be readable, modular, and realistic — suitable for showcasing DevOps skills on GitHub.
