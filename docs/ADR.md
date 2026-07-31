# Architecture Decision Records (ADR) — Radiology AI Platform

> قرارات معمارية مُلزمة — تم الاتفاق عليها في 2026-08-01 بين د. عبد المالك و Z.ai

---

## النظرة العامة

هذا المستند يُوثّق القرارات المعمارية الأساسية للمنصة. أي تنفيذ مستقبلي يجب أن يلتزم بهذه القرارات. تغيير أي قرار يتطلب:
1. مراجعة هذا الملف
2. إضافة ADR جديد يُلغي القديم مع تبرير
3. تحديث الـ dependencies في `setup/requirements.txt`

---

## ADR-001: قاعدة البيانات — asyncpg (Async PostgreSQL)

**الحالة**: ✅ مقبول
**التاريخ**: 2026-08-01

### السياق
نحتاج قاعدة بيانات لتخزين:
- دراسات DICOM + الـ metadata
- التقارير المُولّدة + المُراجَعة
- الـ audit logs
- بيانات المستخدمين

الخيارات المتاحة:
- `psycopg2` (sync) — المعيار التقليدي
- `asyncpg` (async) — حديث وسريع
- `SQLModel` (sync wrapper) — أبسط لكنه أقل نضجاً

### القرار
**استخدام `asyncpg` مع SQLAlchemy 2.0 async mode.**

```python
# settings.py
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

### التبرير
1. **FastAPI يعمل بشكل أفضل مع async** — لا يحتاج لـ thread pool
2. **DICOM upload + AI inference يستغرقان وقتاً** — sync سيُعلق الـ API
3. **asyncpg أسرع 2-3x من psycopg2** في benchmarks الرسمية
4. **SQLAlchemy 2.0 يدعم async بشكل كامل** عبر `create_async_engine`
5. **التوافق مع باقي الـ stack** (Redis async, MinIO async, etc.)

### العواقب
- ✅ أداء أعلى تحت الحمل
- ✅ استجابة الـ API أسرع
- ⚠️ يتطلب `async/await` في كل الـ data layer
- ⚠️ بعض الـ libraries القديمة قد لا تدعم async (نستبدلها)

### الـ dependencies
```
asyncpg==0.30.0
sqlalchemy[asyncio]==2.0.36
```

---

## ADR-002: Job Queue — Celery + Redis + Flower

**الحالة**: ✅ مقبول
**التاريخ**: 2026-08-01

### السياق
نحتاج نظام مهام خلفية لـ:
- توليد التقارير بالـ AI (5-30 ثانية لكل تقرير)
- معالجة DICOM (de-identification + indexing)
- تدريب النماذج (ساعات)
- تنظيف دوري (purge old temp files)

الخيارات المتاحة:
- `FastAPI BackgroundTasks` — مدمج لكنه بسيط
- `RQ` (Redis Queue) — أبسط من Celery
- `Celery` — معيار الصناعة
- `Temporal` — حديث لكنه معقّد

### القرار
**استخدام Celery + Redis كـ broker + Flower للمراقبة.**

```python
# inference_worker.py
from celery import Celery

app = Celery("radiology_ai", broker="redis://localhost:6379/0")

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_report(self, study_id: str, model: str = "r2gen-v1.2"):
    try:
        # ... inference logic ...
        return {"report_id": report.id, "status": "generated"}
    except ModelLoadError as exc:
        # Don't retry on model errors
        raise
    except (TimeoutError, ConnectionError) as exc:
        # Retry on transient errors
        raise self.retry(exc=exc, countdown=60)
    except Exception as exc:
        # Generic retry
        raise self.retry(exc=exc, countdown=60 * self.request.retries)
```

### التبرير
1. **BackgroundTasks يعمل فقط أثناء الـ request** — إذا سقط الـ server تُفقد المهمة
2. **RQ أبسط لكنه لا يدعم** scheduling + monitoring مثل Celery
3. **Celery يدعم**:
   - **Retry logic** (مهم للـ AI inference — GPU قد يكون مشغولاً)
   - **Monitoring** (Flower dashboard — `http://localhost:5555`)
   - **Scheduling** (periodic tasks للـ cleanup, audit log rotation)
   - **Multiple workers** (GPU worker منفصل عن API worker)
   - **Task priorities** (تقرير طارئ يسبق تنظيفاً دورياً)

### العواقب
- ✅ موثوقية عالية — المهام لا تُفقد
- ✅ قابل للتوسع (cluster of workers)
- ✅ مراقبة ممتازة عبر Flower
- ⚠️ تعقيد تشغيلي أكبر (Redis + Celery worker + Flower)
- ⚠️ debugging أصعب من الـ sync

### الـ dependencies
```
celery==5.4.0
redis==5.2.0
flower==2.0.1
```

### البنية
```
┌─────────────────┐     ┌─────────┐     ┌──────────────────┐
│   FastAPI       │────►│  Redis  │◄────│  Celery Worker   │
│   (producer)    │     │ (broker)│     │  (consumer)      │
└─────────────────┘     └────┬────┘     └──────────────────┘
                             │
                             ▼
                        ┌─────────┐
                        │ Flower  │ (monitoring)
                        └─────────┘
```

### الـ Queues المقترحة
| Queue | الأولوية | الـ workers |
|-------|---------|------------|
| `default` | متوسطة | 2 (CPU) |
| `inference` | عالية | 1 (GPU) |
| `training` | منخفضة | 1 (GPU dedicated) |
| `cleanup` | منخفضة جداً | 1 (CPU) |

---

## ADR-003: Migrations — Alembic + SQLAlchemy 2.0

**الحالة**: ✅ مقبول
**التاريخ**: 2026-08-01

### السياق
نحتاج نظام migrations لإدارة تطور schema قاعدة البيانات.

الخيارات المتاحة:
- `Alembic` — المعيار الصناعي
- `SQLModel` (يولّد schema تلقائياً)
- `Django migrations` — ليس لنا (لسنا Django)
- `Hand-written SQL` — بدائي

### القرار
**استخدام Alembic + SQLAlchemy 2.0 declarative models (ليس SQLModel).**

```bash
# الإعداد
alembic init migrations

# توليد migration من الـ models
alembic revision --autogenerate -m "add studies table"

# تطبيق
alembic upgrade head

# rollback
alembic downgrade -1
```

```python
# models/study.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Study(Base):
    __tablename__ = "studies"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_pseudo_id: Mapped[str] = mapped_column(String(64))
    modality: Mapped[str] = mapped_column(String(16))
    # ...
```

### التبرير
1. **SQLModel مبني على SQLAlchemy لكنه أقل نضجاً** — bugs متكررة في الإنتاج (خاصة مع الـ async)
2. **Alembic هو المعيار الصناعي للـ migrations** — يدعم:
   - **Auto-generation** من SQLAlchemy models
   - **Branching + merging** للـ migrations المتوازية
   - **Rollback آمن** (downgrade)
   - **Offline mode** (توليد SQL بدون اتصال بالـ DB)
3. **SQLAlchemy 2.0 أحدث وأكثر استقراراً** من SQLModel
4. **التوافق مع asyncpg** (ADR-001) — كلاهما يدعم async

### العواقب
- ✅ migrations مُنظّمة وقابلة للمراجعة
- ✅ rollback آمن عند الأخطاء
- ✅ team collaboration (كل developer يُنشئ migration منفصل)
- ⚠️ يجب توليد migration عند كل تغيير في الـ models
- ⚠️ SQLModel أبسط في الكتابة لكن يُكلّفنا في الصيانة

### الـ dependencies
```
alembic==1.14.0
sqlalchemy[asyncio]==2.0.36
```

### قواعد الـ migrations
1. **كل PR يُغيّر الـ schema يجب أن يحتوي migration**
2. **لا تعدّل migration قديم** — أنشئ جديداً للتصحيح
3. **اختبر migration على بيانات وهمية قبل الإنتاج**
4. **Backup قاعدة البيانات قبل كل migration في الإنتاج**

---

## ADR-004: المصادقة — JWT Short-Lived + Refresh Tokens

**الحالة**: ✅ مقبول
**التاريخ**: 2026-08-01

### السياق
نحتاج نظام مصادقة للـ API. المستخدمون:
- أطباء إشعاعيون (يستخدمون الـ web UI لساعات طويلة)
- فنيون (يرفعون DICOM)
- admins (يديرون النظام)

الخيارات المتاحة:
- **Session-based** (cookies + DB) — تقليدي
- **JWT short-lived only** (15 دقيقة، إعادة login متكرر)
- **JWT + Refresh tokens** — hybrid
- **OAuth2 فقط** (Keycloak) — معقّد للـ MVP

### القرار
**استخدام JWT hybrid: Access Token قصير (15 دقيقة) + Refresh Token طويل (7 أيام).**

```python
# settings.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "HS256"  # upgrade to RS256 in production
JWT_ISSUER = "radiology-ai-platform"
JWT_AUDIENCE = "radiology-clients"
```

### التبرير
1. **Access token قصير** يُقلل الـ damage إذا سُرق (15 دقيقة فقط)
2. **Refresh token طويل** لا يُجبر الطبيب على re-login كل 15 دقيقة (UX جيد)
3. **Refresh token يُخزّن في `httpOnly` cookie** — مقاوم لـ XSS
4. **Access token في `Authorization: Bearer` header** — مرن
5. **Revocation list للـ refresh tokens** — إذا سُرق الجهاز، يمكن إلغاء الجلسة

### التنفيذ

#### Login Flow
```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Client  │────────►│   API    │────────►│   DB     │
│          │  POST   │          │  verify │          │
│          │  /login │          │  pwd    │          │
│          │◄────────│          │◄────────│          │
│          │         │          │         │          │
│          │ Set:    │          │         │          │
│          │ refresh │          │         │          │
│          │ cookie  │          │         │          │
│          │ (7d)    │          │         │          │
│          │         │          │         │          │
│          │ Return: │          │         │          │
│          │ access  │          │         │          │
│          │ token   │          │         │          │
│          │ (15m)   │          │         │          │
└──────────┘         └──────────┘         └──────────┘
```

#### Token Refresh Flow
```
Client sends request with expired access token (401)
   ↓
Client calls POST /auth/refresh with refresh cookie
   ↓
API verifies refresh token signature + expiry + revocation list
   ↓
API issues NEW access token (15 min) + NEW refresh token (7d, rotated)
   ↓
Old refresh token is invalidated (rotation prevents replay)
```

#### Logout Flow
```
Client calls POST /auth/logout
   ↓
API adds refresh token to revocation list (Redis TTL: 7 days)
   ↓
API clears refresh cookie
   ↓
Client discards access token (will expire in ≤15 min)
```

### Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user ID
  "email": "dr.saleh@hospital.com",
  "role": "radiologist",
  "permissions": ["studies:read", "reports:write", "reports:approve"],
  "iat": 1722500000,
  "exp": 1722500900,  // +15 min
  "iss": "radiology-ai-platform",
  "aud": "radiology-clients",
  "jti": "unique-token-id-for-logging"
}
```

### Refresh Token Storage

| المكان | التفاصيل |
|--------|---------|
| **Client (cookie)** | `httpOnly`, `Secure`, `SameSite=Strict`, `Path=/auth/refresh` |
| **Server (Redis)** | `refresh_token:{jti}` → `{user_id, issued_at, last_used}` with TTL=7d |
| **Revocation list** | `revoked_refresh:{jti}` with TTL = remaining validity |

### العواقب
- ✅ أمان عالٍ — access token قصير يحد من الخطر
- ✅ UX جيد — refresh تلقائي عبر cookie
- ✅ Revocation ممكن — خلال ثوانٍ من اكتشاف السرقة
- ⚠️ تعقيد أعلى من session-based
- ⚠️ Redis مطلوب للـ revocation list
- ⚠️ Token rotation يتطلب تنسيق دقيق (race conditions عند الـ concurrent refresh)

### الـ dependencies
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pyotp==2.9.0  # for MFA
```

### MFA (Multi-Factor Authentication) — للـ Admins و Radiologists
- **TOTP** عبر `pyotp` (مثل Google Authenticator)
- **إجباري** للـ admin و radiologist roles
- **اختياري** للـ technician و viewer

### الترقية المستقبلية (Phase 4 — Production)
1. **الانتقال من HS256 → RS256** (asymmetric keys — أفضل للأمان)
2. **Key rotation** تلقائي كل 90 يوماً
3. **Token introspection endpoint** (للـ revocation الفورية)
4. **Integration مع Keycloak** لو احتجنا SSO مع المستشفيات

---

## ملخص القرارات (Cheat Sheet)

```
التقنيات المختارة:

1. Database: asyncpg (PostgreSQL async via SQLAlchemy 2.0)
2. Job Queue: Celery + Redis + Flower (monitoring)
3. Migrations: Alembic + SQLAlchemy 2.0 (no SQLModel)
4. Auth: JWT short-lived (15min access) + refresh tokens (7 days, httpOnly cookie)
```

---

## القرارات المعلّقة (Pending ADRs)

- [ ] ADR-005: Orthanc vs dcm4che للـ PACS server
- [ ] ADR-006: Milvus vs Weaviate vs Qdrant للـ Vector DB
- [ ] ADR-007: Flower vs NVFlare للـ Federated Learning
- [ ] ADR-008: نموذج عربي Fine-tuned vs Translation pipeline
- [ ] ADR-009: On-Premise vs Cloud vs Hybrid للنشر
- [ ] ADR-010: FHIR R4 vs FHIR R5 للـ export

---

## قواعد مراجعة القرارات

1. **كل قرار يُراجع بعد 6 أشهر** من الإطلاق — قد تتغير الظروف
2. **أي قرار يُلغى يتطلب ADR جديد** يُبرّر الإلغاء
3. **القرارات تُخزّن في `docs/adr/`** كملفات منفصلة (مستقبلاً)
4. **الـ commits تغيّر القرار يجب أن تشير للـ ADR** في الـ message

---

> آخر تحديث: 2026-08-01 — المؤلف: د. عبد المالك بالتعاون مع Z.ai
