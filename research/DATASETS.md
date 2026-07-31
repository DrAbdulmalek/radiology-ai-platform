# Datasets — Medical Imaging Datasets for Training

> قائمة شاملة بالـ datasets العامة والبروتوكول المتبع للبيانات الخاصة

---

## 1. الـ Datasets العامة (Public)

### 1.1 MIMIC-CXR

**الموقع**: [physionet.org/content/mimic-cxr](https://physionet.org/content/mimic-cxr/2.0.0/)
**الحجم**: 377,110 صورة + 227,835 تقرير
**النوع**: X-ray صدر
**اللغة**: إنجليزية
**الترخيص**: PhysioNet Credentialed Health Data License

#### المحتوى
- 65,379 مريض فريد
- 227,835 دراسة
- 377,110 صورة (frontal + lateral)
- تقارير سريرية حقيقية (radiologist-signed)

#### الـ Labels (CheXpert labeler)
14 مرض:
1. Atelectasis
2. Cardiomegaly
3. Consolidation
4. Edema
5. Enlarged Cardiomediastinum
6. Fracture
7. Lung Lesion
8. Lung Opacity
9. No Finding
10. Pleural Effusion
11. Pleural Other
12. Pneumonia
13. Pneumothorax
14. Support Devices

#### الوصول
1. إنشاء حساب على [PhysioNet](https://physionet.org/)
2. إكمال **CITI Data or Specimens Only Research** training
3. طلب الوصول لـ MIMIC-CXR v2.0.0
4. انتظار الموافقة (1-2 أسبوع)
5. تحميل البيانات عبر `wget` أو `gsutil`

#### التكامل مع مشروعنا
- **Pre-training** للنموذج (تعليم النموذج أنماط التقارير الإنجليزية)
- **Evaluation** على test set بعد fine-tuning على بياناتنا
- **Transfer learning** إلى بياناتنا العربية

---

### 1.2 CheXpert

**الموقع**: [stanfordmlgroup.github.io/competitions/chexpert](https://stanfordmlgroup.github.io/competitions/chexpert/)
**الحجم**: 224,316 صورة
**النوع**: X-ray صدر
**اللغة**: إنجليزية
**الترخيص**: Stanford Research Use Agreement

#### المحتوى
- 65,240 مريض
- 14 labels (نفس MIMIC-CXR)
- تقسيم رسمي: train (191,229), validation (1,766), test (no labels)

#### الاستخدام
- **Pre-trained classifier** (vision encoder)
- **Benchmark** للمقارنة
- **CheXpert labeler** كأداة لتقييم التقارير

---

### 1.3 PadChest

**الموقع**: [bimcv.cipf.es/bimcv-projects/padchest](https://bimcv.cipf.es/bimcv-projects/padchest/)
**الحجم**: 160,868 صورة + 109,931 تقرير
**النوع**: X-ray صدر
**اللغة**: إسبانية
**الترخيص**: Research Use

#### المميزات الفريدة
- ✅ التقارير بالإسبانية (لغة لاتينية، قريبة من العربية في التركيب)
- ✅ 174 مختلف finding labels
- ✅ تقارير موسّعة (8 جمل في المتوسط)

#### الاستراتيجية للعربية
- استخدام PadChest لـ pre-training على لغة لاتينية مختلفة
- ثم fine-tune على بيانات عربية
- "Bridge" بين الإنجليزية والعربية عبر الإسبانية

---

### 1.4 CT-RATE

**الموقع**: [github.com/bowang-lab/CT-RATE](https://github.com/bowang-lab/CT-RATE)
**الحجم**: 1,763 دراسة CT (3D)
**النوع**: CT صدر
**اللغة**: إنجليزية (findings فقط)
**الترخيص**: CC BY-NC 4.0

#### المحتوى
- 1,763 دراسة CT للصدر (3D volumes)
- 1,259 مريض فريد
- 65 findings مختلفة
- تقسيم رسمي: train (1,253), validation (297), test (213)

#### الاستخدام
- ✅ بيانات 3D (نادر في الـ datasets العامة)
- ✅ مناسب لتدريب RadFM على CT

---

### 1.5 IU X-Ray (Open-I)

**الموقع**: [openi.nlm.nih.gov](https://openi.nlm.nih.gov/)
**الحجم**: 7,470 صورة + 3,955 تقرير
**النوع**: X-ray متعدد
**اللغة**: إنجليزية
**الترخيص**: Open Access

#### الاستخدام
- ✅ Small dataset مناسب للـ prototyping
- ✅ المعيار القياسي للـ benchmarks في الـ papers
- ✅ سريع التحميل والتدريب

---

### 1.6 BraTS — Brain Tumor Segmentation

**الموقع**: [braintumorsegmentation.org](https://www.med.upenn.edu/cbica/brats2023/)
**الحجم**: ~1,250 دراسة MRI للدماغ
**النوع**: MRI (4 modalities: T1, T1c, T2, FLAIR)
**الترخيص**: Research Use

#### الاستخدام
- تدريب نماذج segmentation (وليس report generation)
- ✅ مناسب للتوسع المستقبلي نحو brain MRI analysis

---

### 1.7 مجموعات أخرى مفيدة

| Dataset | النوع | الحجم | الرابط |
|---------|------|------|--------|
| **NIH ChestX-ray14** | X-ray | 112,120 | [nihcc.app.box.com](https://nihcc.app.box.com/v/ChestXray-NIHCC) |
| **VinDr-CXR** | X-ray | 18,000 | [github.com/vinbigdata-medical/vindr-cxr](https://github.com/vinbigdata-medical/vindr-cxr) |
| **RSNA Pneumonia** | X-ray | 30,000 | [kaggle.com/c/rsna-pneumonia-detection-challenge](https://www.kaggle.com/c/rsna-pneumonia-detection-challenge) |
| **COVID-19 Radiography** | X-ray | 21,165 | [kaggle.com/tawsifurrahman/covid19-radiography-database](https://www.kaggle.com/tawsifurrahman/covid19-radiography-database) |
| **DeepLesion** | CT | 32,735 | [github.com/MASILab/DeepLesion](https://github.com/MASILab/DeepLesion) |
| **MedMNIST** | Mixed | 708,069 | [medmnist.com](https://medmnist.com/) |

---

## 2. الـ Datasets الخاصة (Private — عبر المستشفى الشريك)

### 2.1 البروتوكول

```
┌─────────────────────────────────────────────────────┐
│ المستشفى الشريك (Hospital Partner)                  │
│                                                      │
│ 1. موافقة أخلاقية (IRB Approval)                    │
│    ↓                                                 │
│ 2. Data Sharing Agreement (DSA) موقّع                │
│    ↓                                                 │
│ 3. استخراج البيانات من PACS                          │
│    (by hospital IT, NOT by us)                       │
│    ↓                                                 │
│ 4. De-identification داخل المستشفى                   │
│    (using our scripts, run by hospital)              │
│    ↓                                                 │
│ 5. نقل آمن (SFTP or encrypted drive)                 │
│    ↓                                                 │
│ 6. استلام البيانات في بيئة آمنة                      │
│    (air-gapped or dedicated cloud VPC)               │
│    ↓                                                 │
│ 7. تدقيق نهائي للـ de-identification                 │
│    ↓                                                 │
│ 8. بدء التدريب                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 متطلبات الـ Datasets الخاصة

#### الكمية (Volume)
| المرحلة | الحد الأدنى | الموصى به |
|--------|----------|----------|
| Phase 2 (Prototype) | 500 زوج | 1,000+ زوج |
| Phase 3 (Pilot) | 2,000 زوج | 5,000+ زوج |
| Phase 4 (Production) | 10,000 زوج | 50,000+ زوج |

#### التنوع (Diversity)
- ✅ ≥3 modalities (CT, MRI, X-ray)
- ✅ ≥5 body parts (Chest, Brain, Abdomen, MSK, Spine)
- ✅ ≥3 أجهزة مختلفة (Siemens, GE, Philips)
- ✅ ≥2 مستشفيات مختلفة (للـ federated learning)

#### الجودة (Quality)
- ✅ تقارير مُعتمدة من استشاري إشعاعي (وليس مقيم)
- ✅ صور بدقة ≥512x512
- ✅ لا توجد صور مكررة أو ناقصة
- ✅ metadata كاملة (Modality, BodyPart, StudyDescription)

---

### 2.3 الـ IRB Approval (Institutional Review Board)

#### ما هو IRB؟
لجنة أخلاقية في المستشفى تُراجع أي بحث ي involves بيانات مرضى.

#### الخطوات
1. **تقديم بروتوكول البحث** (Research Protocol)
   - الهدف من البحث
   - البيانات المطلوبة
   - تدابير حماية الخصوصية
   - خطة النشر (هل سيتم نشر نتائج؟)
2. **مراجعة IRB** (4-8 أسابيع)
3. **الموافقة** أو **طلب تعديلات**
4. **تجديد سنوي** (إن استمر البحث)

#### النقاط الحرجة في البروتوكول
- ✅ "ستُستخدم البيانات لتطوير نموذج ذكاء اصطناعي يُولّد تقارير إشعاعية مساعدة"
- ✅ "ستُخفى هوية جميع البيانات قبل الاستخدام وفق DICOM PS3.15"
- ✅ "لن تُنشر أي بيانات فردية — فقط نتائج مجمّعة"
- ✅ "ستُخزّن البيانات في بيئة معزولة ومشفّرة"
- ✅ "سيتم تدمير البيانات بعد انتهاء البحث (أو حسب اتفاقية)"

---

### 2.4 الـ Data Sharing Agreement (DSA)

بنود أساسية:

```
1. الأطراف (المستشفى + الباحث)
2. الغرض من استخدام البيانات
3. حجم ونوع البيانات
4. مدة الاحتفاظ بالبيانات
5. الإجراءات الأمنية المطلوبة
6. حقوق الملكية الفكرية للنماذج المُدرّبة
7. حقوق النشر (publications)
8. الإنهاء المبكر والاسترجاع
9. المسؤولية القانونية
10. القانون المُحكِّم (Saudi, UAE, etc.)
```

---

## 3. Pre-processing Pipeline للبيانات الخاصة

```python
"""
Pipeline مُقترح لمعالجة البيانات الخاصة قبل التدريب.
"""

import json
import shutil
from pathlib import Path

import pydicom

from scripts.dicom_deidentify import deidentify_dicom


def preprocess_private_data(
    input_dir: Path,
    output_dir: Path,
    reports_csv: Path,
    audit_file: Path
):
    """
    1. استقبال DICOM + reports CSV من المستشفى
    2. De-identification لكل ملف DICOM
    3. ربط التقارير بالصور عبر StudyInstanceUID
    4. حفظ في هيكل train/val/test
    """

    # 1. قراءة التقارير
    reports = {}
    with open(reports_csv) as f:
        for row in csv.DictReader(f):
            study_uid = row["study_instance_uid"]
            reports[hash_value(study_uid)] = {
                "report_text": row["report"],
                "modality": row["modality"],
                "body_part": row["body_part"],
            }

    # 2. معالجة كل ملف DICOM
    all_data = []
    for dcm_file in input_dir.rglob("*.dcm"):
        # De-identify
        log = deidentify_dicom(dcm_file, output_dir / "images", date_shift=-365)
        all_data.append(log)

    # 3. ربط الصور بالتقارير
    pairs = []
    for entry in all_data:
        study_hash = entry["study_hash"]
        if study_hash in reports:
            pairs.append({
                "image_path": entry["output_file"],
                "report": reports[study_hash]["report_text"],
                "modality": reports[study_hash]["modality"],
                "body_part": reports[study_hash]["body_part"],
            })

    # 4. تقسيم train/val/test (70/15/15)
    import random
    random.seed(42)
    random.shuffle(pairs)

    n = len(pairs)
    train = pairs[: int(0.7 * n)]
    val = pairs[int(0.7 * n) : int(0.85 * n)]
    test = pairs[int(0.85 * n) :]

    # 5. حفظ
    for split, data in [("train", train), ("val", val), ("test", test)]:
        out_file = output_dir / f"{split}.json"
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # 6. Audit log
    audit_file.write_text(json.dumps(all_data, indent=2, ensure_ascii=False))

    print(f"✅ Processed {n} pairs: train={len(train)}, val={len(val)}, test={len(test)}")
```

---

## 4. الـ Quality Control

### 4.1 فحوصات تلقائية

```python
def quality_check(dataset_dir: Path) -> dict:
    """فحص جودة الـ dataset قبل التدريب."""
    report = {
        "total_studies": 0,
        "issues": [],
        "stats": {
            "modalities": {},
            "body_parts": {},
            "manufacturers": {},
        }
    }

    for json_file in ["train.json", "val.json", "test.json"]:
        data = json.loads((dataset_dir / json_file).read_text())
        for item in data:
            report["total_studies"] += 1

            # تحقق من وجود الصورة
            if not Path(item["image_path"]).exists():
                report["issues"].append(f"Missing image: {item['image_path']}")
                continue

            # تحقق من DICOM
            try:
                ds = pydicom.dcmread(item["image_path"])
                modality = getattr(ds, "Modality", "Unknown")
                body_part = getattr(ds, "BodyPartExamined", "Unknown")
                manufacturer = getattr(ds, "Manufacturer", "Unknown")

                report["stats"]["modalities"][modality] = \
                    report["stats"]["modalities"].get(modality, 0) + 1
                report["stats"]["body_parts"][body_part] = \
                    report["stats"]["body_parts"].get(body_part, 0) + 1
                report["stats"]["manufacturers"][manufacturer] = \
                    report["stats"]["manufacturers"].get(manufacturer, 0) + 1
            except Exception as e:
                report["issues"].append(f"DICOM read error: {e}")

            # تحقق من التقرير
            if len(item["report"]) < 50:
                report["issues"].append(f"Short report: {item['image_path']}")

    return report
```

### 4.2 فحوصات بشرية
- عينة عشوائية (5%) يفحصها طبيب إشعاعي
- التحقق من:
  - مطابقة الصورة للتقرير
  - عدم وجود بيانات شخصية متبقية
  - جودة الصورة (لا تكون شديدة التشويش)

---

## 5. الـ Data Augmentation

### 5.1 الآمن للصور الطبية

| Transform | آمن؟ | ملاحظات |
|-----------|------|--------|
| Random Rotation (±10°) | ✅ | للـ X-ray (وليس CT/MRI) |
| Random Flip (LR) | ⚠️ | فقط للـ chest (القلب على اليسار!) |
| Random Flip (UD) | ❌ | غير طبيعي طبياً |
| Random Crop | ✅ | مع الحفاظ على الـ center |
| Random Zoom (0.9-1.1) | ✅ | لمحاكاة أجهزة مختلفة |
| Intensity Shift | ✅ | صغير فقط (±0.1) |
| Gaussian Noise | ✅ | لمحاكاة sensor noise |
| Random Bias Field | ✅ | لـ MRI |
| Elastic Deformation | ❌ | يغير التشريح |

### 5.2 أمثلة (MONAI)

```python
from monai.transforms import (
    Compose, RandRotate, RandZoom, RandShiftIntensity,
    RandGaussianNoise, RandBiasField
)

safe_transforms = Compose([
    RandRotate(range_x=0.17, prob=0.5),  # ±10°
    RandZoom(min_zoom=0.9, max_zoom=1.1, prob=0.3),
    RandShiftIntensity(offsets=0.1, prob=0.5),
    RandGaussianNoise(prob=0.2, mean=0, std=0.01),
])

# لـ MRI فقط
mri_transforms = Compose([
    safe_transforms,
    RandBiasField(prob=0.5),
])
```

---

## 6. الـ Bias والـ Fairness

### 6.1 أنواع الـ Bias في الـ Medical AI

| Bias | السبب | الحل |
|------|------|-----|
| **Selection Bias** | بيانات من مستشفى واحد فقط | متعدد المستشفيات |
| **Demographic Bias** | عدم تنوع عمر/جنس/عرق | فحص الـ distribution |
| **Equipment Bias** | أجهزة من شركة واحدة | متعدد الـ manufacturers |
| **Label Bias** | تقارير بأسلوب طبيب واحد | متعدد الأطباء |
| **Length Bias** | تقارير قصيرة جداً أو طويلة جداً | فلترة |

### 6.2 Fairness Metrics

لكل مجموعة (age, sex, etc.):
- **Demographic Parity**: نسبة التقارير المُعتمدة متساوية عبر المجموعات
- **Equal Opportunity**: نسبة الـ true positives متساوية
- **Disparate Impact**: ratio < 0.8 يعني bias

---

## 7. الـ References

### Datasets Catalogs
- [PhysioNet](https://physionet.org/) — MIT-LCP
- [The Cancer Imaging Archive (TCIA)](https://www.cancerimagingarchive.net/)
- [Medical Imaging Datasets on GitHub](https://github.com/sfikas/medical-imaging-datasets)

### Papers on Dataset Bias
- "Fairness in Medical AI: A Review" (2024)
- "Demographic Bias in Chest X-ray Datasets" (2023)

### Tools
- [MONAI Data Loading](https://docs.monai.io/en/stable/data.html)
- [TorchIO Datasets](https://torchio.readthedocs.io/datasets.html)

---

> آخر تحديث: 2026-08-01
