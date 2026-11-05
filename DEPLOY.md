# NoteIQ Production Deployment Guide

This guide covers production deployment for NoteIQ on a single Linux VPS (Ubuntu 22.04 LTS / 24.04 LTS) using Docker Compose and Caddy, as well as managed cloud alternatives (Railway, Render, AWS ECS).

---

## 1. Prerequisites & Environment Checklist

Ensure the following variables are set in `.env.production`:

```ini
APP_NAME=NoteIQ
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# PostgreSQL with pgvector
POSTGRES_USER=noteiq_admin
POSTGRES_PASSWORD=your_secure_db_password_here
POSTGRES_DB=noteiq_production
DATABASE_URL=postgresql+psycopg://noteiq_admin:your_secure_db_password_here@db:5432/noteiq_production

# Redis Queue
REDIS_URL=redis://:your_redis_password@redis:6379/0

# Auth & Security
JWT_SECRET=generate_with_openssl_rand_hex_32_characters_minimum
JWT_EXPIRE_MINUTES=60
REFRESH_EXPIRE_DAYS=14
COOKIE_SECURE=true

# Object Storage (Cloudflare R2, AWS S3, or Backblaze B2)
S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
S3_BUCKET=noteiq-production-files
S3_ACCESS_KEY=your_r2_access_key
S3_SECRET_KEY=your_r2_secret_key
S3_REGION=auto
SIGNED_URL_EXPIRE_SECONDS=300
MAX_UPLOAD_MB=25

# AI Provider Configuration
LLM_PROVIDER=gemini
LLM_API_KEY=your_production_gemini_api_key
LLM_MODEL_ANALYSIS=gemini-2.5-flash
LLM_MODEL_CHAT=gemini-2.5-flash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIM=768
ANALYSIS_RUBRIC_VERSION=v1
```

---

## 2. Single-VPS Deployment (Docker Compose + Caddy)

### 2.1 Server Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git curl
sudo systemctl enable --now docker
```

### 2.2 Clone & Configure
```bash
git clone https://github.com/prachizala/Ai_Notes_Rating_System.git /opt/noteiq
cd /opt/noteiq
cp .env.example .env.production
nano .env.production
```

### 2.3 Run Database Migrations and Seed
```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm backend python ../scripts/seed_reference_data.py
```

### 2.4 Launch Full Production Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 3. Scaling Background Workers

If document upload volume increases, scale the RQ background worker service:
```bash
docker compose -f docker-compose.prod.yml up -d --scale worker=4
```

---

## 4. Rollback Procedure

To roll back to a previous git commit or image tag:
```bash
git checkout <previous_commit_hash>
docker compose -f docker-compose.prod.yml up -d --build
```
If a database rollback is required:
```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic downgrade -1
```

---

## 5. Automated Daily Backup & Restore

### Automated Cron Job
Add to root crontab (`crontab -e`):
```cron
0 2 * * * cd /opt/noteiq && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U noteiq_admin noteiq_production | gzip > /opt/noteiq/backups/backup_$(date +\%F).sql.gz
```

### Restore Database
```bash
gunzip -c /opt/noteiq/backups/backup_2026-11-05.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U noteiq_admin -d noteiq_production
```
