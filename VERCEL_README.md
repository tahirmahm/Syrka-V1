# 🚨 Deploying Syrka to Vercel - READ THIS FIRST

## The Problem You're Experiencing

You're seeing a `404: NOT_FOUND` error because Syrka is a **complex ML-powered backend** that exceeds Vercel's serverless limitations.

### Why Vercel Won't Work Fully:

1. **Dependency Size**: Our ML libraries (sentence-transformers, FAISS, PyMuPDF, etc.) exceed Vercel's 250MB deployment limit
2. **Execution Timeout**: ML model loading and inference take >10s (Vercel hobby limit)
3. **No Persistent Storage**: Vector indices and FAISS stores need persistent disk storage
4. **Cold Start Issues**: Loading ML models on every cold start = 30s+ response times

## ✅ What You CAN Do

### Option A: Deploy Limited Version to Vercel (Not Recommended)

The files I've created (`vercel.json`, `api/index.py`, root `requirements.txt`) will deploy a **bare-bones API** with:
- ✅ Basic authentication
- ✅ User CRUD
- ✅ Job CRUD (without scraping)
- ❌ No ML-powered matching
- ❌ No RAG/embeddings
- ❌ No curriculum generation
- ❌ No PDF processing
- ❌ No automated applications

**To deploy this limited version:**

1. Make sure you have:
   - `vercel.json` (root)
   - `api/index.py` (created)
   - `requirements.txt` (root - minimal version)

2. Set environment variables in Vercel dashboard:
   ```
   DATABASE_URL=your_postgres_connection_string
   SECRET_KEY=your_secret_key_min_32_chars
   ```

3. Deploy:
   ```bash
   vercel --prod
   ```

### Option B: Use Railway (5 Minutes) ⭐ **RECOMMENDED**

Railway is **designed for apps like this** and costs ~$5/month.

**Quick Start:**
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Create new project
railway init

# 4. Add PostgreSQL
railway add

# 5. Set environment variables
railway variables set DATABASE_URL=...
railway variables set SECRET_KEY=...
railway variables set OPENAI_API_KEY=...

# 6. Deploy (auto-detects Dockerfile)
railway up
```

**Done!** Your app is live with ALL features working.

### Option C: Use Render (Free Tier Available)

**Setup:**
1. Go to https://render.com
2. "New" → "Web Service"
3. Connect your GitHub repository
4. **Settings:**
   - Environment: Docker
   - Plan: Free (or Starter $7/month for production)
5. Add PostgreSQL database (free tier available)
6. Set environment variables
7. Deploy

---

## 🔧 Required Environment Variables

For ANY deployment (including Vercel limited version):

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=generate-a-secure-random-32-char-string

# Optional (for full features on Railway/Render)
OPENAI_API_KEY=sk-...
GMAIL_CREDENTIALS_PATH=/tmp/credentials.json
ADZUNA_API_KEY=...
REED_API_KEY=...
```

---

## 🗄️ Database Setup

You need a PostgreSQL database. Options:

### For Vercel:
- [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) (paid)
- [Supabase](https://supabase.com) (free tier)
- [Neon](https://neon.tech) (free tier)

### For Railway/Render:
- They provide managed PostgreSQL (click to add)

**Initialize database:**
```bash
psql $DATABASE_URL -f migrations/initial_schema.sql
```

---

## 📊 Feature Comparison

| Feature | Vercel (Limited) | Railway/Render | Self-Hosted |
|---------|------------------|----------------|-------------|
| Basic API | ✅ | ✅ | ✅ |
| Authentication | ✅ | ✅ | ✅ |
| Job Matching | ❌ | ✅ | ✅ |
| RAG/Embeddings | ❌ | ✅ | ✅ |
| Curriculum Gen | ❌ | ✅ | ✅ |
| PDF Processing | ❌ | ✅ | ✅ |
| Application Auto | ❌ | ✅ | ✅ |
| Cost/month | $0-20 | $5-15 | $10+ |
| Setup Time | 5 min | 5 min | 30 min |

---

## 🚀 Fastest Path to Success

**For MVP Testing:**
→ Use Railway (full features, 5 min setup, $5/month)

**For Free Tier:**
→ Use Render Free (full features, slower, $0/month)

**For Production:**
→ Use AWS/GCP/DigitalOcean (scalable, $50+/month)

**If You Must Use Vercel:**
→ Deploy limited version, accept missing features, or...
→ Split architecture: Frontend on Vercel, Backend on Railway

---

## 🔧 Quick Fix for Your Current Error

The 404 error is because Vercel can't find your app entry point. I've fixed this by creating:

1. `/api/index.py` - Vercel entry point
2. `/vercel.json` - Vercel configuration
3. `/requirements.txt` (root) - Minimal dependencies

**To deploy now:**

```bash
# In your terminal
cd Syrka-V1

# Deploy to Vercel
vercel --prod

# Set environment variables in Vercel dashboard:
# - DATABASE_URL
# - SECRET_KEY
```

But remember: **You'll only get basic CRUD, no ML features.**

---

## 💡 My Recommendation

**Don't waste time fighting Vercel's limitations.**

Instead, spend 5 minutes deploying to Railway with full functionality:

1. Go to https://railway.app
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add PostgreSQL database
6. Set environment variables
7. Click Deploy

You'll have the FULL application running with:
- ✅ ML-powered job matching
- ✅ RAG policy analysis
- ✅ Automated curriculum generation
- ✅ All features working

For $5/month vs. fighting Vercel's limitations.

---

## 📚 Full Documentation

- **Deployment Guide**: See `DEPLOYMENT.md` for all options
- **API Documentation**: Available at `/docs` once deployed
- **Main README**: See `syrka/README.md` for features

---

## Still Want to Try Vercel?

If you're committed to Vercel despite limitations:

1. **Commit the changes I made:**
   ```bash
   git add .
   git commit -m "Add Vercel configuration"
   git push
   ```

2. **In Vercel Dashboard:**
   - Import your repository
   - Environment Variables → Add:
     - `DATABASE_URL`
     - `SECRET_KEY`
   - Deploy

3. **Test:**
   ```bash
   curl https://your-app.vercel.app/health
   ```

4. **Accept that these features won't work:**
   - ML matching
   - RAG queries
   - Curriculum generation
   - PDF processing
   - Heavy computations

---

**Need help?** Check `DEPLOYMENT.md` for detailed guides for all platforms.
