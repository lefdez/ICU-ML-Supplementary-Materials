# Changelog

All notable changes to this repository are documented here. This project accompanies a
manuscript under peer review; this changelog exists so that any reader can see exactly what
changed between releases and why, alongside the immutable git tags for each version.

## [v1.5.0] — 2026-09-04

Forest-plot legibility fix in `results/forest_plots/forest_plots_by_model.tex`, mirroring an
identical, same-day correction applied to the manuscript's own supplementary material
(`supplementary_material_bdcc.tex`, primary manuscript repository) after a reader-reported
legibility issue.

- The 29 individual per-model forest plots (Section 2, "Individual AUC-ROC Forest Plots by
  Model," and the equivalent Precision–Recall section) were rendered at `scale=0.6` — small
  enough that axis and per-study row labels were hard to read, and in several figures the
  longest row labels (e.g., "Tschoellitsch 2024 / Comp. (ext.)") were being clipped at the
  page's right margin once enlarged, because a portrait page has no room left once such a
  label is legible. Both figures are now rendered at native scale (`scale=1.0`, ≈67% larger
  than before) inside a landscape page (`pdflscape`), which resolves the clipping and makes
  every label clearly legible.
- Each figure's subsection heading (e.g., "2.1 Logistic Regression...") now sits on the same
  landscape page as its figure, rather than stranded alone on a preceding portrait page; the
  two section-level headings ("Individual AUC-ROC Forest Plots by Model" and "Individual
  Precision–Recall Forest Plots by Model") are treated the same way. Net effect: 34 pages (up
  from 22), not one wasted page per heading plus one per figure.
- The "Global Forest Plot" summary figure (Section 1.1) was audited and left unchanged: it
  was already rendered at native scale with no `scale=` reduction and fits a portrait page
  without any overflow.
- Removed local, gitignored, orphaned build artifacts left over from the
  `forest_plots_por_modelo_latex` → `forest_plots_by_model` rename in v1.2.0
  (`.aux`/`.log`/`.out`/`.pdf`); per `.gitignore`, none of these were ever tracked by git.

Also audited today, and confirmed **not** affected by anything corrected in the primary
manuscript repository:
- **Bibliography completeness**: `references/references.bib` and all four
  `results/tables/*.tex` files already cite all 8 included studies (Curth2020, Dam2025,
  DeHond2023, Khodadadi2023, Shickel2022, Sun2024, Thoral2021, Tschoellitsch2024) — covered by
  the v1.3.0 bibliography sync. A separate, file-local citation omission was found and fixed
  today only in the primary repository's `supplementary_material_bdcc.tex` (three studies named
  in that file's Table S-Rep without an accompanying `\cite`); it has no counterpart here, since
  this repository's own table fragments do not use `\cite` commands for any study.
- **Mortality-horizon subgroup figures**: a numeric inconsistency was found and corrected today
  in the primary manuscript (`articulo_bdcc.tex`) between its Results narrative and its own
  Table 4, for the in-hospital/admission-referenced mortality subgroup (stale: k=24, I²=99.8%,
  AUC-ROC=0.832; corrected to k=19, I²=99.1%, AUC-ROC=0.846, matching that manuscript's own
  GRADE summary table throughout). This repository has no equivalent stratified
  mortality-horizon table or figure, so nothing here required a corresponding change.
- `results/tables/*.tex` (all four): `adjustbox`-scaled table fragments with no page geometry
  of their own, unaffected by the page-orientation issue described above.

## [v1.4.0] — 2026-09-02

Corrected `supplementary/graphical_abstract.png`, which had never been updated after the
statistical correction round (logit-scale pooling, Sun M. et al. excluded from AUC-ROC pooling,
outcome-stratified subgroups). Investigation found that **neither existing copy of this
graphic was current**: this repository's copy and the primary manuscript repository's own
reference copy (`graphical_abstract_bdcc.png`) carried two different sets of stale numbers
(pooled AUC-ROC 0.791 here vs. 0.797 there), and no dedicated generator script for this
graphic existed at all — the only script found (`scripts/generate_graphical_abstract.py` in
the primary repository) was for a different, unrelated journal submission.

- Pooled AUC-ROC headline: replaced the single stale value (0.791, 95% CI 0.775–0.807,
  I²=86.5%) with the current dual primary/exploratory report: primary (k=7) 0.814 (95% CI
  0.746–0.868, I²=98.5%); exploratory (k=68) 0.807 (95% CI 0.786–0.826, I²=98.8%).
- "Top Model Architectures" panel: replaced the old model-only pooled bars — two of which
  (CTCL 0.874, GRU+Attention 0.868) no longer exist as valid pooled quantities at all under
  the corrected, outcome-stratified methodology — with the current top 6 outcome-stratified
  values (all mortality: Transformer 0.956, Patient Forest 0.834, XGBoost 0.823, Logistic
  Regression 0.816, Random Forest 0.815, SVM 0.812), matching
  `results/tables/model_subgroup_table.tex`.
- "Precision–Recall Metrics" panel: replaced four fabricated "pooled" values for Sun M. et
  al. (0.853/0.834/0.829/0.803 — these were never valid pooled estimates and are now 8
  separate k=1 descriptive rows per `results/tables/pr_subgroup_table.tex`) with the only
  genuinely pooled PR values (Patient Forest AUPRC 0.596, XGBoost AUPRC 0.126, Random Forest
  AP 0.114, XGBoost AP 0.113), and relabeled the panel to make clear these are pooled-only,
  with Sun's individual range (0.762–0.869) noted separately as not comparable at face value.
- "Key Conclusions" bullets rewritten to name the correct top-performing models and outcome,
  cite the correct heterogeneity (I²≥98%, not 86.5%), and mention Sun M. et al.'s exclusion
  from AUC-ROC pooling — the single most important methodological change of the correction
  round, previously absent from this graphic entirely.
- PRISMA flow counts, PROBAST risk-of-bias counts, GRADE certainty rating, and the bottom
  summary-statistics strip were all audited and confirmed still accurate — unchanged.

Also audited `supplementary/PRISMA_2020_checklist_completed.md` for the same kind of drift:
confirmed **not stale** — its 27 PRISMA-item-to-section mappings still match the primary
manuscript's own labels exactly, and PRISMA checklist items are standardized reporting
categories, not a summary of results, so they are unaffected by the statistical correction.

## [v1.3.0] — 2026-09-02

Bibliography sync in response to two reference-hygiene issues raised by the journal editor
during peer review of the manuscript.

- **`references/references.bib`** (50 entries, up from 49):
  - Removed `Freund1997AdaBoost` (Freund & Schapire, 1997, *JCSS*) and replaced it with
    `Schapire2003Boosting` (Schapire, "The Boosting Approach to Machine Learning: An Overview,"
    in *Nonlinear Estimation and Classification*, Springer, 2003, DOI
    `10.1007/978-0-387-21579-2_9`) — a background citation supporting a single passing mention
    of AdaBoost's origin. The editor's automated check flagged the 1997 paper as carrying an
    official correction record; no such record could be independently confirmed via CrossRef,
    Elsevier, or Retraction Watch, but since it is a low-stakes, single-use background citation
    it was swapped anyway rather than relying on an unconfirmed absence of evidence. A
    candidate replacement (the original 1996 ICML conference paper) was considered and rejected
    because its only resolvable identifier (ACM Digital Library) returns HTTP 403 to automated
    link-checkers — the same class of false-positive failure this change is meant to avoid.
  - Added `DeHond2023Erratum` (*Crit Care Med.* 2023;51(4):e105, DOI
    `10.1097/CCM.0000000000005818`, PMID 36928025), cited alongside the original `DeHond2023`
    entry. De Hond et al. (2023) is one of the 8 studies this review analyzes, not a background
    citation, so — unlike the AdaBoost citation — it could not simply be removed or substituted
    without misrepresenting which study was actually analyzed. The erratum is a purely
    bibliographic author-name correction (unrelated to any data, method, or metric extracted for
    this review); standard practice for an included study with a cosmetic erratum is to cite the
    correction alongside the original, not to swap out the study.
  - Added a `pmid` field (7063747) to `HanleyMcNeil1982`. Its DOI was flagged by the editor as
    inaccessible; independent verification (CrossRef, a live `doi.org` redirect, and PubMed)
    confirmed the DOI is valid and resolves correctly — the RSNA journal site returns an HTTP 403
    to automated bots, which is almost certainly what the editor's checker encountered. The DOI
    itself was not changed; the PMID is added as a bot-friendly secondary access point.

## [v1.2.0] — 2026-09-02

Full-English-language pass and a public-release readiness review, prompted by a request to
confirm this repository is free of residual Spanish text and to assess journal-copyright
readiness before any further public update.

### Language normalization
- `protocol/protocol_study.md`: fully translated to English (title, research question, PICO
  framework, eligibility criteria, and the "Registration and Public Availability" section added
  in v1.1.0 — same argument, translated, not reworded).
- `data/extracted_models.json` (renamed from `data/modelos_extraidos.json`, see below): field
  names translated (`estudio_id`→`study_id`, `pdf_nombre`→`pdf_name`, `modelo`→`model`,
  `tarea`→`task`, `contexto`→`context`), and the Spanish values of `task`, `cohort_label`, and
  `outcome_note` translated across all 78 records, using the same English terminology already
  established for these studies in the main manuscript's own supplementary material. All
  numeric fields are byte-identical to the previous version (verified field-by-field before
  writing). **This intentionally diverges from the internal working copy of this dataset kept in
  the primary manuscript repository, which remains in Spanish because it feeds that repository's
  own analysis pipeline** — the numeric content is identical; only this repository's copy has
  translated metadata, for readers of the public supplementary materials.
- `results/tables/study_detail_table.tex`, `study_detail_table_pr.tex`,
  `model_subgroup_table.tex`, `pr_subgroup_table.tex` (renamed, see below): column headers, row
  labels, and footnotes translated to English, using the exact terminology already validated in
  the equivalent English tables in the main manuscript. All numeric values are unchanged.
- `supplementary/PRISMA_2020_checklist_completed.md` and
  `results/forest_plots/forest_plots_by_model.tex`: reworded two sentences that named
  Spanish-language file names from the primary manuscript repository (`articulo_bdcc.tex`, the
  original model-only figure-generation script) by description instead of by their literal
  (Spanish) file names — those files themselves are out of scope and are not being renamed.

### File renames (content already covered above)
- `data/modelos_extraidos.json` → `data/extracted_models.json`
- `results/tables/tabla_detalle_estudios.tex` → `results/tables/study_detail_table.tex`
- `results/tables/tabla_detalle_estudios_pr.tex` → `results/tables/study_detail_table_pr.tex`
- `results/tables/tabla_subanalisis_ml.tex` → `results/tables/model_subgroup_table.tex`
- `results/tables/tabla_subanalisis_pr.tex` → `results/tables/pr_subgroup_table.tex`
- `results/forest_plots/forest_plots_por_modelo_latex.tex` →
  `results/forest_plots/forest_plots_by_model.tex`

All cross-references to these six files in `README.md` and in this changelog's own v1.1.0 entry
were updated accordingly.

### Documented exception (not changed)
- `supplementary/studies_screening/screening_results_2026-05-09.csv`: the `Reason_Criteria`
  column remains in Spanish across all 2,213 rows. This was evaluated and deliberately left
  untranslated in this release, to avoid risking the scientific fidelity of a high-volume,
  unreviewed mechanical translation of screening justifications. Translating this column is
  tracked as a separate, future task.

### Copyright and public-release readiness review
A review was conducted of MDPI/BDCC's copyright and open-access policy, and of third-party
rights exposure within this repository, ahead of any further public update. Summary:
- No blocking issue was found for publishing this repository's pending updates. MDPI/BDCC
  operates under CC BY (authors retain copyright), the `LICENSE` and this repository's license
  section apply only to the authors' own original material, and no MDPI-typeset content,
  branding, or PDF is tracked in this repository. The "submitted" status of the manuscript is
  disclosed clearly and consistently throughout.
- A genuine, pre-existing gray area was identified and deliberately left unchanged: this
  repository's screening CSV (all 2,213 rows) and 35 entries in `references/references.bib`
  retain full verbatim abstract text exported from Scopus, Web of Science, IEEE Xplore, and
  PubMed. This is not an MDPI policy issue but a potential third-party database/publisher
  terms-of-use consideration. It reflects common practice in publicly shared systematic-review
  screening records, with no known enforcement precedent in this space, and has already been
  public since the v1.0.0 release with no apparent issue; it is intentionally not addressed in
  this release.
- Not independently verifiable with text-based tools: the authors should personally confirm that
  `supplementary/graphical_abstract.png` is original artwork and does not carry any MDPI/BDCC
  template, logo, or watermark.

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
- `results/tables/study_detail_table.tex` (then named `tabla_detalle_estudios.tex`; renamed in
  v1.2.0, see below): added the standard-error tier column (Reported / Hanley–McNeil), added
  confidence intervals to all rows, and marked Sun M. et al.'s 10 rows as excluded from pooling
  (previously presented as ordinary data rows).
- `results/tables/model_subgroup_table.tex` (then named `tabla_subanalisis_ml.tex`): rebuilt
  from a model-only grouping (which mixed outcomes in most rows) to the 15 model×outcome strata
  described above.
- `results/tables/pr_subgroup_table.tex` (then named `tabla_subanalisis_pr.tex`): Sun M. et al.'s
  four AUC-PRC model rows (CTCL, Transformer, RF, LR) are now split into 8 outcome-level
  descriptive rows instead of 4 combined ("pooled") rows.
- `results/forest_plots/forest_plots_by_model.tex` (then named
  `forest_plots_por_modelo_latex.tex`): rebuilt to match the corrected
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
- The dataset (then `data/modelos_extraidos.json`, renamed to `data/extracted_models.json` in
  v1.2.0) was unchanged in this release (already consistent with the current manuscript).
- `results/risk_of_bias_assessment.md` is unchanged (already consistent: 3 low risk, 5 some
  concerns, 0 high risk, matching the manuscript's PROBAST assessment).
- `results/tables/study_detail_table_pr.tex` (then named `tabla_detalle_estudios_pr.tex`;
  AUC-PRC study-level detail) is unchanged in this release (already consistent — this table was
  not affected by the AUC-ROC pooling changes).
- `references/references.ris` is unchanged. It was already out of sync with `references.bib`
  before this release and remains so; regenerating it is tracked as a separate, outstanding task
  that also affects the primary manuscript repository and is out of scope for this release.

## [v1.0.0] — 2026-05-09

Initial public release of the supplementary materials repository.
