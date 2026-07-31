# Architecture — Radiology AI Platform

> البنية التقنية الكاملة لمنصة توليد التقارير الإشعاعية بالذكاء الاصطناعي

---

## 1. النظرة العامة

المنصة تعمل بنمط **Microservices** مع ربط غير متزامن (Async Message Bus). كل خدمة مسؤولة عن مهمة واحدة، والاتصال بينها عبر REST + Message Queue. هذا يسمح بقياس كل خدمة على حدة وفق الحمل.

### المبادئ التصميمية

1. **Privacy by Design** — إخفاء الهوية يحدث قبل أي تخزين دائم
2. **Audit Everything** — كل عملية (قراءة، كتابة، توليد، تعديل) موثّقة في audit log غير قابل للحذف
3. **HITL Mandatory** — لا تقرير يخرج بدون مراجعة بشرية
4. **Federated First** — يمكن تدريب النماذج على بيانات موزّعة دون نقلها
5. **Cloud-Agnostic** — يعمل على AWS / GCP / Azure / On-Premise بنفس الكود

---

## 2. المخطط العام (High-Level Diagram)

```
                          ┌──────────────────────┐
                          │   Web Frontend       │
                          │   (React + Cornerstone)│
                          └──────────┬───────────┘
                                     │ HTTPS
                                     ▼
                          ┌──────────────────────┐
                          │   API Gateway        │
                          │   (FastAPI + OAuth2) │
                          └──────────┬───────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
                ▼                    ▼                    ▼
      ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
      │ Ingestion Svc   │  │ Inference Svc   │  │ Review Svc      │
      │ - DICOM parser  │  │ - Model loading │  │ - HITL queue    │
      │ - Validation    │  │ - Report gen    │  │ - Diff viewer   │
      │ - De-id pipeline│  │ - Confidence    │  │ - Approval flow │
      └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │   Message Bus        │
                          │   (Redis + Celery)   │
                          └──────────┬───────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
      ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
      │ Orthanc PACS    │  │ Object Storage  │  │ Vector DB       │
      │ (DICOM store)   │  │ (MinIO/S3)      │  │ (Milvus)        │
      └─────────────────┘  └─────────────────┘  └─────────────────┘
                │                    │                    │
                └────────────────────┼────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   PostgreSQL         │
                          │   (Metadata + Audit) │
                          └──────────────────────┘
```

---

## 3. المكونات التفصيلية

### 3.1 Ingestion Service

المسؤول عن استقبال ملفات DICOM الخام، التحقق منها، وإخفاء هويتها.

**التدفقات:**
- DICOM Web Upload (STOW-RS)
- C-STORE (DICOM Network Protocol)
- Filesystem Watcher (للمجلدات المشتركة)

**خطوات المعالجة:**
1. استقبال الملف + فحص الـ DICOM header للتحقق من السلامة
2. استخراج الـ metadata (Modality, StudyInstanceUID, SeriesDescription)
3. تشغيل De-identification Pipeline (انظر `scripts/dicom_deidentify.py`)
4. تخزين الصورة في Orthanc + رفع الـ metadata إلى PostgreSQL
5. نشر رسالة في Redis: `image.ingested` للخدمات الأخرى

**الـ endpoints:**
- `POST /api/v1/ingest/dicom` — رفع ملف DICOM واحد
- `POST /api/v1/ingest/study` — رفع دراسة كاملة (ZIP)
- `GET /api/v1/ingest/{id}/status` — حالة المعالجة

### 3.2 Inference Service

المسؤول عن توليد التقارير من الصور باستخدام نماذج Vision-Language.

**النماذج المدعومة (مرحلياً):**
- **Phase 1**: R2Gen (بسيط، سريع، جيد للـ X-ray)
- **Phase 2**: RadFM (أقوى، يدعم CT/MRI)
- **Phase 3**: نموذج عربي مُخصّص (Fine-tuned)

**خطوات المعالجة:**
1. استقبال `study_id` من قائمة الانتظار
2. تحميل الصور من Orthanc (C-GET أو WADO-RS)
3. Preprocessing: Resampling, Normalization, Windowing (انظر `DATA_GUIDE.md`)
4. تشغيل النموذج + حساب Confidence Score لكل جملة
5. تخزين التقرير المُولّد + الـ confidence map في PostgreSQL
6. نشر `report.generated` للمراجعة

**الـ endpoints:**
- `POST /api/v1/inference/{study_id}/generate` — توليد تقرير
- `GET /api/v1/inference/{report_id}/confidence` — درجات الثقة
- `GET /api/v1/inference/models` — النماذج المتاحة

### 3.3 Review Service (HITL)

المسؤول عن مراجعة التقارير المُولّدة من قبل أطباء إشعاعيين.

**الميزات:**
- Diff Viewer: مقارنة بين التقرير المُولّد والتعديلات اليدوية
- Visual Grounding: تظليل المناطق في الصورة المذكورة في كل جملة
- Confidence Heatmap: الجمل ذات الثقة المنخفضة مظللة بالأحمر
- Audit Trail: كل تعديل موثّق بـ timestamp + user ID + reason

**الـ endpoints:**
- `GET /api/v1/review/queue` — قائمة الانتظار
- `POST /api/v1/review/{report_id}/approve` — اعتماد
- `POST /api/v1/review/{report_id}/edit` — تعديل
- `POST /api/v1/review/{report_id}/reject` — رفض مع سبب

### 3.4 Training Pipeline (Offline)

لا يعمل كخدمة بل كـ batch job عبر Celery + Kubernetes Jobs.

**المراحل:**
1. Data Selection: اختيار أزواج (صورة، تقرير معتمد) من قاعدة البيانات
2. Augmentation: تطبيق transforms من MONAI/TorchIO
3. Pretraining: Masked Image Modeling على الصور غير المُعنونة
4. Supervised Fine-tuning: Cross-entropy على أزواج (صورة، تقرير)
5. RLHF: PPO مع rewards من طبيب إشعاعي
6. Evaluation: على test set + مقاييس سريرية (CheXbert, BERTScore)

---

## 4. قاعدة البيانات (PostgreSQL Schema)

```sql
-- Studies (دراسة = مجموعة صور لمريض في جلسة واحدة)
CREATE TABLE studies (
    id UUID PRIMARY KEY,
    patient_pseudo_id VARCHAR(64) NOT NULL,  -- hashed
    study_instance_uid_hash VARCHAR(64) UNIQUE NOT NULL,
    study_date DATE,  -- date-shifted
    modality VARCHAR(16) NOT NULL,  -- CT, MR, XR, US
    body_part VARCHAR(64),
    accession_number VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Images (صورة واحدة داخل دراسة)
CREATE TABLE images (
    id UUID PRIMARY KEY,
    study_id UUID REFERENCES studies(id),
    sop_instance_uid_hash VARCHAR(64) UNIQUE NOT NULL,
    series_number INTEGER,
    instance_number INTEGER,
    rows INTEGER,
    columns INTEGER,
    pixel_spacing FLOAT[],
    slice_thickness FLOAT,
    window_center FLOAT,
    window_width FLOAT,
    orthanc_id VARCHAR(64) NOT NULL,  -- reference to Orthanc
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reports (تقارير)
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    study_id UUID REFERENCES studies(id),
    report_type VARCHAR(32) NOT NULL,  -- generated, reviewed, final
    content TEXT NOT NULL,
    content_ar TEXT,  -- الترجمة العربية
    model_name VARCHAR(64),
    model_version VARCHAR(32),
    confidence_scores JSONB,  -- per-sentence confidence
    generated_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    reviewer_id UUID,
    status VARCHAR(16) DEFAULT 'draft',  -- draft, pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log (غير قابل للحذف)
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    action VARCHAR(32) NOT NULL,  -- create, read, update, delete, generate, approve
    resource_type VARCHAR(32),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- إنشاء index للأداء
CREATE INDEX idx_images_study_id ON images(study_id);
CREATE INDEX idx_reports_study_id ON reports(study_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_audit_user_resource ON audit_log(user_id, resource_type, resource_id);
```

---

## 5. الأمان

### 5.1 طبقات الحماية

```
┌─ WAF (Web Application Firewall) — CloudFlare/AWS WAF
│  └─ Rate limiting, DDoS protection
├─ TLS 1.3 — جميع الاتصالات مشفّرة
│  └─ HSTS, Certificate Pinning
├─ OAuth2 + JWT — مصادقة قوية
│  └─ Refresh tokens, MFA for admins
├─ RBAC — صلاحيات دقيقة
│  └─ Admin, Radiologist, Technician, Viewer
├─ Audit Logging — غير قابل للحذف
│  └─ WORM storage, tamper-evident
└─ Encryption at Rest
   └─ PostgreSQL: AES-256, MinIO: SSE-KMS
```

### 5.2 إخفاء الهوية (De-identification)

يتبع المعيار **DICOM PS3.15 Annex E** (Basic Application Level Confidentiality Profile):

- **Tags تُحذف**: PatientName, PatientAddress, TelephoneNumbers, ReferringPhysicianName
- **Tags تُهاش**: PatientID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID
- **Tags تُزاح تواريخها**: StudyDate, SeriesDate, PatientBirthDate (shift بـ N يوم عشوائي)
- **Tags تُفحص للـ burned-in text**: صور قد تحتوي على اسم المريض محفور فيها

التنفيذ: `scripts/dicom_deidentify.py`

للتفاصيل الكاملة: [SECURITY.md](SECURITY.md)

---

## 6. البنية التحتية (Infrastructure)

### 6.1 Docker Compose (Development)

الملف: `setup/docker-compose.yml`

الخدمات:
- **orthanc**: PACS server لتخزين DICOM
- **postgres**: قاعدة البيانات الرئيسية
- **minio**: Object storage للصور الكبيرة
- **milvus**: Vector DB للبحث الدلالي في التقارير
- **redis**: Message broker + cache
- **api**: FastAPI service
- **worker**: Celery worker للمهام غير المتزامنة
- **flower**: مراقبة Celery

### 6.2 Kubernetes (Production)

للإنتاج، يُنصح بـ:
- **GPU nodes**: لخدمة Inference (NVIDIA T4 أو A10)
- **CPU nodes**: لباقي الخدمات
- **Persistent Volumes**: للبيانات (ceph, EBS, Azure Disk)
- **Ingress**: NGINX Ingress + cert-manager
- **Monitoring**: Prometheus + Grafana + Loki

---

## 7. التوسع (Scaling)

| الخدمة | استراتيجية التوسع |
|--------|------------------|
| API Gateway | Horizontal — كل instance عديم الحالة |
| Ingestion | Horizontal — كل ملف مستقل |
| Inference | Horizontal + GPU — قائمة انتظار لكل GPU |
| Review | Horizontal — مع قفل متفائل (optimistic locking) |
| Training | Vertical — حسب حجم الـ GPU المتاح |
| Orthanc | Vertical + Read Replicas — نمط CQRS |

---

## 8. المراقبة (Observability)

- **Metrics**: Prometheus (latency, throughput, error rates, GPU utilization)
- **Logs**: structured JSON إلى Loki/ELK
- **Tracing**: OpenTelemetry + Jaeger
- **Alerts**: AlertManager → PagerDuty/Slack

الـ metrics الحرجة:
- `ingestion_latency_seconds` — زمن استقبال ومعالجة DICOM
- `inference_latency_seconds` — زمن توليد التقرير
- `review_backlog_count` — عدد التقارير بانتظار المراجعة
- `model_confidence_distribution` — توزيع درجات الثقة
- `audit_log_events_total` — عدد أحداث الـ audit

---

## 9. الـ Disaster Recovery

| المكون | RPO | RTO | الاستراتيجية |
|--------|-----|-----|--------------|
| PostgreSQL | 5 min | 30 min | Streaming replication + daily snapshots |
| Orthanc | 1 hr | 2 hr | Nightly backup to S3 |
| MinIO | 1 hr | 1 hr | Cross-region replication |
| Models | 24 hr | 4 hr | Versioned in model registry |

---

## 10. القرارات المعمارية المفتوحة (ADRs Pending)

- [ ] ADR-001: استخدام PostgreSQL vs MongoDB للـ metadata
- [ ] ADR-002: Orthanc vs dcm4che للـ PACS
- [ ] ADR-003: Milvus vs Weaviate vs Qdrant للـ Vector DB
- [ ] ADR-004: Celery vs Temporal للـ workflow engine
- [ ] ADR-005: نموذج عربي Fine-tuned vs Translation pipeline

---

> آخر تحديث: 2026-08-01
