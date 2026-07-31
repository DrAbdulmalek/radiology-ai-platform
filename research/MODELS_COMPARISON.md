# Models Comparison — Vision-Language Models for Radiology

> مقارنة شاملة للنماذج المتاحة لتوليد التقارير الإشعاعية

---

## 1. الـ Summary Table

| Model | السنة | الحجم | VRAM | الـ Modalities | العربية | الـ License |
|-------|------|------|------|---------------|--------|-----------|
| **R2Gen** | 2020 | ~250MB | 8GB+ | X-ray | ❌ | Apache 2.0 |
| **R2GenCMN** | 2022 | ~280MB | 8GB+ | X-ray | ❌ | Apache 2.0 |
| **RadFM** | 2023 | ~14GB | 40GB+ | CT, MR, X-ray | ❌ | Apache 2.0 |
| **Med-PaLM M** | 2023 | ~550B | متعدد GPUs | CT, MR, X-ray, Derm | ❌ | Closed |
| **LLaVA-Med** | 2024 | ~13GB | 40GB+ | Multi-modal | ❌ | Apache 2.0 |
| **CheXbert** | 2020 | ~440MB | 8GB+ | X-ray (classifier) | ❌ | MIT |
| **Jais** | 2023 | 13B | 30GB+ | Text only | ✅ | Apache 2.0 |
| **AceGPT** | 2023 | 13B | 30GB+ | Text only | ✅ | Apache 2.0 |

---

## 2. R2Gen — Recursive Neural Network for Report Generation

**الورقة**: "Generating Radiology Reports via Memory-driven Large Language Model" (EMNLP 2020)
**الموقع**: [github.com/cuhksz-iccv/R2Gen](https://github.com/cuhksz-iccv/R2Gen)
**الترخيص**: Apache 2.0

### المميزات
- ✅ أبسط نموذج للبدء به
- ✅ متطلبات GPU معقولة (V100 16GB)
- ✅ كود training و inference جاهز
- ✅ أداء جيد على X-ray الصدر
- ✅ سريع في الـ inference (~1-3 ثوان لكل دراسة)

### العيوب
- ❌ يدعم X-ray فقط (لا CT أو MRI)
- ❌ التقارير بالإنجليزية فقط
- ❌ الـ architecture قديمة نسبياً (2020)
- ❌ لا يدعم visual grounding

### الأداء (على IU X-Ray dataset)
| Metric | Score |
|--------|-------|
| BLEU-1 | 0.470 |
| BLEU-2 | 0.304 |
| BLEU-3 | 0.219 |
| BLEU-4 | 0.165 |
| CIDEr | 0.353 |
| ROUGE-L | 0.371 |

### الحجم والمتطلبات
- **Model size**: ~250MB
- **VRAM للتدريب**: 8GB (batch_size=8)
- **VRAM لـ inference**: 4GB
- **زمن التدريب**: ~12 ساعة على V100 (على IU X-Ray)

### متى نستخدمه؟
- ✅ Phase 2: النموذج الأولي الأول
- ✅ عندما تكون البيانات X-ray فقط
- ✅ عندما تكون موارد GPU محدودة

---

## 3. R2GenCMN — Cross-modal Memory Networks

**الورقة**: "Cross-modal Memory Networks for Radiology Report Generation" (ACL 2022)
**الموقع**: [github.com/cuhksz-iccv/R2GenCMN](https://github.com/cuhksz-iccv/R2GenCMN)

### الفرق عن R2Gen
- إضافة cross-modal memory
- أداء أفضل قليلاً على BLEU-4 (+0.01)
- حجم أكبر قليلاً (~280MB)

### الأداء
| Metric | R2Gen | R2GenCMN |
|--------|-------|----------|
| BLEU-4 | 0.165 | 0.176 |
| CIDEr | 0.353 | 0.372 |

### متى نستخدمه؟
- بديل عن R2Gen إذا احتجنا دقة أعلى قليلاً
- لا يزال يدعم X-ray فقط

---

## 4. RadFM — Radiology Foundation Model

**الورقة**: "Radiology-Llama2: Best-in-Class Large Language Model for Radiology" (2023)
**الموقع**: [github.com/BoyiLa/RadFM](https://github.com/BoyiLa/RadFM)
**الترخيص**: Apache 2.0

### المميزات
- ✅ يدعم CT و MRI (وليس فقط X-ray)
- ✅ قادر على الإجابة عن أسئلة طبية
- ✅ Fine-tunable على بياناتنا
- ✅ مبني على LLaMA-2 (قوي)

### العيوب
- ❌ حجم ضخم (~14GB)
- ❌ يحتاج A100 40GB على الأقل للتدريب
- ❌ الـ inference بطيء بدون GPU قوي
- ❌ التقارير بالإنجليزية فقط
- ❌ لا يدعم visual grounding مباشرة

### المتطلبات
- **GPU للتدريب**: 4x A100 40GB (أو 2x A100 80GB)
- **VRAM لـ inference**: 40GB (أو 20GB مع 4-bit quantization)
- **RAM**: 64GB+
- **التخزين**: 100GB للنموذج + datasets

### متى نستخدمه؟
- ✅ Phase 3: عند الحاجة لدعم CT/MRI
- ✅ عندما تكون موارد GPU متوفرة
- ✅ بعد إثبات جدوى المشروع في Phase 2

---

## 5. LLaVA-Med

**الورقة**: "LLaVA-Med: Training a Large Language-and-Vision Assistant for Biomedicine in One Day" (2024)
**الموقع**: [github.com/microsoft/LLaVA-Med](https://github.com/microsoft/LLaVA-Med)
**الترخيص**: Apache 2.0

### المميزات
- ✅ مبني على LLaVA (قاعدة قوية)
- ✅ يدعم أنواع متعددة من الصور الطبية
- ✅ يمكن تخصيصه للإشعاعية
- ✅ Microsoft-supported

### العيوب
- ❌ ليس متخصصاً للإشعاع (general medical)
- ❌ حجم كبير (~13GB)
- ❌ الـ inference يحتاج GPU

### متى نستخدمه؟
- بديل عن RadFM إذا أردنا دعم أوسع (وليس فقط إشعاع)
- مفيد للـ "second opinion" على نتائج متعددة

---

## 6. CheXbert — Report Labeling

**الورقة**: "CheXbert: Automating Chest X-ray Interpretation with Deep Learning" (2020)
**الموقع**: [github.com/stanfordmlgroup/chexpert-labeler](https://github.com/stanfordmlgroup/chexpert-labeler)

### الوظيفة المختلفة
CheXbert ليس مولّداً للتقارير — بل **مُصنّفاً**:
- يأخذ تقريراً نصياً
- يُرجع 14 labels ثنائية (Atelectasis, Cardiomegaly, Consolidation, Edema, ...)

### الاستخدام في مشروعنا
- **تقييم التقارير المُولّدة**: مقارنة labels من النص المُولّد مع labels من النص المرجعي
- **مراقبة جودة النموذج**: إذا اختلف الـ labels كثيراً، النموذج يفشل
- **تدريب RLHF**: الـ labels كـ reward signal

### المميزات
- ✅ سريع جداً (CPU كافٍ)
- ✅ دقة عالية على التقارير الإنجليزية
- ✅ مفيد للـ evaluation

### العيوب
- ❌ التقارير الإنجليزية فقط
- ❌ يحتاج تعديل للعربية (أو translation pipeline)

---

## 7. النماذج العربية (Arabic LLMs)

### Jais
**الموقع**: [github.com/inceptionai/jais](https://github.com/inceptionai/jais)
- 13B parameters
- مُدرّب على نصوص عربية كثيرة
- Apache 2.0
- متاح على HuggingFace: `inceptionai/jais-13b`

### AceGPT
**الموقع**: [github.com/FreedomIntelligence/AceGPT](https://github.com/FreedomIntelligence/AceGPT)
- 13B parameters (مبني على LLaMA-2)
- مُحسّن للهجات الخليجية
- Apache 2.0

### الاستراتيجية المقترحة
1. **Phase 1-3**: استخدام R2Gen/RadFM بالإنجليزية
2. **Phase 4**: 
   - توليد التقرير بالإنجليزية
   - ترجمة عالية الجودة إلى العربية (بواسطة طبيب)
   - Fine-tune Jais على أزواج (إنجليزي، عربي)
3. **Phase 5** (مستقبلي): تدريب نموذج vision-language عربي من الصفر

---

## 8. Hardware Requirements Summary

### Minimum (Development)
```
GPU: NVIDIA RTX 3090 (24GB) — $1500
RAM: 64GB DDR4 — $200
Storage: 2TB NVMe — $200
Total: ~$1900
```

### Recommended (Phase 2 — Training R2Gen)
```
GPU: NVIDIA A100 40GB — $10,000 (or rent on AWS: $3/hour)
RAM: 128GB DDR4 — $400
Storage: 4TB NVMe — $400
Total: ~$10,800 (or $3/hour cloud)
```

### Production (Phase 3+ — RadFM)
```
GPU: 2x NVIDIA A100 80GB — $40,000
RAM: 256GB DDR5 — $1000
Storage: 10TB NVMe + 50TB HDD — $1500
Total: ~$42,500
```

### Cloud Alternatives
| Provider | GPU | Price/hour |
|----------|-----|-----------|
| AWS p4d.24xlarge | 8x A100 40GB | $32.77 |
| AWS p3.2xlarge | 1x V100 16GB | $3.06 |
| GCP a2-highgpu-1g | 1x A100 40GB | $3.67 |
| Azure NDm A100 v4 | 1x A100 80GB | $3.40 |
| RunPod A100 80GB | 1x A100 80GB | $1.89 |
| Lambda Labs A100 | 1x A100 40GB | $1.29 |

---

## 9. Evaluation Metrics

### NLG Metrics (Natural Language Generation)

| Metric | الوصف | الجيد |
|--------|------|------|
| **BLEU-1** | unigram precision | >0.40 |
| **BLEU-4** | 4-gram precision with brevity penalty | >0.15 |
| **CIDEr** | Consensus-based image description evaluation | >0.30 |
| **ROUGE-L** | Longest common subsequence | >0.30 |
| **METEOR** | F-score with synonyms | >0.20 |

### Clinical Metrics

| Metric | الوصف | الجيد |
|--------|------|------|
| **CheXbert F1** | F1 على 14 labels | >0.85 |
| **CE (Clinical Efficacy)** | Micro/Macro F1 | >0.80 |
| **BERTScore** | Semantic similarity | >0.85 |
| **Green Score** | Semantic + clinical (recent) | >0.70 |

### Human Evaluation

| المعيار | السؤال |
|--------|------|
| **Fluency** | "هل التقرير مكتوب بشكل سليم؟" (1-5) |
| **Correctness** | "هل النتائج دقيقة؟" (1-5) |
| **Completeness** | "هل التقرير شامل؟" (1-5) |
| **Usefulness** | "هل يفيد الطبيب سريرياً؟" (1-5) |

---

## 10. القرارات النهائية

### Phase 2 (Q1 2027)
- ✅ **R2Gen** كنموذج أولي
- ✅ **CheXbert** للـ evaluation

### Phase 3 (Q2 2027)
- ✅ **RadFM** كنموذج رئيسي (مع fine-tuning)
- ✅ **CheXbert** للـ continuous evaluation

### Phase 4 (Q3-Q4 2027)
- ✅ **Jais** أو **AceGPT** للنصوص العربية
- ✅ **Pipeline**: RadFM (English) → Translate → Jais (polish Arabic)

### Phase 5 (مستقبلي)
- ✅ تدريب نموذج vision-language عربي من الصفر
- ✅ يعتمد على نجاح Phase 4 + توفّر بيانات عربية كافية

---

## 11. الـ References

### Papers
1. R2Gen: [arxiv.org/abs/2006.11313](https://arxiv.org/abs/2006.11313)
2. R2GenCMN: [arxiv.org/abs/2204.10108](https://arxiv.org/abs/2204.10108)
3. RadFM: [arxiv.org/abs/2308.02463](https://arxiv.org/abs/2308.02463)
4. LLaVA-Med: [arxiv.org/abs/2306.00890](https://arxiv.org/abs/2306.00890)
5. CheXbert: [arxiv.org/abs/2004.12223](https://arxiv.org/abs/2004.12223)
6. Jais: [arxiv.org/abs/2308.09288](https://arxiv.org/abs/2308.09288)

### Surveys
- "A Survey of Deep Learning-Based Radiology Report Generation" (2024)
- "Vision-Language Models in Medical Imaging: A Comprehensive Survey" (2024)

### Benchmarks
- [IU X-Ray](https://openi.nlm.nih.gov/) — 7,470 images + 3,955 reports
- [MIMIC-CXR](https://physionet.org/content/mimic-cxr/) — 377,110 images + 227,835 reports
- [CheXpert](https://stanfordmlgroup.github.io/competitions/chexpert/) — 224,316 images

---

> آخر تحديث: 2026-08-01
