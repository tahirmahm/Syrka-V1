# Syrka Architecture Documentation

## System Overview

Syrka is a National Workforce Mobility Operating System that bridges education systems, labour markets, and national development policies using AI and data analytics.

```
┌─────────────────────────────────────────────────────────────┐
│                    SYRKA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         LAYER 1: WORKFORCE MOBILITY ENGINE           │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │  │
│  │  │Job Scraping│ │AI Matching │ │Auto-Apply      │  │  │
│  │  │& Ingestion │ │Engine      │ │(Gmail + LLM)   │  │  │
│  │  └────────────┘ └────────────┘ └────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     LAYER 2: HUMAN-CAPITAL INTELLIGENCE DASHBOARD    │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │  │
│  │  │Labour      │ │Skills      │ │Demand          │  │  │
│  │  │Heatmaps    │ │Shortage    │ │Forecasting     │  │  │
│  │  └────────────┘ └────────────┘ └────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       LAYER 3: EDUCATION ALIGNMENT LAYER             │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │  │
│  │  │Policy RAG  │ │Priority    │ │Curriculum      │  │  │
│  │  │System      │ │Extraction  │ │Generation      │  │  │
│  │  └────────────┘ └────────────┘ └────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     HORIZONTAL: AI ROADMAP PIPELINE                  │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │  │
│  │  │Vector Store│ │Embeddings  │ │LLM Chain       │  │  │
│  │  │(FAISS)     │ │(ST/OpenAI) │ │(LangChain)     │  │  │
│  │  └────────────┘ └────────────┘ └────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             DATA LAYER                                │  │
│  │  PostgreSQL + AsyncPG | FAISS Vector Store           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Framework
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI server for production
- **Python 3.11+** - Programming language

### Database
- **PostgreSQL 15** - Relational database
- **AsyncPG** - Async PostgreSQL driver
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations

### AI & Machine Learning
- **LangChain** - LLM orchestration framework
- **OpenAI/DeepSeek API** - Large language models
- **Sentence Transformers** - Text embeddings
- **FAISS** - Vector similarity search
- **PyTorch** - ML framework backend

### Authentication & Security
- **JWT (JSON Web Tokens)** - Stateless authentication
- **Bcrypt** - Password hashing
- **Pydantic** - Data validation

### External Integrations
- **Gmail API** - Email automation
- **Adzuna API** - Job aggregation
- **Reed API** - Job aggregation
- **Beautiful Soup** - Web scraping

---

## Component Architecture

### 1. Job Ingestion Pipeline

```python
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Scraper   │ ───> │  Normalizer  │ ───> │ Orchestrator│
│ (LinkedIn,  │      │  (Unify      │      │ (Skills +   │
│  Indeed)    │      │   Format)    │      │  Embeddings)│
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
┌─────────────┐      ┌──────────────┐             │
│ API Ingestor│ ───> │  Normalizer  │ ───────────>│
│ (Adzuna,    │      │              │             │
│  Reed)      │      │              │             ▼
└─────────────┘      └──────────────┘      ┌─────────────┐
                                            │  PostgreSQL │
                                            │  + FAISS    │
                                            └─────────────┘
```

**Components:**
- `scraper.py` - Web scraping (LinkedIn, Indeed)
- `api_ingestor.py` - API integration (Adzuna, Reed)
- `normalizer.py` - Standardize job data format
- `orchestrator.py` - Coordinate pipeline, extract skills, generate embeddings

**Flow:**
1. Scrape/fetch jobs from multiple sources
2. Normalize to standard format
3. Extract skills using NLP
4. Generate embeddings for semantic search
5. Store in PostgreSQL + FAISS

---

### 2. Matching Engine

```python
┌─────────────┐
│    User     │
│  Profile    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│        MATCHING ENGINE                  │
│  ┌──────────────┐  ┌─────────────────┐│
│  │  Similarity  │  │   Heuristics    ││
│  │   Scorer     │  │   (Location,    ││
│  │ (Embeddings) │  │   Seniority)    ││
│  └──────────────┘  └─────────────────┘│
│         │                  │           │
│         └────────┬─────────┘           │
│                  ▼                     │
│          ┌──────────────┐              │
│          │    Ranker    │              │
│          │ (Weighted    │              │
│          │  Scoring)    │              │
│          └──────────────┘              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
          ┌──────────────┐
          │ Ranked Jobs  │
          │ with Scores  │
          └──────────────┘
```

**Components:**
- `skill_extractor.py` - Extract skills from text
- `similarity.py` - Cosine similarity on embeddings
- `heuristics.py` - Location, seniority, sector matching
- `ranker.py` - Combine scores with configurable weights
- `engine.py` - Orchestrate all matching components

**Scoring Formula:**
```
Final Score = (w1 × similarity) + (w2 × heuristics) + (w3 × skill_overlap)
```

Default weights: similarity=0.5, heuristics=0.3, skill_overlap=0.2

---

### 3. RAG System (Policy Documents)

```python
┌─────────────┐
│   PDF Doc   │
└──────┬──────┘
       │
       ▼
┌──────────────┐      ┌───────────────┐
│ PDF Processor│ ───> │    Chunker    │
│  (PyMuPDF)   │      │ (512 tokens)  │
└──────────────┘      └───────┬───────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Embedding       │
                    │  Service         │
                    │ (Transformers)   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Vector Store    │
                    │    (FAISS)       │
                    └────────┬─────────┘
                             │
┌─────────────┐              │
│   Query     │              │
└──────┬──────┘              │
       │                     │
       ▼                     ▼
┌──────────────┐      ┌───────────────┐
│  Retriever   │ <──> │   PostgreSQL  │
│  (Top-K)     │      │   Metadata    │
└──────┬───────┘      └───────────────┘
       │
       ▼
┌──────────────┐
│  LLM Chain   │
│ (LangChain)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Answer     │
└──────────────┘
```

**Components:**
- `pdf_processor.py` - Extract text from PDFs
- `chunker.py` - Split text into semantic chunks
- `embeddings.py` - Generate vector embeddings
- `vector_store.py` - FAISS index management
- `retriever.py` - Semantic search over chunks
- `chain.py` - LangChain RAG pipeline

**Flow:**
1. Upload PDF policy document
2. Extract text using PyMuPDF
3. Chunk into 512-token segments with 50-token overlap
4. Generate embeddings for each chunk
5. Store in FAISS + PostgreSQL
6. Query: Retrieve top-K similar chunks
7. Feed chunks to LLM for answer generation

---

### 4. Application Automation

```python
┌─────────────┐      ┌──────────────┐
│    User     │      │     Job      │
└──────┬──────┘      └──────┬───────┘
       │                    │
       └─────────┬──────────┘
                 │
                 ▼
        ┌─────────────────┐
        │   Applicator    │
        │   Orchestrator  │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ CV Generator │  │ Cover Letter │
│   (LLM)      │  │  Generator   │
│              │  │    (LLM)     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌──────────────┐
        │ Gmail Client │
        │ (OAuth2)     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │  Application │
        │    Sent      │
        └──────────────┘
```

**Components:**
- `cv_generator.py` - Tailor CV using LLM
- `cover_letter_generator.py` - Generate cover letter
- `gmail_client.py` - Gmail API integration
- `applicator.py` - Orchestrate application process

**Flow:**
1. User selects job to apply
2. LLM generates tailored CV highlighting relevant experience
3. LLM generates personalized cover letter
4. Authenticate with Gmail OAuth2
5. Send email with CV and cover letter attached
6. Track application status

---

### 5. Curriculum Generation

```python
┌─────────────────┐
│ National Policy │
│   (via RAG)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Curriculum Generator (LLM)    │
│                                  │
│  ┌──────────────────────────┐  │
│  │ 1. Extract priorities    │  │
│  │ 2. Identify skill gaps   │  │
│  │ 3. Generate modules      │  │
│  │ 4. Create assessments    │  │
│  │ 5. Add microcredentials  │  │
│  └──────────────────────────┘  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Curriculum    │
│   - Modules     │
│   - Units       │
│   - Outcomes    │
│   - Assessments │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Exporter      │
│ - JSON          │
│ - Markdown      │
│ - SCORM (LMS)   │
└─────────────────┘
```

**Components:**
- `templates.py` - Curriculum templates
- `structure.py` - Pydantic models
- `generator.py` - LLM-powered generation
- `exporter.py` - Multiple format exports

**Features:**
- Policy-aligned curriculum design
- Modular structure (Modules → Units → Content)
- Learning outcomes and assessments
- Microcredentials integration
- LMS-compatible export (SCORM)

---

## Data Models

### Core Entities

```
User
├── id (UUID)
├── email (unique)
├── hashed_password
├── full_name
├── role (user/educator/government)
├── skills (Array)
├── experience_years
├── location
├── sector_preference
└── resume_text

Job
├── id (UUID)
├── title
├── company
├── description
├── requirements
├── location
├── sector
├── seniority_level
├── salary_min/max
├── posted_at
├── source (linkedin/indeed/adzuna/reed)
├── external_id
├── skills_extracted (Array)
└── embedding (Vector)

Application
├── id (UUID)
├── user_id (FK)
├── job_id (FK)
├── status (draft/sent/replied/rejected)
├── tailored_cv
├── cover_letter
├── sent_at
└── gmail_message_id

PolicyDocument
├── id (UUID)
├── title
├── file_path
├── content_text
├── country
├── document_type
└── chunks (One-to-Many)

PolicyChunk
├── id (UUID)
├── document_id (FK)
├── chunk_index
├── content
├── embedding (Vector)
└── chunk_metadata (JSON)

Curriculum
├── id (UUID)
├── title
├── target_sector
├── target_skills (Array)
├── level
├── duration_weeks
└── modules (One-to-Many)
```

---

## API Architecture

### Layered Structure

```
┌─────────────────────────────────┐
│         FastAPI Routes          │  (HTTP Endpoints)
│  /auth, /users, /jobs, etc.     │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│        Service Layer            │  (Business Logic)
│  AuthService, JobService, etc.  │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│      Pipeline/Engine Layer      │  (Core Operations)
│  Matching, RAG, Curriculum      │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│        Database Layer           │  (Data Access)
│    SQLAlchemy + AsyncPG         │
└─────────────────────────────────┘
```

### Request Flow

```
Client Request
     │
     ▼
┌──────────────┐
│  Middleware  │ (CORS, Auth)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Router     │ (/jobs/matches)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Dependencies │ (get_current_user, get_db)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Handler    │ (Route function)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Service    │ (Business logic)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Database   │ (ORM queries)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Response   │ (JSON)
└──────────────┘
```

---

## Security Architecture

### Authentication Flow

```
1. User registers → Password hashed with bcrypt
2. User logs in → JWT token generated
3. Token includes: user_id, role, exp
4. Client stores token (localStorage/cookie)
5. Each request includes: Authorization: Bearer {token}
6. Server validates token → Extracts user info
7. Role-based access control applied
```

### Security Measures

- **Password Hashing:** Bcrypt with salt
- **JWT Tokens:** HS256 algorithm, 60-minute expiration
- **Role-Based Access Control (RBAC):** User/Educator/Government roles
- **Input Validation:** Pydantic schemas
- **SQL Injection Protection:** SQLAlchemy ORM
- **XSS Protection:** FastAPI auto-escaping
- **CORS:** Configurable allowed origins
- **Rate Limiting:** Planned feature

---

## Scalability Considerations

### Current Architecture
- **Vertical Scaling:** Single server, can upgrade CPU/RAM
- **Database:** PostgreSQL with connection pooling
- **Async Operations:** Non-blocking I/O with async/await

### Future Scaling Strategies

1. **Horizontal Scaling:**
   - Multiple API server instances
   - Load balancer (Nginx/HAProxy)
   - Sticky sessions for WebSocket support

2. **Database Scaling:**
   - Read replicas for query distribution
   - Connection pooling (PgBouncer)
   - Partitioning for large tables (jobs, applications)

3. **Caching:**
   - Redis for frequently accessed data
   - Cache job listings, user profiles
   - Cache RAG query results

4. **Async Task Queue:**
   - Celery + RabbitMQ/Redis
   - Offload: job scraping, email sending, curriculum generation
   - Background processing for heavy ML operations

5. **Vector Store Scaling:**
   - FAISS sharding for large indices
   - Distributed vector search (Milvus/Weaviate)
   - GPU acceleration for embeddings

---

## Deployment Architecture

### Production Setup

```
┌──────────────────────────────────────────────┐
│              Load Balancer                   │
│               (Nginx/ALB)                    │
└────────────────┬─────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  API Server  │  │  API Server  │
│   (Docker)   │  │   (Docker)   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
    ┌───────────────────────┐
    │   PostgreSQL + FAISS  │
    │   (Managed Service)   │
    └───────────────────────┘
```

### Container Architecture

```dockerfile
FROM python:3.11-slim
# Install system deps
# Copy application
# Install Python deps
# Expose port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## Monitoring & Observability

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log aggregation: ELK Stack or CloudWatch

### Metrics
- Request latency
- Error rates
- Database query performance
- ML model inference time
- Job ingestion throughput

### Health Checks
- `/health` endpoint
- Database connectivity check
- External API status

---

## Performance Optimization

### Database
- Indexes on frequently queried fields
- Async queries (no blocking)
- Connection pooling
- Query optimization (EXPLAIN ANALYZE)

### ML Operations
- Batch embeddings generation
- Model caching (keep in memory)
- GPU acceleration when available
- Async processing for non-critical paths

### API
- Response compression (gzip)
- Pagination for list endpoints
- Field selection (sparse fields)
- ETags for caching

---

## Future Architecture Enhancements

1. **Microservices:**
   - Separate services: Matching, RAG, Curriculum
   - Service mesh (Istio)
   - gRPC for inter-service communication

2. **Event-Driven Architecture:**
   - Event bus (Kafka/RabbitMQ)
   - Events: JobPosted, ApplicationSent, CurriculumGenerated
   - Enables real-time processing and notifications

3. **GraphQL API:**
   - Alternative to REST
   - Client-specified queries
   - Reduced over-fetching

4. **Real-time Features:**
   - WebSocket support for live job updates
   - Server-sent events for notifications
   - Live dashboard updates

5. **ML Model Serving:**
   - Separate model serving infrastructure
   - TensorFlow Serving / TorchServe
   - Model versioning and A/B testing
