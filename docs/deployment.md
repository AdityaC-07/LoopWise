# AWS Deployment Architecture — LoopWise

> **Status:** Proposed Architecture | **Updated:** 2026-10
> This document outlines the recommended AWS deployment architecture for LoopWise production.

---

## 1. Architecture Overview

### 1.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                               │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   ALB /      │───▶│   ECS Fargate│    │   AWS RDS    │       │
│  │   CloudFront │    │   Backend    │◀──▶│ PostgreSQL   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                  │                      │              │
│         │                  ▼                      │              │
│         │          ┌──────────────┐              │              │
│         │          │ElastiCache   │              │              │
│         │          │   Redis      │              │              │
│         │          └──────────────┘              │              │
│         │                  │                      │              │
│         │                  ▼                      │              │
│         │          ┌──────────────┐              │              │
│         └─────────▶│   AWS S3     │              │              │
│                    │   Images     │              │              │
│                    └──────────────┘              │              │
│                                                   │              │
│                                                   ▼              │
│                                          ┌──────────────┐       │
│                                          │  CloudWatch  │       │
│                                          │  Logs/Metrics│       │
│                                          └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Purpose | Notes |
|---|---|---|
| **Application Load Balancer (ALB)** | Frontend TLS termination, traffic distribution | SSL/TLS certificates via AWS Certificate Manager |
| **CloudFront** (optional) | CDN for static assets, DDoS protection | Cache static frontend assets; forward API requests to ALB |
| **ECS Fargate** | Container orchestration for backend | Run FastAPI backend containers; auto-scaling enabled |
| **AWS RDS PostgreSQL** | Primary database | Multi-AZ deployment for high availability; automated backups |
| **ElastiCache Redis** | Caching layer | Analytics cache, session storage, Celery broker |
| **AWS S3** | Consent-gated image storage | Server-side encryption (AES-256); lifecycle policies |
| **CloudWatch** | Logging and monitoring | Container logs, application metrics, alarm notifications |
| **AWS Secrets Manager** | Secret storage | DATABASE_URL, SECRET_KEY, S3 credentials |

---

## 2. Infrastructure Prerequisites

### 2.1 AWS Account Setup

1. **AWS Account**: Active AWS account with appropriate IAM permissions
2. **Region**: Recommended region: `ap-south-1` (Mumbai) or nearest to target users
3. **VPC**: Existing VPC with at least 2 private subnets for RDS and 2 public subnets for ALB/ECS
4. **IAM Roles**: Service-linked roles for ECS, RDS, and ElastiCache

### 2.2 Required AWS Services

| Service | Configuration |
|---|---|
| **VPC** | CIDR block: `10.0.0.0/16` (or existing) |
| **Subnets** | 2 public subnets (ALB, NAT Gateway), 2 private subnets (ECS, RDS, Redis) |
| **Route 53** | Hosted zone for domain (e.g., `loopwise.example.com`) |
| **ACM** | SSL/TLS certificate for domain |
| **ECS Cluster** | Fargate cluster named `loopwise-cluster` |
| **ECR Repositories** | `loopwise-backend`, `loopwise-frontend` |
| **RDS PostgreSQL** | Instance class: `db.t3.medium` (minimum); version: PostgreSQL 15+ |
| **ElastiCache Redis** | Node type: `cache.t3.micro` (minimum); version: Redis 7+ |
| **S3 Bucket** | Bucket for image storage; versioning enabled; encryption enabled |
| **CloudWatch Logs** | Log groups for ECS tasks |
| **Secrets Manager** | Secret for database credentials and app secrets |

### 2.3 Domain and DNS

- **Domain**: Registered domain (e.g., via Route 53 or external registrar)
- **DNS Records**:
  - `A` record for `api.loopwise.example.com` → ALB
  - `A` record for `loopwise.example.com` → CloudFront (if used) or ALB
  - `CNAME` for `www.loopwise.example.com` → `loopwise.example.com`

---

## 3. Database Configuration

### 3.1 Production PostgreSQL (AWS RDS)

**Connection String Template:**
```
postgresql+asyncpg://user:password@loopwise-db.xxxx.ap-south-1.rds.amazonaws.com:5432/loopwise
```

**Environment Variables:**
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/loopwise
```

**RDS Configuration:**
- **Engine**: PostgreSQL 15.x or later
- **Instance Class**: `db.t3.medium` (scale based on traffic)
- **Storage**: 20 GB SSD (gp3); auto-scaling enabled
- **Multi-AZ**: Enabled for production (recommended)
- **Backup Retention**: 7 days (minimum)
- **Parameter Group**: Custom group with:
  - `max_connections`: 100
  - `shared_buffers`: 256MB
  - `effective_cache_size`: 1GB
  - `maintenance_work_mem`: 64MB

### 3.2 Local Development (SQLite)

**Connection String Template:**
```
sqlite+aiosqlite:///./loopwise.db
```

**Environment Variables:**
```bash
DATABASE_URL=sqlite+aiosqlite:///./loopwise.db
```

**Notes:**
- SQLite database file is excluded from Git (see `.gitignore`)
- Use SQLite for local development only
- Switch to PostgreSQL for staging/production

---

## 4. Storage Configuration

### 4.1 S3 Bucket for Images

**Bucket Policy Template:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::loopwise-images/*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

**Environment Variables:**
```bash
S3_BUCKET=loopwise-images
AWS_REGION=ap-south-1
```

**IAM Role Requirements:**
- ECS task role must have `s3:PutObject` and `s3:GetObject` permissions on the bucket
- Use IAM role, not access keys

### 4.2 Lifecycle Policy

- **Transition to Standard-IA**: After 30 days
- **Transition to Glacier**: After 90 days
- **Expiration**: After 1 year (configurable based on retention policy)

---

## 5. Redis Configuration

### 5.1 ElastiCache Redis

**Connection String Template:**
```
redis://loopwise-redis.xxxx.cache.amazonaws.com:6379/0
```

**Environment Variables:**
```bash
REDIS_URL=redis://loopwise-redis.xxxx.cache.amazonaws.com:6379/0
```

**Configuration:**
- **Node Type**: `cache.t3.micro` (scale based on traffic)
- **Engine Version**: Redis 7.x
- **Parameter Group**: Default (or custom with `maxmemory-policy=allkeys-lru`)
- **Encryption at Rest**: Enabled (recommended)
- **Encryption in Transit**: Enabled (recommended)

---

## 6. Application Configuration

### 6.1 Backend Environment Variables

```bash
# Application Mode
DEMO_MODE=false
ENVIRONMENT=production

# Data Stores
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/loopwise
REDIS_URL=redis://loopwise-redis.xxxx.cache.amazonaws.com:6379/0

# ML & Storage
MODEL_PATH=/app/models/model.onnx
CLASS_INDEX_MAP=/app/models/class_index_map.json
MODEL_VERSION=yolo26-v1
S3_BUCKET=loopwise-images
AWS_REGION=ap-south-1

# Security & Auth
SECRET_KEY=<generated-secure-key-min-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
CORS_ORIGINS=https://loopwise.example.com,https://www.loopwise.example.com
```

### 6.2 Frontend Environment Variables

```bash
VITE_API_BASE_URL=https://api.loopwise.example.com
```

**Note:** Frontend uses Vite environment variables (prefixed with `VITE_`).

---

## 7. Deployment Pipeline

### 7.1 CI/CD Workflow (GitHub Actions or AWS CodePipeline)

**Stages:**
1. **Build**: Build Docker images for frontend and backend
2. **Push**: Push images to ECR
3. **Deploy Backend**: Update ECS task definition with new image
4. **Deploy Frontend**: Update ECS task definition with new image
5. **Database Migrations**: Run Alembic migrations via ECS task
6. **Health Check**: Verify deployment via `/api/v1/health`

### 7.2 Docker Build and Push

```bash
# Backend
cd backend
docker build -t loopwise-backend:latest .
docker tag loopwise-backend:latest <account-id>.dkr.ecr.<region>.amazonaws.com/loopwise-backend:latest
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/loopwise-backend:latest

# Frontend
cd frontend
docker build -t loopwise-frontend:latest .
docker tag loopwise-frontend:latest <account-id>.dkr.ecr.<region>.amazonaws.com/loopwise-frontend:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/loopwise-frontend:latest
```

### 7.3 Database Migrations

**Run migrations via ECS one-off task:**
```bash
aws ecs run-task \
  --cluster loopwise-cluster \
  --task-definition loopwise-migrations \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"
```

**Migration task definition includes:**
```dockerfile
CMD ["alembic", "upgrade", "head"]
```

---

## 8. Security Considerations

### 8.1 Network Security

- **VPC**: Private subnets for application and database
- **Security Groups**:
  - ALB: Allow 80/443 from internet
  - ECS: Allow 8000 from ALB only
  - RDS: Allow 5432 from ECS only
  - Redis: Allow 6379 from ECS only
- **NACLs**: Default deny all; allow specific traffic

### 8.2 Secrets Management

- **AWS Secrets Manager**: Store `DATABASE_URL`, `SECRET_KEY`, and other sensitive values
- **IAM Roles**: Grant ECS task role read access to Secrets Manager
- **Rotation**: Enable automatic secret rotation for database credentials

### 8.3 Encryption

- **In Transit**: TLS/SSL for all external connections (ALB, RDS, Redis, S3)
- **At Rest**:
  - RDS: Encryption enabled
  - S3: Server-side encryption (AES-256)
  - ElastiCache: Encryption at rest enabled
  - EBS volumes: Encrypted by default

### 8.4 Access Control

- **IAM**: Least privilege principle for all roles
- **MFA**: Required for AWS console access
- **Audit Logging**: CloudTrail enabled for API calls

---

## 9. Monitoring and Logging

### 9.1 CloudWatch Metrics

- **ECS**: CPU utilization, memory utilization, task count
- **ALB**: Request count, latency, HTTP 5xx errors
- **RDS**: CPU, connections, free storage
- **Redis**: CPU, memory, evictions

### 9.2 CloudWatch Logs

- **Log Groups**:
  - `/ecs/loopwise-backend`
  - `/ecs/loopwise-frontend`
- **Retention**: 7 days (configurable)
- **Log Format**: JSON structured logs for easy querying

### 9.3 Alarms

| Metric | Threshold | Action |
|---|---|---|
| ALB 5xx Error Rate | > 5% | SNS notification |
| ECS CPU Utilization | > 80% | Auto-scale out |
| RDS CPU Utilization | > 85% | SNS notification |
| RDS Free Storage | < 2 GB | SNS notification |
| Redis CPU Utilization | > 85% | SNS notification |

---

## 10. Cost Estimates (Monthly)

| Service | Configuration | Est. Cost (USD) |
|---|---|---|
| **ECS Fargate** | 2 tasks × 0.5 vCPU × 1 GB, 24/7 | ~$30 |
| **ALB** | Standard load balancer | ~$20 |
| **RDS PostgreSQL** | db.t3.medium, 20 GB | ~$35 |
| **ElastiCache Redis** | cache.t3.micro | ~$15 |
| **S3** | 10 GB storage + requests | ~$2 |
| **CloudWatch** | Logs + metrics | ~$10 |
| **Data Transfer** | 100 GB out | ~$9 |
| **Total** | | **~$121/month** |

*Note: Estimates are approximate and vary by region and usage.*

---

## 11. Deployment Checklist

### Pre-Deployment

- [ ] AWS account and VPC configured
- [ ] Domain registered and DNS configured
- [ ] SSL/TLS certificate provisioned via ACM
- [ ] ECR repositories created
- [ ] RDS PostgreSQL instance created and configured
- [ ] ElastiCache Redis cluster created and configured
- [ ] S3 bucket created with lifecycle policy
- [ ] IAM roles and policies created
- [ ] Secrets Manager secrets created
- [ ] ECS cluster and task definitions created
- [ ] ALB and target groups created
- [ ] CloudWatch log groups created
- [ ] Alarm notifications configured

### Deployment

- [ ] Docker images built and pushed to ECR
- [ ] Database migrations run successfully
- [ ] Backend ECS service updated
- [ ] Frontend ECS service updated
- [ ] Health checks passing (`/api/v1/health`)
- [ ] Smoke tests completed

### Post-Deployment

- [ ] Verify API endpoints accessible
- [ ] Verify image upload works (with consent)
- [ ] Verify analytics data persists
- [ ] Verify demo mode disabled in production
- [ ] Monitor CloudWatch metrics for 24 hours
- [ ] Review logs for errors

---

## 12. Rollback Procedure

If deployment fails:

1. **ECS**: Roll back to previous task definition revision
2. **Database**: Run `alembic downgrade -1` if migration caused issues
3. **Frontend**: Roll back to previous Docker image
4. **Verify**: Health checks passing after rollback

```bash
# Rollback ECS service
aws ecs update-service \
  --cluster loopwise-cluster \
  --service loopwise-backend \
  --task-definition loopwise-backend:<previous-revision>
```

---

## 13. ML Artifacts Required from Agniv

The following ML artifacts must be obtained from Agniv before production deployment:

1. **ONNX Model File**: `model.onnx` — YOLO26 fine-tuned weights in ONNX format
2. **Class Index Mapping**: `class_index_map.json` — Mapping from model output indices to material IDs
3. **Model Version**: Exact version string (e.g., `yolo26-v1`) to match code configuration
4. **Model Input Dimensions**: Confirmed input size (e.g., 640×640) for preprocessing
5. **Preprocessing Configuration**: Normalization parameters (mean, std) if required

**Storage Location:**
- Place model files in S3 bucket: `s3://loopwise-models/models/`
- Mount S3 bucket to ECS task or download at startup
- Environment variable: `MODEL_PATH=/app/models/model.onnx`

---

## 14. References

- [AWS ECS Fargate Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS PostgreSQL Documentation](https://docs.aws.amazon.com/rds/)
- [AWS ElastiCache Redis Documentation](https://docs.aws.amazon.com/elasticache/)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [LoopWise Architecture Document](/docs/architecture.md)
