# CLAUDE.md - EVE Incursions Companion

**Project**: EVE Online Incursions Companion
**Status**: Production
**URL**: https://eve-incursions.lab.hq.solidrust.net
**Shaun's Golden Rule**: No workarounds, no temp fixes, complete solutions only

---

## ⚡ AGENT QUICK START

**You are working on**: EVE Online Incursions Companion - A Flask-based web application for EVE Online incursion tracking
**Deploy with**: `.\deploy.ps1` or `.\deploy.ps1 -Build -Push` (if image needs update)
**Logs**: `kubectl logs -n eve-incursions -l app=eve-incursions -f`
**Architecture**: Flask + Gunicorn → PostgreSQL (CNPG) + Redis → vLLM inference (future integration)

**Key Context**:
- Multi-component Flask app (base, sso, worker) - currently deploying base only
- Uses platform PostgreSQL (CNPG) instead of original MySQL
- Integrates with EVE Online ESI (EVE Swagger Interface) API
- Will integrate with vLLM inference service for AI-enhanced features
- Requires ESI OAuth credentials from https://developers.eveonline.com/

---

## 📚 PLATFORM INTEGRATION (ChromaDB Knowledge Base)

**When working in this submodule**, you cannot access the parent srt-hq-k8s repository files. Use ChromaDB to query platform capabilities and integration patterns.

**Collection**: `srt-hq-k8s-platform-guide` (43 docs, updated 2025-11-11)

**Why This Matters for EVE Incursions Companion**:
This application integrates deeply with the srt-hq-k8s platform:
- **Database**: Uses platform CNPG PostgreSQL cluster (`postgres-rw.postgres-system.svc.cluster.local`)
- **Ingress**: DNS-01 Let's Encrypt certificates via cert-manager
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **vLLM Integration**: Will use `vllm.lab.hq.solidrust.net` for AI inference features

**Query When You Need**:
- Platform architecture and three-tier taxonomy (core/addons/apps)
- PostgreSQL (CNPG) connection details and credentials management
- Ingress patterns and SSL certificate configuration
- Monitoring integration (Prometheus, Grafana)
- vLLM inference API endpoints and authentication
- Storage classes and persistent volume options

**Example Queries**:
```
"What is the srt-hq-k8s platform architecture?"
"How do I connect to the PostgreSQL CNPG cluster?"
"What are the ingress SSL certificate requirements?"
"How do I integrate with the vLLM inference service?"
"What monitoring endpoints are available?"
```

**When NOT to Query**:
- ❌ Flask development patterns (use Flask docs)
- ❌ EVE Online ESI API usage (use EVE developers docs)
- ❌ Python/SQLAlchemy syntax (see requirements.txt and base.py)
- ❌ Docker build process (use build-and-push.ps1 and Dockerfile)

---

## 📍 PROJECT OVERVIEW

**What it is**: Web application for tracking EVE Online incursions, player fleets, and ship fittings with SSO authentication

**Tech Stack**:
- **Backend**: Python 3.11 + Flask + SQLAlchemy
- **WSGI Server**: Gunicorn (4 workers, 2 threads)
- **Database**: PostgreSQL (via platform CNPG cluster)
- **Cache/Queue**: Redis (for RQ background workers)
- **EVE API**: ESIPy (EVE Swagger Interface client)
- **Auth**: Flask-Login + EVE Online SSO OAuth2
- **Future**: vLLM inference integration for AI-enhanced features

**Features**:
- EVE Online SSO authentication
- Incursion fleet tracking
- Ship fitting management
- Player statistics
- Real-time EVE API integration
- Background job processing with RQ

**Components**:
- `base/` - Main Flask web application (currently deployed)
- `sso/` - SSO authentication service (future deployment)
- `worker/` - RQ background worker (future deployment)
- `data/` - Data processing service (future deployment)
- `implants/` - Implant fitting tools (future feature)

---

## 🗂️ LOCATIONS

**Repository Locations**:
- **Standalone**: `/mnt/c/Users/shaun/repos/eve-incursions-companion`
- **Submodule**: `/mnt/c/Users/shaun/repos/srt-hq-k8s/manifests/apps/eve-incursions`

**Deployment**:
- **URL**: https://eve-incursions.lab.hq.solidrust.net
- **Namespace**: `eve-incursions`
- **Image**: `suparious/eve-incursions:latest`

**Related Services**:
- **Database**: `postgres-rw.postgres-system.svc.cluster.local:5432` (CNPG cluster)
- **Redis**: `redis.eve-incursions.svc.cluster.local:6379` (future deployment)
- **vLLM API**: `https://vllm.lab.hq.solidrust.net` (future integration)

---

## 🛠️ TECH STACK

**Frontend**:
- Flask templates (Jinja2)
- HTML/CSS/JavaScript
- Bootstrap (legacy, may need modernization)

**Backend**:
- Python 3.11
- Flask 0.12.1+ (legacy, may need upgrade)
- SQLAlchemy 1.1.9+
- Flask-Login (session management)
- Flask-Migrate (database migrations)
- ESIPy 1.0.0+ (EVE Online ESI client)

**Infrastructure**:
- Docker (multi-stage build)
- Kubernetes (Deployment + Service + Ingress)
- Gunicorn WSGI server
- PostgreSQL 16 (via CNPG)
- Redis 7 (for RQ workers)
- Nginx Ingress Controller
- Cert-Manager (Let's Encrypt DNS-01)

**AI Integration (Planned)**:
- vLLM inference service
- OpenAI-compatible API
- LLaMA models for fleet advice, fitting optimization

---

## 📁 PROJECT STRUCTURE

```
eve-incursions-companion/
├── base/                          # Main Flask application
│   ├── base.py                    # Flask app entry point
│   ├── config.dist                # Configuration template
│   ├── requirements.txt           # Python dependencies
│   ├── templates/                 # Jinja2 templates
│   └── migrations/                # Alembic database migrations
├── sso/                           # SSO authentication service
│   ├── sso.py                     # SSO Flask app
│   ├── requirements.txt           # SSO dependencies
│   └── migrations/                # SSO database migrations
├── worker/                        # RQ background worker
│   ├── worker.py                  # Worker entry point
│   └── requirements.txt           # Worker dependencies
├── data/                          # Data processing service
│   └── app.py                     # Data service entry point
├── implants/                      # Implant fitting tools
├── scratch/                       # Development scratch space
├── k8s/                          # Kubernetes manifests
│   ├── 01-namespace.yaml         # Namespace definition
│   ├── 02-configmap.yaml         # Configuration
│   ├── 03-secret.yaml            # Secrets (ESI credentials, DB password)
│   ├── 04-deployment.yaml        # Deployment
│   ├── 05-service.yaml           # Service
│   └── 06-ingress.yaml           # Ingress + TLS
├── Dockerfile                     # Multi-stage Docker build
├── .dockerignore                  # Docker build exclusions
├── build-and-push.ps1            # Build and push script
├── deploy.ps1                     # Kubernetes deployment script
├── CLAUDE.md                      # This file
└── README-K8S.md                  # Kubernetes deployment guide
```

---

## 🚀 DEVELOPMENT WORKFLOW

### Local Development

**Prerequisites**:
- Python 3.11+
- PostgreSQL or MySQL
- Redis (for background workers)
- EVE Online developer account

**Setup**:
```bash
cd base/
cp config.dist config.py
# Edit config.py with database credentials and ESI credentials

# Install dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade

# Run development server
flask run
```

### Docker Build & Test

**Build locally**:
```powershell
.\build-and-push.ps1
```

**Test locally** (port 5000):
```bash
docker run --rm -p 5000:5000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  -e SECRET_KEY="dev-secret-key" \
  -e ESI_CLIENT_ID="your-client-id" \
  -e ESI_SECRET_KEY="your-secret-key" \
  suparious/eve-incursions:latest
```

Access: http://localhost:5000

### Production Deployment

**Quick deploy** (using existing image):
```powershell
cd /mnt/c/Users/shaun/repos/srt-hq-k8s/manifests/apps/eve-incursions
.\deploy.ps1
```

**Build and deploy**:
```powershell
.\deploy.ps1 -Build -Push
```

**Uninstall**:
```powershell
.\deploy.ps1 -Uninstall
```

---

## 📋 DEPLOYMENT

### Quick Deploy
```powershell
# From submodule directory
.\deploy.ps1
```

### Manual Deployment
```bash
# Apply manifests
kubectl apply -f k8s/

# Watch rollout
kubectl rollout status deployment/eve-incursions -n eve-incursions

# Check status
kubectl get pods,svc,ingress,certificate -n eve-incursions
```

### Configuration Required

**Before first deployment**, update `k8s/03-secret.yaml` with:
1. **Database credentials** (`DB_USER`, `DB_PASSWORD`)
2. **Flask secret key** (`SECRET_KEY`) - generate with `openssl rand -hex 32`
3. **ESI OAuth credentials** from https://developers.eveonline.com/:
   - `ESI_CLIENT_ID`
   - `ESI_SECRET_KEY`
   - `ESI_CALLBACK_URL` (should be `https://eve-incursions.lab.hq.solidrust.net/sso/callback`)

**Database Setup**:
```bash
# Create database in CNPG cluster
kubectl cnpg psql postgres -- -c "CREATE DATABASE eve_incursions;"
kubectl cnpg psql postgres -- -c "CREATE USER eve_incursions WITH PASSWORD 'your-secure-password';"
kubectl cnpg psql postgres -- -c "GRANT ALL PRIVILEGES ON DATABASE eve_incursions TO eve_incursions;"
```

---

## 🔧 COMMON TASKS

### View Logs
```bash
# All pods
kubectl logs -n eve-incursions -l app=eve-incursions -f

# Specific pod
kubectl logs -n eve-incursions <pod-name> -f
```

### Update Deployment
```powershell
# Rebuild and redeploy
.\deploy.ps1 -Build -Push

# Or just apply manifest changes
kubectl apply -f k8s/
kubectl rollout restart deployment/eve-incursions -n eve-incursions
```

### Check Certificate Status
```bash
kubectl get certificate -n eve-incursions
# Expected: READY=True (may take 1-2 minutes)
```

### Database Migrations
```bash
# Shell into pod
kubectl exec -n eve-incursions -it <pod-name> -- /bin/bash

# Run migrations
flask db upgrade
```

### Troubleshooting

**Pods not starting**:
```bash
kubectl describe pod -n eve-incursions <pod-name>
kubectl logs -n eve-incursions <pod-name>
```

**Common issues**:
- Missing ESI credentials → Check `k8s/03-secret.yaml`
- Database connection failed → Verify CNPG cluster is running, credentials correct
- Certificate not issuing → Check cert-manager logs, Cloudflare API token

**Platform checks**:
```bash
# Check CNPG cluster
kubectl get cluster -n postgres-system

# Check ingress
kubectl get ingress -n eve-incursions

# Check events
kubectl get events -n eve-incursions --sort-by='.lastTimestamp'
```

---

## 🎯 USER PREFERENCES (CRITICAL)

**Context**: Cloud engineer, learning K8s for work, building production-quality lab

**Solutions**:
- ✅ Complete, immediately deployable, production-ready
- ✅ Run PowerShell/Makefile directly (don't ask permission)
- ✅ Full manifests (not patches), reproducible
- ❌ NO workarounds, temp files, disabled features, cruft

**Workflow**:
- User monitors Claude's changes in real-time, stops/corrects anything off-vision
- Validate end-to-end, document in appropriate location
- Use ChromaDB to query platform integration patterns

---

## 💡 KEY DECISIONS

### Why Flask?
- **Legacy Application**: Existing EVE Online community tool
- **Python Ecosystem**: Rich libraries for EVE API integration (ESIPy)
- **Simple Deployment**: Well-understood, easy to containerize

### Why PostgreSQL over MySQL?
- **Platform Standard**: srt-hq-k8s uses CNPG (CloudNativePG)
- **Better Features**: Superior JSON support, ACID compliance
- **High Availability**: CNPG provides automatic failover
- **Compatibility**: SQLAlchemy works with both, minimal migration effort

### Why Gunicorn?
- **Production WSGI**: Flask development server not production-ready
- **Performance**: Multi-worker, multi-threaded model
- **Stability**: Industry standard for Python web apps

### Future vLLM Integration
- **AI Features**: Fleet composition advice, fitting optimization
- **Local Inference**: $0 per token vs cloud APIs
- **Privacy**: Player data stays in-cluster
- **Custom Models**: Fine-tune LLaMA for EVE-specific knowledge

---

## 🔍 VALIDATION

### Post-Deployment Checks

**1. Pods Running**:
```bash
kubectl get pods -n eve-incursions
# Expected: 2/2 running
```

**2. Service Accessible**:
```bash
kubectl get svc -n eve-incursions
# Expected: ClusterIP with port 80
```

**3. Ingress Configured**:
```bash
kubectl get ingress -n eve-incursions
# Expected: Shows ADDRESS (172.20.75.200)
```

**4. Certificate Issued**:
```bash
kubectl get certificate -n eve-incursions
# Expected: READY=True
```

**5. HTTP Access**:
```bash
curl -k https://eve-incursions.lab.hq.solidrust.net
# Expected: HTTP 200, HTML response
```

**6. Browser Test**:
- Navigate to: https://eve-incursions.lab.hq.solidrust.net
- **Expected**: Green padlock, Flask app loads

**7. ESI Integration** (after configuration):
- Click "Login with EVE Online"
- **Expected**: Redirects to EVE SSO, successful auth

---

## 🎓 AGENT SUCCESS CRITERIA

**Good Looks Like**:
- ✅ All pods healthy (2/2 running)
- ✅ Certificate issued and valid
- ✅ Application accessible via HTTPS with green padlock
- ✅ EVE SSO authentication working
- ✅ Database migrations applied successfully
- ✅ No errors in logs
- ✅ Meets user's "no workarounds" rule

**Red Flags**:
- ❌ Pods crash-looping
- ❌ Certificate stuck in "Not Ready"
- ❌ 404 or 500 errors
- ❌ Database connection errors
- ❌ ESI API authentication failures
- ❌ Temporary fixes or disabled features

---

## 📅 CHANGE HISTORY

### 2025-11-13 - Initial K8s Deployment
- Created multi-stage Dockerfile for Flask application
- Created Kubernetes manifests (namespace, configmap, secret, deployment, service, ingress)
- Created PowerShell deployment scripts (build-and-push.ps1, deploy.ps1)
- Configured PostgreSQL (CNPG) integration
- Configured Let's Encrypt DNS-01 SSL certificates
- Added comprehensive documentation (CLAUDE.md, README-K8S.md)
- Onboarded as git submodule to srt-hq-k8s platform

**Current State**: Base component ready for deployment, SSO/worker components pending

**Next Steps**:
1. Configure ESI OAuth credentials
2. Create database and run migrations
3. Test deployment end-to-end
4. Deploy SSO component (separate deployment)
5. Deploy worker component with Redis
6. Integrate with vLLM inference service for AI features

---

**Last Updated**: 2025-11-13
**Maintained By**: Shaun Prince
**Used With**: Claude Code (Sonnet 4.5)
