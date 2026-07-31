# API Specification — Radiology AI Platform

> مواصفات REST API الكاملة للمنصة

---

## 1. النظرة العامة

### الـ Base URL
```
Production:  https://api.radiology-ai.example.com/api/v1
Staging:     https://staging-api.radiology-ai.example.com/api/v1
Development: http://localhost:8000/api/v1
```

### المصادقة
- **Scheme**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <access_token>`
- **Access token lifetime**: 15 minutes
- **Refresh token lifetime**: 24 hours

### الـ Content Types
- **Requests**: `application/json` (default), `multipart/form-data` (uploads)
- **Responses**: `application/json`
- **Errors**: `application/problem+json` (RFC 7807)

---

## 2. الـ Endpoints

### 2.1 المصادقة (Authentication)

#### POST /auth/login
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "email": "radiologist@hospital.com",
  "password": "secure_password_here"
}
```

**Response 200**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "radiologist@hospital.com",
    "role": "radiologist",
    "name": "Dr. Al-Saleh"
  }
}
```

#### POST /auth/refresh
```http
POST /api/v1/auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /auth/logout
```http
POST /api/v1/auth/logout HTTP/1.1
Authorization: Bearer <access_token>
```

#### POST /auth/mfa/verify
```http
POST /api/v1/auth/mfa/verify HTTP/1.1
Content-Type: application/json

{
  "mfa_token": "123456",
  "session_token": "temp_session_token_from_login"
}
```

---

### 2.2 الدراسات (Studies)

#### POST /studies
رفع دراسة DICOM جديدة (ملف واحد أو ZIP).

```http
POST /api/v1/studies HTTP/1.1
Authorization: Bearer <token>
Content-Type: multipart/form-data

------boundary
Content-Disposition: form-data; name="file"; filename="study.zip"
Content-Type: application/zip

(binary data)
------boundary--
```

**Response 202** (Accepted):
```json
{
  "study_id": "abc123-def456",
  "status": "processing",
  "estimated_time_seconds": 30,
  "poll_url": "/api/v1/studies/abc123-def456/status"
}
```

#### GET /studies
قائمة الدراسات مع pagination وfilters.

```http
GET /api/v1/studies?modality=CT&date_from=2026-01-01&page=1&per_page=20 HTTP/1.1
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | الوصف |
|-----------|------|------|
| `modality` | string | CT, MR, CR, DX, US, etc. |
| `date_from` | date | YYYY-MM-DD |
| `date_to` | date | YYYY-MM-DD |
| `patient_pseudo_id` | string |hashed patient ID |
| `status` | string | processing, ready, archived |
| `page` | int | default: 1 |
| `per_page` | int | default: 20, max: 100 |

**Response 200**:
```json
{
  "data": [
    {
      "id": "abc123-def456",
      "modality": "CT",
      "study_date": "2026-07-15",
      "body_part": "Chest",
      "study_description": "CT Chest with contrast",
      "images_count": 250,
      "status": "ready",
      "created_at": "2026-07-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 145,
    "total_pages": 8
  }
}
```

#### GET /studies/{study_id}
تفاصيل دراسة واحدة.

```http
GET /api/v1/studies/abc123-def456 HTTP/1.1
Authorization: Bearer <token>
```

**Response 200**:
```json
{
  "id": "abc123-def456",
  "modality": "CT",
  "study_date": "2026-07-15",
  "body_part": "Chest",
  "study_description": "CT Chest with contrast",
  "patient": {
    "pseudo_id": "a1b2c3d4e5f67890",
    "age": 45,
    "sex": "M"
  },
  "series": [
    {
      "id": "series-001",
      "number": 1,
      "description": "Axial 5mm",
      "images_count": 80,
      "rows": 512,
      "columns": 512,
      "pixel_spacing": [0.5, 0.5],
      "slice_thickness": 5.0
    }
  ],
  "reports": [
    {
      "id": "report-001",
      "status": "approved",
      "created_at": "2026-07-15T11:00:00Z"
    }
  ]
}
```

#### GET /studies/{study_id}/status
حالة معالجة الدراسة.

**Response 200**:
```json
{
  "study_id": "abc123-def456",
  "status": "ready",
  "progress": 100,
  "stages": [
    {"name": "upload", "status": "completed", "duration_ms": 1200},
    {"name": "validation", "status": "completed", "duration_ms": 350},
    {"name": "deidentification", "status": "completed", "duration_ms": 2100},
    {"name": "storage", "status": "completed", "duration_ms": 850}
  ]
}
```

#### DELETE /studies/{study_id}
حذف دراسة (soft delete + audit log).

```http
DELETE /api/v1/studies/abc123-def456 HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "duplicate_upload"
}
```

---

### 2.3 الصور (Images)

#### GET /studies/{study_id}/images
قائمة الصور في دراسة.

#### GET /studies/{study_id}/images/{image_id}
metadata صورة واحدة.

#### GET /studies/{study_id}/images/{image_id}/pixel
بيانات البكسل (PNG or JPEG).

```http
GET /api/v1/studies/abc123-def456/images/img-001/pixel?format=png&window=lung HTTP/1.1
Authorization: Bearer <token>
Accept: image/png
```

**Query Parameters**:
| Parameter | Options |
|-----------|---------|
| `format` | `png`, `jpeg`, `dicom` |
| `window` | `brain`, `lung`, `bone`, `soft_tissue`, `mediastinum`, `custom` |
| `window_center` | int (if window=custom) |
| `window_width` | int (if window=custom) |
| `quality` | int (1-100, default: 90 for jpeg) |

---

### 2.4 التقارير (Reports)

#### POST /studies/{study_id}/reports/generate
توليد تقرير بالـ AI.

```http
POST /api/v1/studies/abc123-def456/reports/generate HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "model": "r2gen-v1.2",
  "language": "ar",
  "include_visual_grounding": true
}
```

**Response 202**:
```json
{
  "report_id": "report-001",
  "status": "generating",
  "estimated_time_seconds": 5,
  "poll_url": "/api/v1/reports/report-001"
}
```

#### GET /reports/{report_id}
تفاصيل تقرير.

```http
GET /api/v1/reports/report-001 HTTP/1.1
Authorization: Bearer <token>
```

**Response 200**:
```json
{
  "id": "report-001",
  "study_id": "abc123-def456",
  "status": "pending_review",
  "report_type": "generated",
  "model": {
    "name": "r2gen",
    "version": "v1.2"
  },
  "content": {
    "examination": "CT Brain without contrast",
    "clinical_indication": "Headache",
    "technique": "Axial 5mm slices",
    "findings": "The brain demonstrates normal parenchymal attenuation...",
    "impression": "No acute intracranial abnormality"
  },
  "content_ar": {
    "examination": "تصوير مقطعي للدماغ بدون صبغة",
    "clinical_indication": "صداع",
    "technique": "شرائح محورية بسماكة 5 مم",
    "findings": "يُظهر الدماغ كثافة طبيعية...",
    "impression": "لا يوجد اعتلال داخل القحف حاد"
  },
  "confidence_scores": {
    "examination": 0.98,
    "clinical_indication": 0.95,
    "technique": 0.92,
    "findings": [
      {"text": "The brain demonstrates...", "score": 0.91},
      {"text": "No acute hemorrhage...", "score": 0.87},
      {"text": "The ventricular system...", "score": 0.94}
    ],
    "impression": 0.89
  },
  "visual_grounding": [
    {
      "sentence_index": 0,
      "bbox": [120, 80, 380, 290],
      "image_id": "img-001"
    }
  ],
  "generated_at": "2026-07-15T11:00:00Z",
  "review_deadline": "2026-07-15T23:59:59Z"
}
```

#### PATCH /reports/{report_id}
تعديل تقرير (من قبل طبيب).

```http
PATCH /api/v1/reports/report-001 HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": {
    "findings": "The brain demonstrates normal parenchymal attenuation. No acute hemorrhage. Small low-density area in the right frontal lobe, likely old infarct."
  },
  "edit_reason": "added incidental finding"
}
```

#### POST /reports/{report_id}/approve
اعتماد تقرير.

```http
POST /api/v1/reports/report-001/approve HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "Approved with minor edits"
}
```

#### POST /reports/{report_id}/reject
رفض تقرير.

```http
POST /api/v1/reports/report-001/reject HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "findings_inaccurate",
  "comment": "Model missed a fracture"
}
```

#### GET /reports/{report_id}/export
تصدير بصيغة مختلفة.

```http
GET /api/v1/reports/report-001/export?format=dicom_sr HTTP/1.1
Authorization: Bearer <token>
Accept: application/dicom
```

**Supported formats**:
- `json` — JSON structure
- `pdf` — PDF report
- `dicom_sr` — DICOM Structured Report
- `fhir` — FHIR DiagnosticReport
- `txt` — Plain text

---

### 2.5 المراجعة (Review Queue)

#### GET /review/queue
قائمة التقارير بانتظار المراجعة.

```http
GET /api/v1/review/queue?status=pending&modality=CT&page=1 HTTP/1.1
Authorization: Bearer <token>
```

#### POST /review/{report_id}/claim
حجز تقرير للمراجعة (منع التضارب).

```http
POST /api/v1/review/report-001/claim HTTP/1.1
Authorization: Bearer <token>
```

#### POST /review/{report_id}/release
إلغاء الحجز.

---

### 2.6 النماذج (Models)

#### GET /models
النماذج المتاحة.

```http
GET /api/v1/models HTTP/1.1
Authorization: Bearer <token>
```

**Response 200**:
```json
{
  "data": [
    {
      "name": "r2gen",
      "version": "v1.2",
      "modality": "CR",
      "body_parts": ["chest"],
      "languages": ["en", "ar"],
      "avg_inference_time_ms": 3200,
      "active": true
    },
    {
      "name": "radfm",
      "version": "v0.9",
      "modality": "CT",
      "body_parts": ["brain", "chest", "abdomen"],
      "languages": ["en"],
      "avg_inference_time_ms": 8500,
      "active": false
    }
  ]
}
```

---

### 2.7 الـ Audit Log

#### GET /audit
سجل الأحداث (للـ admins فقط).

```http
GET /api/v1/audit?user_id=550e8400&action=read&date_from=2026-07-01 HTTP/1.1
Authorization: Bearer <admin_token>
```

---

### 2.8 الإحصائيات (Statistics)

#### GET /stats/overview
```json
{
  "studies_total": 1542,
  "studies_this_month": 87,
  "reports_generated": 1203,
  "reports_approved": 987,
  "reports_rejected": 89,
  "pending_review": 127,
  "avg_review_time_minutes": 4.2,
  "model_acceptance_rate": 0.82
}
```

---

## 3. الـ Webhooks

### الأحداث المتاحة

| Event | Trigger | Payload |
|-------|---------|---------|
| `study.ingested` | دراسة جديدة جاهزة | `{study_id, modality, image_count}` |
| `report.generated` | تقرير مُولّد | `{report_id, study_id, model}` |
| `report.approved` | تقرير مُعتمد | `{report_id, study_id, reviewer_id}` |
| `report.rejected` | تقرير مرفوض | `{report_id, study_id, reason}` |
| `study.archived` | دراسة أُرشفت | `{study_id, archived_at}` |

### التسجيل
```http
POST /api/v1/webhooks HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://hospital.example.com/webhooks/radiology",
  "events": ["report.approved", "report.rejected"],
  "secret": "webhook_secret_for_signing"
}
```

### التوقيع
يُرسل header `X-Signature-256` مع HMAC-SHA256 للـ payload باستخدام الـ secret.

---

## 4. الـ Rate Limiting

| الـ endpoint | الحد |
|------------|-----|
| `POST /auth/login` | 5 requests/minute |
| `POST /studies` (upload) | 10 requests/hour |
| `POST /reports/generate` | 20 requests/hour |
| `GET /*` | 1000 requests/hour |

عند تجاوز الحد:
```json
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Retry after 60 seconds.",
  "retry_after_seconds": 60
}
```

---

## 5. الـ Error Handling

كل الأخطاء بصيغة [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807):

```json
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://radiology-ai.example.com/errors/not-found",
  "title": "Resource not found",
  "status": 404,
  "detail": "Study with ID abc123 not found",
  "instance": "/api/v1/studies/abc123",
  "trace_id": "req_550e8400"
}
```

### رموز الأخطاء الشائعة

| Status | Code | السبب |
|--------|------|------|
| 400 | `bad_request` | بيانات غير صالحة |
| 401 | `unauthorized` | token مفقود أو منتهي |
| 403 | `forbidden` | صلاحيات غير كافية |
| 404 | `not_found` | مورد غير موجود |
| 409 | `conflict` | تعارض (مثلاً: study_id مكرر) |
| 413 | `payload_too_large` | ملف > 500MB |
| 415 | `unsupported_media_type` | نوع ملف غير مدعوم |
| 422 | `unprocessable_entity` | DICOM تالف |
| 429 | `rate_limit_exceeded` | تجاوز rate limit |
| 500 | `internal_error` | خطأ في الخادم |
| 503 | `service_unavailable` | صيانة أو عطل |

---

## 6. الـ Pagination

كل الـ endpoints التي تُرجع قوائم تستخدم cursor-based pagination:

```http
GET /api/v1/studies?page=2&per_page=20 HTTP/1.1
```

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 145,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

---

## 7. الـ Versioning

- **URL versioning**: `/api/v1/`, `/api/v2/`
- **Backward compatibility**: 12 شهراً على الأقل
- **Deprecation notice**: header `Sunset` + email للأطباء
- **Changelog**: في `/api/v1/changelog`

---

## 8. الـ SDK (مستقبلاً)

### Python
```python
from radiology_ai import RadiologyAIClient

client = RadiologyAIClient(api_key="...")
study = client.studies.upload("patient.dcm")
report = client.reports.generate(study.id, language="ar")
print(report.content_ar)
```

### JavaScript
```javascript
import { RadiologyAIClient } from '@radiology-ai/sdk';

const client = new RadiologyAIClient({ apiKey: '...' });
const study = await client.studies.upload(file);
const report = await client.reports.generate(study.id, { language: 'ar' });
console.log(report.content_ar);
```

---

## 9. الـ OpenAPI Schema

الـ schema الكامل متاح في:
- **Production**: `https://api.radiology-ai.example.com/openapi.json`
- **Docs (Swagger)**: `https://api.radiology-ai.example.com/docs`
- **ReDoc**: `https://api.radiology-ai.example.com/redoc`

---

> آخر تحديث: 2026-08-01
