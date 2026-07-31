# Open Source Integrations — Radiology AI Platform

> المشاريع مفتوحة المصدر المقترحة للتكامل، مرتّبة حسب الأولوية

---

## 1. الـ Decision Matrix

| الأولوية | المشروع | الترخيص | النضج | التوثيق | الحجم |
|---------|--------|--------|------|--------|------|
| 🥇 قصوى | MONAI | Apache 2.0 | ⭐⭐⭐⭐⭐ | ممتاز | كبير |
| 🥇 قصوى | pydicom | MIT | ⭐⭐⭐⭐⭐ | ممتاز | متوسط |
| 🥇 قصوى | RadFM | Apache 2.0 | ⭐⭐⭐ | محدود | كبير |
| 🥇 قصوى | R2Gen | Apache 2.0 | ⭐⭐⭐ | محدود | صغير |
| 🥈 عالية | Highdicom | MIT | ⭐⭐⭐⭐ | جيد | متوسط |
| 🥈 عالية | dcmqi | BSD-3 | ⭐⭐⭐ | جيد | متوسط |
| 🥈 عالية | TorchIO | MIT | ⭐⭐⭐⭐ | ممتاز | متوسط |
| 🥈 عالية | ANTsPy | Apache 2.0 | ⭐⭐⭐⭐ | جيد | كبير |
| 🥉 متوسطة | CheXpert | Research | ⭐⭐⭐ | محدود | dataset |
| 🥉 متوسطة | MIMIC-CXR | PhysioNet | ⭐⭐⭐⭐ | ممتاز | dataset |
| 🥉 متوسطة | PadChest | Research | ⭐⭐⭐ | محدود | dataset |
| 🥉 متوسطة | Orthanc | AGPL | ⭐⭐⭐⭐⭐ | ممتاز | متوسط |

---

## 2. Tier 1 — أولوية قصوى (ابدأ بهذه)

### 2.1 MONAI — Medical Open Network for AI

**الموقع**: [github.com/Project-MONAI/MONAI](https://github.com/Project-MONAI/MONAI)
**الترخيص**: Apache 2.0
**الوظيفة**: إطار PyTorch متخصص للصور الطبية

**ما يوفّره**:
- Transformations مُحسّنة للصور الطبية (3D, 4D)
- Data loaders سريعة
- Loss functions متخصصة (Dice, Focal, Tversky)
- Metrics طبية (Dice, Hausdorff, Surface Distance)
- Network architectures جاهزة (UNet, VNet, AHNet)
- Federated Learning support (MONAI FL)

**الاستخدام في مشروعنا**:
```python
from monai.transforms import Compose, LoadImage, ToTensor, NormalizeIntensity
from monai.networks.nets import UNet

# Preprocessing pipeline
transforms = Compose([
    LoadImage(image_only=True),
    NormalizeIntensity(),
    ToTensor(),
])

# نموذج segmentation
model = UNet(
    spatial_dims=3,
    in_channels=1,
    out_channels=2,
    channels=(16, 32, 64, 128, 256),
    strides=(2, 2, 2, 2),
)
```

**التكامل مع roadmapنا**:
- Phase 1: preprocessing + augmentation
- Phase 2: training R2Gen
- Phase 4: Federated Learning

---

### 2.2 pydicom

**الموقع**: [github.com/pydicom/pydicom](https://github.com/pydicom/pydicom)
**الترخيص**: MIT
**الوظيفة**: قراءة/كتابة/تعديل ملفات DICOM في Python

**ما يوفّره**:
- قراءة جميع Transfer Syntaxes (مع pylibjpeg)
- وصول كامل لكل tags
- تعديل الـ metadata
- كتابة ملفات جديدة
- دعم multiframe و enhanced DICOM

**الاستخدام في مشروعنا**:
- Ingestion service: قراءة الملفات المرفوعة
- De-identification: تعديل الـ tags
- Export: كتابة DICOM SR للتقارير

**مثال**:
```python
import pydicom

ds = pydicom.dcmread("patient.dcm")
print(ds.PatientName)  # "Al-Saleh^Abdulmalek"
print(ds.Modality)     # "CT"
print(ds.pixel_array.shape)  # (512, 512)
```

---

### 2.3 RadFM — Radiology Foundation Model

**الموقع**: [github.com/BoyiLa/RadFM](https://github.com/BoyiLa/RadFM)
**الترخيص**: Apache 2.0
**الورقة**: "Radiology-Llama2: Best-in-Class Large Language Model for Radiology" (2023)
**الوظيفة**: نموذج Vision-Language مُدرّب على بيانات إشعاعية ضخمة

**ما يوفّره**:
- فهم ثنائي الاتجاه (صورة + نص)
- دعم CT و MRI (وليس فقط X-ray)
- قابل لـ fine-tuning على بياناتنا
- 14B parameters (يحتاج GPU كبير)

**المتطلبات**:
- GPU: ≥40GB VRAM (A100 40GB أو أفضل)
- RAM: 64GB+
- التخزين: 100GB للنموذج

**التكامل**:
- Phase 3: استبدال R2Gen بـ RadFM للقدرات المتقدمة
- Fine-tune على بياناتنا العربية

**تحذير**: النموذج كبير — استخدم quantization (4-bit) لو الـ GPU محدود.

---

### 2.4 R2Gen — Report Generation

**الموقع**: [github.com/cuhksz-iccv/R2Gen](https://github.com/cuhksz-iccv/R2Gen)
**الترخيص**: Apache 2.0
**الورقة**: "Generating Radiology Reports via Memory-driven Large Language Model" (MICCAI 2024)
**الوظيفة**: توليد تقارير إشعاعية من صور X-ray

**ما يوفّره**:
- نموذج أصغر من RadFM (أسهل في التدريب)
- جودة جيدة على X-ray الصدر
- كود training + inference جاهز
- Memory-driven generation (يقلل التكرار)

**المتطلبات**:
- GPU: ≥16GB VRAM (V100 أو أفضل)
- RAM: 32GB
- التخزين: 10GB للنموذج

**التكامل**:
- Phase 2: النموذج الأولي الأول
- نهج "ابدأ صغيراً ثم توسّع"

---

## 3. Tier 2 — أولوية عالية

### 3.1 Highdicom

**الموقع**: [github.com/herrmannlab/highdicom](https://github.com/herrmannlab/highdicom)
**الترخيص**: MIT
**الوظيفة**: إنشاء DICOM Structured Reports (SR) و segmentation objects

**الاستخدام**:
- إنتاج تقارير بصيغة DICOM SR قابلة للتبادل مع PACS
- إنشاء segmentation masks كـ DICOM SEG objects
- توحيد الـ codes (SNOMED, LOINC)

**مثال**:
```python
import highdicom as hd
from pydicom.uid import generate_uid

# إنشاء SR
content = hd.sr.CodeContentItem(
    name=hd.sr.CodedConcept("121071", "SCT", "Finding"),
    value=hd.sr.CodedConcept("17621005", "SCT", "Normal"),
)
sr_document = hd.sr.ComprehensiveSR(
    series_instance_uid=generate_uid(),
    sop_instance_uid=generate_uid(),
    series_number=1,
    instance_number=1,
    content=[content],
)
```

---

### 3.2 dcmqi

**الموقع**: [github.com/QIICR/dcmqi](https://github.com/QIICR/dcmqi)
**الترخيص**: BSD-3
**الوظيفة**: تحويل بين DICOM SR/SEG وصيغ أخرى (JSON, NRRD)

**الاستخدام**:
- تحويل segmentation masks من NIfTI إلى DICOM SEG
- استخراج measurements بصيغة JSON من DICOM SR
- التوافق مع Quantitative Imaging (QIICR)

---

### 3.3 TorchIO

**الموقع**: [github.com/fepegar/torchio](https://github.com/fepegar/torchio)
**الترخيص**: MIT
**الوظيفة**: Augmentation للصور الطبية 3D

**ما يوفّره**:
- 30+ transforms مُحسّنة للصور الطبية
- دعم 4D (وقت + 3D)
- Adaptive sampling للـ patches
- Integration مع PyTorch Lightning

**مثال**:
```python
import torchio as tio

transform = tio.Compose([
    tio.RandomAffine(degrees=10, translation=5),
    tio.RandomFlip(axes=('LR',), p=0.5),  # NOT for chest!
    tio.RandomBiasField(p=0.5),
    tio.RandomNoise(p=0.5),
    tio.RescaleIntensity((-1, 1)),
])
```

---

### 3.4 ANTsPy

**الموقع**: [github.com/ANTsX/ANTsPy](https://github.com/ANTsX/ANTsPy)
**الترخيص**: Apache 2.0
**الوظيفة**: تسجيل الصور الطبية (Image Registration)

**الاستخدام**:
- مواءمة صور المريض عبر الزمن (longitudinal studies)
- تسجيل صور المريض إلى atlas مرجعي
- مقارنة بين دراسات مختلفة

**تحذير**: بطيء على CPU — استخدم GPU أو قلّل الـ resolution.

---

## 4. Tier 3 — أولوية متوسطة (Datasets)

### 4.1 MIMIC-CXR

**الموقع**: [physionet.org/content/mimic-cxr](https://physionet.org/content/mimic-cxr/2.0.0/)
**الترخيص**: PhysioNet Credentialed Health Data License
**الحجم**: 377,110 صورة + 227,835 تقرير

**الوصول**:
1. إنشاء حساب على PhysioNet
2. إكمال CITI Data training
3. طلب الوصول لـ MIMIC-CXR
4. انتظار الموافقة (عادة 1-2 أسبوع)

**الاستخدام**:
- Pre-training لنموذج الـ report generation
- تعلّم أنماط التقارير الإنجليزية
- نقل المعرفة (transfer learning) للعربية

---

### 4.2 CheXpert

**الموقع**: [stanfordmlgroup.github.io/competitions/chexpert](https://stanfordmlgroup.github.io/competitions/chexpert/)
**الترخيص**: Stanford Research Use Agreement
**الحجم**: 224,316 صورة + 14 labels

**الاستخدام**:
- Pre-trained classifier لـ 14 مرض رئوي شائع
- يمكن استخدامه كـ vision encoder للـ report generator
- Benchmark للمقارنة

---

### 4.3 PadChest

**الموقع**: [bimcv.cipf.es/bimcv-projects/padchest](https://bimcv.cipf.es/bimcv-projects/padchest/)
**الترخيص**: Research Use
**الحجم**: 160,868 صورة + تقارير بالإسبانية
**الميزة**: تقارير بإسبانية (لغة لاتينية) — مفيدة لتعلّم النقل للعربية

---

### 4.4 CT-RATE

**الموقع**: [github.com/bowang-lab/CT-RATE](https://github.com/bowang-lab/CT-RATE)
**الترخيص**: CC BY-NC 4.0
**الحجم**: 1,763 دراسة CT للصدر (3D)
**الميزة**: بيانات 3D (وليس 2D فقط)

---

## 5. Tier 4 — البنية التحتية

### 5.1 Orthanc — PACS Server

**الموقع**: [orthanc-server.com](https://orthanc.uclouvain.be/)
**الترخيص**: AGPL (متوفر كـ Docker image)
**الوظيفة**: PACS server مفتوح المصدر

**ما يوفّره**:
- تخزين DICOM + استرجاع
- دعم DICOM Web (STOW, WADO, QIDO)
- دعم DICOM Network (C-STORE, C-FIND, C-MOVE)
- Plugins: PostgreSQL, MySQL, S3, Azure Blob
- REST API كامل
- Python plugin لـ scripting

**التكامل**: service رئيسي في `docker-compose.yml`

---

### 5.2 Milvus — Vector Database

**الموقع**: [github.com/milvus-io/milvus](https://github.com/milvus-io/milvus)
**الترخيص**: Apache 2.0
**الوظيفة**: قاعدة بيانات متجهية للبحث الدلالي

**الاستخدام**:
- تخزين embeddings للتقارير
- البحث "أوجد التقارير المشابهة لهذا"
- Retrieval-Augmented Generation (RAG) للنموذج

---

### 5.3 MinIO — Object Storage

**الموقع**: [github.com/minio/minio](https://github.com/minio/minio)
**الترخيص**: AGPLv3
**الوظيفة**: S3-compatible object storage

**الاستخدام**:
- تخزين الصور الكبيرة (وليس في PostgreSQL)
- Versioning للنماذج
- Lifecycle policies للـ archival

---

### 5.4 Flower — Federated Learning

**الموقع**: [github.com/adap/flower](https://github.com/adap/flower)
**الترخيص**: Apache 2.0
**الوظيفة**: إطار Federated Learning

**الاستخدام** (Phase 4):
- تدريب موزّع على مستشفيات متعددة دون نقل البيانات
- دعم PyTorch + MONAI
- Differential Privacy integration

---

## 6. Tier 5 — لمستقبل بعيد

### 6.1 OHIF Viewer

**الموقع**: [github.com/OHIF/Viewer](https://github.com/OHIF/Viewer)
**الترخيص**: MIT
**الوظيفة**: واجهة ويب قوية لعرض الصور الطبية

**متى نستخدمه**: عند الحاجة لميزات متقدمة (3D rendering, MPR, fusion) لا يوفرها Cornerstone.js مباشرة.

---

### 6.2 Cornerstone3D

**الموقع**: [github.com/cornerstonejs/cornerstone3D](https://github.com/cornerstonejs/cornerstone3D)
**الترخيص**: MIT
**الوظيفة**: مكتبة JavaScript لعرض DICOM

**متى نستخدمه**: مدمج في واجهتنا من البداية (أخف من OHIF).

---

### 6.3 dcm4che

**الموقع**: [github.com/dcm4che/dcm4che](https://github.com/dcm4che/dcm4che)
**الترخيص**: Apache 2.0
**الوظيفة**: بديل لـ Orthanc (Java)

**متى نستخدمه**: إذا احتجنا ميزات لا يدعمها Orthanc (مثل archive tiers).

---

## 7. الـ Decision Log

لماذا اخترنا X ولم نختر Y؟

### Q: لماذا Orthanc وليس dcm4che؟
**A**: 
- Orthanc أبسط وأخف
- Python plugin يسهّل الـ scripting
- Docker image رسمي مدعوم
- AGPL يلائم مشروعنا مفتوح المصدر

### Q: لماذا R2Gen قبل RadFM؟
**A**:
- R2Gen أصغر وأسرع في التدريب
- نختبر الفكرة قبل الاستثمار الكبير
- رضا الأطباء أهم من حجم النموذج

### Q: لماذا Milvus وليس Weaviate؟
**A**:
- Milvus أسرع على الـ scale الكبير
- دعم GPU indexing
- مجتمع أكبر في الـ medical AI

### Q: لماذا Flower وليس Tensorflow Federated؟
**A**:
- Flower مستقل عن الـ framework (يعمل مع PyTorch)
- أبسط في الإعداد
- يدعم Differential Privacy

---

## 8. المتابعة (Monitoring)

### كل 3 أشهر
- [ ] مراجعة releases جديدة لكل مشاريع Tier 1 و Tier 2
- [ ] تقييم مشاريع جديدة ظهرت في الـ community
- [ ] تحديث هذا المستند

### كل سنة
- [ ] إعادة تقييم كل الاختيارات (قد يظهر بديل أفضل)
- [ ] مراجعة التراخيص (قد تتغير)
- [ ] تحديث الـ Decision Log

---

## 9. الـ References

- [MONAI Consortium](https://monai.io/)
- [Medical Imaging Community on GitHub](https://github.com/topics/medical-imaging)
- [MICCAI Society](https://miccai.org/)
- [Society for Imaging Informatics in Medicine](https://siim.org/)

---

> آخر تحديث: 2026-08-01
