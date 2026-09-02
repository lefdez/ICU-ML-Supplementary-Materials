# Individual Study Results (Item 19)

Summary of predictive-performance metrics reported by each study, **as originally published** (headline value from the study's own abstract or main results).

**Important note:** these as-published headline values may differ from the standardized, prespecified per-study estimate used in the primary meta-analysis (Table S-Rep / Table `tab:detalle_auc`), which applies the same outcome-selection rule across all studies for comparability. Two notable examples: Shickel et al.'s headline AUC (0.929) is the **mean across six Transformer evaluations** (readmission, in-hospital mortality, and mortality at 7/30/90 days and 1 year), whereas the standardized representative estimate used in pooling is the single in-hospital-mortality value for the same architecture (**0.978**) — higher than the mean because the mean is pulled down by the longer, progressively harder horizons. De Hond et al.'s headline AUC (0.79) is the retrained/post-intervention value, whereas the representative estimate used in pooling is the pre-retraining external-validation value (**0.720**), per the study's own baseline/internal selection rule and its documented exception. Neither discrepancy is an error — both tables are correct for their respective purpose (as-published vs. standardized-for-pooling).

| Study | AUC-ROC | PR (AUC-PRC / AP) | Sensitivity | Specificity | Accuracy | F1-Score |
|-------|---------|--------------------|-------------|-------------|----------|----------|
| Dam, Tariq A (2025) | 76.5% ± 1.9% | Not reported | Not reported | Not reported | Not reported | Not reported |
| Sun, Mengxuan (2024) | 0.8941 ± 0.0028 | 0.869 (AUC-PRC) | Not reported | Not reported | Not reported | 0.7625 ± 0.0038 |
| Tschoellitsch, Thomas (2024) | 0.721 ± 0.029 | 0.080 (AP) | Not reported | Not reported | Not reported | Not reported |
| Khodadadi, Atieh (2023) | 0.8690 | 0.619 (AUC-PRC) | Not reported | Not reported | Not reported | Not reported |
| De Hond (2023) | 0.79 (95% CI 0.75–0.82) | Not reported | Not reported | Not reported | Not reported | Not reported |
| Shickel, Benjamin (2022) | 0.929 (Mean across all tasks)* | Not reported | Not reported | Not reported | Not reported | Not reported |
| Thoral, Patrick J (2021) | 0.78 (95% CI, 0.75–0.81) | 0.189 (AUC-PRC) | 0.72 | 0.70 | Not reported | Not reported |
| Curth, Alicia (2020) | 0.800 (0.005) | Not reported | Not reported | Not reported | Not reported | Not reported |

\* Mean AUC-ROC across the six Transformer evaluations reported by Shickel et al. (readmission; in-hospital mortality; and mortality at 7, 30 and 90 days and 1 year). The standardized representative estimate used for this study in the primary meta-analysis is the single in-hospital-mortality value for the same architecture (0.978) — see the note above.

---
*Version for supplementary submission (curated content). Last synchronized with the manuscript's Table `tab:individual` on 2026-09-02.*
