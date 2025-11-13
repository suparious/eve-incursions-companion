# EVE Incursions Companion - Kubernetes Deployment

Flask-based web application for tracking EVE Online incursions, deployed to srt-hq-k8s production cluster.

**Production URL**: https://eve-incursions.lab.hq.solidrust.net

---

## 🚀 Quick Start

### Development
```bash
cd base/
cp config.dist config.py
pip install -r requirements.txt
flask run
```
Access: http://localhost:5000

### Docker
```powershell
.\build-and-push.ps1
docker run --rm -p 5000:5000 suparious/eve-incursions:latest
```
Access: http://localhost:5000

### Kubernetes
```powershell
# Quick deploy
.\deploy.ps1

# Build and deploy
.\deploy.ps1 -Build -Push

# Uninstall
.\deploy.ps1 -Uninstall
```
Access: https://eve-incursions.lab.hq.solidrust.net

---

## 🔧 Maintenance

### Update Deployment
```powershell
# Rebuild and redeploy
.\deploy.ps1 -Build -Push

# Or apply manifest changes
kubectl apply -f k8s/
kubectl rollout restart deployment/eve-incursions -n eve-incursions
```

### View Logs
```bash
kubectl logs -n eve-incursions -l app=eve-incursions -f
```

### Database Migrations
```bash
kubectl exec -n eve-incursions -it <pod-name> -- /bin/bash
flask db upgrade
```

### Troubleshooting
```bash
# Check pods
kubectl get pods -n eve-incursions

# Check events
kubectl get events -n eve-incursions --sort-by='.lastTimestamp'

# Check certificate
kubectl get certificate -n eve-incursions

# Check logs
kubectl logs -n eve-incursions <pod-name>
```

---

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python 3.11 + Flask + SQLAlchemy + ESIPy
- **WSGI**: Gunicorn (4 workers, 2 threads)
- **Database**: PostgreSQL 16 (via CNPG cluster)
- **Cache**: Redis 7 (for RQ background workers)
- **Container**: Docker multi-stage build
- **Orchestration**: Kubernetes (Deployment + Service + Ingress)

### Resources
- **CPU**: 200m request, 1000m limit
- **Memory**: 256Mi request, 512Mi limit
- **Replicas**: 2 (HA deployment)

### Networking
- **Service**: ClusterIP on port 80
- **Ingress**: Nginx + Let's Encrypt DNS-01 SSL
- **Domain**: eve-incursions.lab.hq.solidrust.net

### Storage
- **Database**: External PostgreSQL CNPG cluster
- **Redis**: To be deployed (for RQ workers)

---

## ✨ Features

- EVE Online SSO authentication (OAuth2)
- Incursion fleet tracking
- Ship fitting management
- Player statistics
- Real-time EVE ESI API integration
- Background job processing with RQ
- Future: vLLM AI integration for fleet advice

---

## 📁 Files Overview

### Kubernetes Manifests (`k8s/`)
- `01-namespace.yaml` - Namespace definition
- `02-configmap.yaml` - Configuration (DB, Redis, ESI settings)
- `03-secret.yaml` - Secrets (DB password, ESI credentials, Flask secret key)
- `04-deployment.yaml` - Deployment (2 replicas, Gunicorn)
- `05-service.yaml` - ClusterIP service
- `06-ingress.yaml` - Ingress + TLS certificate

### Application Files
- `Dockerfile` - Multi-stage build (Python builder → slim runtime)
- `.dockerignore` - Docker build exclusions
- `build-and-push.ps1` - Build and push script
- `deploy.ps1` - Kubernetes deployment script
- `CLAUDE.md` - Comprehensive AI agent context
- `README-K8S.md` - This file

### Application Components
- `base/` - Main Flask application (currently deployed)
- `sso/` - SSO authentication service (pending deployment)
- `worker/` - RQ background worker (pending deployment)
- `data/` - Data processing service (pending deployment)
- `implants/` - Implant fitting tools (pending deployment)

---

## 🔧 Configuration

### Required Secrets

Before first deployment, configure `k8s/03-secret.yaml`:

1. **Database Credentials**:
   ```yaml
   DB_USER: "eve_incursions"
   DB_PASSWORD: "your-secure-password"
   ```

2. **Flask Secret Key** (generate with `openssl rand -hex 32`):
   ```yaml
   SECRET_KEY: "your-random-secret-key"
   ```

3. **ESI OAuth Credentials** (from https://developers.eveonline.com/):
   ```yaml
   ESI_CLIENT_ID: "your-esi-client-id"
   ESI_SECRET_KEY: "your-esi-secret-key"
   ESI_CALLBACK_URL: "https://eve-incursions.lab.hq.solidrust.net/sso/callback"
   ```

### Database Setup

Create database in CNPG cluster:
```bash
kubectl cnpg psql postgres -- -c "CREATE DATABASE eve_incursions;"
kubectl cnpg psql postgres -- -c "CREATE USER eve_incursions WITH PASSWORD 'your-password';"
kubectl cnpg psql postgres -- -c "GRANT ALL PRIVILEGES ON DATABASE eve_incursions TO eve_incursions;"
```

---

## 📊 Useful Commands

### Deployment
```bash
# Deploy
.\deploy.ps1

# Build and deploy
.\deploy.ps1 -Build -Push

# Uninstall
.\deploy.ps1 -Uninstall
```

### Monitoring
```bash
# Status
kubectl get all,certificate,ingress -n eve-incursions

# Logs
kubectl logs -n eve-incursions -l app=eve-incursions -f

# Events
kubectl get events -n eve-incursions --sort-by='.lastTimestamp'

# Shell access
kubectl exec -n eve-incursions -it <pod-name> -- /bin/bash
```

### Docker
```bash
# Build
.\build-and-push.ps1

# Build and push
.\build-and-push.ps1 -Login -Push
```

---

## 🔗 Links

- **Production**: https://eve-incursions.lab.hq.solidrust.net
- **Docker Hub**: https://hub.docker.com/r/suparious/eve-incursions
- **GitHub**: https://github.com/suparious/eve-incursions-companion
- **EVE Developers**: https://developers.eveonline.com/
- **ESI Docs**: https://esi.evetech.net/ui/

---

## 📋 Prerequisites

- Kubernetes cluster (srt-hq-k8s)
- PostgreSQL CNPG cluster
- Nginx Ingress Controller
- Cert-Manager (Let's Encrypt DNS-01)
- Docker (for building images)
- kubectl CLI
- PowerShell 7+

---

## 🎯 Next Steps

1. Configure ESI OAuth credentials at https://developers.eveonline.com/
2. Update `k8s/03-secret.yaml` with credentials
3. Create database in CNPG cluster
4. Deploy: `.\deploy.ps1 -Build -Push`
5. Verify: https://eve-incursions.lab.hq.solidrust.net
6. Run database migrations
7. Test EVE SSO authentication
8. Deploy SSO component (future)
9. Deploy worker component with Redis (future)
10. Integrate vLLM inference service (future)

---

**Last Updated**: 2025-11-13
**Maintained By**: Shaun Prince
