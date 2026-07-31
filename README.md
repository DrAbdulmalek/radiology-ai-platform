# Radiology AI Platform

> منصة ذكاء اصطناعي لتوليد التقارير الإشعاعية بالعربية — من صورة DICOM إلى تقرير سريري احترافي

[![Status](https://img.shields.io/badge/Status-Planning-yellow)](docs/ROADMAP.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)
[![Security](https://img.shields.io/badge/Security-HIPAA%20%7C%20GDPR%20%7C%20PDPL-red)](docs/SECURITY.md)
[![DICOM](https://img.shields.io/badge/DICOM-3.0-blue)](docs/DATA_GUIDE.md)

---

## 🎯 الرؤية

بناء منصة ذكاء اصطناعي متكاملة تقبل صوراً طبية بتنسيق DICOM (CT, MRI, X-ray, Ultrasound) وتُولّد تقارير إشعاعية احترافية باللغة العربية، مع نظام مراجعة بشرية (HITL) لضمان الدقة السريرية.

المنصة مُصمّمة لتكون **مساعدة (Assistive)** وليست بديلة عن الطبيب الإشعاعي — كل تقرير مُولّد يحتاج اعتماداً طبياً قبل الاستخدام السريري.

---

## ⚠️ حالة المشروع

```
الحالة: 📋 التخطيط والتصميم (Planning Phase)
التاريخ المتوقع للبدء الفعلي: Q4 2026 - Q1 2027
المنتج القابل للعرض: غير متوقع قبل 6-12 شهراً من بدء التطوير
```

هذا المستودع **حالياً يحتوي على**:
- ✅ وثائق التصميم التقني الكاملة
- ✅ مقارنة النماذج والـ Datasets المتاحة
- ✅ خطة تنفيذ مرحلية مفصّلة
- ✅ سكربتات أولية (De-identification, Setup)
- ✅ قواعد الأمان والخصوصية
- ⏳ لا يوجد كود تطبيقي بعد (سيُضاف عند بدء التطوير)

---

## 📋 المحتويات

| القسم | الوصف |
|------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | البنية التقنية الكاملة (Diagram + Components + Data Flow) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | خطة التنفيذ من Q4 2026 إلى Q4 2027 |
| [docs/SECURITY.md](docs/SECURITY.md) | HIPAA, GDPR, PDPL + DICOM De-identification |
| [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) | دليل DICOM + Windowing + Preprocessing |
| [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) | المشاريع مفتوحة المصدر المقترحة (5 Tiers) |
| [docs/API_SPEC.md](docs/API_SPEC.md) | مواصفات REST API المستقبلية |
| [research/MODELS_COMPARISON.md](research/MODELS_COMPARISON.md) | مقارنة RadFM / R2Gen / Med-PaLM / CheXbert |
| [research/DATASETS.md](research/DATASETS.md) | Datasets عامة + بروتوكول البيانات الخاصة |
| [setup/docker-compose.yml](setup/docker-compose.yml) | Orthanc + PostgreSQL + MinIO + Milvus + Redis |
| [scripts/dicom_deidentify.py](scripts/dicom_deidentify.py) | سكربت إخفاء هوية DICOM (PS3.15 compliant) |

---

## 🏗️ البنية عالية المستوى

```
┌────────────────────────────────────────────────────────────────┐
│                   Radiology AI Platform                         │
├────────────────────────────────────────────────────────────────┤
│  DICOM Ingestion → Image Preprocessing → Report Generation     │
│      (pydicom)       (MONAI)          (RadFM / R2Gen)          │
│                          │                                      │
│                          ▼                                      │
│              De-identification Engine                           │
│        (PHI removal + metadata anonymization)                  │
│                          │                                      │
│                          ▼                                      │
│              Training Pipeline (Federated)                      │
│        (Vision-Language Pretraining + SFT + RLHF)              │
│                          │                                      │
│                          ▼                                      │
│              Report Review & Validation                         │
│         (HITL + Confidence Scoring + Audit Trail)              │
└────────────────────────────────────────────────────────────────┘
```

للتفاصيل الكاملة: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔗 العلاقة مع المستودعات الأخرى

| المستودع | العلاقة |
|---------|--------|
| [`omni-medical-suite`](https://github.com/DrAbdulmalek/omni-medical-suite) | المنصة الأم — OCR للمستندات الطبية المكتوبة |
| [`intelli-file-manager`](https://github.com/DrAbdulmalek/intelli-file-manager) | مدير الملفات الذكي — سيُضاف إليه دعم DICOM viewer |
| [`dictionaries-csv`](https://github.com/DrAbdulmalek/dictionaries-csv) | القواميس الطبية — ستُستخدم للتحقق من المصطلحات في التقارير المُولّدة |
| [`telegram-tools`](https://github.com/DrAbdulmalek/telegram-tools) | أدوات Telegram — للإشعارات أثناء التدريب |

---

## 🚀 البدء السريع (عند بدء التطوير)

### المتطلبات
- Docker 24+ و Docker Compose v2
- Python 3.11+
- GPU NVIDIA مع CUDA 12+ (للتدريب)
- 100GB+ مساحة فارغة (للبيانات والنماذج)

### الإعداد
```bash
# 1. استنساخ المستودع
git clone https://github.com/DrAbdulmalek/radiology-ai-platform.git
cd radiology-ai-platform

# 2. تشغيل سكربت الإعداد
chmod +x scripts/setup_repo.sh
./scripts/setup_repo.sh

# 3. تعديل .env بكلمات مرور قوية
nano .env

# 4. اختبار إخفاء هوية DICOM
python scripts/dicom_deidentify.py \
  --input examples/ \
  --output data/deidentified/ \
  --date-shift -365
```

### الخدمات المتاحة بعد الإعداد
- **Orthanc PACS**: http://localhost:8042
- **MinIO Console**: http://localhost:9001
- **FastAPI Docs**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 🛡️ التحذيرات القانونية

> ⚠️ **هذا المشروع مساعد طبي (Assistive AI)، وليس أداة تشخيصية مستقلة.**
>
> كل تقرير مُولّد بالذكاء الاصطناعي **يجب أن يُراجع ويعتمد من طبيب إشعاعي مرخّص** قبل أي استخدام سريري.
>
> لا تُخزّن ملفات DICOM الحقيقية في Git. لا تُدرّب النماذج على بيانات مرضى بدون موافقة أخلاقية (IRB). لا تُعلن أن النظام "يُشخّص" — هذا يفتح مسؤولية قانونية.

للتفاصيل الكاملة: [docs/SECURITY.md](docs/SECURITY.md)

---

## 📊 المشاريع مفتوحة المصدر المعتمدة

| الأولوية | المشروع | الوظيفة |
|---------|---------|---------|
| 🥇 قصوى | [MONAI](https://github.com/Project-MONAI/MONAI) | إطار PyTorch للصور الطبية |
| 🥇 قصوى | [pydicom](https://github.com/pydicom/pydicom) | قراءة/كتابة DICOM |
| 🥇 قصوى | [RadFM](https://github.com/BoyiLa/RadFM) | نموذج Vision-Language للأشعة |
| 🥇 قصوى | [R2Gen](https://github.com/cuhksz-iccv/R2Gen) | توليد تقارير إشعاعية |
| 🥈 عالية | [Highdicom](https://github.com/herrmannlab/highdicom) | DICOM Structured Reports |
| 🥈 عالية | [TorchIO](https://github.com/fepegar/torchio) | Augmentation للصور 3D |
| 🥉 متوسطة | [CheXpert](https://stanfordmlgroup.github.io/competitions/chexpert/) | Dataset + نموذج X-ray |

للقائمة الكاملة: [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)

---

## 📜 الترخيص

[Apache License 2.0](LICENSE) — Copyright 2026 DrAbdulmalek

---

## 📞 التواصل

- **GitHub Issues**: للأسئلة التقنية والـ bugs
- **Email**: للتعاون الأكاديمي أو السريري

---

> آخر تحديث: 2026-08-01 — الحالة: تخطيط وتصميم
