# 🚀 Syrka Deployment Guide

## ⚠️ Important: Vercel Limitations

**Vercel is NOT recommended for this application** due to:

1. **Heavy ML Dependencies**: Sentence-transformers, FAISS, PyMuPDF exceed Vercel's 250MB limit
2. **Serverless Timeouts**: 10s timeout (hobby) / 60s (pro) insufficient for ML operations
3. **No Persistent Storage**: Vector indices and embeddings need persistent storage
4. **Cold Starts**: ML model loading causes slow cold starts in serverless

### If you must use Vercel:
The current `vercel.json` and root `requirements.txt` provide a **minimal API** without:
- ❌ ML-powered matching
- ❌ RAG/embeddings features
- ❌ PDF processing
- ❌ Curriculum generation

Only basic CRUD operations will work.

---

## ✅ Recommended Deployment Options

### Option 1: Railway (Easiest) ⭐ RECOMMENDED

Railway supports Docker and persistent volumes, perfect for Syrka.

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Setup:**
1. Create new project on [Railway](https://railway.app)
2. Connect GitHub repository
3. Railway auto-detects Dockerfile
4. Add PostgreSQL database service
5. Set environment variables from `.env.template`
6. Deploy

**Cost:** ~$5-10/month with usage-based pricing

---

### Option 2: Render

Similar to Railway, excellent for FastAPI apps.

**Setup:**
1. Go to [Render](https://render.com)
2. New Web Service → Connect repository
3. Build: `Docker`
4. Add PostgreSQL database
5. Set environment variables
6. Deploy

**Cost:** Free tier available, $7/month for production

---

### Option 3: AWS (Production)

For production scale with full control.

**Using AWS ECS + RDS:**

```bash
# Build and push to ECR
aws ecr create-repository --repository-name syrka
docker build -t syrka .
docker tag syrka:latest <account>.dkr.ecr.<region>.amazonaws.com/syrka:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/syrka:latest

# Deploy to ECS using provided task definition
aws ecs create-cluster --cluster-name syrka-cluster
aws ecs create-service --cluster syrka-cluster --service-name syrka-api ...
```

**Services needed:**
- ECS Fargate (container hosting)
- RDS PostgreSQL (database)
- S3 (file storage)
- ALB (load balancer)
- CloudWatch (logging)

**Cost:** ~$50-100/month base

---

### Option 4: DigitalOcean App Platform

Middle ground between simplicity and control.

**Setup:**
1. Create app on [DigitalOcean](https://cloud.digitalocean.com/apps)
2. Connect GitHub
3. Select Dockerfile deployment
4. Add managed PostgreSQL database
5. Configure environment variables
6. Deploy

**Cost:** $12/month basic + $15/month database

---

### Option 5: Google Cloud Run

Serverless containers with better limits than Vercel.

```bash
# Build and deploy
gcloud run deploy syrka \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...
```

**Cost:** Pay per use, generous free tier

---

## 🐳 Docker Deployment (Any VPS)

Works on any VPS (DigitalOcean Droplet, AWS EC2, Linode, etc.)

```bash
# On your VPS
git clone <repository>
cd Syrka-V1/syrka

# Copy and configure environment
cp .env.template .env
nano .env  # Add your API keys

# Deploy
docker-compose up -d

# View logs
docker-compose logs -f
```

**VPS Requirements:**
- 2GB RAM minimum (4GB recommended)
- 2 CPU cores
- 20GB storage
- Ubuntu 20.04+ or similar

**Cost:** $10-20/month (DigitalOcean, Linode, Vultr)

---

## 🔧 Environment Variables

Required for all deployments:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/syrka

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=sk-...

# Gmail (optional)
GMAIL_CREDENTIALS_PATH=credentials.json

# External APIs (optional)
ADZUNA_API_KEY=...
ADZUNA_APP_ID=...
REED_API_KEY=...
```

---

## 🗄️ Database Setup

All platforms need PostgreSQL. Run initial migration:

```bash
# Connect to your PostgreSQL instance
psql $DATABASE_URL -f migrations/initial_schema.sql
```

---

## 📊 Post-Deployment Checklist

After deploying:

1. **Test Health Endpoint**
   ```bash
   curl https://your-app.com/health
   ```

2. **Check API Docs**
   Visit: `https://your-app.com/docs`

3. **Create Admin User**
   ```bash
   curl -X POST https://your-app.com/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@example.com",
       "password": "secure-password",
       "full_name": "Admin User",
       "role": "government"
     }'
   ```

4. **Ingest Test Data**
   ```bash
   # Ingest jobs
   curl -X POST https://your-app.com/jobs/ingest \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"sources": ["adzuna"], "params": {"query": "software"}}'
   ```

---

## 🔍 Troubleshooting

### App won't start
- Check environment variables are set
- Verify database connection string
- Check logs: `docker-compose logs` or platform logs

### Database connection errors
- Verify `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
- Check database is accessible from app
- Ensure database exists

### ML features not working
- Verify `OPENAI_API_KEY` is set
- Check you have sufficient API credits
- For local models, ensure sufficient RAM (4GB+)

### Job ingestion failing
- Some scrapers may be blocked (use VPN or proxy)
- API integrations require valid API keys
- Check rate limits on external APIs

---

## 🎯 Quick Comparison

| Platform | Difficulty | Cost/mo | ML Support | Persistent Storage | Recommended For |
|----------|------------|---------|------------|-------------------|-----------------|
| **Railway** | ⭐ Easy | $5-10 | ✅ Full | ✅ Yes | **Startups, MVPs** |
| **Render** | ⭐ Easy | $0-7 | ✅ Full | ✅ Yes | **Free tier testing** |
| **DigitalOcean** | ⭐⭐ Medium | $27+ | ✅ Full | ✅ Yes | **Production** |
| **AWS** | ⭐⭐⭐ Hard | $50+ | ✅ Full | ✅ Yes | **Enterprise** |
| **GCP Cloud Run** | ⭐⭐ Medium | Pay/use | ⚠️ Limited | ⚠️ Limited | **Serverless scale** |
| **VPS Docker** | ⭐⭐ Medium | $10+ | ✅ Full | ✅ Yes | **Self-hosting** |
| **Vercel** | ⭐ Easy | $0-20 | ❌ None | ❌ No | **❌ Not suitable** |

---

## 🚀 Recommended: Deploy to Railway Now

The fastest way to get Syrka running:

1. **Fork/Clone repository**
2. **Go to [Railway.app](https://railway.app)**
3. **Click "Start a New Project" → "Deploy from GitHub repo"**
4. **Select Syrka-V1 repository**
5. **Add PostgreSQL database** (Railway marketplace)
6. **Add environment variables** from `.env.template`
7. **Deploy!** Railway auto-detects Dockerfile

Your API will be live at `https://syrka-production.up.railway.app` in ~5 minutes.

---

## 📞 Need Help?

- Check logs first
- Review environment variables
- Verify database connection
- Test locally with Docker first
- Check API documentation at `/docs` endpoint
