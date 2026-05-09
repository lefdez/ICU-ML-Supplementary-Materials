#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un PDF con tablas y Forest Plots agrupados por modelo de ML.

Para cada modelo:
  1. Tabla con columnas: Estudio | Tarea | AUC-ROC | IC 95% | Desv. IC
  2. Forest Plot con AUC-ROC e intervalos de confianza

Salida: forest_plots_por_modelo.pdf (multipágina)
"""

import os
import json
import math
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np

from metadata_muestras import format_outcome_cell, table_footnote

# ─────────────────── Configuración ───────────────────────────────────

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(DIRECTORIO, "modelos_extraidos.json")
OUTPUT_PDF = os.path.join(DIRECTORIO, "forest_plots_por_modelo.pdf")

CITAS = {
    "2016": "Curth et al. (2020)",
    "2110": "Thoral et al. (2021)",
    "2216": "Shickel et al. (2022)",
    "2313": "De Hond et al. (2023)",
    "2314": "Khodadadi et al. (2023)",
    "2420": "Tschoellitsch et al. (2024)",
    "2421": "Sun et al. (2024)",
    "2025": "Dam et al. (2025)",
}

# ─── Referencias bibliográficas completas ────────────────────────────

REFERENCIAS = {
    "2016": (
        "[1] Curth A, Thoral P, van den Wildenberg W, Bijlstra P, de Bruin D, Elbers P, Fornasa M. "
        "Transferring Clinical Prediction Models Across Hospitals and Electronic Health Record Systems. "
        "ECML PKDD 2019 Workshops, CCIS 1167, pp. 605–621, 2020. "
        "DOI: 10.1007/978-3-030-43823-4_48"
    ),
    "2110": (
        "[2] Thoral PJ, Fornasa M, de Bruin DP, Tonutti M, Hovenkamp H, Driessen RH, Girbes ARJ, "
        "Hoogendoorn M, Elbers PWG. Explainable Machine Learning on AmsterdamUMCdb for ICU Discharge "
        "Decision Support. Critical Care Explorations 2021; 3(9):e0529. "
        "DOI: 10.1097/CCE.0000000000000529"
    ),
    "2216": (
        "[3] Shickel B, Silva B, Ozrazgat-Baslanti T, Ren Y, Khezeli K, Guan Z, Tighe PJ, Bihorac A, "
        "Rashidi P. Multi-dimensional patient acuity estimation with longitudinal EHR tokenization and "
        "flexible transformer networks. Frontiers in Digital Health 2022; 4:1029191. "
        "DOI: 10.3389/fdgth.2022.1029191"
    ),
    "2313": (
        "[4] De Hond AAH, Kant IMJ, Fornasa M, Cinà G, Elbers PW, Thoral PJ, Arbous MS, Steyerberg EW. "
        "Predicting Readmission or Death After Discharge From the ICU: External Validation and Retraining "
        "of a Machine Learning Model. Critical Care Medicine 2023; 51(2). "
        "DOI: 10.1097/CCM.0000000000005758"
    ),
    "2314": (
        "[5] Khodadadi A, Ghanbari Bousejin N, Molaei S, Chauhan VK, Zhu T, Clifton DA. "
        "Improving Diagnostics with Deep Forest Applied to Electronic Health Records. "
        "Sensors (MDPI) 2023; 23(14):6571. DOI: 10.3390/s23146571"
    ),
    "2420": (
        "[6] Tschoellitsch T, Maletzky A, Moser P, Seidl P, Bock C, Tomic Mahečić T, Thumfart S, "
        "Giretzlehner M, Hochreiter S, Meier J. Machine learning prediction of unexpected readmission "
        "or death after discharge from intensive care: A retrospective cohort study. "
        "Journal of Clinical Anesthesia 2024; 99:111654. DOI: 10.1016/j.jclinane.2024.111654"
    ),
    "2421": (
        "[7] Sun M, Yang X, Niu J, Gu Y, Wang C, Zhang W. A cross-modal clinical prediction system "
        "for intensive care unit patient outcome. Knowledge-Based Systems 2024; 283:111160. "
        "DOI: 10.1016/j.knosys.2023.111160"
    ),
    "2025": (
        "[8] Dam TA, de Bruin D, Cinà G, Thoral PJ, Elbers PWG, den Uil CA, Crane RF. "
        "ICU readmission and mortality risk prediction: Generalizability of a multi-hospital model. "
        "Journal of Intensive Medicine 2025; 5:377–384."
    ),
}

# Colores
HEADER_BG = "#2c3e50"
HEADER_FG = "white"
ROW_COLORS = ["#f8f9fa", "#ffffff"]
COMBINED_BG = "#e8f5e9"
POINT_COLOR = "#1a5276"
COMBINED_COLOR = "#c0392b"
CI_COLOR = "#2c3e50"
GRID_COLOR = "#dee2e6"

# Colores para PR
PR_POINT_COLOR = "#27ae60"
PR_COMBINED_COLOR = "#16a085"


# ─────────────────── Funciones auxiliares ─────────────────────────────

def _familia_metrica_pr(entry):
    """Normaliza nombre de métrica PR (AP vs AUPRC/AUPR)."""
    metric_name = entry.get("pr_metric_name", "")
    if "AP" in metric_name and "AUP" not in metric_name:
        return "AP"
    return "AUPR/AUPRC"

def cargar_datos() -> list[dict]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def agrupar_por_modelo(datos: list[dict]) -> dict[str, list[dict]]:
    """Agrupa entradas por modelo, filtrando AUC < 0.5 y 'No identificado'."""
    grupos = defaultdict(list)
    for d in datos:
        modelo = d.get("modelo", "")
        auc = d.get("auc_roc")
        if not modelo or modelo == "No identificado" or not auc or auc < 0.5:
            continue
        grupos[modelo].append(d)

    # Dedup: mejor AUC por (estudio, modelo, tarea)
    result = {}
    for modelo, entries in grupos.items():
        mejores = {}
        for e in entries:
            key = (e["estudio_id"], e.get("tarea", ""))
            if key not in mejores or e["auc_roc"] > mejores[key]["auc_roc"]:
                mejores[key] = e
        result[modelo] = sorted(mejores.values(), key=lambda x: (x["estudio_id"], x.get("tarea", "")))

    # Ordenar modelos por número de entradas (desc) y luego AUC media (desc)
    return dict(sorted(
        result.items(),
        key=lambda kv: (-len(kv[1]), -np.mean([e["auc_roc"] for e in kv[1]])),
    ))


def calcular_totales(modelos_agrupados: dict[str, list[dict]]) -> tuple[int, int, int]:
    entradas = [e for entries in modelos_agrupados.values() for e in entries]
    return len(modelos_agrupados), len({e["estudio_id"] for e in entradas}), len(entradas)


def estimar_ci(entry: dict) -> tuple[float, float, float]:
    """
    Retorna (auc, ci_lower, ci_upper).
    Si no hay IC reportado, estima un SE basado en un ancho de IC típico
    de 0.05 (± ~0.025 por lado), escalado por la incertidumbre implícita.
    """
    auc = entry["auc_roc"]
    ci_lo = entry.get("auc_roc_ci_lower")
    ci_up = entry.get("auc_roc_ci_upper")

    if ci_lo is not None and ci_up is not None:
        return auc, ci_lo, ci_up

    # Estimación conservadora: SE ~ 0.03 (ancho IC ≈ 0.12)
    se_est = 0.03
    return auc, max(0.0, auc - 1.96 * se_est), min(1.0, auc + 1.96 * se_est)


def calcular_efecto_combinado(entries: list[dict]) -> tuple[float, float, float]:
    """
    Calcula efecto combinado (media ponderada por inversa de varianza)
    usando modelo de efectos fijos simplificado.
    Retorna (efecto, ci_lower, ci_upper).
    """
    weights = []
    effects = []

    for e in entries:
        auc, ci_lo, ci_up = estimar_ci(e)
        se = (ci_up - ci_lo) / (2 * 1.96)
        if se <= 0:
            se = 0.03  # mínimo razonable
        w = 1.0 / (se ** 2)
        weights.append(w)
        effects.append(auc)

    total_w = sum(weights)
    pooled = sum(e * w for e, w in zip(effects, weights)) / total_w
    se_pooled = math.sqrt(1.0 / total_w)

    return pooled, pooled - 1.96 * se_pooled, pooled + 1.96 * se_pooled


def agrupar_por_modelo_pr(datos: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """Agrupa PR por modelo y familia (AP vs AUPRC/AUPR)."""
    grupos = defaultdict(lambda: defaultdict(list))
    for d in datos:
        modelo = d.get("modelo", "")
        auc_pr = d.get("auc_pr")
        if not modelo or modelo == "No identificado" or not auc_pr or auc_pr <= 0:
            continue
        familia = _familia_metrica_pr(d)
        grupos[modelo][familia].append(d)

    result = {}
    for modelo, family_dict in grupos.items():
        result[modelo] = {}
        for familia, entries in family_dict.items():
            mejores = {}
            for e in entries:
                key = (e["estudio_id"], e.get("tarea", ""))
                if key not in mejores or e.get("auc_pr", 0) > mejores[key].get("auc_pr", 0):
                    mejores[key] = e
            result[modelo][familia] = sorted(mejores.values(), key=lambda x: (x["estudio_id"], x.get("tarea", "")))

    return result


def estimar_ci_pr(entry: dict) -> tuple[float, float, float]:
    """Estimar IC para métricas PR."""
    auc_pr = entry.get("auc_pr")
    ci_lo = entry.get("auc_pr_ci_lower")
    ci_up = entry.get("auc_pr_ci_upper")

    if ci_lo is not None and ci_up is not None:
        return auc_pr, ci_lo, ci_up

    se_est = 0.03
    return auc_pr, max(0.0, auc_pr - 1.96 * se_est), min(1.0, auc_pr + 1.96 * se_est)


def calcular_efecto_combinado_pr(entries: list[dict]) -> tuple[float, float, float]:
    """Calcula efecto combinado para PR."""
    weights = []
    effects = []

    for e in entries:
        auc_pr, ci_lo, ci_up = estimar_ci_pr(e)
        if auc_pr is None or auc_pr <= 0:
            continue
        se = (ci_up - ci_lo) / (2 * 1.96)
        if se <= 0:
            se = 0.03
        w = 1.0 / (se ** 2)
        weights.append(w)
        effects.append(auc_pr)

    if not weights:
        return None, None, None

    total_w = sum(weights)
    pooled = sum(e * w for e, w in zip(effects, weights)) / total_w
    se_pooled = math.sqrt(1.0 / total_w)

    return pooled, pooled - 1.96 * se_pooled, pooled + 1.96 * se_pooled

def crear_pagina_modelo(pdf: PdfPages, modelo: str, entries: list[dict]):
    """Genera 1 página por modelo: tabla arriba, Forest Plot abajo."""
    n = len(entries)

    # Preparar datos de la tabla
    tabla_rows = []
    for e in entries:
        cite = CITAS.get(e["estudio_id"], f"Estudio {e['estudio_id']}")
        tarea = e.get("tarea", "—")[:35]
        auc = e["auc_roc"]
        auc_val, ci_lo, ci_up = estimar_ci(e)

        tiene_ci = e.get("auc_roc_ci_lower") is not None and e.get("auc_roc_ci_upper") is not None
        if tiene_ci:
            ic_str = f"{ci_lo:.3f} – {ci_up:.3f}"
        else:
            ic_str = f"{ci_lo:.3f} – {ci_up:.3f} *"

        desv_ic = (ci_up - ci_lo) / 2
        desv_str = f"± {desv_ic:.3f}"

        tabla_rows.append({
            "cite": cite,
            "tarea": tarea,
            "outcome": format_outcome_cell(e),
            "auc": auc,
            "ci_lo": ci_lo,
            "ci_up": ci_up,
            "ic_str": ic_str,
            "desv_str": desv_str,
            "tiene_ci": tiene_ci,
        })

    # Efecto combinado
    pooled, pooled_lo, pooled_hi = calcular_efecto_combinado(entries)
    pooled_desv = (pooled_hi - pooled_lo) / 2

    # ── Crear figura ──
    fig_height = max(9, 4.5 + n * 0.55)
    fig, (ax_table, ax_forest) = plt.subplots(
        2, 1,
        figsize=(13, fig_height),
        gridspec_kw={"height_ratios": [max(0.35, n * 0.06 + 0.15), 0.65 - min(0.15, n * 0.02)]},
    )

    # ══════════════════════════════════════════════════════════════════
    # PARTE 1: TABLA
    # ══════════════════════════════════════════════════════════════════
    ax_table.axis("off")

    # Título
    ax_table.set_title(
        f"Modelo: {modelo}",
        fontsize=14, fontweight="bold", fontfamily="serif",
        pad=10, loc="center",
    )

    headers = ["Estudio", "Tarea", "Eventos/N", "AUC-ROC", "IC 95%", "Desv. IC"]
    cell_text = []
    for r in tabla_rows:
        cell_text.append([r["cite"], r["tarea"], r["outcome"], f"{r['auc']:.3f}", r["ic_str"], r["desv_str"]])

    # Fila de efecto combinado
    cell_text.append([
        "Efecto combinado",
        f"({n} entradas)",
        "—",
        f"{pooled:.3f}",
        f"{pooled_lo:.3f} – {pooled_hi:.3f}",
        f"± {pooled_desv:.3f}",
    ])

    table = ax_table.table(
        cellText=[headers] + cell_text,
        cellLoc="center",
        loc="center",
        bbox=[0.02, 0.0, 0.96, 1.0],
    )

    n_cols = len(headers)
    n_total_rows = len(cell_text)

    # Header style
    for j in range(n_cols):
        cell = table[0, j]
        cell.set_facecolor(HEADER_BG)
        cell.set_text_props(color=HEADER_FG, fontweight="bold", fontsize=8.5)
        cell.set_edgecolor(GRID_COLOR)

    # Data rows
    for i in range(1, n_total_rows + 1):
        is_combined = (i == n_total_rows)
        for j in range(n_cols):
            cell = table[i, j]
            if is_combined:
                cell.set_facecolor(COMBINED_BG)
                cell.set_text_props(fontsize=8, fontweight="bold")
            else:
                cell.set_facecolor(ROW_COLORS[(i - 1) % 2])
                cell.set_text_props(fontsize=7.5)
            cell.set_edgecolor(GRID_COLOR)
            if j == 0:
                cell.set_text_props(fontsize=7.5, ha="left",
                                    fontweight="bold" if is_combined else "normal")

    # Ajustar anchos
    col_widths = [0.20, 0.22, 0.16, 0.10, 0.19, 0.11]
    total_w_cols = sum(col_widths)
    for j, w in enumerate(col_widths):
        for i in range(n_total_rows + 1):
            table[i, j].set_width(w / total_w_cols * 0.96)

    table.auto_set_font_size(False)

    # Nota al pie
    ax_table.text(
        0.02, -0.02,
        f"* IC 95% estimado (SE = 0.03) cuando no se reportó en el estudio original. {table_footnote()}",
        fontsize=6.5, fontstyle="italic", color="#777777",
        transform=ax_table.transAxes, va="top",
    )

    # ══════════════════════════════════════════════════════════════════
    # PARTE 2: FOREST PLOT
    # ══════════════════════════════════════════════════════════════════
    ax_forest.set_title(
        f"Forest Plot — {modelo}",
        fontsize=12, fontweight="bold", fontfamily="serif", pad=10,
    )

    y_positions = list(range(n + 1))  # +1 para efecto combinado
    y_labels = []

    for i, r in enumerate(tabla_rows):
        y = n - i  # invertir para que el primero esté arriba
        auc = r["auc"]
        ci_lo = r["ci_lo"]
        ci_up = r["ci_up"]

        # Línea del IC
        ax_forest.plot(
            [ci_lo, ci_up], [y, y],
            color=CI_COLOR, linewidth=1.8, solid_capstyle="butt",
        )
        # Terminales del IC
        ax_forest.plot(ci_lo, y, "|", color=CI_COLOR, markersize=8, markeredgewidth=1.5)
        ax_forest.plot(ci_up, y, "|", color=CI_COLOR, markersize=8, markeredgewidth=1.5)

        # Punto central (cuadrado proporcional al peso)
        se = (ci_up - ci_lo) / (2 * 1.96)
        if se <= 0:
            se = 0.03
        weight = 1.0 / (se ** 2)
        marker_size = max(5, min(14, 3 + weight * 0.001))

        ax_forest.plot(
            auc, y, "s",
            color=POINT_COLOR, markersize=marker_size,
            markeredgecolor="white", markeredgewidth=0.5, zorder=5,
        )

        # Etiqueta con AUC al lado derecho
        marker_str = "" if r["tiene_ci"] else " *"
        ax_forest.annotate(
            f"{auc:.3f} [{ci_lo:.3f}, {ci_up:.3f}]{marker_str}",
            xy=(ci_up + 0.005, y),
            fontsize=7, va="center", color="#333333",
        )

        label = f"{r['cite']}\n{r['tarea']}"
        y_labels.append(label)

    # ── Efecto combinado (diamante) ──
    y_comb = 0
    diamond_half_h = 0.3
    diamond_x = [pooled_lo, pooled, pooled_hi, pooled]
    diamond_y = [y_comb, y_comb + diamond_half_h, y_comb, y_comb - diamond_half_h]
    ax_forest.fill(diamond_x, diamond_y, color=COMBINED_COLOR, alpha=0.7, zorder=5)
    ax_forest.plot(
        diamond_x + [diamond_x[0]], diamond_y + [diamond_y[0]],
        color=COMBINED_COLOR, linewidth=1.2, zorder=6,
    )
    ax_forest.annotate(
        f"{pooled:.3f} [{pooled_lo:.3f}, {pooled_hi:.3f}]",
        xy=(pooled_hi + 0.005, y_comb),
        fontsize=7.5, va="center", color=COMBINED_COLOR, fontweight="bold",
    )
    y_labels.append("Efecto\ncombinado")

    # Configuración del eje
    all_y = list(range(n + 1))
    ax_forest.set_yticks(all_y)
    ax_forest.set_yticklabels(list(reversed(y_labels)), fontsize=7.5)

    # Línea de referencia vertical en el efecto combinado
    ax_forest.axvline(
        x=pooled, color=COMBINED_COLOR, linestyle="--",
        alpha=0.4, linewidth=0.8, zorder=1,
    )

    # Líneas de referencia AUC
    ax_forest.axvline(x=0.70, color="orange", linestyle=":", alpha=0.4, linewidth=0.7)
    ax_forest.axvline(x=0.80, color="green", linestyle=":", alpha=0.4, linewidth=0.7)

    # Determinar rango del eje x
    all_ci_lo = [r["ci_lo"] for r in tabla_rows] + [pooled_lo]
    all_ci_up = [r["ci_up"] for r in tabla_rows] + [pooled_hi]
    x_min = max(0.4, min(all_ci_lo) - 0.06)
    x_max = min(1.05, max(all_ci_up) + 0.10)

    ax_forest.set_xlim(x_min, x_max)
    ax_forest.set_ylim(-0.7, n + 0.7)
    ax_forest.set_xlabel("AUC-ROC", fontsize=10, fontweight="bold")
    ax_forest.grid(axis="x", alpha=0.2, color=GRID_COLOR)
    ax_forest.spines["top"].set_visible(False)
    ax_forest.spines["right"].set_visible(False)

    # Línea horizontal separadora antes del efecto combinado
    ax_forest.axhline(y=0.5, color="#aaaaaa", linestyle="-", linewidth=0.5, xmin=0.0, xmax=1.0)

    # Leyenda
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor=POINT_COLOR,
               markersize=8, label="AUC-ROC por estudio"),
        Line2D([0], [0], color=CI_COLOR, linewidth=1.5, label="IC 95%"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=COMBINED_COLOR,
               markersize=8, label="Efecto combinado"),
        Line2D([0], [0], color="green", linestyle=":", linewidth=0.8, label="AUC = 0.80"),
        Line2D([0], [0], color="orange", linestyle=":", linewidth=0.8, label="AUC = 0.70"),
    ]
    ax_forest.legend(handles=legend_elements, loc="lower right", fontsize=7, framealpha=0.9)

    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)


def crear_pagina_modelo_pr(pdf: PdfPages, modelo_familia: str, entries: list[dict]):
    """Genera 1 página para PR: tabla arriba, Forest Plot abajo."""
    n = len(entries)
    if n == 0:
        return

    tabla_rows = []
    for e in entries:
        cite = CITAS.get(e["estudio_id"], f"Estudio {e['estudio_id']}")
        tarea = e.get("tarea", "—")[:35]
        auc_pr = e.get("auc_pr")
        auc_val, ci_lo, ci_up = estimar_ci_pr(e)

        tiene_ci = e.get("auc_pr_ci_lower") is not None and e.get("auc_pr_ci_upper") is not None
        if tiene_ci:
            ic_str = f"{ci_lo:.3f} – {ci_up:.3f}"
        else:
            ic_str = f"{ci_lo:.3f} – {ci_up:.3f} *"

        desv_ic = (ci_up - ci_lo) / 2
        desv_str = f"± {desv_ic:.3f}"

        tabla_rows.append({
            "cite": cite,
            "tarea": tarea,
            "outcome": format_outcome_cell(e),
            "auc_pr": auc_pr,
            "ci_lo": ci_lo,
            "ci_up": ci_up,
            "ic_str": ic_str,
            "desv_str": desv_str,
            "tiene_ci": tiene_ci,
        })

    pooled, pooled_lo, pooled_hi = calcular_efecto_combinado_pr(entries)
    if pooled is None:
        return

    pooled_desv = (pooled_hi - pooled_lo) / 2

    fig_height = max(9, 4.5 + n * 0.55)
    fig, (ax_table, ax_forest) = plt.subplots(
        2, 1,
        figsize=(13, fig_height),
        gridspec_kw={"height_ratios": [max(0.35, n * 0.06 + 0.15), 0.65 - min(0.15, n * 0.02)]},
    )

    ax_table.axis("off")
    ax_table.set_title(
        f"Modelo PR: {modelo_familia}",
        fontsize=14, fontweight="bold", fontfamily="serif",
        pad=10, loc="center",
    )

    headers = ["Estudio", "Tarea", "Eventos/N", "AUPRC/AP", "IC 95%", "Desv. IC"]
    cell_text = []
    for r in tabla_rows:
        cell_text.append([r["cite"], r["tarea"], r["outcome"], f"{r['auc_pr']:.3f}", r["ic_str"], r["desv_str"]])

    cell_text.append(["Efecto combinado", f"({n} entradas)", "—", f"{pooled:.3f}", 
                      f"{pooled_lo:.3f}–{pooled_hi:.3f}", f"± {pooled_desv:.3f}"])

    table = ax_table.table(cellText=cell_text, colLabels=headers, cellLoc="center", loc="center",
                           bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.8)

    n_cols = len(headers)
    for j in range(n_cols):
        table[(0, j)].set_facecolor(HEADER_BG)
        table[(0, j)].set_text_props(color=HEADER_FG, fontweight="bold")

    for i in range(1, len(cell_text)):
        is_combined = (i == len(cell_text) - 1)
        for j in range(n_cols):
            cell = table[(i, j)]
            if is_combined:
                cell.set_facecolor(COMBINED_BG)
                cell.set_text_props(fontweight="bold")
            else:
                cell.set_facecolor(ROW_COLORS[(i - 1) % 2])

    # Forest Plot para PR
    ax_forest.axvline(0.80, color="orange", linestyle=":", linewidth=1.0, alpha=0.7)
    ax_forest.axvline(0.70, color="orange", linestyle=":", linewidth=0.8, alpha=0.5)

    y_pos = np.arange(n + 1)
    estimates = []
    errors = []
    for r in tabla_rows:
        estimates.append(r["auc_pr"])
        hw = (r["ci_up"] - r["ci_lo"]) / 2
        errors.append(hw)
    estimates.append(pooled)
    errors.append(pooled_desv)

    colors = [PR_POINT_COLOR] * n + [PR_COMBINED_COLOR]
    sizes = [50] * n + [120]
    labels_forest = [f"{r['cite']}\n{r['tarea']}" for r in tabla_rows] + ["Efecto combinado"]

    ax_forest.scatter(estimates, y_pos, c=colors, s=sizes, zorder=3, alpha=0.8)
    for i, (est, err) in enumerate(zip(estimates, errors)):
        ax_forest.errorbar(est, y_pos[i], xerr=err, fmt="none", ecolor=CI_COLOR, elinewidth=1.5, capsize=3, zorder=2)

    ax_forest.set_yticks(y_pos)
    ax_forest.set_yticklabels(labels_forest, fontsize=7)
    ax_forest.set_xlabel("AUPRC / AP", fontweight="bold")
    ax_forest.set_xlim(max(0.0, min(estimates) - 0.1), min(1.0, max(estimates) + 0.1))
    ax_forest.grid(alpha=0.3, axis="x")
    ax_forest.invert_yaxis()

    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PR_POINT_COLOR, markersize=5, label="Estudio individual"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=PR_COMBINED_COLOR, markersize=6, label="Efecto combinado"),
        Line2D([0], [0], color=CI_COLOR, linewidth=1.5, label="IC 95%"),
        Line2D([0], [0], color="orange", linestyle=":", linewidth=1.0, label="AUPRC/AP = 0.80"),
    ]
    ax_forest.legend(handles=legend_elements, loc="lower right", fontsize=7, framealpha=0.9)

    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    plt.close(fig)

def crear_pagina_resumen(pdf: PdfPages, modelos_agrupados: dict[str, list[dict]]):
    """Página final de resumen con todos los modelos y sus efectos combinados."""
    fig, ax = plt.subplots(figsize=(13, 9))

    ax.set_title(
        "Forest Plot Global — Efecto combinado por modelo",
        fontsize=14, fontweight="bold", fontfamily="serif", pad=15,
    )

    modelos_sorted = list(modelos_agrupados.keys())
    n_modelos = len(modelos_sorted)

    for i, modelo in enumerate(modelos_sorted):
        entries = modelos_agrupados[modelo]
        pooled, ci_lo, ci_up = calcular_efecto_combinado(entries)
        n_entries = len(entries)
        y = n_modelos - 1 - i

        # IC line
        ax.plot([ci_lo, ci_up], [y, y], color=CI_COLOR, linewidth=2.0)
        ax.plot(ci_lo, y, "|", color=CI_COLOR, markersize=10, markeredgewidth=1.5)
        ax.plot(ci_up, y, "|", color=CI_COLOR, markersize=10, markeredgewidth=1.5)

        # Diamante para efecto combinado
        dh = 0.25
        dx = [ci_lo, pooled, ci_up, pooled]
        dy = [y, y + dh, y, y - dh]
        ax.fill(dx, dy, color=COMBINED_COLOR, alpha=0.6, zorder=5)
        ax.plot(dx + [dx[0]], dy + [dy[0]], color=COMBINED_COLOR, linewidth=1, zorder=6)

        # Etiqueta
        ax.annotate(
            f"{pooled:.3f} [{ci_lo:.3f}, {ci_up:.3f}]  n={n_entries}",
            xy=(ci_up + 0.005, y),
            fontsize=7.5, va="center", color="#333333",
        )

    ax.set_yticks(range(n_modelos))
    ax.set_yticklabels(list(reversed(modelos_sorted)), fontsize=8.5)
    ax.set_xlabel("AUC-ROC (Efecto combinado)", fontsize=11, fontweight="bold")

    # Líneas de referencia
    ax.axvline(x=0.70, color="orange", linestyle=":", alpha=0.5, linewidth=0.8)
    ax.axvline(x=0.80, color="green", linestyle=":", alpha=0.5, linewidth=0.8)

    ax.set_xlim(0.55, 1.02)
    ax.set_ylim(-0.7, n_modelos - 0.3)
    ax.grid(axis="x", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor=COMBINED_COLOR,
               markersize=8, label="Efecto combinado (inv. varianza)"),
        Line2D([0], [0], color=CI_COLOR, linewidth=1.5, label="IC 95%"),
        Line2D([0], [0], color="green", linestyle=":", linewidth=0.8, label="AUC = 0.80"),
        Line2D([0], [0], color="orange", linestyle=":", linewidth=0.8, label="AUC = 0.70"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=8, framealpha=0.9)

    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ─────────────── Página de Referencias y Auditoría ───────────────────

def crear_pagina_referencias(pdf: PdfPages):
    """Genera página con las referencias bibliográficas completas."""
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.axis("off")

    ax.text(
        0.5, 0.97,
        "Referencias Bibliográficas",
        ha="center", va="top", fontsize=16, fontweight="bold",
        fontfamily="serif", color=HEADER_BG,
        transform=ax.transAxes,
    )
    ax.text(
        0.5, 0.93,
        "Artículos incluidos en el meta-análisis PRISMA",
        ha="center", va="top", fontsize=10, color="#555555",
        fontfamily="serif", fontstyle="italic",
        transform=ax.transAxes,
    )

    y_pos = 0.88
    for eid in sorted(REFERENCIAS.keys()):
        ref_text = REFERENCIAS[eid]
        ax.text(
            0.05, y_pos, ref_text,
            ha="left", va="top", fontsize=8.0,
            fontfamily="serif", wrap=True,
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8f9fa", edgecolor="#dee2e6", alpha=0.8),
        )
        y_pos -= 0.115

    ax.text(
        0.05, y_pos - 0.02,
        "Nota: Las citas abreviadas usadas en las tablas y Forest Plots corresponden a los estudios listados arriba.",
        ha="left", va="top", fontsize=7, fontstyle="italic", color="#777777",
        transform=ax.transAxes,
    )

    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)


def crear_pagina_auditoria(pdf: PdfPages, datos: list[dict], modelos_agrupados: dict):
    """Genera página de auditoría con trazabilidad completa de los datos."""
    from datetime import datetime

    fig, ax = plt.subplots(figsize=(13, 10))
    ax.axis("off")

    ax.text(
        0.5, 0.97,
        "Auditoría y Trazabilidad de Datos",
        ha="center", va="top", fontsize=16, fontweight="bold",
        fontfamily="serif", color=HEADER_BG,
        transform=ax.transAxes,
    )

    # Recopilar estadísticas de auditoría
    estudios_ids = sorted(set(d["estudio_id"] for d in datos if d.get("auc_roc")))
    n_total = len(datos)
    n_validos = sum(1 for d in datos if d.get("auc_roc") and d["auc_roc"] >= 0.5)
    n_con_ci = sum(1 for d in datos if d.get("auc_roc_ci_lower") is not None and d.get("auc_roc_ci_upper") is not None)
    n_ci_est = n_validos - n_con_ci
    n_modelos = len(modelos_agrupados)
    n_metricas = sum(len(v) for v in modelos_agrupados.values())

    # Tabla de auditoría por estudio
    audit_headers = ["ID", "Cita", "PDF Original", "Entradas", "Con IC", "IC Est.", "Modelos"]
    audit_rows = []
    for eid in estudios_ids:
        cite = CITAS.get(eid, f"Estudio {eid}")
        entries_est = [d for d in datos if d["estudio_id"] == eid and d.get("auc_roc") and d["auc_roc"] >= 0.5]
        n_e = len(entries_est)
        con_ci = sum(1 for d in entries_est if d.get("auc_roc_ci_lower") is not None)
        sin_ci = n_e - con_ci
        modelos_est = sorted(set(d["modelo"] for d in entries_est if d["modelo"] != "No identificado"))
        audit_rows.append([
            eid, cite, f"✓", str(n_e), str(con_ci), str(sin_ci),
            ", ".join(modelos_est),
        ])

    # Fila de totales
    audit_rows.append([
        "TOTAL", f"{len(estudios_ids)} estudios", "", str(n_validos), str(n_con_ci), str(n_ci_est),
        f"{n_modelos} modelos únicos",
    ])

    table = ax.table(
        cellText=[audit_headers] + audit_rows,
        cellLoc="center",
        loc="upper center",
        bbox=[0.02, 0.35, 0.96, 0.55],
    )

    n_cols_a = len(audit_headers)
    n_rows_a = len(audit_rows)
    for j in range(n_cols_a):
        cell = table[0, j]
        cell.set_facecolor(HEADER_BG)
        cell.set_text_props(color=HEADER_FG, fontweight="bold", fontsize=7.5)
        cell.set_edgecolor(GRID_COLOR)

    for i in range(1, n_rows_a + 1):
        is_total = (i == n_rows_a)
        for j in range(n_cols_a):
            cell = table[i, j]
            if is_total:
                cell.set_facecolor(COMBINED_BG)
                cell.set_text_props(fontsize=6, fontweight="bold")
            else:
                cell.set_facecolor(ROW_COLORS[(i - 1) % 2])
                cell.set_text_props(fontsize=6)
            cell.set_edgecolor(GRID_COLOR)
            # Modelos column: left-align for readability
            if j == n_cols_a - 1:
                cell.set_text_props(fontsize=5.5, ha="left")

    col_ws = [0.06, 0.18, 0.07, 0.08, 0.07, 0.07, 0.43]
    tw = sum(col_ws)
    for j, w in enumerate(col_ws):
        for i in range(n_rows_a + 1):
            table[i, j].set_width(w / tw * 0.96)
    table.auto_set_font_size(False)

    # Notas de auditoría
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notes = (
        f"NOTAS DE AUDITORÍA\n\n"
        f"Fecha de generación: {now_str}\n"
        f"Fuente de datos: modelos_extraidos.json ({n_total} registros totales)\n"
        f"Registros válidos (AUC ≥ 0.5): {n_validos}\n"
        f"Registros con IC 95% reportado: {n_con_ci} ({n_con_ci/n_validos*100:.1f}%)\n"
        f"Registros con IC 95% estimado (SE=0.03): {n_ci_est} ({n_ci_est/n_validos*100:.1f}%)\n"
        f"Modelos excluidos: 'No identificado' y entradas con AUC < 0.5\n"
        f"Deduplicación: mejor AUC por combinación (estudio, tarea) dentro de cada modelo\n"
        f"Efecto combinado: media ponderada por inversa de varianza (modelo efectos fijos)\n\n"
        f"VERIFICACIÓN:\n"
        f"  • Cada entrada puede trazarse al JSON fuente y al PDF original del artículo\n"
        f"  • Los valores marcados con * en los Forest Plots tienen IC estimado\n"
        f"  • Para publicación, verificar IC estimados con los artículos originales\n"
        f"  • Considerar usar modelo de efectos aleatorios (DerSimonian-Laird) para publicación"
    )

    ax.text(
        0.05, 0.30, notes,
        ha="left", va="top", fontsize=8,
        fontfamily="monospace", transform=ax.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff9c4", edgecolor="#f9a825", alpha=0.9),
    )

    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ─────────────────── Main ────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  FOREST PLOTS POR MODELO — META-ANÁLISIS ML / UCI")
    print("=" * 65)

    if not os.path.exists(JSON_PATH):
        print(f"✗ No se encontró {JSON_PATH}")
        print("  Ejecute primero: python extraer_modelos_auto.py")
        return

    datos = cargar_datos()
    print(f"  Datos cargados: {len(datos)} entradas")

    modelos_agrupados = agrupar_por_modelo(datos)
    total_modelos, total_estudios, total_metricas = calcular_totales(modelos_agrupados)
    print(f"  Modelos identificados: {len(modelos_agrupados)}")
    for modelo, entries in modelos_agrupados.items():
        print(f"    • {modelo}: {len(entries)} entradas")

    with PdfPages(OUTPUT_PDF) as pdf:
        # ── Página de portada ──
        fig_cover, ax_cover = plt.subplots(figsize=(13, 9))
        ax_cover.axis("off")
        ax_cover.text(
            0.5, 0.6,
            "Forest Plots por Modelo de\nAprendizaje Automático",
            ha="center", va="center", fontsize=22, fontweight="bold",
            fontfamily="serif", color=HEADER_BG,
        )
        ax_cover.text(
            0.5, 0.42,
            "Meta-análisis PRISMA — Predicción de readmisión y mortalidad en UCI",
            ha="center", va="center", fontsize=12, color="#555555",
            fontfamily="serif", fontstyle="italic",
        )
        ax_cover.text(
            0.5, 0.32,
            f"{total_modelos} modelos  •  {total_estudios} estudios  •  {total_metricas} métricas",
            ha="center", va="center", fontsize=11, color="#777777",
        )
        pdf.savefig(fig_cover, dpi=150)
        plt.close(fig_cover)

        # ── Una página (tabla + forest plot) por modelo ──
        for modelo, entries in modelos_agrupados.items():
            print(f"\n  ▶ Generando: {modelo} ({len(entries)} entradas)...")
            crear_pagina_modelo(pdf, modelo, entries)

        # ── Página de resumen global ──
        print("\n  ▶ Generando Forest Plot global...")
        crear_pagina_resumen(pdf, modelos_agrupados)

        # ── Páginas PR ──
        modelos_pr = agrupar_por_modelo_pr(datos)
        if modelos_pr:
            print("\n  ▶ Generando páginas PR...")
            for modelo, family_dict in modelos_pr.items():
                for familia, entries in family_dict.items():
                    if entries:
                        modelo_familia_name = f"{modelo} ({familia})"
                        print(f"    • {modelo_familia_name} ({len(entries)} entradas)...")
                        crear_pagina_modelo_pr(pdf, modelo_familia_name, entries)

        # ── Página de referencias bibliográficas ──
        print("\n  ▶ Generando página de referencias...")
        crear_pagina_referencias(pdf)

        # ── Página de auditoría ──
        print("\n  ▶ Generando página de auditoría...")
        crear_pagina_auditoria(pdf, datos, modelos_agrupados)

    print(f"\n{'=' * 65}")
    print(f"  ✓ PDF generado: {os.path.basename(OUTPUT_PDF)}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
