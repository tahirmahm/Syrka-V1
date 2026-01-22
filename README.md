# 🚀 Syrka - National Workforce Mobility Operating System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **AI-powered platform that unifies education systems, labour markets, and national development policies to maximize workforce mobility and economic growth.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [API Reference](#api-reference)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Syrka is a comprehensive workforce mobility platform designed to bridge three critical systems:

1. **Education Systems** - Curriculum generation aligned with national priorities
2. **Labour Markets** - AI-powered job matching and application automation
3. **National Policies** - RAG-powered policy analysis and workforce planning

### The Problem

- **Education-Employment Gap:** Curricula don't align with labour market demands
- **Inefficient Job Search:** Manual, time-consuming, low success rates
- **Policy Disconnect:** Government policies lack real-time workforce data
- **Skills Shortage:** Critical skills gaps go unidentified and unaddressed

### The Solution

Syrka uses AI to:
- ✅ Match job seekers with opportunities using ML-powered algorithms
- ✅ Automate job applications with personalized CVs and cover letters
- ✅ Generate policy-aligned curricula for workforce development
- ✅ Provide real-time labour market intelligence to governments
- ✅ Identify and forecast skills shortages before they become critical

---

## ✨ Key Features

### 🎯 For Job Seekers

- **AI-Powered Job Matching** - Semantic matching using embeddings and heuristics
- **Automated Applications** - LLM-generated CVs and cover letters
- **Gmail Integration** - Automated sending and tracking
- **Skill Gap Analysis** - Identify missing skills for target jobs
- **Career Recommendations** - Personalized career path suggestions

### 👨‍🏫 For Educators

- **Curriculum Generation** - LLM-powered, policy-aligned course design
- **Skills Mapping** - Align learning outcomes with market demands
- **Microcredentials** - Stackable, industry-recognized certifications
- **LMS Export** - SCORM-compatible for easy integration
- **Progress Tracking** - Student competency development

### 🏛️ For Government

- **Labour Market Dashboard** - Real-time analytics and visualization
- **Skills Shortage Detection** - Identify critical gaps by region/sector
- **Demand Forecasting** - 3-5 year workforce predictions
- **Policy Impact Analysis** - RAG over national development plans
- **Heatmaps** - Regional workforce distribution visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SYRKA LAYERS                         │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Workforce Mobility Engine                      │
│   ├─ Job Scraping (LinkedIn, Indeed)                    │
│   ├─ API Integration (Adzuna, Reed)                     │
│   ├─ AI Matching (Embeddings + Heuristics)              │
│   └─ Auto-Apply (Gmail + LLM)                           │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Human-Capital Intelligence Dashboard           │
│   ├─ Labour Market Heatmaps                             │
│   ├─ Skills Shortage Analysis                           │
│   └─ Demand Forecasting (ML-based)                      │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Education Alignment Layer                      │
│   ├─ Policy RAG System                                  │
│   ├─ Priority Extraction (LLM)                          │
│   └─ Curriculum Generation                              │
├─────────────────────────────────────────────────────────┤
│ Horizontal: AI Roadmap Pipeline                         │
│   ├─ FAISS Vector Store                                 │
│   ├─ Sentence Transformers                              │
│   └─ LangChain + LLM                                    │
├─────────────────────────────────────────────────────────┤
│ Data Layer: PostgreSQL + FAISS                          │
└─────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Backend:** FastAPI + Python 3.11+
- **Database:** PostgreSQL 15 + AsyncPG
- **AI/ML:** LangChain, OpenAI/DeepSeek, Sentence Transformers, FAISS
- **Integrations:** Gmail API, Adzuna, Reed
- **Deployment:** Docker + Docker Compose

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- DeepSeek/OpenAI API key

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/Syrka-V1.git
cd Syrka-V1/syrka

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up PostgreSQL
createdb syrka
psql syrka -f migrations/initial_schema.sql

# 5. Configure environment
cp .env.template .env
# Edit .env with your API keys and database URL

# 6. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access

- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📚 Documentation

Comprehensive documentation available in `/docs`:

- **[API Documentation](docs/API.md)** - Complete API reference with examples
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and components
- **[Testing Guide](docs/TESTING.md)** - How to run and write tests
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions

---

## 🔌 API Reference

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "role": "user",
    "skills": ["Python", "FastAPI"],
    "experience_years": 5,
    "location": "New York",
    "sector_preference": "Technology"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Job Matching

```bash
# Get job matches
curl -X GET http://localhost:8000/matching/matches \
  -H "Authorization: Bearer YOUR_TOKEN"

# Explain match
curl -X GET http://localhost:8000/matching/explain/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Applications

```bash
# Prepare application
curl -X POST http://localhost:8000/applications/prepare/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Send application
curl -X POST http://localhost:8000/applications/{app_id}/send \
  -H "Authorization: Bearer YOUR_TOKEN"
```

See [API Documentation](docs/API.md) for complete reference.

---

## 💻 Development

### Project Structure

```
syrka/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── pipelines/           # Data pipelines
│   │   ├── job_ingestion/   # Job scraping & ingestion
│   │   └── policy_ingestion/ # Policy document processing
│   ├── rag/                 # RAG components
│   ├── matching/            # Job matching engine
│   ├── automation/          # Application automation
│   ├── curriculum/          # Curriculum generation
│   ├── dashboard/           # Analytics
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── migrations/              # Database migrations
└── data/                    # Data storage
```

### Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **pylint** for linting
- **mypy** for type checking

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint
pylint app/

# Type check
mypy app/
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific categories
pytest -m unit
pytest -m integration
pytest -m api

# Specific file
pytest tests/test_auth.py -v
```

### Test Categories

- **Unit Tests** - Individual functions/classes
- **Integration Tests** - Multiple components working together
- **API Tests** - HTTP endpoint testing
- **Load Tests** - Performance testing (Locust)

See [Testing Guide](docs/TESTING.md) for details.

---

## 🚢 Deployment

### Docker

```bash
# Build
docker build -t syrka .

# Run
docker-compose up -d
```

### Production

Recommended platforms:
- **Railway** - Easiest, ~$5/month (⭐ Recommended)
- **Render** - Free tier available
- **AWS ECS** - Production scale
- **DigitalOcean** - App Platform

See [Deployment Guide](DEPLOYMENT.md) for detailed instructions.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Ensure tests pass (`pytest`)
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 📊 Metrics & Performance

- **API Response Time:** < 200ms (95th percentile)
- **Job Matching:** < 2s for 1000+ jobs
- **Database Queries:** Optimized with indexes
- **Concurrent Users:** 1000+ (with horizontal scaling)
- **Uptime:** 99.9% target

---

## 🗺️ Roadmap

### Q1 2026
- [x] Core MVP (Job matching, Applications, RAG)
- [x] Government dashboard
- [x] Curriculum generation
- [ ] Mobile app (React Native)

### Q2 2026
- [ ] Real-time notifications (WebSocket)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with more job boards

### Q3 2026
- [ ] AI interview preparation
- [ ] Skill assessment platform
- [ ] Employer dashboard
- [ ] API marketplace

### Q4 2026
- [ ] Blockchain credentials
- [ ] Predictive career modeling
- [ ] Global expansion
- [ ] White-label solution

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- FastAPI for excellent async framework
- LangChain for LLM orchestration
- OpenAI/DeepSeek for language models
- Sentence Transformers for embeddings
- FAISS for vector search
- PostgreSQL for reliable database

---

## 📧 Contact & Support

- **Email:** support@syrka.io
- **Documentation:** https://docs.syrka.io
- **Issues:** https://github.com/yourusername/Syrka-V1/issues
- **Discord:** https://discord.gg/syrka

---

<div align="center">

**Built with ❤️ for workforce mobility and economic empowerment**

[Website](https://syrka.io) • [Documentation](docs/) • [API](docs/API.md) • [Blog](https://blog.syrka.io)

</div>
