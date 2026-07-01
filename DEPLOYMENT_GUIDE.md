# Deployment Guide: FastAPI App on an Oracle VM with GitHub Actions

This guide walks you through deploying the FastAPI service from scratch to a free Oracle VM using GitHub Actions and Docker.

## 1. Prerequisites

Before you begin, make sure you have:

- A GitHub account
- A GitHub repository containing this project
- An Oracle Cloud Infrastructure (OCI) account
- A free Oracle VM instance running Ubuntu or similar Linux
- SSH access to the VM
- Docker installed on the VM
- A public IP address or hostname for the VM

## 2. Prepare the Oracle VM

Connect to your VM over SSH:

```bash
ssh <your-user>@<your-vm-public-ip>
```

You can automate the usual setup steps with the included script:

```bash
curl -fsSL https://raw.githubusercontent.com/boofinka/ci-cd-python-microservice/main/scripts/setup-vm.sh -o setup-vm.sh
chmod +x setup-vm.sh
./setup-vm.sh
```

If you prefer to run the steps manually, the equivalent commands are:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

The setup script is idempotent, so future runs will skip Docker installation if it is already present and will also open TCP port 443 for HTTPS traffic.

Log out and back in so the Docker group takes effect.

Verify Docker is working:

```bash
docker --version
```

Allow traffic on port 80:

If you are using UFW:

```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

If you are using OCI security lists or firewall rules, make sure inbound TCP port 80 is open.

## 3. Create a GitHub Repository Secret

In your GitHub repository:

1. Open Settings
2. Go to Secrets and variables → Actions
3. Create the following repository secrets:
   - `ORACLE_VM_HOST`: your VM public IP or hostname
   - `ORACLE_VM_USER`: your SSH username, usually `ubuntu` or `opc`
   - `ORACLE_VM_SSH_KEY`: the private SSH key that matches the public key on the VM

## 4. Make Sure the Repository Workflow Is Present

The repository already contains a GitHub Actions workflow at:

- [.github/workflows/ci-cd.yaml](.github/workflows/ci-cd.yaml)

That workflow will:

1. install dependencies
2. run tests
3. build a Docker image
4. push it to GHCR
5. deploy it to your Oracle VM over SSH

## 5. Push the Code to GitHub

From your local machine:

```bash
git add .
git commit -m "Prepare VM deployment"
git push origin main
```

GitHub Actions will start automatically.

## 6. Watch the GitHub Actions Run

Go to:

- GitHub → Your repository → Actions

You should see the workflow running through:

- `test`
- `build-and-push`
- `deploy`

If anything fails, open the failed job and read the logs.

## 7. Verify the App on the VM

Once deployment succeeds, test the app from the VM itself:

```bash
curl http://127.0.0.1/health
```

You should get a response like:

```json
{"status":"ok"}
```

Test from outside the VM using your public IP:

```bash
curl http://<your-vm-public-ip>/health
```

## 8. Check the Running Container

On the VM, you can inspect the container with:

```bash
docker ps
docker logs python-microservice
```

## 9. Common Problems and Fixes

### Problem: GitHub Actions cannot connect to the VM

Possible causes:

- the SSH key is wrong
- the username is wrong
- port 22 is blocked
- the VM public IP is incorrect

Fix:

- verify the SSH secret contents
- test SSH manually from your machine:

```bash
ssh -i /path/to/private_key <user>@<vm-ip>
```

### Problem: The app is not reachable on port 80

Possible causes:

- Docker container did not start
- port 80 is blocked by firewall or OCI security rules
- the app inside the container is not listening on port 8000

Fix:

- check container logs
- check Docker container status
- open port 80 in the VM firewall and OCI security list

### Problem: The container exits immediately

Possible causes:

- the image failed to start
- the app crashed due to an environment issue

Fix:

- inspect logs with:

```bash
docker logs python-microservice
```

## 10. Optional: Make the App More Production-Ready

After the initial deployment works, you may want to add:

- HTTPS with Nginx or Caddy
- a domain name
- Docker Compose for easier management
- persistent logs
- environment variables
- a reverse proxy for better security

## 11. Expected Result

When everything is configured correctly, the app should be available at:

```text
http://<your-vm-public-ip>/health
```

and the response should be:

```json
{"status":"ok"}
```
