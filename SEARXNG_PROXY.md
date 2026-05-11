# SearXNG Proxy Configuration

This guide explains how to configure SearXNG to route requests through a network proxy.

## Quick Setup

### 1. Set Proxy Environment Variables

Edit your `.env` file:

```bash
# HTTP/HTTPS Proxy
PROXY_HTTP=http://proxy.example.com:8080
PROXY_HTTPS=http://proxy.example.com:8080

# OR SOCKS5 Proxy
PROXY_SOCKS5=socks5://proxy.example.com:1080

# No Proxy (bypass) - comma-separated
NO_PROXY=localhost,127.0.0.1,internal.local
```

### 2. Restart SearXNG

```bash
cd ~/rag-stack
docker compose restart searxng
# OR if not running
docker compose up -d searxng
```

### 3. Verify Configuration

```bash
# Check if proxy is active
docker compose exec searxng curl -v http://example.com 2>&1 | grep -i proxy

# Or test through proxy directly
docker compose exec searxng curl -x http://proxy.example.com:8080 https://www.google.com
```

## Environment Variables

### Docker Compose (Recommended)

Set in `.env` file or pass via `-e` flag:

```yaml
# docker-compose.yml
environment:
  HTTP_PROXY: ${PROXY_HTTP:-}
  HTTPS_PROXY: ${PROXY_HTTPS:-}
  ALL_PROXY: ${PROXY_SOCKS5:-}
  NO_PROXY: localhost,127.0.0.1
```

### Manual Docker Command

```bash
docker run -d \
  -e HTTP_PROXY=http://proxy.example.com:8080 \
  -e HTTPS_PROXY=http://proxy.example.com:8080 \
  -e NO_PROXY=localhost,127.0.0.1 \
  -p 8888:8080 \
  searxng/searxng:latest
```

## Proxy Types

### HTTP/HTTPS Proxy (Most Common)

```bash
PROXY_HTTP=http://proxy.example.com:8080
PROXY_HTTPS=http://proxy.example.com:8080
```

Used for forwarding HTTP and HTTPS traffic through an HTTP proxy.

### SOCKS5 Proxy

```bash
PROXY_SOCKS5=socks5://proxy.example.com:1080
# OR with authentication
PROXY_SOCKS5=socks5://username:password@proxy.example.com:1080
```

Used for forwarding all traffic through a SOCKS proxy.

### Proxy with Authentication

```bash
# HTTP Proxy with auth
PROXY_HTTP=http://username:password@proxy.example.com:8080
PROXY_HTTPS=http://username:password@proxy.example.com:8080

# SOCKS5 with auth
PROXY_SOCKS5=socks5://username:password@proxy.example.com:1080
```

## Advanced Configuration

### Custom SearXNG Settings File

Create `searxng/settings.yml`:

```yaml
outgoing:
  request_timeout: 3.0
  max_retries: 0
  proxies:
    http: "http://proxy.example.com:8080"
    https: "http://proxy.example.com:8080"
    # Uncomment for SOCKS5
    # socks5: "socks5://proxy.example.com:1080"
  
  # Bypass proxy for internal networks
  # no_proxy: 
  #   - localhost
  #   - 127.0.0.1
  #   - internal.local
  #   - 192.168.*
```

Mount in `docker-compose.yml`:

```yaml
services:
  searxng:
    volumes:
      - ./searxng/settings.yml:/etc/searxng/settings.yml:ro
```

### Conditional Proxy per Request

```bash
# Override proxy for single request
docker compose exec searxng \
  curl -x http://alt-proxy.example.com:8080 https://example.com
```

## Testing Proxy Configuration

### 1. Test HTTP Request Through Proxy

```bash
docker compose exec searxng curl -v -x http://proxy.example.com:8080 http://example.com
```

### 2. Test HTTPS Request

```bash
docker compose exec searxng curl -v -x http://proxy.example.com:8080 https://example.com
```

### 3. Check Environment Variables Inside Container

```bash
docker compose exec searxng env | grep -i proxy
```

### 4. Test with Real Search

Open http://localhost:8888 and perform a search. Check logs:

```bash
docker compose logs searxng -f
```

Look for:
- Successful proxied requests
- Connection timeouts (proxy unreachable)
- Authentication failures (bad credentials)

## Troubleshooting

### Proxy Connection Refused

**Error:** `Connection refused` or `Network is unreachable`

**Solutions:**
1. Verify proxy address and port
2. Check network connectivity: `docker compose exec searxng ping proxy.example.com`
3. Verify firewall allows access to proxy
4. Check proxy is running and accepting connections

### Proxy Authentication Failed

**Error:** `407 Proxy Authentication Required`

**Solutions:**
1. Add username and password to proxy URL:
   ```bash
   PROXY_HTTP=http://user:pass@proxy.example.com:8080
   ```
2. Verify credentials are correct
3. Check proxy requires authentication (some bypass localhost)

### SSL/TLS Certificate Errors

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions:**
1. Add proxy CA certificate to container:
   ```bash
   # Copy cert to container
   docker cp /path/to/ca.crt searxng:/etc/ssl/certs/
   ```
2. Or disable verification (not recommended for production):
   ```bash
   docker run -e PYTHONHTTPSVERIFY=0 ...
   ```

### Timeout Issues

**Error:** `Connection timed out`

**Solutions:**
1. Increase timeout in settings.yml:
   ```yaml
   outgoing:
     request_timeout: 10.0  # was 3.0
   ```
2. Verify proxy is reachable
3. Check network latency: `ping proxy.example.com`

### No Proxy List Not Working

**Problem:** `NO_PROXY` environment variable ignored

**Solutions:**
1. Use lowercase `no_proxy`:
   ```bash
   no_proxy=localhost,127.0.0.1
   ```
2. Or configure in `searxng/settings.yml`
3. Test with: `docker compose exec searxng env | grep -i proxy`

## Corporate Network Setup

### Example: Corporate Proxy with Authentication

```bash
# .env
PROXY_HTTP=http://AD_USERNAME:AD_PASSWORD@corporate-proxy.internal:8080
PROXY_HTTPS=http://AD_USERNAME:AD_PASSWORD@corporate-proxy.internal:8080
NO_PROXY=localhost,127.0.0.1,.internal,.local
```

### Example: Proxy Bypass for Internal Services

```bash
# .env
PROXY_HTTP=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1,qdrant,chroma,*.internal,192.168.*
```

This allows SearXNG to reach internal services (Qdrant, Chroma) without going through the proxy, while external searches go through the proxy.

## Deployment Considerations

### GitHub Actions Secrets

For automatic deployment, add secrets:

```bash
# Go to GitHub → Settings → Secrets and variables → Actions
# Add:
PROXY_HTTP_DEPLOY=http://proxy.example.com:8080
PROXY_HTTPS_DEPLOY=http://proxy.example.com:8080
```

Then use in deployment workflow:

```yaml
- name: Deploy
  env:
    PROXY_HTTP: ${{ secrets.PROXY_HTTP_DEPLOY }}
    PROXY_HTTPS: ${{ secrets.PROXY_HTTPS_DEPLOY }}
  run: |
    docker compose up -d
```

### Server-Specific Configuration

Create `.env.server` on your deployment server (not committed to git):

```bash
# Only on server
PROXY_HTTP=http://internal-proxy:8080
PROXY_HTTPS=http://internal-proxy:8080
SEARXNG_BASE_URL=https://search.internal
```

Then reference in deployment script:

```bash
if [ -f .env.server ]; then
  source .env.server
fi
docker compose up -d
```

## Monitoring Proxy Usage

### View Proxy Traffic

```bash
docker compose logs searxng | grep -i "proxy\|request"
```

### Monitor Proxy Health

```bash
# Add to health check script
docker compose exec searxng curl -f -x http://proxy.example.com:8080 https://www.google.com && echo "Proxy OK" || echo "Proxy FAILED"
```

## References

- [Docker Proxy Configuration](https://docs.docker.com/config/containers/container-networking/#proxy-configuration)
- [SearXNG Documentation](https://docs.searxng.org)
- [curl Proxy Options](https://curl.se/docs/manpage.html#-x)
