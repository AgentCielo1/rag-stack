# Deployment Automation Guide

## GitHub Actions Deployment Workflow

The `.github/workflows/deploy.yml` workflow automatically deploys the RAG stack to your server whenever you push changes to `main`.

## Setup

### 1. Generate SSH Key (on your deployment server)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -C "github-deploy"
# Press Enter twice (no passphrase recommended for CI)
```

### 2. Add Public Key to Server

```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 3. Add GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `DEPLOY_HOST` | Your server's IP or domain | `192.168.1.100` or `api.example.com` |
| `DEPLOY_USER` | SSH username | `ubuntu` or `deploy` |
| `DEPLOY_SSH_KEY` | Private key contents | (paste `~/.ssh/github_deploy`) |
| `DEPLOY_PORT` | SSH port (optional) | `22` or `2222` |
| `DEPLOY_PATH` | Remote deployment path | `~/rag-stack` or `/opt/rag-stack` |

**To get private key contents:**
```bash
cat ~/.ssh/github_deploy
# Copy everything including BEGIN/END lines
```

### 4. Prepare Your Server

SSH into your server and run:

```bash
# Create deployment directory
mkdir -p ~/rag-stack
cd ~/rag-stack

# Initialize empty git repo (optional, for tracking deploys)
git init

# Create .env file with your settings
cat > .env << EOF
SEARXNG_BASE_URL=http://your-domain:8888/
PROXY_HTTP=http://proxy.example.com:8080
PROXY_HTTPS=http://proxy.example.com:8080
EOF

# Install Docker (if not already installed)
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

## Deployment Flow

1. **Push to main**
   ```bash
   git add -A
   git commit -m "Update configuration"
   git push origin main
   ```

2. **Workflow triggers automatically:**
   - Validates docker-compose.yml
   - Connects via SSH
   - Pulls latest images
   - Stops old containers
   - Starts new containers
   - Runs health checks
   - Rolls back on failure

3. **Check deployment status:**
   - Go to https://github.com/AgentCielo1/rag-stack/actions
   - Click latest "Deploy RAG Stack" workflow
   - View logs in real-time

## Manual Deployment

Trigger manually anytime:

1. Go to Actions tab
2. Click "Deploy RAG Stack" workflow
3. Click "Run workflow"
4. Choose environment (production/staging)
5. Click "Run workflow"

## SSH Access to Server

Test your SSH setup:

```bash
ssh -i ~/.ssh/github_deploy -p 22 ubuntu@192.168.1.100
```

From server, verify RAG stack:

```bash
cd ~/rag-stack
docker compose ps
./rag-stack.sh health
```

## Secrets Best Practices

- **Never commit SSH keys** to git
- **Rotate keys regularly** (quarterly)
- **Use environment-specific secrets** for prod/staging
- **Monitor Actions logs** for failed deployments
- **Keep backup copies** of SSH keys in secure location

## Rollback on Failure

The workflow automatically:
1. Backs up `docker-compose.yml` before deployment
2. Rolls back if services fail health checks
3. Restores previous configuration

Manual rollback:

```bash
ssh ubuntu@your-server
cd ~/rag-stack
mv docker-compose.yml.bak docker-compose.yml
docker compose down -v
docker compose up -d
```

## Troubleshooting

**SSH connection refused:**
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/github_deploy
chmod 700 ~/.ssh

# Verify public key on server
cat ~/.ssh/authorized_keys | grep github_deploy

# Test connection
ssh -i ~/.ssh/github_deploy ubuntu@your-server
```

**Deployment hangs:**
- Increase timeout in workflow (change `timeout-minutes`)
- Check server disk space: `df -h`
- Check Docker daemon: `docker ps`

**Services fail health checks:**
```bash
# SSH to server and check logs
docker compose logs qdrant
docker compose logs chroma
docker compose logs open-webui-rag
```

**Images won't pull:**
- Ensure `docker login ghcr.io` works on server
- Check image exists at `ghcr.io/AgentCielo1/rag-stack`
- Verify registry credentials in GitHub Actions

## Multi-Server Deployment

For multiple servers, duplicate secrets with environment prefixes:

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST_PROD` | prod.example.com |
| `DEPLOY_HOST_STAGING` | staging.example.com |
| `DEPLOY_USER_PROD` | deploy-user |
| etc. | ... |

Then create separate workflows or use environment conditions in deploy.yml.

## Monitoring Deployments

Set up alerts for failed deployments:

1. Go to Settings → Notifications
2. Enable email alerts for workflow failures
3. Or integrate with Slack:
   - Use `actions-slack` action
   - Post to Slack channel on success/failure

## Continuous Deployment Checklist

- ✅ SSH key added to GitHub Secrets
- ✅ Server firewall allows SSH from GitHub Actions runners (0.0.0.0/0)
- ✅ `.env` file created on server
- ✅ Docker installed on server
- ✅ Sufficient disk space (20GB+ recommended)
- ✅ Tested SSH connection manually
- ✅ Backup strategy in place
- ✅ Monitoring/logging configured

## Next Steps

- Add Slack notifications
- Set up monitoring dashboard (Portainer)
- Configure database backups
- Add load balancing (nginx/Traefik)
- Set up SSL/TLS certificates
