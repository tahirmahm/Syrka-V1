-- Syrka Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    skills JSONB DEFAULT '[]'::jsonb,
    experience_years INTEGER DEFAULT 0,
    location VARCHAR(255),
    sector_preference VARCHAR(100),
    resume_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    location VARCHAR(255),
    sector VARCHAR(100),
    seniority_level VARCHAR(50),
    salary_min INTEGER,
    salary_max INTEGER,
    source VARCHAR(100),
    embedding BYTEA,
    skills_extracted JSONB DEFAULT '[]'::jsonb,
    posted_at TIMESTAMP WITH TIME ZONE,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_sector ON jobs(sector);
CREATE INDEX idx_jobs_is_active ON jobs(is_active);

-- Applications table
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'draft',
    tailored_cv TEXT,
    cover_letter TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    gmail_message_id VARCHAR(255),
    last_status_check TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_status ON applications(status);

-- Skills table
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    embedding BYTEA,
    demand_score FLOAT DEFAULT 0.0,
    supply_score FLOAT DEFAULT 0.0
);

CREATE INDEX idx_skills_name ON skills(name);

-- Skill demands table
CREATE TABLE skill_demands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    sector VARCHAR(100),
    region VARCHAR(255),
    demand_count INTEGER DEFAULT 0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skill_demands_skill_id ON skill_demands(skill_id);
CREATE INDEX idx_skill_demands_sector ON skill_demands(sector);

-- Policy documents table
CREATE TABLE policy_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    source_url TEXT,
    file_path VARCHAR(500) NOT NULL,
    content_text TEXT NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    country VARCHAR(100),
    document_type VARCHAR(100)
);

CREATE INDEX idx_policy_documents_title ON policy_documents(title);
CREATE INDEX idx_policy_documents_country ON policy_documents(country);

-- Policy chunks table
CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES policy_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding BYTEA,
    chunk_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_policy_chunks_document_id ON policy_chunks(document_id);

-- Curricula table
CREATE TABLE curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    target_sector VARCHAR(100),
    target_skills JSONB DEFAULT '[]'::jsonb,
    policy_alignment_score FLOAT DEFAULT 0.0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_curricula_title ON curricula(title);
CREATE INDEX idx_curricula_target_sector ON curricula(target_sector);

-- Curriculum modules table
CREATE TABLE curriculum_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curriculum_id UUID NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    duration_hours INTEGER DEFAULT 0
);

CREATE INDEX idx_curriculum_modules_curriculum_id ON curriculum_modules(curriculum_id);

-- Curriculum units table
CREATE TABLE curriculum_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_id UUID NOT NULL REFERENCES curriculum_modules(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    competencies JSONB DEFAULT '[]'::jsonb,
    learning_outcomes JSONB DEFAULT '[]'::jsonb,
    assessment_criteria JSONB DEFAULT '{}'::jsonb,
    microcredential_id VARCHAR(255)
);

CREATE INDEX idx_curriculum_units_module_id ON curriculum_units(module_id);

-- Labour stats table
CREATE TABLE labour_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region VARCHAR(255),
    sector VARCHAR(100),
    metric_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_labour_stats_region ON labour_stats(region);
CREATE INDEX idx_labour_stats_sector ON labour_stats(sector);
CREATE INDEX idx_labour_stats_metric_type ON labour_stats(metric_type);
