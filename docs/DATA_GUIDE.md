# Data Guide — DICOM & Medical Imaging

> دليل شامل للتعامل مع ملفات DICOM، المعالجة المسبقة، وهيكل التقارير

---

## 1. ما هو DICOM؟

**DICOM** (Digital Imaging and Communications in Medicine) هو المعيار الدولي لتخزين ونقل الصور الطبية. أي صورة طبية (CT, MRI, X-ray, Ultrasound, Mammography) تُخزَّن بصيغة `.dcm` تحتوي على:

1. **Pixel Data**: الصورة الفعلية (2D أو 3D)
2. **Metadata**: معلومات المريض، الجهاز، الإعدادات
3. **Optional overlays**: رسمات فوق الصورة (arrow, ROI)

### لماذا ليس JPG؟
| الخاصية | JPG | DICOM |
|--------|-----|-------|
| عمق البكسل | 8-bit | 12-16 bit |
| Metadata | EXIF (محدود) | 1000+ tag |
| 3D support | ❌ | ✅ (multi-frame) |
| قياسات دقيقة | ❌ | ✅ (PixelSpacing) |
| معلومات المريض | ❌ | ✅ |

---

## 2. هيكل DICOM Tag

كل معلومة في DICOM تُمثَّل بـ tag:

```
(Group, Element)  VR  VM  Value
(0010, 0010)      PN  1   "Abdulmalek^Al-Saleh"
```

- **Group**: (4 hex digits) — فئة المعلومة (0010 = patient)
- **Element**: (4 hex digits) — الحقل المحدد (0010 = name)
- **VR** (Value Representation): نوع البيانات (PN = Person Name, DA = Date, LO = Long String)
- **VM** (Value Multiplicity): عدد القيم (1 = single, 1-n = array)
- **Value**: القيمة الفعلية

### الـ Tags الأكثر استخداماً

| Tag | Name | VR | مثال |
|-----|------|----|----|
| (0010,0010) | PatientName | PN | "Al-Saleh^Abdulmalek" |
| (0010,0020) | PatientID | LO | "MRN12345" |
| (0010,0030) | PatientBirthDate | DA | "19850315" |
| (0010,0040) | PatientSex | CS | "M" / "F" / "O" |
| (0008,0020) | StudyDate | DA | "20260801" |
| (0008,0030) | StudyTime | TM | "143022.500000" |
| (0008,0060) | Modality | CS | "CT" / "MR" / "XR" |
| (0008,0070) | Manufacturer | LO | "Siemens" / "GE" / "Philips" |
| (0008,1030) | StudyDescription | LO | "CT Brain w/o contrast" |
| (0008,103E) | SeriesDescription | LO | "Axial 5mm" |
| (0020,000D) | StudyInstanceUID | UI | "1.2.840.113619..." |
| (0020,000E) | SeriesInstanceUID | UI | "1.2.840.113619.2.1..." |
| (0008,0018) | SOPInstanceUID | UI | "1.2.840.113619.2.1.1..." |
| (0028,0010) | Rows | US | 512 |
| (0028,0011) | Columns | US | 512 |
| (0028,0030) | PixelSpacing | DS | "0.5\0.5" |
| (0018,0050) | SliceThickness | DS | "5.0" |
| (0028,1050) | WindowCenter | DS | "40" |
| (0028,1051) | WindowWidth | DS | "400" |

---

## 3. Modalities المدعومة

| Code | الاسم | الأبعاد | استخدام شائع |
|------|------|--------|------------|
| **CT** | Computed Tomography | 3D | الدماغ، الصدر، البطن |
| **MR** | Magnetic Resonance | 3D/4D | الدماغ، المفاصل، العمود الفقري |
| **CR** | Computed Radiography | 2D | X-ray تقليدي |
| **DX** | Digital Radiography | 2D | X-ray رقمي |
| **MG** | Mammography | 2D | الثدي |
| **US** | Ultrasound | 2D/3D | البطن، النساء |
| **XA** | X-Ray Angiography | 2D | الأوعية |
| **PT** | PET | 3D | الأورام |
| **NM** | Nuclear Medicine | 2D/3D | القلب، الغدد |

---

## 4. المعالجة المسبقة (Preprocessing)

### 4.1 Windowing (Window/Level)

صور CT تحتوي قيم Hounsfield من -1000 (هواء) إلى +3000 (معدن). لا يمكن عرضها مباشرة على شاشة عادية (8-bit). الحل: **windowing**.

```python
import numpy as np

def apply_window(image: np.ndarray, center: int, width: int) -> np.ndarray:
    """Apply window/level to a CT slice."""
    min_val = center - width // 2
    max_val = center + width // 2
    windowed = np.clip(image, min_val, max_val)
    windowed = ((windowed - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    return windowed
```

#### نوافذ شائعة (Common Windows)

| النافذة | Center | Width | الاستخدام |
|--------|--------|-------|---------|
| Brain | 40 | 80 | أنسجة الدماغ |
| Lung | -600 | 1500 | الرئة |
| Bone | 400 | 1800 | العظام |
| Soft Tissue | 40 | 400 | الأنسجة الرخوة (البطن) |
| Mediastinum | 50 | 350 | المنصف |

### 4.2 Resampling

الصور قد تكون بأبعاد بكسل مختلفة (anisotropic). يجب توحيدها قبل التدريب.

```python
import SimpleITK as sitk

def resample_image(image: sitk.Image, new_spacing: tuple = (1.0, 1.0, 1.0)) -> sitk.Image:
    """Resample to isotropic 1mm spacing."""
    original_spacing = image.GetSpacing()
    original_size = image.GetSize()
    new_size = [
        int(round(osz * ospc / nspc))
        for osz, ospc, nspc in zip(original_size, original_spacing, new_spacing)
    ]
    resampler = sitk.ResampleImageFilter()
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetSize(new_size)
    resampler.SetInterpolator(sitk.sitkLinear)
    return resampler.Execute(image)
```

### 4.3 Normalization

```python
def normalize_hu(image: np.ndarray) -> np.ndarray:
    """Normalize HU values to [0, 1] for ML models."""
    image = (image - (-1000)) / (3000 - (-1000))
    return np.clip(image, 0, 1)
```

### 4.4 Augmentation (للتدريب)

استخدم **MONAI** أو **TorchIO** للـ augmentation المخصص للصور الطبية:

```python
from monai.transforms import (
    Compose, RandRotate90, RandFlip, RandZoom, RandShiftIntensity
)

train_transforms = Compose([
    RandRotate90(prob=0.5, spatial_axes=(0, 1)),
    RandFlip(prob=0.5, spatial_axis=0),
    RandFlip(prob=0.5, spatial_axis=1),
    RandZoom(min_zoom=0.9, max_zoom=1.1, prob=0.3),
    RandShiftIntensity(offsets=0.1, prob=0.5),
])
```

**تحذير**: لا تستخدم `RandomHorizontalFlip` على صور الصدر — القلب يكون دائماً على اليسار!

---

## 5. هيكل التقارير الإشعاعية

### 5.1 الأقسام القياسية (Standard Sections)

التقرير الإشعاعي الاحترافي يحتوي على:

1. **Examination** (النوع): "CT Brain without contrast"
2. **Clinical Indication** (السبب): "Headache, rule out mass"
3. **Technique** (الطريقة): "Axial 5mm slices, 120 kVp, 250 mAs"
4. **Comparison** (المقارنة): "Compared to previous study from 2025-01-15"
5. **Findings** (النتائج): وصف تفصيلي لما رُؤي
6. **Impression** (الخلاصة): التشخيص التفريقي + التوصيات

### 5.2 مثال على تقرير إنجليزي

```
EXAMINATION: CT Brain without contrast
CLINICAL INDICATION: 45-year-old male with sudden severe headache.
TECHNIQUE: Axial 5mm slices were obtained from the skull base to the
vertex without intravenous contrast administration.
COMPARISON: None.
FINDINGS:
The brain demonstrates normal parenchymal attenuation. No acute
intracranial hemorrhage or extra-axial fluid collection is identified.
The ventricular system is normal in size and configuration. The basal
cisterns are patent. No mass effect or midline shift.
The skull vault and skull base are intact.
IMPRESSION:
No acute intracranial abnormality.
```

### 5.3 مثال على تقرير عربي

```
الفحص: تصوير مقطعي للدماغ بدون صبغة
الاستطباب السريري: مريض 45 سنة يعاني من صداع شديد مفاجئ.
الطريقة: تم الحصول على شرائح محورية بسماكة 5 مم من قاعدة الجمجمة
إلى القمة دون إعطاء صبغة وريدية.
المقارنة: لا يوجد.
النتائج:
يُظهر الدماغ كثافة طبيعية في النسيج الدماغي. لا يوجد نزيف
داخل القحف حاد أو تجمع سوائل خارج المحور. الجهاز البطني
بحجم وتشكل طبيعيين. الأهداب القاعدية مفتوحة. لا يوجد تأثير
كتلي أو انحراف عن الخط المتوسط.
قبوة الجمجمة وقاعدتها سليمتان.
الخلاصة:
لا يوجد اعتلال داخل القحف حاد.
```

### 5.4 Structured Reporting (DICOM SR)

للتبادل مع أنظمة PACS/HIS، يجب إنتاج تقارير بصيغة **DICOM Structured Report (SR)**:

```python
import highdicom as hd
from pydicom.uid import generate_uid

# إنشاء تقرير SR
sr = hd.sr.ComprehensiveSR(
    series_instance_uid=generate_uid(),
    series_number=1,
    sop_instance_uid=generate_uid(),
    instance_number=1,
    institution_name="Radiology AI Platform",
    observational_characteristics=True,
)

# إضافة findings
finding = hd.sr.TextContentItem(
    name=hd.sr.CodedConcept("121071", "SCT", "Finding"),
    value="No acute intracranial abnormality"
)
```

---

## 6. DICOM Web Protocols

للتفاعل مع Orthanc وغيره من PACS servers:

| Protocol | الوصف | HTTP Method |
|----------|------|------------|
| **STOW-RS** | Store Over Web (رفع) | POST `/dicom-web/studies` |
| **WADO-RS** | Web Access to DICOM Objects (تنزيل) | GET `/dicom-web/studies/{study}` |
| **QIDO-RS** | Query Based on ID for DICOM Objects (بحث) | GET `/dicom-web/studies?PatientID=123` |
| **C-STORE** | DICOM Network (legacy) | TCP port 104 |
| **C-FIND** | DICOM Query (legacy) | TCP port 104 |
| **C-MOVE** | DICOM Retrieve (legacy) | TCP port 104 |

### مثال: رفع ملف عبر STOW-RS

```bash
curl -X POST "http://orthanc:8042/dicom-web/studies" \
  -H "Content-Type: multipart/related; type=application/dicom" \
  -H "Authorization: Bearer $TOKEN" \
  --data-binary @patient.dcm
```

---

## 7. الـ Storage Strategy

### 7.1 التسلسل الهرمي للمجلدات

```
data/
├── raw/                          # ملفات DICOM الأصلية (محمية)
│   ├── 2026/
│   │   ├── 08/
│   │   │   ├── 01/
│   │   │   │   ├── study_abc123/
│   │   │   │   │   ├── 1.dcm
│   │   │   │   │   ├── 2.dcm
│   │   │   │   │   └── ...
│   │   │   │   └── study_def456/
│   │   │   └── 02/
│   │   └── 09/
├── deidentified/                 # ملفات بعد إخفاء الهوية
│   └── (نفس الهيكل)
├── reports/                      # التقارير المُولّدة + المُراجَعة
│   ├── generated/                # نص خام من النموذج
│   ├── reviewed/                 # بعد المراجعة البشرية
│   └── final/                    # بعد الاعتماد النهائي
├── metadata/                     # metadata مستخرجة (JSON)
└── checksums/                    # SHA-256 checksums للتحقق
```

### 7.2 التسمية

```python
# بعد إخفاء الهوية، الملفات تُسمّى بـ hash
filename = f"{hash_value(study_uid)}_{series_number}_{instance_number}.dcm"
# مثال: a1b2c3d4e5f6_3_45.dcm
```

### 7.3 الـ Checksums

```python
import hashlib

def compute_checksum(file_path: Path) -> str:
    """SHA-256 checksum for integrity verification."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
```

---

## 8. أدوات مفيدة

### 8.1 Command-line Tools

| الأداة | الوظيفة | التثبيت |
|--------|--------|---------|
| `dcmtk` | مجموعة شاملة (dcmdump, storescp, etc.) | `apt install dcmtk` |
| `dcm2niix` | تحويل DICOM إلى NIfTI | `apt install dcm2niix` |
| `dciodvfy` | التحقق من توافق DICOM | download من DCMTK |
| `gdcmanon` | إخفاء هوية DICOM | `apt install gdcm` |

### 8.2 Python Libraries

```python
# القراءة الأساسية
import pydicom
ds = pydicom.dcmread("patient.dcm")
pixel_array = ds.pixel_array  # numpy array

# الكتابة المتقدمة (SR)
import highdicom as hd

# معالجة الصور
import SimpleITK as sitk
import monai

# الـ Augmentation
import torchio as tio
```

### 8.3 Viewers

| الـ Viewer | النوع | الاستخدام |
|-----------|------|---------|
| **OHIF Viewer** | Web | الأقوى، مفتوح المصدر |
| **Cornerstone.js** | Web Library | للتضمين في تطبيقاتنا |
| **3D Slicer** | Desktop | للأبحاث |
| **Horos** | Mac (Desktop) | للأطباء |
| **MicroDICOM** | Windows (Desktop) | للأطباء |

---

## 9. التحديات الشائعة

### 9.1 DICOM Transfer Syntax

ملفات DICOM قد تكون:
- **Uncompressed** (Explicit VR Little Endian) — سهلة
- **JPEG Lossless** — تحتاج decoder خاص
- **JPEG 2000** — تحتاج OpenJPEG
- **RLE Lossless** — نادر لكن مدمج

```python
# تثبيت decoders
# pip install pylibjpeg pylibjpeg-openjpeg pylibjpeg-libjpeg

# القراءة (pydicom يتعامل معها تلقائياً إذا كانت المكتبات مثبتة)
ds = pydicom.dcmread("compressed.dcm")
pixel_array = ds.pixel_array  # numpy array بعد فك الضغط
```

### 9.2 الـ Multiframe DICOM

بعض الصور (مثل Echo) تحتوي عدة إطارات في ملف واحد:

```python
ds = pydicom.dcmread("echo.dcm")
print(ds.NumberOfFrames)  # مثلاً: 30
# pixel_array.shape = (30, 512, 512)
```

### 9.3 الـ Enhanced DICOM

التنسيق الحديث يدعم:
- عدسة ديناميكية (Dynamic Contrast)
- 4D (وقت + 3D)
- Per-frame functional groups

تحتاج `pydicom` ≥ 2.3 + فهم لـ `PerFrameFunctionalGroupsSequence`.

---

## 10. الـ References

- [DICOM Standard Browser](https://dicom.innolitics.com/)
- [pydicom Documentation](https://pydicom.github.io/)
- [MONAI Tutorials](https://github.com/Project-MONAI/tutorials)
- [Highdicom Documentation](https://highdicom.readthedocs.io/)
- [DICOM Library](https://www.dicomlibrary.com/) — لفحص ملفات DICOM online

---

> آخر تحديث: 2026-08-01
