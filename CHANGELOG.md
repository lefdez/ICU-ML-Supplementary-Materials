# Changelog

All notable changes to this repository are documented here. This project accompanies a
manuscript under peer review; this changelog exists so that any reader can see exactly what
changed between releases and why, alongside the immutable git tags for each version.

## [v1.1.0] — 2026-09-02

Synchronization with the post-review correction round applied to the manuscript during peer
review. **This is a fidelity update, not a post-publication revision of new findings**: every
change below reflects a correction already made to, and verified against, the main manuscript
and its own supplementary material in the primary project repository, in response to
methodological review. Nothing in this repository was changed independently of that process.

### Statistical methodology
- The primary AUC-ROC meta-analysis is now pooled on the **logit scale** (previously the raw
  scale), so that confidence and prediction intervals can no longer exceed the mathematically
  admissible bounds of the AUC-ROC (0, 1). Two model-family pooled estimates that previously had
  a 95% CI reaching 1.000 (GRU, GRU + Attention) no longer exist as pooled values — see below.
- **Sun M. et al. (2024)** is now excluded from AUC-ROC pooling (both the primary and
  exploratory analyses): this study's eICU-CRD evaluation cohorts do not report the event counts
  needed to reconstruct a standard error under the Hanley–McNeil sampling-variance formula, and no
  reliable substitute was found to be defensible. Its 10 AUC-ROC estimates are retained and
  reported **descriptively only**. It is *not* excluded from the AUC-PRC synthesis, since that
  pooling method does not depend on event counts.
- The primary analysis now pools **k=7** representative estimates (one per study, Sun M. et al.
  excluded): AUC-ROC = 0.814 (95% CI 0.746–0.868, I² = 98.5%). The exploratory analysis now pools
  **k=68** estimates (down from 78, for the same reason): AUC-ROC = 0.807 (95% CI 0.786–0.826,
  I² = 98.8%).
- Standard errors for Khodadadi et al. and Tschoellitsch et al.'s internal-cohort estimates are
  now corrected for the study's actual evaluation-set size (a 25% train/test split in both cases)
  rather than the full reported cohort size, which previously understated their true sampling
  variance.
- Model-level subgroup pooling (AUC-ROC and AUC-PRC) is now stratified by **outcome**
  (mortality / readmission / composite) rather than combining different outcomes into a single
  pooled number per model. This is the largest structural change to the subgroup tables and
  forest plots (see below) — e.g., Transformer's mortality and readmission estimates are no
  longer mixed into one "0.909" figure; CTCL's two Sun M. et al. estimates are no longer pooled
  into "0.874"; GRU and GRU + Attention are no longer pooled at all (each has only one estimate
  per outcome).
- Egger's test / funnel-plot asymmetry is no longer treated as evidence of publication bias: the
  apparent asymmetry is a mechanical consequence of the Hanley–McNeil formula coupling an AUC
  estimate to its own standard error, not evidence of selective reporting. No downgrade for
  publication bias is applied.

### Documents affected
- `results/tables/tabla_detalle_estudios.tex`: added the standard-error tier column
  (Reported / Hanley–McNeil), added confidence intervals to all rows, and marked Sun M. et al.'s
  10 rows as excluded from pooling (previously presented as ordinary data rows).
- `results/tables/tabla_subanalisis_ml.tex`: rebuilt from a model-only grouping (which mixed
  outcomes in most rows) to the 15 model×outcome strata described above.
- `results/tables/tabla_subanalisis_pr.tex`: Sun M. et al.'s four AUC-PRC model rows (CTCL,
  Transformer, RF, LR) are now split into 8 outcome-level descriptive rows instead of 4 combined
  ("pooled") rows.
- `results/forest_plots/forest_plots_por_modelo_latex.tex`: rebuilt to match the corrected
  forest plots now used in the manuscript's own supplementary material — row labels that
  previously failed to render for some "Sun 2024 / ..." and "Pooled: ..." categories are fixed;
  marker size is now proportional to each estimate's inverse-variance weight within its pooling
  stratum (previously uniform); outcome-mixing pooled diamonds (CTCL, Transformer, GRU,
  GRU + Attention) have been removed; four model sections that were evaluated in the review but
  missing from this file (Ensemble, AdaBoost, Naive Bayes, K-Nearest Neighbors) have been added;
  the global AUC-ROC and AUC-PRC/AP forest plots are rebuilt to the same outcome-stratified
  structure. This file is now in English, matching the manuscript and its own supplementary
  material 1:1 (previously partly in Spanish).
- `results/individual_results.md`: added the PR (AUC-PRC/AP) column and a note clarifying that
  these as-published "headline" values intentionally differ from the standardized
  representative estimates used in pooling (e.g., Shickel et al.: headline 0.929 vs.
  representative 0.978; De Hond et al.: headline 0.790 vs. representative 0.720).
- `results/prisma_flow_diagram.md`: corrected the total records-identified count (4105, not
  4101: 4099 from 4 databases + 6 from other sources), relabeled the databases/other-sources
  split, and corrected "reports assessed for eligibility" to 13 (all 13 sought reports were
  retrieved and assessed; of those, 5 were excluded and 8 included — the previous figure of 8
  conflated "assessed" with "included").
- `references/references.bib`: replaced with the current master bibliography (49 entries, up
  from 44), adding `Deeks2005`, `Koumantakis2025`, `Dhami2025`, `Sun2025NICC`,
  `HanleyMcNeil1982`, and `Higgins2009` — all of which are actively cited in the manuscript.
- `protocol/protocol_study.md`: added a statement on the protocol's registration and public-availability
  timeline (see "Transparency note" below).
- `README.md`: updated the headline pooled-AUC-ROC and heterogeneity figures to the current
  primary/exploratory dual reporting, and added this version history.

### Transparency note: protocol availability timeline
An earlier version of this repository's documentation, and of a paragraph in the manuscript
itself, described this repository's protocol as having been made public before the review was
conducted. On review, that was not precise: this repository (the GitHub release referenced by
the manuscript) was not made public until **2026-05-09**, after the review had been
substantially conducted. The protocol existed in documented form before the manuscript was
drafted, but its *public* availability postdates the review's conduct, and the manuscript and
this repository have both been corrected to say so explicitly rather than imply otherwise. This
does not change the protocol's content — no amendments were made to it relative to the analyses
reported in the manuscript.

### Not changed
- The dataset `data/modelos_extraidos.json` is unchanged (already consistent with the current
  manuscript).
- `results/risk_of_bias_assessment.md` is unchanged (already consistent: 3 low risk, 5 some
  concerns, 0 high risk, matching the manuscript's PROBAST assessment).
- `results/tables/tabla_detalle_estudios_pr.tex` (AUC-PRC study-level detail) is unchanged
  (already consistent — this table was not affected by the AUC-ROC pooling changes).
- `references/references.ris` is unchanged. It was already out of sync with `references.bib`
  before this release and remains so; regenerating it is tracked as a separate, outstanding task
  that also affects the primary manuscript repository and is out of scope for this release.

## [v1.0.0] — 2026-05-09

Initial public release of the supplementary materials repository.
