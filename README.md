## 1. Bài toán là gì?

Người tìm việc tại Việt Nam gặp ba khó khăn lớn: 

(1) thông tin tuyển dụng phân tán trên nhiều site, không chuẩn hóa; 

(2) khó tự đánh giá mình thiếu kỹ năng gì so với thị trường; 

(3) không biết một vị trí cạnh tranh đến mức nào để ưu tiên ứng tuyển. 

a/ Actor chính:

- Job Seeker
- Adminstrator

b/ External System

- ItViec
- TopCV
- VietnamWorks
- LinkedIn
- Telegram API

c/ Time Actor

- Time Trigger

![System Context](docs\images\architecture.png)

## 2. Kiến trúc tổng thể

Hệ thống được thiết kế theo mô hình **Modular Monolith (Java) + AI/Data Service (Python)**.

- **Spring Boot Backend** là trung tâm của hệ thống, chịu trách nhiệm xử lý nghiệp vụ (Business Logic), xác thực người dùng, cung cấp REST API và điều phối các dịch vụ khác.
- **FastAPI AI Service** chịu trách nhiệm thực hiện các tác vụ Trí tuệ nhân tạo như sinh embedding, tính toán độ tương đồng (SBERT), Recommendation, Skill Gap Analysis và Competition Prediction.
- **Data Pipeline** hoạt động độc lập theo lịch (Batch Processing), thực hiện Crawl dữ liệu tuyển dụng, ETL, làm sạch dữ liệu và cập nhật Data Warehouse.
- **PostgreSQL** lưu trữ toàn bộ dữ liệu của hệ thống, bao gồm dữ liệu tuyển dụng, hồ sơ người dùng và dữ liệu phục vụ Machine Learning.

Kiến trúc này chỉ tách các thành phần **khác ngôn ngữ lập trình (Java/Python)** và **khác vòng đời xử lý (Real-time/Batch)**, giúp giảm độ phức tạp nhưng vẫn dễ mở rộng trong tương lai.

### Sơ đồ kiến trúc

```text
                    Người dùng
                        │
                        ▼
              Spring Boot Backend
      (Business Logic, REST API, JWT)
            │                     │
            │                     │
            ▼                     ▼
     FastAPI AI Service      PostgreSQL
(SBERT, XGBoost, Recommendation) (Data Warehouse)
            ▲
            │
            │
      Data Pipeline
 (Crawler + ETL theo lịch)
```

### Vai trò của từng thành phần

| Thành phần | Chức năng |
|------------|-----------|
| **Spring Boot Backend** | Xử lý nghiệp vụ, xác thực người dùng, REST API, điều phối hệ thống |
| **FastAPI AI Service** | Tính toán AI (SBERT, Similarity, Recommendation, Competition Prediction) |
| **Data Pipeline** | Crawl dữ liệu, ETL, làm sạch dữ liệu, Feature Engineering |
| **PostgreSQL** | Lưu trữ dữ liệu tuyển dụng, hồ sơ người dùng và Data Warehouse |


## 3. Lựa chọn công nghệ

| Công nghệ           | Yêu cầu phục vụ                        | Phương án thay thế | Lý do chọn                                                              |
| ------------------- | -------------------------------------- | ------------------ | ----------------------------------------------------------------------- |
| Java Spring Boot    | Backend enterprise, REST API, Security | NodeJS, ASP.NET    | Hệ sinh thái enterprise mạnh                                            |
| FastAPI             | AI Inference Service                   | Flask, Django      | Async, Pydantic validation, OpenAPI tự động                             |
| PostgreSQL          | OLTP + Data Warehouse                  | MySQL, MongoDB     | ACID, hỗ trợ SQL mạnh, pgvector, dễ JOIN                                |
| pgvector            | Semantic Search                        | FAISS, Milvus      | Không cần thêm hệ thống mới, tích hợp trực tiếp PostgreSQL              |
| Redis               | Cache, Ranking, Session                | Memcached          | Có TTL, Pub/Sub, nhiều cấu trúc dữ liệu                                 |
| Scrapy + Playwright | Crawl dữ liệu tuyển dụng               | BeautifulSoup      | Scrapy crawl nhanh, Playwright xử lý website JavaScript                 |
| Next.js             | Dashboard Web                          | React SPA          | Routing, SSR, cấu trúc project tốt, dễ mở rộng                          |
| Docker Compose      | Deploy đồ án                           | Cài thủ công       | Tái tạo môi trường nhanh, dễ demo, dễ CI/CD                             |

## 4. Thiết kế Database

Danh sách các entity

1. Authentication Domain

Chịu trách nhiệm xác thực, phân quyền và quản lý tài khoản.

| Entity | Mô tả |
|---------|------|
| `user_credential` | Thông tin đăng nhập (email, password hash, trạng thái) |
| `role` | Danh sách vai trò (Admin, Job Seeker, ...) |
| `user_role` | Quan hệ giữa người dùng và vai trò (N-N) |

2. User Domain

Quản lý hồ sơ và thông tin nghề nghiệp của người dùng.

| Entity | Mô tả |
|---------|------|
| `user_profile` | Hồ sơ cá nhân |
| `user_skill` | Kỹ năng của người dùng |
| `user_certification` | Chứng chỉ |
| `telegram_link` | Liên kết tài khoản Telegram để nhận thông báo |

3. Job Domain

Quản lý dữ liệu tuyển dụng.

| Entity | Mô tả |
|---------|------|
| `company` | Thông tin công ty |
| `job` | Tin tuyển dụng |
| `job_skill` | Kỹ năng yêu cầu của công việc |
| `job_embedding` | Vector embedding của Job Description phục vụ AI |

4. Dictionary Domain

Các bảng danh mục dùng chung trong toàn hệ thống.

| Entity | Mô tả |
|---------|------|
| `skill` | Danh mục kỹ năng chuẩn hóa |
| `skill_alias` | Đồng nghĩa của kỹ năng (ReactJS → React) |
| `location` | Địa điểm |
| `education_level` | Trình độ học vấn |
| `industry` | Ngành nghề |
| `job_family` | Nhóm nghề nghiệp |
| `weight_profile` | Cấu hình trọng số MatchScore |

5. Matching Domain

Quản lý kết quả AI và quá trình matching.

| Entity | Mô tả |
|---------|------|
| `match_history` | Lưu kết quả matching |
| `competition_prediction` | Điểm cạnh tranh của ứng viên đối với từng công việc |

6. Notification Domain

Quản lý thông báo.

| Entity | Mô tả |
|---------|------|
| `notification` | Lịch sử gửi thông báo |
| `notification_job` *(Optional)* | Liên kết giữa thông báo và các công việc được gửi |

7. Data Pipeline Domain

Quản lý quá trình thu thập và xử lý dữ liệu.

| Entity | Mô tả |
|---------|------|
| `crawl_run` | Nhật ký mỗi lần crawler chạy |
| `raw_job_posting` | Dữ liệu thô thu thập từ các website tuyển dụng |
| `data_quality_metric` | Thống kê chất lượng dữ liệu sau ETL |


LƯU Ý: XEM KỸ SƠ ĐỒ TẠI https://dbdiagram.io/d/Job-Matching-and-Skill-Gap-Platform-6a3f3fe8b3ebc94a7da2539f

## 5. API Endpoint

| Code | Ý nghĩa|
|---------|------|
| `200 / 201` | OK / Đã tạo |
| `202` | Đã nhận, xử lý bất đồng bộ (nếu matching chạy nền) |
| `400` | Request sai cú pháp |
| `401 / 403` | Chưa xác thực / Không đủ quyền |
| `404` | Không tìm thấy tài nguyên |
| `409` | Xung đột (vd email đã tồn tại) |
| `422` | Cú pháp đúng nhưng nghiệp vụ không hợp lệ |
| `429` | Quá rate limit |
| `500` | Lỗi server |

1. Quy ước chung

Base path: `/api/v1/...` (public), `/internal/v1/...` => Khi muốn thêm version mới đổi thành `v2`

Auth path: JWT Bearer cho mọi endpoint trừ `/auth/*` , Nếu đối với cá nhân dùng `me`

Pagination: mọi endpoint trả danh sách dùng ?page=&size= (mặc định size=20, max=100). Response kèm page, size, totalElements, totalPages.

2. Error Response chuẩn (RFC 7807)

```
{
  "type": "https://api.example.com/problems/conflict",
  "title": "Email already exists",
  "status": 409,
  "detail": "Email 'a@b.com' đã được đăng ký.",
  "instance": "/api/v1/auth/register",
  "timestamp": "2026-06-28T10:20:30Z",
  "traceId": "5f1c7c1a5b",
  "errors": [
    { "field": "email", "message": "must be unique" }
  ]
}
```

errors[] chỉ xuất hiện với lỗi validation/422.

Ví dụ "email đã tồn tại" dùng 409

3. Public API — Endpoint Contract

| Method   | Endpoint                                    | Chức năng                                          | Auth / Role            | Request DTO            | Response DTO                 | Success                                                    | Error                      |
| -------- | ------------------------------------------- | -------------------------------------------------- | ---------------------- | ---------------------- | ---------------------------- | ---------------------------------------------------------- | -------------------------- |
| **POST** | `/api/v1/auth/register`                     | Đăng ký tài khoản                                  | Public                 | `RegisterRequest`      | `UserResponse`               | **201 Created**                                            | `400`, `409`, `422`, `500` |
| **POST** | `/api/v1/auth/login`                        | Đăng nhập và nhận JWT                              | Public                 | `LoginRequest`         | `JwtResponse`                | **200 OK**                                                 | `400`, `401`, `500`        |
| **POST** | `/api/v1/auth/refresh`                      | Làm mới Access Token                               | Public (Refresh Token) | `RefreshRequest`       | `JwtResponse`                | **200 OK**                                                 | `401`                      |
| **GET**  | `/api/v1/me/profile`                        | Xem thông tin hồ sơ cá nhân                        | JWT                    | —                      | `ProfileResponse`            | **200 OK**                                                 | `401`, `404`               |
| **PUT**  | `/api/v1/me/profile`                        | Cập nhật hồ sơ cá nhân                             | JWT                    | `UpdateProfileRequest` | `ProfileResponse`            | **200 OK**                                                 | `400`, `401`, `422`        |
| **POST** | `/api/v1/me/telegram`                       | Liên kết tài khoản Telegram                        | JWT                    | `TelegramLinkRequest`  | `TelegramLinkResponse`       | **200 OK**                                                 | `401`, `409`               |
| **GET**  | `/api/v1/me/recommendations?page=&size=`    | Lấy danh sách Top-N việc làm phù hợp               | JWT                    | Query Parameters       | `RecommendationPageResponse` | **200 OK** *(hoặc **202 Accepted** nếu xử lý bất đồng bộ)* | `401`, `429`, `500`        |
| **GET**  | `/api/v1/me/skill-gap?jobFamily=`           | Phân tích kỹ năng còn thiếu theo nhóm nghề         | JWT                    | Query Parameters       | `SkillGapResponse`           | **200 OK**                                                 | `401`, `404`, `422`        |
| **GET**  | `/api/v1/jobs/{id}`                         | Xem chi tiết việc làm                              | JWT                    | Path Variable          | `JobDetailResponse`          | **200 OK**                                                 | `401`, `404`               |
| **GET**  | `/api/v1/jobs/{id}/competition`             | Xem mức độ cạnh tranh của vị trí tuyển dụng        | JWT                    | Path Variable          | `CompetitionResponse`        | **200 OK**                                                 | `401`, `404`               |
| **GET**  | `/api/v1/trends/salary?industry=&location=` | Xem dashboard xu hướng lương theo ngành và khu vực | JWT                    | Query Parameters       | `SalaryTrendResponse`        | **200 OK**                                                 | `401`, `404`               |
| **GET**  | `/api/v1/admin/data-quality?runId=`         | Theo dõi chất lượng dữ liệu (Data Quality)         | JWT + `ROLE_ADMIN`     | Query Parameters       | `DataQualityResponse`        | **200 OK**                                                 | `401`, `403`, `404`        |

4. Phân chia trách nhiệm tính điểm 

Python trả tín hiệu, Java ráp điểm

FastAPI: candidate generation (vector search) + tính độ tương đồng ngữ nghĩa kỹ năng cho từng job.

Java: đọc `job_skill.is_required` + `user_skill`, tính **Gate must-have**, tính `exp/edu/cert score`, áp `weight_profile(jobFamily)` → ráp `matchScore` + `components`.

5. Internal API (Spring Boot → FastAPI)

5.1. `POST /internal/v1/candidates` 

Đây là bước Recall.

Nhiệm vụ của AI là:

Trong khoảng 100.000 việc làm,

hãy chọn ra khoảng 200 việc làm có khả năng phù hợp nhất.

Chưa cần xếp hạng chính xác.

5.2. `POST /internal/v1/match-signals`

Đây là bước Ranking, dùng để đánh giá mức độ phù hợp giữa hồ sơ của người dùng và các công việc đã được chọn ở bước trước.

5.3. `POST /internal/v1/competition-score` - độ cạnh tranh của vị trí

Mục đích là tính mức cạnh tranh của một Job

5.4. `POST /internal/v1/skill-gap` - phân tích gap

Nó không chỉ liệt kê kỹ năng còn thiếu mà còn xếp hạng mức độ ưu tiên và giải thích lý do.


**Requirements → Architecture → Tech Selection → Database/ERD → API Contract → UML.**