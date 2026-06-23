# Supplementary Materials — Machine Learning Models for Predicting Unplanned Readmission and Mortality in the ICU

**A Systematic Review and Meta-Analysis**

> Fernandez-Curbelo, L.E.; Rivero-Blanco, T.; Cruz Corona, C.; Zwir, I.  
> *Big Data and Cognitive Computing (BDCC)* (submitted, 2026)

---

## Overview

This repository contains the supplementary materials, extracted data, analysis scripts, and extended results for the systematic review and meta-analysis titled:

**"Machine Learning Models for Predicting Unplanned Readmission and Mortality in the ICU: A Systematic Review and Meta-Analysis"**

The review synthesizes evidence from 8 studies (2020–2025) that simultaneously predict unplanned ICU readmission and mortality using machine learning. The meta-analysis includes 78 AUC-ROC metrics across 17 ML model families and 22 precision–recall metrics from 4 studies.

### Key findings

| Metric | Value |
|--------|-------|
| Studies included | 8 |
| ML model families evaluated | 17 |
| AUC-ROC metrics extracted | 78 |
| AUC-PRC / AP metrics extracted | 22 |
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
│   └── modelos_extraidos.json       # Structured extraction: 78 AUC-ROC + 22 AUC-PRC metrics
├── analysis/
│   ├── extraer_modelos_auto.py      # Automated metric extraction from study PDFs
│   ├── generar_forest_latex.py      # Forest plot generation (LaTeX/pgfplots)
│   ├── generar_forest_por_modelo.py # Model-specific forest plots
│   ├── generar_tabla_latex.py       # Summary tables generation
│   ├── metadata_muestras.py        # Sample metadata & outcome aggregation
│   ├── pipeline_resumen_ml.py      # Main analysis orchestration pipeline
│   └── generate_graphical_abstract.py # Graphical abstract (matplotlib)
├── results/
│   ├── prisma_flow_diagram.md       # PRISMA 2020 flow diagram data
│   ├── study_characteristics.md     # Characteristics of included studies (PRISMA Item 17)
│   ├── risk_of_bias_assessment.md   # PROBAST risk of bias assessment (8 studies × 5 domains)
│   ├── individual_results.md        # Individual study performance metrics
│   ├── forest_plots/
│   │   └── forest_plots_por_modelo_latex.tex  # All forest plots (AUC-ROC + AUC-PRC)
│   └── tables/
│       ├── tabla_detalle_estudios.tex      # AUC-ROC detail (78 metrics)
│       ├── tabla_detalle_estudios_pr.tex   # AUC-PRC detail (22 metrics)
│       ├── tabla_subanalisis_ml.tex        # Subanalysis by ML model (AUC-ROC)
│       └── tabla_subanalisis_pr.tex        # Subanalysis AP vs AUC-PRC
├── supplementary/
│   └── graphical_abstract.png       # Graphical abstract for the manuscript
│   └── PRISMA_2020_checklist_completed.md # Completed PRISMA 2020 checklist (Items 1-27)
└── references/
    ├── references.bib               # BibTeX bibliography (60+ references)
    └── references.ris               # RIS format for reference managers
```

---

## Data description

### `data/modelos_extraidos.json`

Structured JSON database containing all extracted predictive performance metrics:

- **78 AUC-ROC entries**: study, model name, model family, predictive task (readmission / mortality / composite), validation type (internal / external / cross-validation), AUC-ROC value, confidence interval (when reported), sample size, event counts.
- **22 AUC-PRC / AP entries**: same structure, separated by metric family (AUC-PRC vs. Average Precision).

### Results files

- **PRISMA flow diagram**: Full identification → screening → eligibility → inclusion counts.
- **Completed PRISMA checklist**: Explicit mapping of PRISMA 2020 items to the final manuscript sections.
- **Study characteristics**: Population, setting, sample size, ML models, outcomes, validation approach for each of the 8 studies.
- **Risk of bias**: PROBAST assessment across 5 domains (participants, predictors, outcome, analysis, overall) for all 8 studies.
- **Individual results**: Per-study performance metrics including AUC-ROC, AUC-PRC, sensitivity, specificity, accuracy, F1-Score.

---

## Reproducing the analysis

### Requirements

- Python 3.9+
- LaTeX distribution (TeX Live or MiKTeX) with `pgfplots` package
- Python packages: `matplotlib`, `numpy`

### Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/lefdez/ICU-ML-Supplementary-Materials.git
   cd ICU-ML-Supplementary-Materials
   ```

2. Generate forest plots and tables:
   ```bash
   python analysis/generar_forest_por_modelo.py
   python analysis/generar_tabla_latex.py
   ```

3. Compile forest plots to PDF:
   ```bash
   pdflatex results/forest_plots/forest_plots_por_modelo_latex.tex
   ```

4. Generate graphical abstract:
   ```bash
   pip install matplotlib numpy
   python analysis/generate_graphical_abstract.py
   ```

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
- **Code/scripts**: [MIT License](LICENSE)

---

## Contact

Luis E. Fernandez-Curbelo — fernandezcurbelo17@gmail.com  
Department of Computer Science and Artificial Intelligence, Universidad de Granada, Spain
