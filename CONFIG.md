# RAG Stack Configuration Guide

## SearXNG Proxy Settings

SearXNG is configured to use proxies for network requests. Set these in `.env`:

### HTTP/HTTPS Proxy
```bash
PROXY_HTTP=http://proxy.example.com:8080
PROXY_HTTPS=http://proxy.example.com:8080
```

### SOCKS5 Proxy
```bash
PROXY_SOCKS5=socks5://proxy.example.com:1080
```

### No Proxy (Bypass)
Localhost and 127.0.0.1 are always bypassed. To add more:
Edit `searxng/settings.yml` and add to the `outgoing` section:
```yaml
outgoing:
  proxies:
    http: http://proxy.example.com:8080
    https: http://proxy.example.com:8080
```

## Applying Proxy Settings

1. **Edit `.env`:**
```bash
nano ~/rag-stack/.env
```

2. **Uncomment and set proxy variables:**
```
PROXY_HTTP=http://proxy.example.com:8080
PROXY_HTTPS=http://proxy.example.com:8080
```

3. **Restart SearXNG:**
```bash
cd ~/rag-stack
docker compose restart searxng
```

4. **Verify:**
```bash
./rag-stack.sh health
```

## GitHub Actions CI/CD

Two workflows are configured:

### 1. Docker Build & Push (`.github/workflows/docker-build-push.yml`)
- Triggers on: push to `main`, PRs, manual dispatch
- Actions:
  - Validates `docker-compose.yml`
  - Builds all services
  - Pushes to GitHub Container Registry (ghcr.io)
  - Caches layers for faster rebuilds

**Setup:**
1. Push code to GitHub
2. Actions automatically build and push images
3. Deploy with: `docker compose pull && docker compose up -d`

### 2. Health Check (`.github/workflows/health-check.yml`)
- Triggers: Every 6 hours (cron schedule)
- Actions:
  - Validates configuration
  - Lints docker-compose.yml
  - Checks for security issues

**Customize cron schedule in `health-check.yml`:**
```yaml
schedule:
  - cron: '0 */6 * * *'  # Change frequency
```

## Secrets & Environment Variables

For GitHub Actions, add these secrets:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add: `PROXY_HTTP`, `PROXY_HTTPS`, etc.

Reference in workflows:
```yaml
env:
  PROXY_HTTP: ${{ secrets.PROXY_HTTP }}
```

## Testing Locally

```bash
# Validate workflows
docker compose config

# Test with proxy
PROXY_HTTP=http://proxy.example.com:8080 docker compose up -d

# Check SearXNG logs
docker compose logs searxng

# Verify proxy settings
docker compose exec searxng curl -x http://proxy.example.com:8080 http://example.com
```

## Deployment

### Self-Hosted Server
```bash
git clone <your-repo> rag-stack
cd rag-stack
docker login ghcr.io
docker compose pull
docker compose up -d
```

### Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.yml rag-stack
```

### Kubernetes
```bash
# Generate Kubernetes manifests from compose
kompose convert -f docker-compose.yml -o k8s/
kubectl apply -f k8s/
```

## Troubleshooting

**SearXNG can't reach search engines:**
```bash
# Check if proxy is working
docker compose exec searxng curl -x http://proxy.example.com:8080 https://www.google.com

# View SearXNG logs
docker compose logs searxng -f
```

**GitHub Actions workflow not running:**
1. Check `.github/workflows/` files are committed
2. Go to GitHub → Actions → check for errors
3. Verify branch is `main`

**Build failures:**
```bash
# Local rebuild
docker compose build --no-cache

# Push logs to GitHub
git add -A && git commit -m "Fix config" && git push
```
