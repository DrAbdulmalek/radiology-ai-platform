# Roadmap — Radiology AI Platform

> خطة التنفيذ المرحلية من Q4 2026 إلى Q4 2027

---

## النظرة العامة

الخطة مقسّمة إلى 4 مراحل. كل مرحلة لها **مخرجات قابلة للقياس (Deliverables)** و**معايير قبول (Acceptance Criteria)**. عدم تحقيق معايير القبول يعني عدم الانتقال للمرحلة التالية.

```
Phase 1 (Q4 2026)        Phase 2 (Q1 2027)        Phase 3 (Q2 2027)        Phase 4 (Q3-Q4 2027)
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Infrastructure │ ───► │   Prototype     │ ───► │   Pilot         │ ───► │   Production    │
│                 │      │                 │      │                 │      │                 │
│  • DICOM ingest │      │  • R2Gen model  │      │  • RadFM model  │      │  • Arabic LLM   │
│  • De-id pipeline│     │  • HITL UI      │      │  • CT/MRI support│     │  • Federated    │
│  • Storage      │      │  • 1000 reports │      │  • Pilot study  │      │  • FHIR export  │
│                 │      │                 │      │                 │      │  • Cert. prep   │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
       2 months                2 months                3 months                4-6 months
```

---

## المرحلة 1: البنية التحتية (Q4 2026 — شهران)

### الهدف
بناء الأساس التقني: تخزين DICOM، إخفاء الهوية، واجهة عرض، وقاعدة بيانات.

### المهام

#### 1.1 إخفاء الهوية (De-identification) — أسبوعان
- [ ] مراجعة وتطوير `scripts/dicom_deidentify.py` ليتوافق كاملاً مع PS3.15 Annex E
- [ ] إضافة فحص الـ burned-in text (OCR على الصور لكشف الأسماء المحفورة)
- [ ] اختبار على 100 ملف DICOM حقيقي (مع موافقة أخلاقية)
- [ ] توثق الـ audit log لكل عملية
- [ ] **معيار القبول**: 0% بيانات شخصية متبقية (يُفحص بـ tool تحقق خارجي)

#### 1.2 DICOM Storage + Viewer — 3 أسابيع
- [ ] نشر Orthanc PACS في Docker
- [ ] إضافة PostgreSQL backend
- [ ] دعم C-STORE, C-FIND, WADO-RS
- [ ] دمج Cornerstone.js في واجهة الويب
- [ ] دعم multi-frame و series متعددة
- [ ] **معيار القبول**: يمكن رفع دراسة CT كاملة (500 slice) وعرضها في <3 ثوان

#### 1.3 قاعدة البيانات — أسبوعان
- [ ] تنفيذ schema الموضّح في ARCHITECTURE.md
- [ ] Migrations عبر Alembic
- [ ] Backup + restore آلي
- [ ] **معيار القبول**: جميع الـ queries الرئيسية <100ms

#### 1.4 API الأساسي — أسبوعان
- [ ] FastAPI skeleton مع OAuth2
- [ ] endpoints: `/auth`, `/studies`, `/images`, `/reports`
- [ ] RBAC (Admin, Radiologist, Technician)
- [ ] Rate limiting + audit logging
- [ ] **معيار القبول**: 99% uptime في الأسبوع الأخير من الاختبار

### مخرجات المرحلة 1
- ✅ بيئة Docker كاملة تعمل محلياً
- ✅ يمكن رفع DICOM وإخفاء هويته وتخزينه
- ✅ واجهة ويب لعرض الصور
- ✅ API موثّق (OpenAPI/Swagger)
- ✅ 80%+ test coverage للكود الأساسي

---

## المرحلة 2: النموذج الأولي (Q1 2027 — شهران)

### الهدف
تدريب أول نموذج يولّد تقارير، ولو بدقة متوسطة، على بيانات حقيقية.

### المهام

#### 2.1 جمع البيانات — 3 أسابيع
- [ ] جمع 1000+ زوج (صورة، تقرير) من المستشفى الشريك
- [ ] موافقة أخلاقية (IRB approval)
- [ ] De-identification لكل الملفات
- [ ] تقسيم: 70% train, 15% val, 15% test
- [ ] **معيار القبول**: تنوع كافٍ (3+ modalities، 5+ body parts)

#### 2.2 تدريب R2Gen — 3 أسابيع
- [ ] إعداد GPU instance (AWS p4d أو GCP A2)
- [ ] Fine-tune R2Gen على البيانات
- [ ] Hyperparameter tuning (lr, batch size, epochs)
- [ ] Evaluation: BLEU-4, CIDEr, ROUGE-L
- [ ] **معيار القبول**: BLEU-4 > 0.15 على test set (مقارنة بـ 0.10 baseline)

#### 2.3 واجهة HITL — 3 أسابيع
- [ ] Diff viewer (النص المُولّد vs التعديل اليدوي)
- [ ] Confidence heatmap (الجمل ذات الثقة المنخفضة بالأحمر)
- [ ] Visual grounding (تظليل المناطق في الصورة)
- [ ] Approval/rejection workflow
- [ ] **معيار القبول**: طبيب إشعاعي يراجع 10 تقارير/ساعة دون إرهاق

#### 2.4 Inference Service — أسبوعان
- [ ] تحميل النموذج في الذاكرة (model serving)
- [ ] Batch inference (للتقييم)
- [ ] Real-time inference (للاستخدام)
- [ ] Confidence scoring لكل جملة
- [ ] **معيار القبول**: زمن التوليد <5 ثوان لكل دراسة

### مخرجات المرحلة 2
- ✅ نموذج R2Gen مُدرّب على بيانات حقيقية
- ✅ واجهة HITL كاملة
- ✅ pipeline من الصورة إلى التقرير المُراجَع
- ✅ تقرير تقييم شامل (BLEU, CIDEr, Clinical Accuracy)

---

## المرحلة 3: الـ Pilot (Q2 2027 — 3 أشهر)

### الهدف
تجربة المنصة في بيئة سريرية حقيقية مع 1-2 مستشفى شريك، وجمع feedback.

### المهام

#### 3.1 ترقية إلى RadFM — 4 أسابيع
- [ ] استبدال R2Gen بـ RadFM (يدعم CT/MRI وليس فقط X-ray)
- [ ] إعادة تدريب على بيانات أوسع
- [ ] دعم 3D volumes (وليس فقط 2D slices)
- [ ] **معيار القبول**: أداء أفضل من R2Gen بـ 20%+ على كل المقاييس

#### 3.2 Pilot Deployment — 4 أسابيع
- [ ] نشر On-Premise في المستشفى الشريك
- [ ] تدريب 3-5 أطباء إشعاعيين
- [ ] تشغيل لمدة 4 أسابيع على بيانات حقيقية
- [ ] جمع: تقارير مُولّدة، تعديلات، رفض، feedback نوعي
- [ ] **معيار القبول**: 50+ تقرير مُراجَع من كل طبيب

#### 3.3 تحسينات بناءً على الـ Pilot — 4 أسابيع
- [ ] تحليل أنماط الأخطاء (error analysis)
- [ ] إعادة تدريب النموذج على الـ rejected reports
- [ ] تحسين الـ UI بناءً على feedback
- [ ] إضافة ميزات مطلوبة (مثلاً: templates للتقارير الشائعة)
- [ ] **معيار القبول**: رضا الأطباء >4/5 في استبيان نهائي

### مخرجات المرحلة 3
- ✅ RadFM يعمل على CT/MRI/X-ray
- ✅ تقرير Pilot شامل (إيجابيات، سلبيات، توصيات)
- ✅ نموذج محسّن بناءً على بيانات حقيقية
- ✅ قائمة ميزات للإنتاج

---

## المرحلة 4: الإنتاج (Q3-Q4 2027 — 4-6 أشهر)

### الهدف
إطلاق رسمي مع نماذج عربية، Federated Learning، وامتثال تنظيمي كامل.

### المهام

#### 4.1 نموذج عربي Fine-tuned — 6 أسابيع
- [ ] ترجمة 10,000+ تقرير إنجليزي إلى عربي (بواسطة أطباء)
- [ ] Fine-tune نموذج LLM عربي (Jais, AceGPT) على التقارير
- [ ] Vision-Language alignment بالعربية
- [ ] **معيار القبول**: جودة عربية >8/10 من أطباء عرب

#### 4.2 Federated Learning — 6 أسابيع
- [ ] إعداد Flower (مكتبة FL مفتوحة المصدر)
- [ ] تدريب موزّع على 3+ مستشفيات دون نقل البيانات
- [ ] Differential Privacy (ε < 1.0)
- [ ] **معيار القبول**: دقة النموذج المشترك ≥ دقة النموذج المركزي

#### 4.3 FHIR Export — 4 أسابيع
- [ ] تحويل التقارير المُعتمدة إلى DiagnosticReport FHIR R4
- [ ] دعم SNOMED CT codes (النتائج، التشخيصات)
- [ ] دعم LOINC codes (النوع الإشعاعي)
- [ ] **معيار القبول**: validation ناجح على FHIR Validator الرسمي

#### 4.4 الامتثال التنظيمي — 8 أسابيع
- [ ] HIPAA Security Rule assessment
- [ ] GDPR Data Protection Impact Assessment (DPIA)
- [ ] PDPL (Saudi) compliance check
- [ ] ISO 27001 readiness (إن كان مطلوباً)
- [ ] **معيار القبول**: تقرير امتثال من جهة خارجية (third-party audit)

#### 4.5 الإطلاق — 4 أسابيع
- [ ] Documentation كاملة
- [ ] Training materials للأطباء
- [ ] Support process (tickets, SLA)
- [ ] Monitoring dashboards
- [ ] **معيار القبول**: 10+ مستشفى في queue للانضمام

### مخرجات المرحلة 4
- ✅ منصة إنتاجية كاملة بالعربية
- ✅ Federated Learning يعمل
- ✅ FHIR export
- ✅ امتثال HIPAA/GDPR/PDPL
- ✅ إطلاق رسمي

---

## المخاطر والتخفيف (Risk Register)

| الخطر | الاحتمال | التأثير | التخفيف |
|------|--------|--------|--------|
| عدم توفر بيانات كافية | متوسط | 🔴 عالي | تعاون مع 2+ مستشفيات + استخدام public datasets |
| أداء النموذج ضعيف بالعربية | متوسط | 🟡 متوسط | بدء التدريب العربي مبكراً في Phase 2 |
| رفض الأطباء للنظام | منخفض | 🔴 عالي | Pilot مكثف + تحسينات بناءً على feedback |
| مشاكل تنظيمية (IRB) | متوسط | 🟡 متوسط | بدء عملية IRB مبكراً (3-6 أشهر) |
| تكلفة GPU عالية | متوسط | 🟡 متوسط | استخدام spot instances + Federated Learning |
| تسريب بيانات | منخفض | 🔴 عالي | De-identification صارم + audit logs + encryption |

---

## KPIs (Key Performance Indicators)

### KPIs تقنية
- `inference_latency_p95 < 5 seconds`
- `system_uptime > 99.5%`
- `test_coverage > 80%`
- `bug_rate < 1 critical bug/month`

### KPIs سريرية
- `clinical_acceptance_rate > 70%` (نسبة التقارير المُعتمدة دون تعديل جوهري)
- `radiologist_time_saved > 30%` (مقارنة بالكتابة اليدوية)
- `critical_finding_recall > 95%` (نسبة النتائج الحرجة التي يلتقطها النموذج)

### KPIs أمنية
- `phi_leak_incidents = 0`
- `audit_log_completeness = 100%`
- `time_to_detect_breach < 1 hour`

---

## الاعتماديات (Dependencies)

### داخلي
- [`omni-medical-suite`](https://github.com/DrAbdulmalek/omni-medical-suite) — لاستخدام pipeline الـ OCR لاستخراج النص من الـ burned-in annotations
- [`dictionaries-csv`](https://github.com/DrAbdulmalek/dictionaries-csv) — للتحقق من المصطلحات الطبية العربية في التقارير المُولّدة
- [`intelli-file-manager`](https://github.com/DrAbdulmalek/intelli-file-manager) — لإدارة ملفات DICOM (UI موحّد)

### خارجي
- GPU instances (AWS/GCP)
- IRB approval
- Data sharing agreements مع المستشفيات
- FHIR validator service

---

## الميزانية التقديرية (Rough Order of Magnitude)

> هذه أرقام تقديرية للـ cloud infrastructure فقط (لا تشمل رواتب الفريق)

| البند | شهرياً | سنوياً |
|------|--------|--------|
| GPU (p4d.24xlarge × 2 للتدريب) | $8,000 | $96,000 |
| Storage (10TB DICOM + 1TB DB) | $300 | $3,600 |
| Compute (API + workers) | $500 | $6,000 |
| Monitoring + Logging | $200 | $2,400 |
| Backup + DR | $400 | $4,800 |
| **الإجمالي التقريبي** | **$9,400** | **$112,800** |

> 💡 يمكن تخفيض التكلفة 60%+ باستخدام spot instances للـ training و reserved instances للـ production.

---

> آخر تحديث: 2026-08-01
