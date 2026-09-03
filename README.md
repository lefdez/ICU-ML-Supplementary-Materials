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
| AUC-ROC metrics reported | 78 (68 pooled + 10 descriptive, see below) |
| AUC-PRC / AP metrics reported | 22 |
| Pooled AUC-ROC, primary analysis (k=7, one representative estimate per study, logit-scale random-effects) | 0.814 (95% CI: 0.746–0.868) |
| Heterogeneity (I²), primary analysis | 98.5% |
| Pooled AUC-ROC, exploratory analysis (k=68, all extracted estimates, non-independent) | 0.807 (95% CI: 0.786–0.826) |
| Heterogeneity (I²), exploratory analysis | 98.8% |
| Databases searched | Scopus, WoS, PubMed, IEEE Xplore |
| Search period | 2020–2025 |

**Note on Sun M. et al. (2024):** this study's 10 AUC-ROC estimates are excluded from both
pooled analyses above because it does not report the event counts needed to reconstruct a
standard error, and is reported descriptively only (see `results/tables/study_detail_table.tex`).
It does contribute to the AUC-PRC synthesis, since that pooling method does not depend on
event counts — see `results/tables/pr_subgroup_table.tex` for details, including why its
AUC-PRC values should not be compared at face value to the other studies'.

---

## Repository structure

```
├── protocol/
│   └── protocol_study.md            # Study protocol (search strategy, eligibility, analysis plan)
├── data/
│   └── extracted_models.json        # Consolidated performance metrics dataset
├── results/
│   ├── prisma_flow_diagram.md       # PRISMA 2020 flow diagram data
│   ├── study_characteristics.md     # Characteristics of included studies (PRISMA Item 17)
│   ├── risk_of_bias_assessment.md   # PROBAST risk of bias assessment (8 studies × 5 domains)
│   ├── individual_results.md        # Individual study performance metrics
│   ├── forest_plots/
│   │   └── forest_plots_by_model.tex       # Forest plots (AUC-ROC + AUC-PRC)
│   └── tables/
│       ├── study_detail_table.tex          # AUC-ROC detail (78 metrics)
│       ├── study_detail_table_pr.tex       # AUC-PRC detail (22 metrics)
│       ├── model_subgroup_table.tex        # Subanalysis by ML model (AUC-ROC)
│       └── pr_subgroup_table.tex           # Subanalysis AP vs AUC-PRC
├── supplementary/
│   ├── graphical_abstract.png       # Graphical abstract for the manuscript
│   └── PRISMA_2020_checklist_completed.md # Completed PRISMA 2020 checklist (Items 1–27)
└── references/
    ├── references.bib               # BibTeX bibliography
    └── references.ris               # RIS format for reference managers
```

---

## Data description

### `data/extracted_models.json`

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

## Version History

- **v1.4.0** (2026-09-02): Corrected `graphical_abstract.png`, which had never been updated
  after the statistical correction round in either this repository or the primary manuscript
  repository — replaced the stale pooled AUC-ROC, model-architecture, and precision-recall
  panels with current values, and confirmed the PRISMA checklist is not affected. See
  [`CHANGELOG.md`](CHANGELOG.md) for details.
- **v1.3.0** (2026-09-02): Bibliography sync addressing two reference-hygiene issues raised by
  the journal editor (an AdaBoost background citation swapped for one without a correction
  record; an erratum citation added for an included study; a PMID added for a DOI that was
  wrongly flagged as broken). See [`CHANGELOG.md`](CHANGELOG.md) for details.
- **v1.2.0** (2026-09-02): Full-English-language pass (protocol, extracted-data field names and
  values, and all four results tables translated; six Spanish-named files renamed) and a
  public-release copyright/readiness review. See [`CHANGELOG.md`](CHANGELOG.md) for details.
- **v1.1.0** (2026-09-02): Synchronized with the post-review correction round applied to the
  manuscript (logit-scale pooling, exclusion of Sun M. et al. from AUC-ROC pooling,
  outcome-stratified subgroup analyses, corrected forest plots, updated bibliography). See
  [`CHANGELOG.md`](CHANGELOG.md) for the full list of changes and their rationale.
- **[v1.0.0](https://github.com/lefdez/ICU-ML-Supplementary-Materials/releases/tag/v1.0.0)** (2026-05-09): Initial public release, prior to the correction round above.

---

## Contact

Luis E. Fernandez-Curbelo — fernandezcurbelo17@gmail.com  
Department of Computer Science and Artificial Intelligence, Universidad de Granada, Spain
