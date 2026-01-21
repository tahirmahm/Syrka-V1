# Syrka - National Workforce Mobility Operating System

Syrka is an AI-powered platform that unifies education systems, labour market systems, and national development policies into a single intelligent platform.

## Features

### 1. Workforce Mobility Engine
- Job ingestion from multiple sources (LinkedIn, Indeed, Adzuna, Reed)
- AI-powered skill extraction and matching
- Probability-based job-candidate matching
- Automated CV and cover letter generation
- Gmail API integration for application tracking

### 2. Government Dashboard (Human-Capital Intelligence)
- Labour market heatmaps by region/sector
- Skills shortage detection
- Sector-wise demand analytics
- 3-5 year skill demand forecasting
- Policy-to-labour alignment scoring

### 3. Education Alignment Layer
- Policy document ingestion and RAG
- National priority extraction
- Skills-to-industry mapping
- Auto-generated curriculum modules with:
  - Units, competencies, learning outcomes
  - Assessments and microcredentials
- LMS-compatible export

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with async SQLAlchemy
- **Vector Store**: FAISS
- **Embeddings**: sentence-transformers (HuggingFace) + OpenAI
- **LLM**: LangChain with OpenAI
- **Email**: Gmail API
- **PDF Processing**: PyMuPDF

## Setup

### Local Development

1. **Clone repository**:
```bash
git clone <repository-url>
cd syrka
```

2. **Create virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

5. **Setup PostgreSQL**:
```bash
# Install PostgreSQL 16
# Create database
createdb syrka

# Run migrations
psql syrka < migrations/initial_schema.sql
```

6. **Run application**:
```bash
uvicorn app.main:app --reload
```

Access API at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Docker Deployment

1. **Build and run with Docker Compose**:
```bash
docker-compose up --build
```

2. **Access application**:
- API: http://localhost:8000
- Database: localhost:5432

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user

### Jobs
- `GET /jobs` - List jobs with filters
- `GET /jobs/{job_id}` - Get job details

### Matching
- `POST /matching/match` - Get matched jobs for user

### Applications
- `GET /applications` - List user's applications
- `POST /applications` - Create application
- `POST /applications/{id}/send` - Send application

### Curriculum
- `POST /curriculum/generate` - Generate curriculum

### Dashboard (Government only)
- `GET /dashboard/overview` - Overview statistics

## Environment Variables

See `.env.template` for all configuration options.

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `OPENAI_API_KEY` - OpenAI API key

Optional:
- `ADZUNA_API_KEY`, `ADZUNA_APP_ID` - Adzuna job API
- `REED_API_KEY` - Reed job API
- `GMAIL_CREDENTIALS_PATH` - Gmail OAuth credentials

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Syrka Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Workforce Mobility Engine               │  │
│  │  - Job Ingestion  - Matching  - Applications    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │       Human-Capital Intelligence Layer           │  │
│  │  - Heatmaps  - Shortages  - Forecasting         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Education Alignment Layer                │  │
│  │  - Policy RAG  - Curriculum Generation          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │            AI Roadmap Pipeline                   │  │
│  │  - Embeddings  - Vector Store  - LLM            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## License

Copyright © 2024 Syrka. All rights reserved.
