# Supplementary Materials — Machine Learning Models for Predicting Unplanned Readmission and Mortality in the ICU

**A Systematic Review and Meta-Analysis**

> Fernandez-Curbelo, L.E.; Rivero-Blanco, T.; Cruz Corona, C.; Zwir, I.  
> *Big Data and Cognitive Computing (BDCC)* (submitted, 2026)

---

## Overview

This repository contains the final supplementary materials and extended results that accompany the manuscript:

**"Machine Learning Models for Predicting Unplanned Readmission and Mortality in the ICU: A Systematic Review and Meta-Analysis"**

The review synthesizes evidence from 8 studies (2020–2025) that simultaneously predict unplanned ICU readmission and mortality using machine learning.

### Key findings

| Metric | Value |
|--------|-------|
| Studies included | 8 |
| ML model families evaluated | 17 |
| AUC-ROC metrics reported | 78 |
| AUC-PRC / AP metrics reported | 22 |
| Pooled AUC-ROC (random-effects) | 0.791 (95% CI: 0.775–0.807) |
| Heterogeneity (I²) | 86.5% |
| Databases searched | Scopus, WoS, PubMed, IEEE Xplore |
| Search period | 2020–2025 |

---

## Repository structure

```
├── protocol/
│   └── protocol_study.md            # Study protocol (search strategy, eligibility, analysis plan)
├── data/
│   └── modelos_extraidos.json       # Consolidated performance metrics dataset
├── results/
│   ├── prisma_flow_diagram.md       # PRISMA 2020 flow diagram data
│   ├── study_characteristics.md     # Characteristics of included studies (PRISMA Item 17)
│   ├── risk_of_bias_assessment.md   # PROBAST risk of bias assessment (8 studies × 5 domains)
│   ├── individual_results.md        # Individual study performance metrics
│   ├── forest_plots/
│   │   └── forest_plots_por_modelo_latex.tex  # Forest plots (AUC-ROC + AUC-PRC)
│   └── tables/
│       ├── tabla_detalle_estudios.tex      # AUC-ROC detail (78 metrics)
│       ├── tabla_detalle_estudios_pr.tex   # AUC-PRC detail (22 metrics)
│       ├── tabla_subanalisis_ml.tex        # Subanalysis by ML model (AUC-ROC)
│       └── tabla_subanalisis_pr.tex        # Subanalysis AP vs AUC-PRC
├── supplementary/
│   ├── graphical_abstract.png       # Graphical abstract for the manuscript
│   └── PRISMA_2020_checklist_completed.md # Completed PRISMA 2020 checklist (Items 1–27)
└── references/
    ├── references.bib               # BibTeX bibliography
    └── references.ris               # RIS format for reference managers
```

---

## Data description

### `data/modelos_extraidos.json`

Structured database containing predictive performance metrics used in the supplementary tables and forest plots.

### Results files

- **PRISMA flow diagram**: Identification, screening, eligibility, and inclusion counts.
- **Completed PRISMA checklist**: Mapping of PRISMA 2020 items to manuscript sections.
- **Study characteristics**: Population, setting, sample size, ML models, outcomes, and validation approach.
- **Risk of bias**: PROBAST assessment across 5 domains for all included studies.
- **Individual results**: Per-study performance metrics (AUC-ROC, AUC-PRC, sensitivity, specificity, accuracy, F1-score).

---

## Citation

If you use these materials, please cite:

```bibtex
@article{FernandezCurbelo2026,
  title   = {Machine Learning Models for Predicting Unplanned Readmission and
             Mortality in the ICU: A Systematic Review and Meta-Analysis},
  author  = {Fernandez-Curbelo, Luis E. and Rivero-Blanco, Tania and
             Cruz Corona, Carlos and Zwir, Igor},
  journal = {Big Data and Cognitive Computing},
  year    = {2026},
  note    = {Submitted}
}
```

---

## License

- **Data and documentation**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

## Contact

Luis E. Fernandez-Curbelo — fernandezcurbelo17@gmail.com  
Department of Computer Science and Artificial Intelligence, Universidad de Granada, Spain
