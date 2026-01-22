# Syrka API Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Users API](#users-api)
3. [Jobs API](#jobs-api)
4. [Matching API](#matching-api)
5. [Applications API](#applications-api)
6. [Curriculum API](#curriculum-api)
7. [Policy Documents API](#policy-documents-api)
8. [Dashboard API](#dashboard-api)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Authentication

All API endpoints (except public ones) require JWT authentication.

### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "user",
  "skills": ["Python", "FastAPI", "Machine Learning"],
  "experience_years": 5,
  "location": "New York, USA",
  "sector_preference": "Technology"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "skills": ["Python", "FastAPI", "Machine Learning"],
  "created_at": "2026-01-22T10:30:00Z"
}
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Users API

### Get Current User

```http
GET /users/me
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "skills": ["Python", "FastAPI", "Machine Learning"],
  "experience_years": 5,
  "location": "New York, USA",
  "sector_preference": "Technology",
  "created_at": "2026-01-22T10:30:00Z"
}
```

### Update Profile

```http
PUT /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Smith",
  "skills": ["Python", "FastAPI", "ML", "Docker"],
  "experience_years": 6,
  "location": "San Francisco, USA"
}
```

### Upload Resume

```http
POST /users/me/resume
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: resume.pdf
```

---

## Jobs API

### List Jobs

```http
GET /jobs?sector=Technology&location=New York&is_active=true&limit=20&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `sector` (optional): Filter by sector
- `location` (optional): Filter by location
- `seniority_level` (optional): junior/mid/senior/executive
- `is_active` (optional): Filter active jobs
- `limit` (default: 20): Number of results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "jobs": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "title": "Senior Python Developer",
      "company": "TechCorp Inc.",
      "location": "New York, USA",
      "description": "We are looking for an experienced Python developer...",
      "requirements": "5+ years Python experience, FastAPI, Docker",
      "sector": "Technology",
      "seniority_level": "senior",
      "salary_min": 120000,
      "salary_max": 160000,
      "is_active": true,
      "posted_at": "2026-01-20T08:00:00Z",
      "source": "linkedin",
      "skills_extracted": ["Python", "FastAPI", "Docker", "AWS"]
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Get Single Job

```http
GET /jobs/{job_id}
Authorization: Bearer {token}
```

### Ingest Jobs (Admin/Government only)

```http
POST /jobs/ingest
Authorization: Bearer {token}
Content-Type: application/json

{
  "sources": ["adzuna", "reed"],
  "params": {
    "query": "software engineer",
    "location": "London",
    "limit": 50
  }
}
```

**Response:**
```json
{
  "message": "Job ingestion started",
  "sources": ["adzuna", "reed"],
  "total_ingested": 87
}
```

---

## Matching API

### Get Job Matches

```http
GET /matching/matches?limit=20&min_probability=0.6
Authorization: Bearer {token}
```

**Query Parameters:**
- `limit` (default: 20): Max matches to return
- `min_probability` (default: 0.0): Minimum match score (0-1)
- `sector` (optional): Filter by sector
- `location` (optional): Filter by location

**Response:**
```json
{
  "matches": [
    {
      "job": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "New York, USA"
      },
      "match_probability": 0.87,
      "scores": {
        "similarity_score": 0.85,
        "skill_overlap": 0.90,
        "location_score": 1.0,
        "seniority_score": 0.95,
        "sector_score": 1.0
      },
      "matched_skills": ["Python", "FastAPI", "Docker"],
      "missing_skills": ["Kubernetes"]
    }
  ],
  "total": 15
}
```

### Explain Match

```http
GET /matching/explain/{job_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "match_probability": 0.87,
  "scores": {
    "similarity_score": 0.85,
    "skill_overlap": 0.90,
    "location_score": 1.0,
    "seniority_score": 0.95,
    "sector_score": 1.0,
    "matched_skills": ["Python", "FastAPI", "Docker"],
    "missing_skills": ["Kubernetes"]
  },
  "explanation": "You are an excellent match for this position. Your Python and FastAPI expertise aligns perfectly with the requirements. Consider learning Kubernetes to be even more competitive."
}
```

---

## Applications API

### List Applications

```http
GET /applications?status=sent&limit=20
Authorization: Bearer {token}
```

**Query Parameters:**
- `status` (optional): draft/sent/replied/rejected
- `limit` (default: 20)
- `offset` (default: 0)

**Response:**
```json
{
  "applications": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "job": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc."
      },
      "status": "sent",
      "sent_at": "2026-01-21T14:30:00Z",
      "created_at": "2026-01-21T14:00:00Z"
    }
  ],
  "total": 5
}
```

### Prepare Application

```http
POST /applications/prepare/{job_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "draft",
  "tailored_cv": "JOHN DOE\nSenior Software Engineer\n...",
  "cover_letter": "Dear Hiring Manager,\n\nI am excited to apply...",
  "created_at": "2026-01-21T14:00:00Z"
}
```

### Send Application

```http
POST /applications/{application_id}/send
Authorization: Bearer {token}
```

### Bulk Apply

```http
POST /applications/bulk-apply
Authorization: Bearer {token}
Content-Type: application/json

{
  "job_ids": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002"
  ],
  "limit": 5
}
```

---

## Curriculum API

### Generate Curriculum

```http
POST /curriculum/generate
Authorization: Bearer {token} (role: educator or government)
Content-Type: application/json

{
  "target_sector": "Technology",
  "target_skills": ["Python", "Machine Learning", "Data Science"],
  "level": "intermediate",
  "duration_weeks": 12
}
```

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "title": "Data Science and Machine Learning with Python",
  "target_sector": "Technology",
  "target_skills": ["Python", "Machine Learning", "Data Science"],
  "level": "intermediate",
  "duration_weeks": 12,
  "modules": [
    {
      "title": "Python Fundamentals",
      "description": "Core Python programming concepts",
      "order": 1,
      "units": [
        {
          "title": "Variables and Data Types",
          "content": "Introduction to Python variables...",
          "duration_hours": 2
        }
      ]
    }
  ],
  "created_at": "2026-01-22T10:00:00Z"
}
```

### List Curricula

```http
GET /curriculum?sector=Technology&level=intermediate
Authorization: Bearer {token}
```

### Export Curriculum

```http
GET /curriculum/{curriculum_id}/export?format=json
Authorization: Bearer {token}
```

**Formats:** `json`, `markdown`, `scorm`

---

## Policy Documents API

### Upload Policy Document

```http
POST /policy/upload
Authorization: Bearer {token} (role: government)
Content-Type: multipart/form-data

file: national_development_plan.pdf
title: National Development Plan 2026-2030
country: United States
document_type: national_plan
```

### Query Policy (RAG)

```http
POST /policy/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "question": "What are the key priorities for workforce development in the technology sector?",
  "filters": {
    "country": "United States",
    "document_type": "national_plan"
  }
}
```

**Response:**
```json
{
  "answer": "Based on the National Development Plan, the key priorities for workforce development in the technology sector include: 1) Upskilling the workforce in AI and machine learning, 2) Increasing diversity in tech roles, 3) Bridging the digital divide...",
  "sources": [
    {
      "document_title": "National Development Plan 2026-2030",
      "chunk_content": "The technology sector requires...",
      "relevance_score": 0.92
    }
  ]
}
```

### List Policy Documents

```http
GET /policy?country=United States&document_type=national_plan
Authorization: Bearer {token}
```

---

## Dashboard API

### Get Overview (Government only)

```http
GET /dashboard/overview
Authorization: Bearer {token} (role: government)
```

**Response:**
```json
{
  "total_jobs": 15420,
  "active_jobs": 12305,
  "total_applications": 45678,
  "total_users": 8934,
  "total_skills_tracked": 450,
  "critical_shortages": 23,
  "top_sectors": [
    {"sector": "Technology", "count": 4521},
    {"sector": "Healthcare", "count": 3245}
  ],
  "top_regions": [
    {"region": "New York", "count": 2341},
    {"region": "California", "count": 2156}
  ]
}
```

### Generate Heatmap

```http
POST /dashboard/heatmap
Authorization: Bearer {token} (role: government)
Content-Type: application/json

{
  "regions": ["North", "South", "East", "West"],
  "sectors": ["Technology", "Healthcare", "Finance"],
  "metric": "job_postings"
}
```

### Skills Shortage Analysis

```http
GET /dashboard/shortages?severity=critical
Authorization: Bearer {token} (role: government)
```

### Demand Forecasting

```http
POST /dashboard/forecast
Authorization: Bearer {token} (role: government)
Content-Type: application/json

{
  "skill": "Machine Learning",
  "sector": "Technology",
  "years": 5
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Example Error Response

```json
{
  "detail": "Email already registered"
}
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Public endpoints:** 100 requests/hour
- **Authenticated endpoints:** 1000 requests/hour
- **Admin endpoints:** 5000 requests/hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642867200
```

---

## Pagination

List endpoints support pagination:

```http
GET /jobs?limit=20&offset=40
```

**Response includes:**
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 40
}
```

---

## Interactive API Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide:
- Interactive API testing
- Request/response examples
- Schema definitions
- Authentication testing
