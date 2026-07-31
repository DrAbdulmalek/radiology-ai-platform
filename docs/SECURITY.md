# Security & Compliance — Radiology AI Platform

> قواعد الأمان والخصوصية والامتثال التنظيمي

---

## 1. الإطار التنظيمي

المنصة تتعامل مع **بيانات صحية محمية (PHI)**، لذا يجب الالتزام بالمعايير التالية حسب المنطقة الجغرافية:

| المعيار | المنطقة | الوصف |
|--------|--------|------|
| **HIPAA** | USA | Health Insurance Portability and Accountability Act |
| **GDPR** | EU | General Data Protection Regulation — Article 9 (Special Category) |
| **PDPL** | Saudi Arabia | Personal Data Protection Law |
| **DICOM PS3.15** | Global | DICOM De-identification Standard |
| **ISO 27001** | Global | Information Security Management (optional but recommended) |

### المبدأ الأساسي
> **Privacy by Design + Privacy by Default** — لا تُخزَّن أي بيانات شخصية في النظام قبل إخفاء الهوية. إخفاء الهوية يحدث في **نفس اللحظة** التي يُرفع فيها الملف، وقبل أي معالجة أو تخزين دائم.

---

## 2. إخفاء الهوية (De-identification)

### 2.1 المعيار المتبع

نتبع **DICOM PS3.15 Annex E** — Basic Application Level Confidentiality Profile.

### 2.2 تصنيف الـ DICOM Tags

#### Tags تُحذف كاملاً (Removed)
تحتوي على معلومات تعريفية مباشرة:

| Tag | Name | السبب |
|-----|------|------|
| (0010,0010) | PatientName | اسم المريض |
| (0010,1000) | OtherPatientIDs | معرّفات إضافية |
| (0010,1040) | PatientAddress | العنوان |
| (0010,2154) | PatientTelephoneNumbers | الهاتف |
| (0010,21B0) | AdditionalPatientHistory | تاريخ طبي إضافي |
| (0008,0090) | ReferringPhysicianName | اسم الطبيب المُحيل |
| (0008,1048) | PhysiciansOfRecord | أسماء الأطباء |
| (0008,1050) | PerformingPhysicianName | اسم الطبيب المنفّذ |
| (0008,1070) | OperatorsName | اسم الفني |
| (0032,1032) | RequestingPhysician | الطبيب الطالب |
| (4008,0114) | PhysicianApprovingInterpretation | الطبيب المعتمد |

#### Tags تُهاش (Hashed)
معرّفات تحتاج الحفاظ على العلاقات (نفس المريض = نفس الـ hash):

| Tag | Name | الـ hash function |
|-----|------|------------------|
| (0010,0020) | PatientID | SHA-256 + salt, truncated to 16 chars |
| (0020,000D) | StudyInstanceUID | SHA-256 + salt |
| (0020,000E) | SeriesInstanceUID | SHA-256 + salt |
| (0008,0018) | SOPInstanceUID | SHA-256 + salt |
| (0008,1155) | ReferencedSOPInstanceUID | SHA-256 + salt (recursive) |

#### Tags تُزاح تواريخها (Date Shifted)
للحفاظ على الفترات الزمنية بين الأحداث:

| Tag | Name |
|-----|------|
| (0010,0030) | PatientBirthDate |
| (0008,0020) | StudyDate |
| (0008,0021) | SeriesDate |
| (0008,0022) | AcquisitionDate |
| (0008,0023) | ContentDate |
| (0008,0030) | StudyTime |
| (0008,0031) | SeriesTime |
| (0008,0032) | AcquisitionTime |
| (0008,0033) | ContentTime |

**الاستراتيجية**: 
- تُزاح كل التواريخ في دراسة واحدة بنفس عدد الأيام (محفوظة في `study.date_shift_days`)
- عدد الأيام عشوائي بين -365 و +365 لكل دراسة
- سنة الميلاد تُحفظ فقط (إزالة الشهر واليوم) — لاحتساب العمر التقريبي

#### Tags تحتاج فحصاً (Burned-in Text)
بعض الصور تحتوي على نصوص محفورة (مثل: اسم المريض في زاوية الصورة):

| الفحص | الإجراء |
|------|--------|
| OCR على الصورة لكشف الأسماء | إذا وُجد نص يشبه اسم → black box على المنطقة |
| فحص الـ pixel data للأنماط المعروفة | تطبيق `pixel_anonymizer` من `dicom_anonymizer` |

### 2.3 التطبيق

التنفيذ في: [`scripts/dicom_deidentify.py`](../scripts/dicom_deidentify.py)

```bash
# إخفاء هوية ملف واحد
python scripts/dicom_deidentify.py \
  --input patient123.dcm \
  --output data/deidentified/ \
  --date-shift -127

# إخفاء هوية مجلد كامل
python scripts/dicom_deidentify.py \
  --input /dicom/raw/ \
  --output data/deidentified/ \
  --date-shift -127 \
  --audit audit_2026_08_01.json
```

### 2.4 التحقق (Verification)

بعد إخفاء الهوية، يجب التحقق باستخدام:

1. **Automated verification**: سكربت يفحص الـ tags ويرفض إذا وُجد PHI
2. **Manual spot check**: 5% من الملفات يفحصها مشرف بصرياً
3. **External tool**: `dciodvfy` للتحقق من توافق DICOM

**معيار القبول**: 0% PHI متبقية (لا تسامح)

---

## 3. التحكم في الوصول (Access Control)

### 3.1 النموذج: RBAC (Role-Based Access Control)

| الدور | الصلاحيات |
|------|----------|
| **Admin** | إدارة المستخدمين، الإعدادات، audit logs (read-only) |
| **Radiologist** | عرض الصور، توليد التقارير، مراجعتها، اعتمادها |
| **Technician** | رفع DICOM، عرض الصور (لا تقارير) |
| **Researcher** | بيانات مُجمّعة (aggregated)، لا بيانات فردية |
| **Viewer** | عرض التقارير النهائية فقط (لا صور) |

### 3.2 المصادقة

- **OAuth2 + JWT** للـ API
- **MFA إجباري** للـ Admin و Radiologist
- **Refresh tokens** بـ lifetime 24h
- **Access tokens** بـ lifetime 15min
- **Session timeout**: 30 min على الويب

### 3.3 المبدأ: Least Privilege

كل مستخدم يحصل على **أقل صلاحية ممكنة** لأداء عمله. الصلاحيات تُمنح عبر:
- **Groups** (مثلاً: "Radiology Department")
- **Project-specific** (مثلاً: "Pilot Study 2027")
- **Time-bound** (صلاحية تنتهي بعد N يوم)

---

## 4. التشفير (Encryption)

### 4.1 At Rest

| المكون | الطريقة | المفتاح |
|--------|--------|--------|
| PostgreSQL | AES-256 (pgcrypto أو cloud KMS) | Cloud KMS rotation كل 90 يوم |
| MinIO / S3 | SSE-KMS | Cloud KMS |
| Orthanc | AES-256 (volume-level) | Cloud KMS |
| Backups | AES-256 | Separate KMS key |
| Local dev | LUKS (optional) | Manual |

### 4.2 In Transit

- **TLS 1.3** إجباري لكل الاتصالات
- **HSTS** على الويب (max-age=31536000; includeSubDomains; preload)
- **Certificate Pinning** على mobile clients (إن وُجد)
- **mTLS** بين الخدمات الداخلية (في الإنتاج)

### 4.3 إدارة المفاتيح (Key Management)

- **AWS KMS** أو **HashiCorp Vault** لإدارة المفاتيح
- **Rotation كل 90 يوم** للمفاتيح الرئيسية
- **Separation of duties**: من يدير المفاتيح ≠ من يصل للبيانات
- **Audit log** لكل استخدام للمفتاح

---

## 5. الـ Audit Log

### 5.1 ما يُسجَّل

كل عملية في النظام تُسجَّل في `audit_log` table:

| الحقل | مثال |
|------|------|
| `user_id` | `550e8400-e29b-41d4-a716-446655440000` |
| `action` | `read`, `create`, `update`, `delete`, `generate`, `approve`, `reject` |
| `resource_type` | `study`, `image`, `report`, `user` |
| `resource_id` | UUID |
| `details` | JSONB (مثلاً: `{"fields_changed": ["impression"]}`) |
| `ip_address` | `192.168.1.100` |
| `user_agent` | `Mozilla/5.0...` |
| `created_at` | `2027-03-15 10:23:45.123456+03` |

### 5.2 الـ WORM Storage

الـ audit log **غير قابل للتعديل أو الحذف**:
- يُخزَّن في volume منفصل بـ `chattr +a` (append-only)
- يُنسخ يومياً إلى S3 Object Lock (Compliance mode)
- مدة الاحتفاظ: 7 سنوات (حسب HIPAA)

### 5.3 التنبيهات (Alerts)

تنبيه فوري عند:
- محاولة حذف من audit log
- عدد كبير من العمليات في وقت قصير (مثلاً: 100 قراءة في دقيقة)
- وصول من IP غير معتاد
- وصول خارج ساعات العمل (إن كان مُفعّلاً)

---

## 6. أمان الشبكة (Network Security)

### 6.1 الـ VPC Layout

```
┌──────────────────────────────────────────────────┐
│  Public Subnet (10.0.1.0/24)                    │
│  ┌────────────────┐                              │
│  │  Load Balancer │ ◄── Internet                 │
│  └────────┬───────┘                              │
└───────────┼──────────────────────────────────────┘
            │
┌───────────┼──────────────────────────────────────┐
│  Private Subnet (10.0.2.0/24) — App Tier        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   API   │  │ Worker  │  │ Review  │           │
│  └────┬────┘  └────┬────┘  └────┬────┘           │
└───────┼────────────┼────────────┼────────────────┘
        │            │            │
┌───────┼────────────┼────────────┼────────────────┐
│  Data Subnet (10.0.3.0/24) — DB Tier             │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │ PG   │  │Orthanc│ │ MinIO│  │Redis │          │
│  └──────┘  └──────┘  └──────┘  └──────┘          │
└──────────────────────────────────────────────────┘
```

### 6.2 الـ Firewall Rules

- **Inbound**: فقط من Load Balancer إلى API على port 443
- **Between tiers**: API → DB على ports محددة فقط
- **Outbound**: محدود (Pypi, Docker Hub, Cloud APIs فقط)
- **Bastion host**: للـ SSH الإداري مع MFA

### 6.3 الـ VPN / Bastion

- **لا SSH مباشر** إلى الخدمات
- **Bastion host** مع:
  - MFA إجباري
  - Session recording
  - IP allowlist
- **Cloudflare Access** أو **AWS SSM Session Manager** كبديل

---

## 7. الـ Incident Response

### 7.1 خطة الاستجابة

```
Detection (≤1h) → Containment (≤4h) → Eradication → Recovery → Post-mortem
```

### 7.2 الـ Severity Levels

| Level | مثال | زمن الاستجابة |
|-------|------|---------------|
| **P0 — Critical** | تسريب PHI مؤكد | ≤1 ساعة |
| **P1 — High** | محاولة اختراق ناجحة جزئياً | ≤4 ساعات |
| **P2 — Medium** | أنماط مشبوهة (محاولات login فاشلة) | ≤24 ساعة |
| **P3 — Low** | خطأ تكوين غير أمني | ≤7 أيام |

### 7.3 الإبلاغ التنظيمي

| الجهة | المهلة | متى |
|------|--------|-----|
| HHS (HIPAA) | 60 يوم | عند تأكد تسريب ≥500 فرد |
| GDPR | 72 ساعة | عند تأكد تسريب أي بيانات شخصية |
| PDPL (Saudi) | 72 ساعة | عند تأكد تسريب |
| المستخدمون المتأثرون | بدون تأخير غير مبرّر | عند تأكد تسريب |

---

## 8. اختبار الاختراق (Penetration Testing)

### 8.1 الدوري

- **Internal**: كل 3 أشهر
- **External (third-party)**: سنوياً
- **After major changes**: دائماً

### 8.2 النطاق

- OWASP Top 10
- OWASP API Security Top 10
- DICOM-specific attacks (malformed DICOM, XXE in XML)
- ML-specific attacks (adversarial images, model inversion)

### 8.3 Bug Bounty

بعد الإطلاق، فتح برنامج Bug Bounty عبر:
- HackerOne أو Bugcrowd
- Scope: API + Web app
- Rewards: $100 - $5000 حسب الـ severity

---

## 9. التدريب والتوعية (Security Awareness)

كل المستخدمين يجب أن يخضعوا لـ:

| الفئة | التدريب | التكرار |
|------|--------|---------|
| جميع المستخدمين | HIPAA basics + phishing awareness | سنوياً |
| الأطباء | التعامل مع PHI + استخدام النظام | عند الإطلاق + سنوياً |
| المطورين | Secure coding + OWASP | سنوياً |
| الـ Admins | Incident response + forensics | سنوياً |

---

## 10. قائمة التحقق (Pre-Launch Checklist)

قبل الإطلاق الإنتاجي، يجب التأكد من:

- [ ] De-identification pipeline يمر اختبار 1000 ملف بنجاح 100%
- [ ] TLS 1.3 مُفعّل على كل endpoints
- [ ] MFA إجباري لكل الـ Admins و Radiologists
- [ ] Audit log يعمل وغير قابل للحذف
- [ ] Backups يومية + اختبار restore ناجح
- [ ] Penetration test ناجح (لا P0 أو P1)
- [ ] IRB approval ساري
- [ ] Data Sharing Agreements موقّعة مع المستشفيات
- [ ] Disaster recovery plan مُختبر
- [ ] Monitoring dashboards تعمل
- [ ] Incident response plan موثّق ومُدرّب عليه
- [ ] Legal review للـ Terms of Service و Privacy Policy
- [ ] HIPAA / GDPR / PDPL assessment ناجح

---

## 11. الـ Disclosure Policy

إذا اكتُشف ثغرة أمنية:

1. **الإبلاغ**: security@radiology-ai.example.com (PGP key منفصل)
2. **الاستجابة**: خلال 48 ساعة تأكيد الاستلام
3. **الإصلاح**: 
   - Critical: 7 أيام
   - High: 30 يوم
   - Medium: 90 يوم
4. **الإفصاح**: بعد الإصلاح + 90 يوم (إذا رغب الباحث)

---

## 12. الـ References

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [GDPR Article 9](https://gdpr-info.eu/art-9-gdpr/)
- [Saudi PDPL](https://sdaia.gov.sa/en/SDAIA/about/Pages/RegulationPolicies.aspx)
- [DICOM PS3.15 Annex E](https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

> آخر تحديث: 2026-08-01
