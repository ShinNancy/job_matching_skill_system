# Job Market Intelligence & AI Matching Platform

> Nền tảng **Data Mining & AI nâng cao** phục vụ phân tích thị trường tuyển dụng IT tại Việt Nam, xây dựng dữ liệu tri thức nghề nghiệp, huấn luyện nhiều mô hình AI/ML và tích hợp thành hệ thống gợi ý việc làm có thể demo end-to-end.

---

## Mục lục

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Project Goals](#3-project-goals)
4. [Two-Phase Strategy](#4-two-phase-strategy)
5. [Scope](#5-scope)
6. [Team Structure](#6-team-structure)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [High-Level Architecture](#9-high-level-architecture)
10. [Phase 1 — Data Mining & Knowledge Pipeline](#10-phase-1--data-mining--knowledge-pipeline)
11. [Phase 2 — AI Training, Evaluation & Model Serving](#11-phase-2--ai-training-evaluation--model-serving)
12. [Database Design](#12-database-design)
13. [ML Dataset & Feature Design](#13-ml-dataset--feature-design)
14. [Modeling Strategy](#14-modeling-strategy)
15. [Evaluation Strategy](#15-evaluation-strategy)
16. [API Contract](#16-api-contract)
17. [Folder Structure](#17-folder-structure)
18. [Development Roadmap](#18-development-roadmap)
19. [Definition of Done](#19-definition-of-done)
20. [Risks & Mitigation](#20-risks--mitigation)

---

## 1. Project Overview

| Mục | Nội dung |
|---|---|
| **Tên dự án** | Job Market Intelligence & AI Matching Platform |
| **Mục tiêu chính** | Data Mining thị trường tuyển dụng + AI matching nâng cao |
| **Ngữ cảnh** | Dự án nhóm 3 người, định hướng học thuật/portfolio/research engineering |
| **Thị trường mục tiêu** | Việc làm IT tại Việt Nam |
| **Ngôn ngữ tài liệu** | Tiếng Việt |
| **Kiến trúc** | Data-centric system: Data Pipeline → Knowledge Data → ML Pipeline → AI Service → Demo App |
| **Không sử dụng** | Vector Database, pgvector, realtime ANN retrieval |

### Tech Stack tóm tắt

```text
Backend/API      : Java 21, Spring Boot 3
Frontend         : Next.js 14
AI/ML Service    : Python, FastAPI, scikit-learn, XGBoost, LightGBM, pandas
Data Pipeline    : Python, Scrapy, Playwright, BeautifulSoup, APScheduler
Database         : PostgreSQL 16
Cache/Queue      : Redis optional
Migration        : Flyway
Experiment       : MLflow optional hoặc PostgreSQL experiment tables
Deployment       : Docker Compose
CI/CD            : GitHub Actions
```

### Quyết định kiến trúc quan trọng

Dự án **không dùng Vector Database** vì mục tiêu chính không phải realtime semantic search ở quy mô lớn. Hệ thống tập trung vào:

```text
1. Thu thập dữ liệu thật từ nhiều nguồn
2. Làm sạch và chuẩn hóa dữ liệu
3. Xây dựng knowledge data cho thị trường việc làm
4. Sinh dataset có version phục vụ huấn luyện
5. Train và đánh giá nhiều mô hình
6. Tích hợp model tốt nhất vào hệ thống demo
```

---

## 2. Problem Statement

Người tìm việc IT tại Việt Nam thường gặp ba vấn đề lớn:

| # | Vấn đề | Hệ quả |
|---|---|---|
| 1 | Tin tuyển dụng phân tán trên nhiều nền tảng | Khó có cái nhìn tổng thể về thị trường |
| 2 | Dữ liệu tuyển dụng không chuẩn hóa | Khó phân tích kỹ năng, lương, seniority, job family |
| 3 | Người tìm việc khó biết mình phù hợp với công việc nào | Thiếu hệ thống đánh giá skill gap và mức độ phù hợp dựa trên dữ liệu |

Dự án giải quyết vấn đề này bằng cách xây dựng một pipeline dữ liệu hoàn chỉnh và lớp AI/ML phía sau để khai thác tri thức từ dữ liệu tuyển dụng.

---

## 3. Project Goals

### 3.1 Mục tiêu học thuật

| Chủ đề | Nội dung học |
|---|---|
| Data Mining | Crawl, parse, clean, deduplicate, normalize dữ liệu tuyển dụng |
| Data Engineering | ETL pipeline, data quality, knowledge aggregation, dataset versioning |
| Machine Learning | Feature engineering, model training, model comparison, ranking metrics |
| NLP | Text normalization, skill extraction, TF-IDF/SBERT offline features optional |
| Software Engineering | Modular design, clean architecture, API contract, testing |
| MLOps cơ bản | Experiment tracking, model registry, model serving |

### 3.2 Mục tiêu sản phẩm/demo

Hệ thống cuối cùng cần demo được:

1. Chạy crawler và ETL để cập nhật dữ liệu tuyển dụng.
2. Hiển thị dashboard chất lượng dữ liệu và tri thức thị trường.
3. Sinh training dataset từ dữ liệu đã xử lý.
4. Train nhiều mô hình AI/ML và so sánh kết quả.
5. Chọn model tốt nhất và đăng ký vào model registry.
6. Người dùng nhập hồ sơ/kỹ năng và nhận Top-N job phù hợp.
7. Hiển thị lý do match: skill coverage, missing skills, salary/location/experience fit.

---

## 4. Two-Phase Strategy

Dự án được chia thành hai phase chính. Hai phase này độc lập về mục tiêu nhưng liên kết chặt chẽ qua dữ liệu.

```text
Phase 1: Data Mining & Knowledge Pipeline
    Output: Clean Data + Knowledge Data + ML-ready Dataset Base

Phase 2: AI Training, Evaluation & Integration
    Input : Output của Phase 1
    Output: Best Model + Evaluation Report + Prediction API/Demo
```

### 4.1 Phase 1 — Data Mining

Phase 1 tập trung xây dựng dữ liệu chất lượng cao.

```text
Crawler
  ↓
Raw Data Storage
  ↓
Parser & Cleaner
  ↓
Normalized Job Data
  ↓
Skill Extraction & Deduplication
  ↓
Knowledge Aggregation
  ↓
Data Quality Report
  ↓
ML-ready Source Data
```

Output chính của Phase 1:

- `raw_job_posting`
- `job`
- `job_skill`
- `skill`, `skill_alias`
- `company`, `location`, `industry`, `job_family`
- `job_family_skill_stat`
- `skill_cooccurrence`
- `salary_stat`
- `market_demand_stat`
- data quality metrics

### 4.2 Phase 2 — AI

Phase 2 sử dụng output của Phase 1 để tạo dataset train và đánh giá nhiều mô hình.

```text
Knowledge Data
  ↓
Dataset Builder
  ↓
Feature Engineering
  ↓
Train/Validation/Test Split
  ↓
Train Multiple Models
  ↓
Evaluate
  ↓
Register Best Model
  ↓
Serve Prediction API
```

Output chính của Phase 2:

- `ml_dataset_version`
- `user_job_training_sample`
- `ml_experiment`
- `ml_evaluation_metric`
- `model_registry`
- model artifact: `.pkl`, `.joblib`, `.json` hoặc `.txt`
- evaluation report
- prediction API

---

## 5. Scope

### 5.1 In Scope

| Nhóm | Tính năng |
|---|---|
| Data Crawling | Crawl tin tuyển dụng từ tối thiểu 2 nguồn trong MVP |
| Raw Storage | Lưu raw HTML/JSON để debug và reprocess |
| ETL | Parse, clean, normalize title, salary, location, experience, seniority |
| Skill Extraction | Extract skill từ JD bằng dictionary/alias/rule-based NLP |
| Deduplication | Phát hiện trùng lặp dựa trên source URL, content hash, title/company/location |
| Data Quality | Tính tỷ lệ parse success, duplicate, missing salary, missing skills |
| Knowledge Data | Tạo thống kê skill, salary, demand, skill co-occurrence |
| Dataset Builder | Sinh dataset version phục vụ ML |
| AI Training | Train nhiều model: rule-based, logistic regression, random forest, XGBoost/LightGBM |
| Evaluation | Đánh giá bằng classification metrics và ranking metrics |
| Model Registry | Lưu model tốt nhất và metadata |
| Demo App | Dashboard dữ liệu + demo gợi ý job |

### 5.2 Out of Scope

| Tính năng | Lý do |
|---|---|
| Vector Database / pgvector / Qdrant | Không cần realtime ANN retrieval cho mục tiêu Data Mining + AI offline |
| Recruiter đăng tin | Ngoài phạm vi nghiên cứu chính |
| Resume Parsing file CV | Độ phức tạp cao, có thể làm phase sau |
| Chat giữa ứng viên và nhà tuyển dụng | Không liên quan trực tiếp đến Data Mining/AI |
| Payment/Premium | Không cần cho demo học thuật |
| Mobile App | Chỉ tập trung web demo |

---

## 6. Team Structure

Dự án nhóm 3 người nên chia trách nhiệm theo pipeline để tránh chồng chéo.

### Member 1 — Data Mining Engineer

Phụ trách:

- Scrapy/Playwright crawler
- Raw data storage
- Parser theo từng nguồn
- Deduplication
- Data quality report
- Scheduler/demo pipeline

### Member 2 — AI/ML Engineer

Phụ trách:

- Feature engineering
- Dataset builder
- Model training
- Evaluation
- Experiment tracking
- Model registry
- Model serving bằng FastAPI

### Member 3 — Backend/Frontend Integration Engineer

Phụ trách:

- Spring Boot API
- PostgreSQL schema/Flyway
- Admin dashboard API
- Next.js dashboard
- User profile input
- Recommendation demo UI
- Docker Compose/CI

### Collaboration Rule

```text
Member 1 output → clean/knowledge tables
Member 2 input  → clean/knowledge tables
Member 2 output → active model + prediction API
Member 3 input  → pipeline status + model prediction API
```

---

## 7. Functional Requirements

### 7.1 Phase 1 — Data Mining Requirements

| ID | Requirement | Priority |
|---|---|---|
| DM-01 | Hệ thống crawl được job từ ít nhất 2 nguồn tuyển dụng | Must Have |
| DM-02 | Mỗi lần crawl phải tạo một `crawl_run` để tracking | Must Have |
| DM-03 | Raw data phải được lưu trước khi ETL | Must Have |
| DM-04 | ETL phải parse được title, company, salary, location, experience, JD text | Must Have |
| DM-05 | Hệ thống phải chuẩn hóa skill bằng `skill` và `skill_alias` | Must Have |
| DM-06 | Hệ thống phải dedup job theo source URL/hash và heuristics | Must Have |
| DM-07 | Hệ thống phải tính data quality metrics sau mỗi lần ETL | Must Have |
| DM-08 | Hệ thống phải build knowledge tables: skill stat, salary stat, demand stat | Must Have |
| DM-09 | Admin có thể xem trạng thái pipeline và data quality dashboard | Should Have |
| DM-10 | Pipeline có thể chạy manual bằng command để demo | Must Have |
| DM-11 | Pipeline có thể chạy theo lịch bằng scheduler | Should Have |

### 7.2 Phase 2 — AI Requirements

| ID | Requirement | Priority |
|---|---|---|
| AI-01 | Hệ thống tạo được versioned ML dataset từ knowledge data | Must Have |
| AI-02 | Dataset phải có train/validation/test split | Must Have |
| AI-03 | Hệ thống phải sinh feature cho từng cặp user-job | Must Have |
| AI-04 | Hệ thống phải train rule-based baseline | Must Have |
| AI-05 | Hệ thống phải train ít nhất 3 ML models | Must Have |
| AI-06 | Hệ thống phải đánh giá bằng Precision@K, Recall@K, NDCG@K | Must Have |
| AI-07 | Kết quả experiment phải được lưu lại | Must Have |
| AI-08 | Model tốt nhất phải được lưu trong model registry | Must Have |
| AI-09 | FastAPI phải load active model và expose prediction endpoint | Should Have |
| AI-10 | Frontend hiển thị Top-N job recommendation và giải thích điểm match | Should Have |

---

## 8. Non-Functional Requirements

### 8.1 Data Quality

| ID | Requirement | Target |
|---|---|---|
| NFR-DQ-01 | Parse success rate | >= 85% trên nguồn chính |
| NFR-DQ-02 | Duplicate detection rate | Có log duplicate rõ ràng |
| NFR-DQ-03 | Missing required fields | title/company/source_url < 5% |
| NFR-DQ-04 | Missing skill rate | < 35% sau skill extraction |
| NFR-DQ-05 | Missing salary rate | Được đo, không bắt buộc thấp vì thị trường có nhiều job ẩn lương |

### 8.2 Pipeline Reliability

| ID | Requirement | Target |
|---|---|---|
| NFR-P-01 | Pipeline fail không làm mất raw data | Must Have |
| NFR-P-02 | Mỗi raw record có thể reprocess | Must Have |
| NFR-P-03 | Crawl run có status rõ ràng | RUNNING/SUCCESS/FAILED |
| NFR-P-04 | ETL record có status rõ ràng | PENDING/PROCESSED/FAILED/SKIPPED |

### 8.3 ML Reproducibility

| ID | Requirement | Target |
|---|---|---|
| NFR-ML-01 | Dataset phải version hóa | Must Have |
| NFR-ML-02 | Experiment phải lưu hyperparameters | Must Have |
| NFR-ML-03 | Evaluation metrics phải lưu theo split | Must Have |
| NFR-ML-04 | Active model phải xác định được | Must Have |

### 8.4 Performance for Demo

| ID | Requirement | Target |
|---|---|---|
| NFR-PERF-01 | Manual pipeline demo | Chạy được end-to-end trên sample data |
| NFR-PERF-02 | Prediction API latency | P95 < 2s với Top-N demo |
| NFR-PERF-03 | Dashboard API latency | P95 < 1s cho dữ liệu đã aggregate |

---

## 9. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                  Next.js Dashboard/Demo                     │
│  - Data Quality Dashboard                                   │
│  - Market Intelligence Dashboard                            │
│  - User Profile Input                                       │
│  - Job Recommendation Demo                                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST
┌──────────────────────────────▼──────────────────────────────┐
│                    Spring Boot Backend                       │
│  - Auth/Profile optional                                     │
│  - Job/Dictionary API                                        │
│  - Admin Pipeline API                                        │
│  - Recommendation Orchestration                              │
└───────────────┬──────────────────────────────┬──────────────┘
                │                              │
                │ JDBC                         │ HTTP internal
┌───────────────▼──────────────┐   ┌───────────▼──────────────┐
│          PostgreSQL           │   │       FastAPI AI Service  │
│  Raw Data                     │   │  - Dataset builder        │
│  Clean Data                   │   │  - Feature pipeline       │
│  Knowledge Data               │   │  - Model training         │
│  ML Dataset Metadata          │   │  - Evaluation             │
│  Experiment Results           │   │  - Prediction serving     │
└───────────────▲──────────────┘   └───────────▲──────────────┘
                │                              │
┌───────────────┴──────────────────────────────┴──────────────┐
│                    Data Pipeline Layer                        │
│       Scrapy/Playwright → Raw → ETL → Knowledge Data          │
└───────────────────────────────────────────────────────────────┘
```

### Không sử dụng Vector DB

Hệ thống không dùng:

```text
pgvector
Qdrant
Milvus
Weaviate
Realtime ANN vector search
```

Embedding nếu được dùng sẽ là **offline feature**, ví dụ:

```text
JD text + user profile text → TF-IDF/SBERT cosine similarity → feature column
```

Không dùng embedding để làm vector retrieval realtime.

---

## 10. Phase 1 — Data Mining & Knowledge Pipeline

### 10.1 Phase 1 Objective

Mục tiêu của Phase 1 là tạo nguồn dữ liệu đáng tin cậy cho Phase 2.

Output không chỉ là dữ liệu job sạch, mà là bộ dữ liệu tri thức:

```text
Clean Job Data
+ Normalized Skill/Location/Industry/Job Family
+ Market Knowledge Statistics
+ Data Quality Metrics
+ Dataset-ready Source Tables
```

### 10.2 Pipeline Stages

#### Stage 1 — Crawl

Input:

- Job listing pages
- Job detail pages

Output:

- `crawl_run`
- `raw_job_posting`

Yêu cầu:

- Mỗi lần crawl có `crawl_run_id`.
- Mỗi raw job phải có `source_site`, `source_url`, `source_job_id`, `raw_json` hoặc `raw_html`.
- Không parse trực tiếp vào table clean nếu chưa lưu raw.

#### Stage 2 — Parse & Clean

Input:

- `raw_job_posting`

Output:

- parsed fields tạm thời hoặc ghi trực tiếp vào `job`, `company`

Các field cần parse:

```text
title
company
salary
location
experience
seniority
employment_type
remote_policy
posting_date
deadline
job description text
```

#### Stage 3 — Normalize

Chuẩn hóa:

```text
salary text       → salary_min, salary_max, currency, salary_period
experience text   → exp_required, job_level
location text     → location_id
company text      → company_id
job title/JD      → job_family_id
skill text        → skill_id thông qua skill_alias
```

#### Stage 4 — Deduplicate

Dedup theo nhiều mức:

1. Exact duplicate:
   - same `source_url`
   - same `source_site + source_job_id`
   - same `content_hash`

2. Near duplicate:
   - same normalized title
   - same company
   - same location
   - highly similar JD text

Output:

- Job mới được insert.
- Job trùng được skip/log.
- `n_duplicate` trong `crawl_run` được cập nhật.

#### Stage 5 — Skill Extraction

Ưu tiên phương pháp explainable:

```text
skill_alias dictionary
+ regex/token matching
+ normalized lowercase matching
+ optional NLP fallback
```

Output:

- `job_skill`

Mỗi skill nên có metadata:

```text
is_required
weight
source_text
confidence
extract_method
```

#### Stage 6 — Knowledge Aggregation

Sinh các bảng knowledge:

```text
job_family_skill_stat
skill_cooccurrence
salary_stat
market_demand_stat
```

Đây là output quan trọng nhất của Phase 1 cho Phase 2.

#### Stage 7 — Data Quality Check

Tính:

```text
total_raw
parsed_success
failed_parsing
duplicate_count
missing_salary_pct
missing_skill_pct
missing_location_pct
missing_exp_pct
```

Output:

- `data_quality_metric`

---

## 11. Phase 2 — AI Training, Evaluation & Model Serving

### 11.1 Phase 2 Objective

Phase 2 sử dụng dữ liệu từ Phase 1 để:

1. Build dataset train có version.
2. Sinh feature cho user-job matching.
3. Train nhiều model.
4. Đánh giá bằng metric phù hợp cho matching/ranking.
5. Chọn model tốt nhất.
6. Tích hợp model vào AI service để demo recommendation.

### 11.2 Phase 2 Pipeline

```text
Knowledge Data
  ↓
Dataset Version Creation
  ↓
User-Job Pair Generation
  ↓
Feature Engineering
  ↓
Label Generation
  ↓
Train/Validation/Test Split
  ↓
Model Training
  ↓
Evaluation
  ↓
Model Registry
  ↓
Prediction API
```

### 11.3 Label Strategy

Trong MVP, hệ thống có thể chưa có user behavior thật. Vì vậy label có thể là **weak label / synthetic label**.

Ví dụ label positive:

```text
label = 1 nếu:
- required_skill_coverage >= 0.7
- exp_gap <= 1
- location_match = true hoặc remote_allowed = true
```

Ví dụ label negative:

```text
label = 0 nếu:
- required_skill_coverage <= 0.3
- exp_gap > 3
```

Ghi chú trong report:

> Label trong MVP là weak label được sinh bằng rule. Kết quả model phản ánh khả năng học theo proxy label, chưa phải ground truth từ hành vi người dùng thật.

### 11.4 Model Serving

Sau khi train, model tốt nhất được lưu vào `model_registry`.

FastAPI AI Service load active model:

```text
/model-registry active model
        ↓
load artifact
        ↓
predict user-job scores
        ↓
return Top-N recommendations
```

---

## 12. Database Design

### 12.1 Design Layers

Database được tổ chức theo 5 layer:

```text
Layer 1: Raw Data
Layer 2: Clean Data
Layer 3: Knowledge Data
Layer 4: ML Dataset
Layer 5: ML Experiment & Model Registry
```

---

### 12.2 Layer 1 — Raw Data

#### `crawl_run`

Theo dõi mỗi lần crawler chạy.

```sql
crawl_run
- id
- source_site
- started_at
- finished_at
- status
- n_fetched
- n_new
- n_duplicate
- n_failed
- error_message
- duration_seconds
- crawler_version
- config_json
```

#### `raw_job_posting`

Lưu dữ liệu gốc.

```sql
raw_job_posting
- id
- crawl_run_id
- source_site
- source_job_id
- source_url
- raw_json
- raw_html
- content_hash
- crawled_at
- etl_status
- parse_error
- processed_at
```

`etl_status` gồm:

```text
PENDING
PROCESSED
FAILED
SKIPPED_DUPLICATE
SKIPPED_INVALID
```

---

### 12.3 Layer 2 — Clean Data

#### `job`

```sql
job
- id
- company_id
- job_family_id
- location_id
- industry_id
- title
- normalized_title
- salary_min
- salary_max
- currency
- salary_period
- is_salary_visible
- exp_required
- seniority
- job_level
- employment_type
- remote_policy
- posting_date
- deadline
- status
- num_applicants
- source_site
- source_job_id
- source_url
- jd_text
- raw_salary_text
- raw_exp_text
- raw_location_text
- quality_score
- created_at
- updated_at
```

#### `job_skill`

```sql
job_skill
- job_id
- skill_id
- is_required
- weight
- source_text
- confidence
- extract_method
```

#### Dictionary tables

```text
skill
skill_alias
job_family
industry
location
education_level
company
```

---

### 12.4 Layer 3 — Knowledge Data

#### `job_family_skill_stat`

```sql
job_family_skill_stat
- id
- job_family_id
- skill_id
- total_jobs
- required_count
- optional_count
- frequency
- avg_weight
- first_seen_at
- last_seen_at
- computed_at
```

#### `skill_cooccurrence`

```sql
skill_cooccurrence
- id
- skill_id_a
- skill_id_b
- job_family_id
- co_count
- confidence
- lift
- computed_at
```

#### `salary_stat`

```sql
salary_stat
- id
- job_family_id
- location_id
- seniority
- salary_min_p25
- salary_min_p50
- salary_min_p75
- salary_max_p25
- salary_max_p50
- salary_max_p75
- sample_size
- computed_at
```

#### `market_demand_stat`

```sql
market_demand_stat
- id
- job_family_id
- location_id
- period_start
- period_end
- job_count
- company_count
- avg_salary_min
- avg_salary_max
- top_skills_json
- computed_at
```

---

### 12.5 Layer 4 — ML Dataset

#### `ml_dataset_version`

```sql
ml_dataset_version
- id
- name
- description
- source_from
- source_to
- total_samples
- positive_samples
- negative_samples
- feature_config_json
- label_strategy
- created_at
```

#### `user_job_training_sample`

```sql
user_job_training_sample
- id
- dataset_version_id
- user_profile_id
- job_id
- label
- label_source
- skill_overlap_count
- skill_jaccard
- required_skill_coverage
- optional_skill_coverage
- missing_required_skill_count
- exp_gap
- salary_gap
- salary_overlap
- location_match
- remote_match
- education_match
- seniority_match
- market_demand_score
- skill_market_frequency_score
- title_similarity
- jd_profile_similarity
- split
- created_at
```

---

### 12.6 Layer 5 — ML Experiment & Model Registry

#### `ml_experiment`

```sql
ml_experiment
- id
- dataset_version_id
- experiment_name
- model_type
- feature_set_name
- hyperparams_json
- train_started_at
- train_finished_at
- status
- artifact_path
- notes
```

#### `ml_evaluation_metric`

```sql
ml_evaluation_metric
- id
- experiment_id
- metric_name
- metric_value
- k_value
- split
- computed_at
```

#### `model_registry`

```sql
model_registry
- id
- experiment_id
- model_name
- model_version
- model_type
- artifact_path
- is_active
- promoted_at
- notes
```

---

### 12.7 Tables Removed From Original Design

Các bảng sau không còn thuộc MVP chính:

```text
job_embedding
weight_profile
telegram_link
notification
```

Các bảng sau có thể đưa vào phase sau nếu có user interaction thật:

```text
match_history
competition_prediction
user_interaction
```

---

## 13. ML Dataset & Feature Design

### 13.1 Feature Groups

#### Skill Features

```text
skill_overlap_count
skill_jaccard
required_skill_coverage
optional_skill_coverage
missing_required_skill_count
missing_important_skill_count
```

#### Experience Features

```text
user_years_exp
job_exp_required
exp_gap
is_underqualified
is_overqualified
```

#### Salary Features

```text
expected_salary
job_salary_min
job_salary_max
salary_gap
salary_overlap
salary_percentile_in_market
```

#### Location Features

```text
location_match
same_region
remote_allowed
remote_match
```

#### Education/Certification Features

```text
education_match
cert_overlap_count
has_relevant_certification
```

#### Market Knowledge Features

```text
job_family_demand
skill_market_frequency_score
salary_market_percentile
company_rating
```

#### Text Similarity Features Optional

Không dùng Vector DB, nhưng có thể tính offline:

```text
tfidf_title_similarity
tfidf_jd_profile_similarity
sbert_cosine_similarity optional
```

---

## 14. Modeling Strategy

### 14.1 Baseline 1 — Rule-Based Scoring

Dùng để làm baseline bắt buộc.

```text
match_score =
    0.50 * required_skill_coverage
  + 0.20 * optional_skill_coverage
  + 0.10 * experience_score
  + 0.10 * location_score
  + 0.10 * salary_score
```

Lý do:

- Dễ giải thích.
- Là mốc so sánh với ML models.
- Nếu ML không vượt baseline thì feature/label có vấn đề.

### 14.2 Baseline 2 — Logistic Regression

Dùng làm ML baseline.

Ưu điểm:

- Nhanh.
- Explainable.
- Phù hợp báo cáo học thuật.

### 14.3 Tree Models

Train:

```text
Random Forest
Gradient Boosting
XGBoost
LightGBM optional
```

XGBoost/LightGBM là candidate chính vì dữ liệu matching chủ yếu là tabular feature.

### 14.4 Optional NLP Model

Nếu còn thời gian:

- TF-IDF + Logistic Regression
- SBERT offline similarity feature
- MLP trên tabular features

Không bắt buộc dùng deep learning nếu chưa có label thật đủ tốt.

---

## 15. Evaluation Strategy

### 15.1 Classification Metrics

Dùng khi xem bài toán là binary matching.

```text
accuracy
precision
recall
f1
roc_auc
pr_auc
```

### 15.2 Ranking Metrics

Dùng khi hệ thống trả Top-N jobs.

```text
Precision@K
Recall@K
NDCG@K
MAP@K
MRR
```

Metric ưu tiên:

```text
NDCG@10
Precision@10
Recall@10
```

### 15.3 Dataset Split

Ưu tiên:

```text
Train      : 70%
Validation : 15%
Test       : 15%
```

Nếu dữ liệu đủ lớn, dùng time-based split:

```text
Train      : job cũ hơn
Validation : job gần đây
Test       : job mới nhất
```

### 15.4 Experiment Comparison

Mỗi experiment phải lưu:

```text
model_type
feature_set
hyperparameters
dataset_version
metrics
artifact_path
```

Báo cáo cuối phải có bảng so sánh:

```text
Rule-based vs Logistic Regression vs Random Forest vs XGBoost/LightGBM
```

---

## 16. API Contract

### 16.1 Public Backend API

#### Data/Job API

```http
GET /api/v1/jobs
GET /api/v1/jobs/{id}
GET /api/v1/dictionary/skills?q=
GET /api/v1/dictionary/job-families
```

#### User Profile API

```http
GET /api/v1/me/profile
PUT /api/v1/me/profile
GET /api/v1/me/skills
POST /api/v1/me/skills
DELETE /api/v1/me/skills/{skillId}
```

#### Recommendation Demo API

```http
GET /api/v1/me/recommendations?topN=10
GET /api/v1/me/skill-gap?jobFamilyId=
```

#### Admin/Data Pipeline API

```http
GET /api/v1/admin/crawl-runs
GET /api/v1/admin/crawl-runs/{id}
GET /api/v1/admin/data-quality
GET /api/v1/admin/market-demand
GET /api/v1/admin/skill-stats?jobFamilyId=
GET /api/v1/admin/salary-stats
POST /api/v1/admin/pipeline/run
```

#### ML Experiment API

```http
GET /api/v1/admin/ml/datasets
GET /api/v1/admin/ml/experiments
GET /api/v1/admin/ml/experiments/{id}/metrics
GET /api/v1/admin/ml/models/active
```

---

### 16.2 Internal AI Service API

#### Predict Top-N Jobs

```http
POST /internal/v1/predict/recommendations
```

Request:

```json
{
  "userProfileId": 1,
  "candidateJobIds": [101, 102, 103],
  "topN": 10
}
```

Response:

```json
{
  "modelVersion": "xgboost_v3",
  "items": [
    {
      "jobId": 101,
      "matchScore": 0.87,
      "reasons": {
        "requiredSkillCoverage": 0.82,
        "skillJaccard": 0.64,
        "expGap": 0,
        "locationMatch": true,
        "missingSkills": ["Docker", "AWS"]
      }
    }
  ]
}
```

#### Train Model

```http
POST /internal/v1/ml/train
```

#### Evaluate Experiment

```http
POST /internal/v1/ml/evaluate
```

#### Build Dataset

```http
POST /internal/v1/ml/datasets/build
```

---

## 17. Folder Structure

```text
job-market-intelligence-ai/
├── backend/                    # Spring Boot API
├── frontend/                   # Next.js dashboard/demo
├── ai-service/                 # FastAPI prediction/training service
├── data-pipeline/              # Crawlers, ETL, knowledge aggregation
├── ml-pipeline/                # Dataset builder, training, evaluation scripts
├── docs/
│   ├── diagrams/
│   ├── erd/
│   ├── reports/
│   └── experiments/
├── docker-compose.yml
├── .github/
│   └── workflows/
└── README.md
```

### `data-pipeline/`

```text
data-pipeline/
├── crawlers/
│   ├── base_spider.py
│   ├── itviec_spider.py
│   ├── topcv_spider.py
│   └── vietnamworks_spider.py
├── parsers/
│   ├── base_parser.py
│   ├── salary_parser.py
│   ├── experience_parser.py
│   └── location_parser.py
├── etl/
│   ├── transformer.py
│   ├── deduplicator.py
│   ├── skill_extractor.py
│   └── loader.py
├── knowledge/
│   ├── skill_statistics.py
│   ├── skill_cooccurrence.py
│   ├── salary_statistics.py
│   └── market_demand.py
├── quality/
│   └── quality_checker.py
├── scheduler/
│   └── jobs.py
└── tests/
```

### `ml-pipeline/`

```text
ml-pipeline/
├── datasets/
│   ├── dataset_builder.py
│   ├── label_generator.py
│   └── splitter.py
├── features/
│   ├── skill_features.py
│   ├── salary_features.py
│   ├── location_features.py
│   ├── market_features.py
│   └── text_features.py
├── models/
│   ├── rule_based.py
│   ├── logistic_regression.py
│   ├── random_forest.py
│   ├── xgboost_model.py
│   └── lightgbm_model.py
├── evaluation/
│   ├── classification_metrics.py
│   ├── ranking_metrics.py
│   └── report_generator.py
├── registry/
│   └── model_registry.py
└── tests/
```

---

## 18. Development Roadmap

### Phase 0 — Design Finalization

| Task | Deliverable |
|---|---|
| Finalize schema | ERD mới theo 5-layer design |
| Finalize pipeline design | flow crawl → raw → clean → knowledge |
| Finalize ML design | dataset, feature, label, metric |
| Assign team ownership | 3 member responsibilities |

---

### Phase 1 — Data Mining MVP

| Sprint | Deliverable |
|---|---|
| Sprint 1 | PostgreSQL schema + Flyway + Docker Compose |
| Sprint 2 | Crawl nguồn đầu tiên, lưu raw data |
| Sprint 3 | Parser/ETL cho nguồn đầu tiên |
| Sprint 4 | Skill extraction + deduplication |
| Sprint 5 | Crawl nguồn thứ hai |
| Sprint 6 | Knowledge aggregation + data quality dashboard |

Definition of Done Phase 1:

```text
- Crawl được ít nhất 2 nguồn
- Raw data được lưu đầy đủ
- Job clean được insert vào DB
- Skill extraction hoạt động
- Data quality report hiển thị được
- Knowledge tables được build
- Có thể chạy pipeline end-to-end bằng command hoặc scheduler
```

---

### Phase 2 — AI Training & Evaluation

| Sprint | Deliverable |
|---|---|
| Sprint 7 | Dataset builder + weak label strategy |
| Sprint 8 | Feature engineering pipeline |
| Sprint 9 | Rule-based + Logistic Regression baseline |
| Sprint 10 | Random Forest + XGBoost/LightGBM |
| Sprint 11 | Evaluation report + experiment tracking |
| Sprint 12 | Model registry + FastAPI prediction endpoint |

Definition of Done Phase 2:

```text
- Dataset có version
- Có train/validation/test split
- Train được ít nhất 4 models gồm rule-based baseline
- Có metrics classification và ranking
- Có experiment comparison report
- Có active model trong registry
- Prediction API trả được matchScore
```

---

### Phase 3 — Integrated Demo System

| Sprint | Deliverable |
|---|---|
| Sprint 13 | Backend gọi AI Service prediction |
| Sprint 14 | Frontend recommendation page |
| Sprint 15 | Skill gap explanation |
| Sprint 16 | Final dashboard + demo script + documentation |

Definition of Done Phase 3:

```text
- User tạo profile/kỹ năng
- System hiển thị Top-N jobs phù hợp
- Mỗi job có matchScore và explanation
- Admin xem được data pipeline status
- Admin xem được model metrics
- Demo end-to-end: crawl → ETL → train → predict → UI
```

---

## 19. Definition of Done

### 19.1 Project-level DoD

Dự án được xem là hoàn thành khi demo được flow:

```text
1. Chạy crawler lấy job mới
2. ETL tạo clean job + job_skill
3. Knowledge tables được cập nhật
4. Build dataset version mới
5. Train nhiều model
6. So sánh metrics
7. Promote model tốt nhất
8. User nhận Top-N recommendation trên UI
```

### 19.2 Final Deliverables

```text
- Source code đầy đủ
- README hoàn chỉnh
- ERD mới
- Data pipeline documentation
- ML experiment report
- Evaluation report
- Docker Compose runbook
- Demo script
```

---

## 20. Risks & Mitigation

| Risk | Ảnh hưởng | Mitigation |
|---|---|---|
| Website đổi HTML structure | Parser fail | Lưu raw data, tách parser theo source, có parse_error |
| Crawl bị block | Thiếu dữ liệu | Rate limit, user-agent, crawl sample, ưu tiên nguồn ổn định |
| Salary missing nhiều | Feature salary yếu | Đo missing rate, không ép salary là feature bắt buộc |
| Skill extraction sai | Model học sai | Dùng alias dictionary, confidence score, manual review top skills |
| Không có label thật | Evaluation chưa phản ánh thực tế | Ghi rõ weak label, dùng rule baseline, chuẩn bị future `user_interaction` |
| Dataset imbalance | Model bias | Negative sampling, stratified split, report class distribution |
| ML không vượt baseline | Feature/label chưa tốt | Phân tích feature importance, revise label strategy |
| Team 3 người thiếu thời gian | Trễ roadmap | Ưu tiên Phase 1 và ML baseline trước, product feature để sau |

---

## Final Note

Dự án này không đặt trọng tâm vào việc xây dựng một hệ thống recommendation realtime phức tạp bằng Vector DB. Trọng tâm đúng là:

```text
Data Mining tốt
→ Knowledge Data tốt
→ Feature Engineering tốt
→ Model Evaluation nghiêm túc
→ Tích hợp thành demo system rõ ràng
```

Nếu Phase 1 tạo dữ liệu chất lượng kém, Phase 2 sẽ không thể có model tốt. Vì vậy nguyên tắc chính của dự án là:

> Data quality first, model complexity second.
