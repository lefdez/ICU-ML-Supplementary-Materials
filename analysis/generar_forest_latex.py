#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera forest_plots_por_modelo_latex.tex desde modelos_extraidos.json.

Produce un documento LaTeX compilable con:
    1. Forest Plot global (conteo dinámico de modelos)
  2. Forest Plot individual por modelo (≥2 entradas)
  3. Tabla resumen
  4. Referencias

Compilar resultado:  pdflatex forest_plots_por_modelo_latex.tex  (×2)
"""

import json
import math
import os
from collections import defaultdict

from metadata_muestras import aggregate_outcomes, format_aggregate_cell, table_footnote

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(DIRECTORIO, "modelos_extraidos.json")
OUTPUT_TEX = os.path.join(DIRECTORIO, "forest_plots_por_modelo_latex.tex")

CITAS = {
    "2016": "Curth 2020",
    "2110": "Thoral 2021",
    "2216": "Shickel 2022",
    "2313": "De Hond 2023",
    "2314": "Khodadadi 2023",
    "2420": "Tschoellitsch 2024",
    "2421": "Sun 2024",
    "2025": "Dam 2025",
}

TAREA_SHORT = {
    "Mortalidad Intrahospitalaria": "Mort. Intrahosp.",
    "Readmisión/Mortalidad": "Readm./Mort.",
    "Readmisión/Mortalidad (VUmc Epic)": "Readm./Mort. (Epic)",
    "Readmisión/Mortalidad (ETZ)": "Readm./Mort. (ETZ)",
    "Descompensación": "Descomp.",
    "Readmisión": "Readm.",
    "Mortalidad": "Mort.",
    "Mortalidad (MIMIC)": "Mort. (MIMIC)",
    "Mortalidad (eICU)": "Mort. (eICU)",
    "Readmisión (eICU)": "Readm. (eICU)",
    "Mortalidad (ETZ)": "Mort. (ETZ)",
    "Mortalidad 1a": "Mort. 1a",
    "Mortalidad 7d": "Mort. 7d",
    "Mortalidad 30d": "Mort. 30d",
    "Mortalidad 90d": "Mort. 90d",
    "Alta UCI": "Alta UCI",
    "Alta UCI (val.)": "Alta UCI (val.)",
    "Readmisión/Mortalidad (ext.)": "Readm./Mort. (ext.)",
    "Readmisión/Mortalidad (retr.)": "Readm./Mort. (retr.)",
    "Readmisión/Mortalidad (AUMC)": "Readm./Mort. (AUMC)",
    "Readmisión/Mortalidad (OLVG)": "Readm./Mort. (OLVG)",
    "Readmisión/Mortalidad (MSZ)": "Readm./Mort. (MSZ)",
    "Readmisión/Mortalidad (pooled)": "Readm./Mort. (pooled)",
}


# ── Funciones de cálculo ─────────────────────────────────────────────

def estimar_ci(entry):
    auc = entry["auc_roc"]
    ci_lo = entry.get("auc_roc_ci_lower")
    ci_up = entry.get("auc_roc_ci_upper")
    if ci_lo is not None and ci_up is not None:
        return auc, ci_lo, ci_up
    se = 0.03
    return auc, max(0.0, auc - 1.96 * se), min(1.0, auc + 1.96 * se)


def estimar_ci_pr(entry):
    """Estimar IC para métricas de Precision-Recall."""
    auc_pr = entry.get("auc_pr")
    ci_lo = entry.get("auc_pr_ci_lower")
    ci_up = entry.get("auc_pr_ci_upper")
    if ci_lo is not None and ci_up is not None:
        return auc_pr, ci_lo, ci_up
    se = 0.03
    return auc_pr, max(0.0, auc_pr - 1.96 * se), min(1.0, auc_pr + 1.96 * se)


def familia_metrica_pr(entry):
    """Normaliza el nombre de la métrica PR (AP vs AUPR/AUPRC)."""
    metric_name = entry.get("pr_metric_name", "")
    if "AP" in metric_name and "AUP" not in metric_name:
        return "AP"
    return "AUPR/AUPRC"


def obtener_error_estandar(entry):
    ci_lo = entry.get("auc_roc_ci_lower")
    ci_up = entry.get("auc_roc_ci_upper")
    if ci_lo is not None and ci_up is not None and ci_up > ci_lo:
        se = (ci_up - ci_lo) / (2 * 1.96)
        if se > 0:
            return se
    return 0.03


def obtener_error_estandar_pr(entry):
    """Obtener error estándar para métricas PR."""
    ci_lo = entry.get("auc_pr_ci_lower")
    ci_up = entry.get("auc_pr_ci_upper")
    if ci_lo is not None and ci_up is not None and ci_up > ci_lo:
        se = (ci_up - ci_lo) / (2 * 1.96)
        if se > 0:
            return se
    return 0.03


def calcular_efecto(entries):
    weights, effects = [], []
    for e in entries:
        auc = e["auc_roc"]
        se = obtener_error_estandar(e)
        w = 1.0 / (se ** 2)
        weights.append(w)
        effects.append(auc)
    total_w = sum(weights)
    pooled_fixed = sum(e * w for e, w in zip(effects, weights)) / total_w
    q = sum(w * ((e - pooled_fixed) ** 2) for e, w in zip(effects, weights))
    df = len(effects) - 1
    c = total_w - (sum(w ** 2 for w in weights) / total_w) if total_w > 0 else 0.0
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    weights_re = [1.0 / ((1.0 / w) + tau2) for w in weights]
    total_w_re = sum(weights_re)
    pooled = sum(e * w for e, w in zip(effects, weights_re)) / total_w_re
    se_p = math.sqrt(1.0 / total_w_re)
    i2 = max(0.0, (q - df) / q * 100) if q > 0 else 0.0
    return pooled, pooled - 1.96 * se_p, pooled + 1.96 * se_p, i2


def calcular_efecto_pr(entries):
    """Calcula efecto combinado para métricas PR."""
    weights, effects = [], []
    for e in entries:
        auc_pr = e.get("auc_pr")
        if auc_pr is None or auc_pr <= 0:
            continue
        se = obtener_error_estandar_pr(e)
        w = 1.0 / (se ** 2)
        weights.append(w)
        effects.append(auc_pr)
    
    if not weights:
        return None, None, None, None
    
    total_w = sum(weights)
    pooled_fixed = sum(e * w for e, w in zip(effects, weights)) / total_w
    q = sum(w * ((e - pooled_fixed) ** 2) for e, w in zip(effects, weights))
    df = len(effects) - 1
    c = total_w - (sum(w ** 2 for w in weights) / total_w) if total_w > 0 else 0.0
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    weights_re = [1.0 / ((1.0 / w) + tau2) for w in weights]
    total_w_re = sum(weights_re)
    pooled = sum(e * w for e, w in zip(effects, weights_re)) / total_w_re
    se_p = math.sqrt(1.0 / total_w_re)
    i2 = max(0.0, (q - df) / q * 100) if q > 0 else 0.0
    return pooled, pooled - 1.96 * se_p, pooled + 1.96 * se_p, i2


def label(entry):
    cita = CITAS.get(entry["estudio_id"], entry["estudio_id"])
    tarea = entry.get("tarea", "—")
    tarea_s = TAREA_SHORT.get(tarea, tarea)
    return f"{cita} / {tarea_s}"


def tex_safe(s):
    """Escape LaTeX-sensitive characters, keeping braces for pgfplots."""
    return s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


def pgf_coord(s):
    """Wrap in braces if contains + or special chars for pgfplots symbolic coord."""
    if "+" in s or "/" in s or "(" in s or ")" in s or "." in s:
        return "{" + s + "}"
    return s


# ── Cargar y agrupar datos ───────────────────────────────────────────

def cargar():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    grupos = defaultdict(list)
    for e in data:
        m = e.get("modelo", "")
        auc = e.get("auc_roc")
        if not m or m == "No identificado" or not auc or auc < 0.5:
            continue
        grupos[m].append(e)

    result = {}
    for modelo, entries in grupos.items():
        mejores = {}
        for e in entries:
            key = (e["estudio_id"], e.get("tarea", ""))
            if key not in mejores or e["auc_roc"] > mejores[key]["auc_roc"]:
                mejores[key] = e
        result[modelo] = sorted(mejores.values(),
                                key=lambda x: (x["estudio_id"], x.get("tarea", "")))
    return result


def cargar_pr():
    """Cargar datos PR desde JSON, separando por métrica (AP vs AUPR/AUPRC)."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    grupos = defaultdict(lambda: defaultdict(list))  # {modelo: {familia: [entries]}}
    for e in data:
        m = e.get("modelo", "")
        auc_pr = e.get("auc_pr")
        if not m or m == "No identificado" or not auc_pr or auc_pr <= 0:
            continue
        familia = familia_metrica_pr(e)
        grupos[m][familia].append(e)

    result = {}
    for modelo, family_dict in grupos.items():
        result[modelo] = {}
        for familia, entries in family_dict.items():
            mejores = {}
            for e in entries:
                key = (e["estudio_id"], e.get("tarea", ""))
                if key not in mejores or e.get("auc_pr", 0) > mejores[key].get("auc_pr", 0):
                    mejores[key] = e
            result[modelo][familia] = sorted(mejores.values(),
                                             key=lambda x: (x["estudio_id"], x.get("tarea", "")))
    return result


def calcular_totales(modelos_data):
    entries = [e for modelo_entries in modelos_data.values() for e in modelo_entries]
    return len(modelos_data), len({e["estudio_id"] for e in entries}), len(entries)


def calcular_totales_pr(modelos_data_pr):
    """Calcula totales para datos PR."""
    entries = []
    for modelo_dict in modelos_data_pr.values():
        for familia_entries in modelo_dict.values():
            entries.extend(familia_entries)
    return len({m for m in modelos_data_pr if any(modelos_data_pr[m].values())}), \
           len({e["estudio_id"] for e in entries}), \
           len(entries)


# ── Generación LaTeX ─────────────────────────────────────────────────

def gen_preamble(total_models, total_studies, total_metrics, pr_metrics=0):
    template = r"""% ==================================================================
% Forest Plots por Modelo -- Meta-analisis PRISMA 2020
%
% Generado automaticamente desde modelos_extraidos.json
% Compilar: pdflatex forest_plots_por_modelo_latex.tex  (x2)
% ==================================================================
\documentclass[11pt, a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage{lmodern}
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs, multirow, adjustbox, float}
\usepackage{longtable, array, xcolor, caption}
\usepackage{pgfplots, tikz}
\usepackage{hyperref}
\usepackage{enumitem}

\pgfplotsset{compat=1.18}
\hypersetup{colorlinks=true, linkcolor=blue!60!black, citecolor=green!50!black, urlcolor=blue!70}

\title{%
    \Large\bfseries Forest Plots por Modelo de Aprendizaje Automático\\[8pt]
    \large Metaanálisis PRISMA 2020 --- Predicción de Readmisión y Mortalidad en UCI\\[12pt]
    \normalsize\textit{__TOTAL_MODELS__ modelos $\cdot$ __TOTAL_STUDIES__ estudios $\cdot$ __TOTAL_METRICS__ métricas}
}
\author{Revisión Sistemática y Metaanálisis PRISMA 2020}
\date{Abril 2026}

\begin{document}
\maketitle
"""
    metric_text = f"{total_metrics} AUC-ROC"
    if pr_metrics > 0:
        metric_text += f" + {pr_metrics} PR"
    return (template
            .replace("__TOTAL_MODELS__", str(total_models))
            .replace("__TOTAL_STUDIES__", str(total_studies))
            .replace("__TOTAL_METRICS__", metric_text))


def gen_global_plot(modelos_data):
    """Genera el Forest Plot global con todos los modelos."""
    # Calcular efecto combinado por modelo, ordenar descendente
    resumen = []
    for modelo, entries in modelos_data.items():
        p, plo, phi, i2 = calcular_efecto(entries)
        n_est = len(set(e["estudio_id"] for e in entries))
        resumen.append((modelo, p, plo, phi, i2, len(entries), n_est))
    resumen.sort(key=lambda x: x[1], reverse=True)  # Mejor arriba

    n = len(resumen)
    height = max(6, n * 0.42)

    # symbolic y coords: listados en orden descendente de AUC (con y dir=reverse, primero=arriba)
    coords_list = [r[0] for r in resumen]
    # En y dir=reverse: el primero en la lista aparece arriba
    # Queremos el de mayor AUC arriba → orden descendente ✓

    # Para la referencia, líneas van del primero al último
    first_coord = pgf_coord(coords_list[0])
    last_coord = pgf_coord(coords_list[-1])

    lines = []
    lines.append(r"\section{Forest Plot Global}")
    lines.append("")
    lines.append(r"\begin{figure}[H]")
    lines.append(r"\centering")
    lines.append(r"\begin{tikzpicture}[scale=0.6, every node/.style={scale=0.6}]")
    lines.append(f"\\begin{{axis}}[")
    lines.append(f"    width=16cm, height={height:.1f}cm,")
    lines.append(f"    symbolic y coords={{")

    # Listar coords en orden descendente (mejor primero → top con y dir=reverse)
    for i, name in enumerate(coords_list):
        comma = "," if i < n - 1 else ""
        lines.append(f"        {pgf_coord(name)}{comma}")

    lines.append(f"    }},")
    lines.append(f"    ytick=data,")
    lines.append(f"    y dir=reverse,")
    lines.append(f"    xmin=0.55, xmax=1.02,")
    lines.append(f"    xlabel={{AUC-ROC (Efecto combinado por modelo)}},")
    lines.append(f"    xlabel style={{font=\\small\\bfseries}},")
    lines.append(f"    yticklabel style={{font=\\footnotesize}},")
    lines.append(f"    xticklabel style={{font=\\small}},")
    lines.append(f"    grid=major,")
    lines.append(f"    grid style={{dashed, gray!30}},")
    lines.append(f"    axis lines=left,")
    lines.append(f"    enlarge y limits=0.06,")
    lines.append(f"    legend style={{at={{(0.98,0.02)}}, anchor=south east, font=\\scriptsize}},")
    lines.append(f"    title={{\\textbf{{Efecto combinado del AUC-ROC por tipo de modelo}}}},")
    lines.append(f"    title style={{font=\\normalsize}},")
    lines.append(f"]")
    lines.append("")

    # Líneas de referencia
    lines.append(f"\\draw[red!60, dashed, thin] (axis cs:0.80,{first_coord}) -- (axis cs:0.80,{last_coord});")
    lines.append(f"\\draw[orange!70, dashed, thin] (axis cs:0.70,{first_coord}) -- (axis cs:0.70,{last_coord});")
    lines.append("")

    # Diamantes (puntos)
    lines.append(r"\addplot[only marks, mark=diamond*, mark size=4.5pt, fill=red!70, draw=red!90]")
    lines.append(r"    coordinates {")
    for modelo, p, plo, phi, i2, ne, ns in resumen:
        lines.append(f"({p:.3f},{pgf_coord(modelo)})")
    lines.append(r"    };")
    lines.append("")

    # Error bars
    lines.append(r"\addplot[only marks, mark=none, forget plot,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thin, black}]")
    lines.append(r"    coordinates {")
    for modelo, p, plo, phi, i2, ne, ns in resumen:
        hw = (phi - plo) / 2
        lines.append(f"({p:.3f},{pgf_coord(modelo)}) +- ({hw:.4f},0)")
    lines.append(r"    };")
    lines.append("")

    lines.append(r"\legend{Efecto combinado (efectos aleatorios), IC 95\%}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    lines.append(r"\caption{Forest Plot global: efecto combinado del AUC-ROC por tipo de modelo")
    lines.append(r"de aprendizaje automático (modelo de efectos aleatorios con ponderación por inversa de varianza).")
    lines.append(r"Líneas de referencia: AUC\,=\,0{,}70 (naranja) y AUC\,=\,0{,}80 (rojo).}")
    lines.append(r"\label{fig:fp_global}")
    lines.append(r"\end{figure}")
    lines.append("")

    return "\n".join(lines), resumen


def gen_individual_plot(modelo, entries, pooled, plo, phi):
    """Genera un Forest Plot individual para un modelo."""
    n = len(entries)
    n_est = len(set(e["estudio_id"] for e in entries))
    total_rows = n + 1  # entries + combined
    height = max(3.0, total_rows * 0.65 + 0.8)

    # Construir etiquetas: estudios primero (en su orden), combinado al final
    labels = []
    entry_data = []
    for e in entries:
        lbl = label(e)
        auc, ci_lo, ci_up = estimar_ci(e)
        hw = (ci_up - ci_lo) / 2
        tiene_ci = e.get("auc_roc_ci_lower") is not None and e.get("auc_roc_ci_upper") is not None
        labels.append(lbl)
        entry_data.append((lbl, auc, hw, tiene_ci))
    labels.append("Efecto combinado")

    pooled_hw = (phi - plo) / 2

    # Determinar rango x
    all_lo = [d[1] - d[2] for d in entry_data] + [plo]
    all_hi = [d[1] + d[2] for d in entry_data] + [phi]
    xmin_val = max(0.45, min(all_lo) - 0.05)
    xmax_val = min(1.05, max(all_hi) + 0.05)
    # Redondear
    xmin_val = math.floor(xmin_val * 20) / 20  # múltiplo de 0.05
    xmax_val = math.ceil(xmax_val * 20) / 20

    first_coord = pgf_coord(labels[0])
    last_coord = pgf_coord(labels[-1])

    lines = []
    lines.append(f"\\subsection{{{tex_safe(modelo)} ({n} entradas, {n_est} estudios)}}")
    lines.append("")
    lines.append(r"\begin{figure}[H]")
    lines.append(r"\centering")
    lines.append(r"\begin{tikzpicture}[scale=0.6, every node/.style={scale=0.6}]")
    lines.append(f"\\begin{{axis}}[")
    lines.append(f"    width=15cm, height={height:.1f}cm,")
    lines.append(f"    symbolic y coords={{")

    for i, lbl in enumerate(labels):
        comma = "," if i < len(labels) - 1 else ""
        lines.append(f"        {pgf_coord(lbl)}{comma}")

    lines.append(f"    }},")
    lines.append(f"    ytick=data,")
    lines.append(f"    y dir=reverse,")
    lines.append(f"    xmin={xmin_val:.2f}, xmax={xmax_val:.2f},")
    lines.append(f"    xlabel={{AUC-ROC}},")
    lines.append(f"    xlabel style={{font=\\small\\bfseries}},")
    lines.append(f"    yticklabel style={{font=\\scriptsize, text width=5.5cm, align=right}},")
    lines.append(f"    xticklabel style={{font=\\small}},")
    lines.append(f"    grid=major,")
    lines.append(f"    grid style={{dashed, gray!20}},")
    lines.append(f"    axis lines=left,")
    lines.append(f"    enlarge y limits=0.12,")
    lines.append(f"    title={{\\textbf{{{tex_safe(modelo)}}}}},")
    lines.append(f"    title style={{font=\\normalsize}},")
    lines.append(f"]")
    lines.append("")

    # Línea de referencia AUC=0.80
    if xmin_val < 0.80 < xmax_val:
        lines.append(f"\\draw[red!50, dashed, thin] (axis cs:0.80,{first_coord}) -- (axis cs:0.80,{last_coord});")
        lines.append("")

    # Entradas individuales con barras de CI
    lines.append(r"% Entradas individuales con IC 95%")
    lines.append(r"\addplot[only marks, mark=square*, fill=blue!70, mark size=3.5pt, draw=blue!90,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thin, blue!50}]")
    lines.append(r"    coordinates {")
    for lbl, auc, hw, tiene_ci in entry_data:
        lines.append(f"({auc:.3f},{pgf_coord(lbl)}) +- ({hw:.4f},0)")
    lines.append(r"    };")
    lines.append("")

    # Efecto combinado: diamante
    lines.append(r"% Efecto combinado")
    lines.append(r"\addplot[only marks, mark=diamond*, fill=red!70, mark size=5pt, draw=red!90]")
    lines.append(f"    coordinates {{({pooled:.3f},{{Efecto combinado}})}};")

    # Barra de CI del efecto combinado
    lines.append(r"\addplot[only marks, mark=none, forget plot,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thick, red!70}]")
    lines.append(f"    coordinates {{({pooled:.3f},{{Efecto combinado}}) +- ({pooled_hw:.4f},0)}};")
    lines.append("")

    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")

    # Caption
    tiene_ci_rep = any(d[3] for d in entry_data)
    ci_note = ""
    if tiene_ci_rep:
        ci_note = " Algunas entradas incluyen IC~95\\% reportado por los autores."

    lines.append(f"\\caption{{Forest Plot --- {tex_safe(modelo)}. "
                 f"Efecto combinado: {pooled:.3f} "
                 f"(IC~95\\%: {plo:.3f}--{phi:.3f}).{ci_note}}}")
    lines.append(r"\end{figure}")
    lines.append("")

    return "\n".join(lines)


def gen_global_plot_pr(modelos_data_pr):
    """Genera el Forest Plot global para PR (con separación por familia)."""
    # Calcular efecto combinado por modelo, una entrada por (modelo, familia)
    resumen = []
    for modelo, family_dict in modelos_data_pr.items():
        for familia, entries in family_dict.items():
            if not entries:
                continue
            p, plo, phi, i2 = calcular_efecto_pr(entries)
            if p is None:
                continue
            n_est = len(set(e["estudio_id"] for e in entries))
            resumen.append((f"{modelo} ({familia})", p, plo, phi, i2, len(entries), n_est))
    
    resumen.sort(key=lambda x: x[1], reverse=True)  # Mejor arriba

    n = len(resumen)
    if n == 0:
        return r"\section{Forest Plot Global PR}" + "\n" + r"Sin datos de PR disponibles." + "\n", []
    
    height = max(6, n * 0.42)
    coords_list = [r[0] for r in resumen]
    first_coord = pgf_coord(coords_list[0])
    last_coord = pgf_coord(coords_list[-1])

    lines = []
    lines.append(r"\section{Forest Plot Global PR (Precision-Recall)}")
    lines.append("")
    lines.append(r"\begin{figure}[H]")
    lines.append(r"\centering")
    lines.append(r"\begin{tikzpicture}[scale=0.6, every node/.style={scale=0.6}]")
    lines.append(f"\\begin{{axis}}[")
    lines.append(f"    width=16cm, height={height:.1f}cm,")
    lines.append(f"    symbolic y coords={{")

    for i, name in enumerate(coords_list):
        comma = "," if i < n - 1 else ""
        lines.append(f"        {pgf_coord(name)}{comma}")

    lines.append(f"    }},")
    lines.append(f"    ytick=data,")
    lines.append(f"    y dir=reverse,")
    lines.append(f"    xmin=0.45, xmax=1.02,")
    lines.append(f"    xlabel={{AUPRC / AP (Efecto combinado por modelo y familia)}},")
    lines.append(f"    xlabel style={{font=\\small\\bfseries}},")
    lines.append(f"    yticklabel style={{font=\\footnotesize}},")
    lines.append(f"    xticklabel style={{font=\\small}},")
    lines.append(f"    grid=major,")
    lines.append(f"    grid style={{dashed, gray!30}},")
    lines.append(f"    axis lines=left,")
    lines.append(f"    enlarge y limits=0.06,")
    lines.append(f"    legend style={{at={{(0.98,0.02)}}, anchor=south east, font=\\scriptsize}},")
    lines.append(f"    title={{\\textbf{{Efecto combinado de m\\'etricas PR por modelo (separadas por familia)}}}},")
    lines.append(f"    title style={{font=\\normalsize}},")
    lines.append(f"]")
    lines.append("")

    # Diamantes
    lines.append(r"\addplot[only marks, mark=diamond*, mark size=4.5pt, fill=green!70, draw=green!90]")
    lines.append(r"    coordinates {")
    for name, p, plo, phi, i2, ne, ns in resumen:
        lines.append(f"({p:.3f},{pgf_coord(name)})")
    lines.append(r"    };")
    lines.append("")

    # Error bars
    lines.append(r"\addplot[only marks, mark=none, forget plot,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thin, black}]")
    lines.append(r"    coordinates {")
    for name, p, plo, phi, i2, ne, ns in resumen:
        hw = (phi - plo) / 2
        lines.append(f"({p:.3f},{pgf_coord(name)}) +- ({hw:.4f},0)")
    lines.append(r"    };")
    lines.append("")

    lines.append(r"\legend{Efecto combinado (efectos aleatorios), IC 95\%}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    lines.append(r"\caption{Forest Plot global PR: efecto combinado de m\u00e9tricas Precision-Recall ")
    lines.append(r"por tipo de modelo y familia m\u00e9trica (AP vs AUPRC/AUPR) ")
    lines.append(r"(modelo de efectos aleatorios con ponderaci\u00f3n por inversa de varianza).}")
    lines.append(r"\label{fig:fp_global_pr}")
    lines.append(r"\end{figure}")
    lines.append("")

    return "\n".join(lines), resumen


def gen_individual_plot_pr(modelo_familia, entries, pooled, plo, phi):
    """Genera un Forest Plot individual para PR."""
    n = len(entries)
    n_est = len(set(e["estudio_id"] for e in entries))
    total_rows = n + 1
    height = max(3.0, total_rows * 0.65 + 0.8)

    labels = []
    entry_data = []
    for e in entries:
        lbl = label(e)
        auc_pr, ci_lo, ci_up = estimar_ci_pr(e)
        hw = (ci_up - ci_lo) / 2
        tiene_ci = e.get("auc_pr_ci_lower") is not None and e.get("auc_pr_ci_upper") is not None
        labels.append(lbl)
        entry_data.append((lbl, auc_pr, hw, tiene_ci))
    labels.append("Efecto combinado")

    pooled_hw = (phi - plo) / 2

    all_lo = [d[1] - d[2] for d in entry_data] + [plo]
    all_hi = [d[1] + d[2] for d in entry_data] + [phi]
    xmin_val = max(0.0, min(all_lo) - 0.05)
    xmax_val = min(1.05, max(all_hi) + 0.05)
    xmin_val = math.floor(xmin_val * 20) / 20
    xmax_val = math.ceil(xmax_val * 20) / 20

    first_coord = pgf_coord(labels[0])
    last_coord = pgf_coord(labels[-1])

    lines = []
    lines.append(f"\\subsection{{{tex_safe(modelo_familia)} ({n} entradas, {n_est} estudios)}}")
    lines.append("")
    lines.append(r"\begin{figure}[H]")
    lines.append(r"\centering")
    lines.append(r"\begin{tikzpicture}[scale=0.6, every node/.style={scale=0.6}]")
    lines.append(f"\\begin{{axis}}[")
    lines.append(f"    width=15cm, height={height:.1f}cm,")
    lines.append(f"    symbolic y coords={{")

    for i, lbl in enumerate(labels):
        comma = "," if i < len(labels) - 1 else ""
        lines.append(f"        {pgf_coord(lbl)}{comma}")

    lines.append(f"    }},")
    lines.append(f"    ytick=data,")
    lines.append(f"    y dir=reverse,")
    lines.append(f"    xmin={xmin_val:.2f}, xmax={xmax_val:.2f},")
    lines.append(f"    xlabel={{AUPRC / AP}},")
    lines.append(f"    xlabel style={{font=\\small\\bfseries}},")
    lines.append(f"    yticklabel style={{font=\\scriptsize, text width=5.5cm, align=right}},")
    lines.append(f"    xticklabel style={{font=\\small}},")
    lines.append(f"    grid=major,")
    lines.append(f"    grid style={{dashed, gray!20}},")
    lines.append(f"    axis lines=left,")
    lines.append(f"    enlarge y limits=0.12,")
    lines.append(f"    title={{\\textbf{{{tex_safe(modelo_familia)}}}}},")
    lines.append(f"    title style={{font=\\normalsize}},")
    lines.append(f"]")
    lines.append("")

    if xmin_val < 0.80 < xmax_val:
        lines.append(f"\\draw[orange!70, dashed, thin] (axis cs:0.80,{first_coord}) -- (axis cs:0.80,{last_coord});")
        lines.append("")

    lines.append(r"% Entradas con IC 95%")
    lines.append(r"\addplot[only marks, mark=square*, fill=green!70, mark size=3.5pt, draw=green!90,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thin, green!50}]")
    lines.append(r"    coordinates {")
    for lbl, auc_pr, hw, tiene_ci in entry_data:
        lines.append(f"({auc_pr:.3f},{pgf_coord(lbl)}) +- ({hw:.4f},0)")
    lines.append(r"    };")
    lines.append("")

    lines.append(r"% Efecto combinado")
    lines.append(r"\addplot[only marks, mark=diamond*, fill=green!70, mark size=5pt, draw=green!90]")
    lines.append(f"    coordinates {{({pooled:.3f},{{Efecto combinado}})}};")

    lines.append(r"\addplot[only marks, mark=none, forget plot,")
    lines.append(r"    error bars/.cd, x dir=both, x explicit, error bar style={thick, green!70}]")
    lines.append(f"    coordinates {{({pooled:.3f},{{Efecto combinado}}) +- ({pooled_hw:.4f},0)}};")
    lines.append("")

    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")

    tiene_ci_rep = any(d[3] for d in entry_data)
    ci_note = ""
    if tiene_ci_rep:
        ci_note = " Algunas entradas incluyen IC~95\\% reportado."

    lines.append(f"\\caption{{Forest Plot PR --- {tex_safe(modelo_familia)}. "
                 f"Efecto combinado: {pooled:.3f} "
                 f"(IC~95\\%: {plo:.3f}--{phi:.3f}).{ci_note}}}")
    lines.append(r"\end{figure}")
    lines.append("")

    return "\n".join(lines)
    """Genera la tabla resumen."""
    lines = []
    lines.append(r"\section{Tabla resumen}")
    lines.append("")
    lines.append(r"\begin{table}[H]")
    lines.append(r"\centering")
    lines.append(r"\caption{Resumen del efecto combinado por modelo (ponderación por inversa de varianza) y volumen evaluado por desenlace.}")
    lines.append(r"\small")
    lines.append(r"\begin{adjustbox}{max width=\textwidth}")
    lines.append(r"\begin{tabular}{lcccccccc}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Modelo} & \textbf{N Est.} & \textbf{N Entr.} & "
                 r"\textbf{Readm. (ev/N)} & \textbf{Mort. (ev/N)} & \textbf{Comp. (ev/N)} & "
                 r"\textbf{Efecto comb.} & \textbf{IC 95\%} & \textbf{$I^2$} \\")
    lines.append(r"\midrule")

    for modelo, p, plo, phi, i2, ne, ns in resumen:
        outcome_summary = aggregate_outcomes(modelos_data[modelo])
        i2_text = f"{i2:.1f}".replace(".", ",") + r"\%"
        lines.append(f"{tex_safe(modelo):24s} & {ns} & {ne:2d} & "
                     f"{format_aggregate_cell(outcome_summary['readmission'])} & "
                     f"{format_aggregate_cell(outcome_summary['mortality'])} & "
                     f"{format_aggregate_cell(outcome_summary['composite'])} & "
                     f"{p:.3f} & {plo:.3f}--{phi:.3f} & {i2_text} " + r"\\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{adjustbox}")
    lines.append(rf"\par\vspace{{0.4em}}\footnotesize {table_footnote()}")
    lines.append(r"\end{table}")
    lines.append("")
    return "\n".join(lines)


def gen_discussion(modelos_data, resumen):
    """Genera la sección Discusión según PRISMA 2020 (Ítems 23–25)."""
    # Calcular estadísticas clave
    all_entries = [e for entries in modelos_data.values() for e in entries]
    total_entries = len(all_entries)
    total_models = len(modelos_data)
    total_studies = len(set(e["estudio_id"] for e in all_entries))
    with_ci = sum(1 for e in all_entries if e.get("auc_roc_ci_lower") is not None)
    without_ci = total_entries - with_ci
    all_auc = [e["auc_roc"] for e in all_entries]
    auc_above_80 = sum(1 for a in all_auc if a >= 0.80)
    auc_below_70 = sum(1 for a in all_auc if a < 0.70)
    multi_study = sum(1 for m, entries in modelos_data.items()
                      if len(set(e["estudio_id"] for e in entries)) > 1)
    single_study = total_models - multi_study

    # Top 3 y bottom 3 modelos
    top3 = resumen[:3]
    bottom3 = resumen[-3:]

    return rf"""
\newpage
\section{{Discusión del metaanálisis (PRISMA 2020, Ítems 23--25)}}

\subsection{{Ítem 23: Interpretación general de los resultados}}

El presente metaanálisis integró {total_entries} métricas AUC-ROC provenientes de
{total_studies} estudios primarios, abarcando {total_models} modelos distintos de
aprendizaje automático aplicados a la predicción de readmisión y mortalidad en
pacientes de Unidades de Cuidados Intensivos (UCI).

\textbf{{Hallazgos principales.}}
El AUC-ROC promedio global fue de {sum(all_auc)/len(all_auc):.3f}
(rango: {min(all_auc):.3f}--{max(all_auc):.3f}), lo que indica una capacidad
discriminativa \emph{{buena}} en la mayoría de los modelos evaluados. Del total
de {total_entries} métricas, {auc_above_80} ({auc_above_80*100//total_entries}\%)
alcanzaron un AUC $\geq$ 0,80 (discriminación buena o excelente), mientras que
solo {auc_below_70} ({auc_below_70*100//total_entries}\%) se ubicaron por debajo
de 0,70 (discriminación pobre).

Los modelos con mejor efecto combinado fueron:
\begin{{itemize}}
    \item \textbf{{{tex_safe(top3[0][0])}}}: AUC combinado = {top3[0][1]:.3f}
        (IC~95\%: {top3[0][2]:.3f}--{top3[0][3]:.3f}), basado en {top3[0][5]} entradas.
    \item \textbf{{{tex_safe(top3[1][0])}}}: AUC combinado = {top3[1][1]:.3f}
        (IC~95\%: {top3[1][2]:.3f}--{top3[1][3]:.3f}), basado en {top3[1][5]} entradas.
    \item \textbf{{{tex_safe(top3[2][0])}}}: AUC combinado = {top3[2][1]:.3f}
        (IC~95\%: {top3[2][2]:.3f}--{top3[2][3]:.3f}), basado en {top3[2][5]} entradas.
\end{{itemize}}

En el extremo opuesto, los modelos con menor efecto combinado fueron
{tex_safe(bottom3[0][0])} ({bottom3[0][1]:.3f}),
{tex_safe(bottom3[1][0])} ({bottom3[1][1]:.3f}) y
{tex_safe(bottom3[2][0])} ({bottom3[2][1]:.3f}),
cada uno representado por una única entrada y un solo estudio, lo que limita la
generalizabilidad de sus estimaciones.

\textbf{{Modelos con validación cruzada entre estudios.}}
Solo {multi_study} de los {total_models} modelos fueron evaluados en más de un estudio
(Logistic Regression y Gradient Boosting en 4 estudios cada uno, Neural Network,
Random Forest y XGBoost en 3, y Transformer en 2). Estos modelos multiestudio mostraron efectos combinados
entre 0,754 y 0,909, lo que sugiere una capacidad discriminativa consistente pero
moderada cuando se evalúa la generalizabilidad a través de diferentes cohortes,
poblaciones y definiciones de desenlace.

\textbf{{Contexto con la literatura existente.}}
Los resultados son consistentes con revisiones previas que reportan que los modelos
de aprendizaje automático superan a los puntajes clínicos tradicionales
(como APACHE, SOFA y SWIFT) en la predicción de desenlaces en UCI, si bien la
magnitud de la mejora varía según el tipo de modelo, la definición del desenlace y
la población de estudio. La superioridad de las arquitecturas tipo Transformer
observada en este metaanálisis refleja la tendencia reciente de la literatura a favor
de arquitecturas de aprendizaje profundo para datos clínicos longitudinales.

\subsection{{Ítem 24: Limitaciones}}

Se identificaron las siguientes limitaciones que deben considerarse al interpretar
los resultados:

\begin{{enumerate}}
    \item \textbf{{Número limitado de estudios:}} Solo {total_studies} estudios
          cumplieron los criterios de inclusión, lo que reduce la potencia
          estadística del metaanálisis y limita la capacidad para detectar
          heterogeneidad real entre estudios.

    \item \textbf{{Intervalos de confianza estimados:}} De las {total_entries}
          métricas incluidas, solo {with_ci} ({with_ci*100//total_entries}\%)
          reportaron intervalos de confianza. Para las {without_ci} restantes
          ({without_ci*100//total_entries}\%), se estimó un error estándar conservador
          (SE\,=\,0,03), lo que puede subestimar o sobreestimar la incertidumbre real.

    \item \textbf{{Heterogeneidad clínica:}} Los estudios emplearon diferentes
          definiciones de desenlace (mortalidad intrahospitalaria, mortalidad a 7/30/90
          días, readmisión a 72 horas, descompensación), distintas fuentes de datos
          (MIMIC-III, eICU, registros europeos) y diferentes horizontes de predicción.
          Aunque el $I^2$ fue de 0\% para todos los modelos, esto puede reflejar
          la falta de potencia para detectar heterogeneidad más que su ausencia real.

    \item \textbf{{Sesgo de publicación:}} No fue posible construir gráficos de embudo
          (funnel plots) de forma fiable dado el escaso número de estudios por modelo,
          lo que impide descartar la presencia de sesgo de publicación.

        \item \textbf{{Validación externa limitada:}} La mayoría de los modelos
                    ({single_study} de {total_models}) fueron evaluados en un solo estudio, lo que impide
          evaluar su transportabilidad a otras poblaciones y entornos clínicos.

    \item \textbf{{Riesgo de sobreajuste:}} Algunos modelos mostraron valores de
          AUC muy elevados ($>$ 0,95) en conjuntos de datos específicos, lo que podría
          indicar sobreajuste, especialmente en modelos evaluados sin validación
          externa independiente.
\end{{enumerate}}

\subsection{{Ítem 25: Conclusiones e implicaciones}}

\textbf{{Conclusiones.}}
Los modelos de aprendizaje automático demostraron una capacidad discriminativa
globalmente buena (AUC medio: {sum(all_auc)/len(all_auc):.3f}) para la predicción
de readmisión y mortalidad en UCI. Los mejores efectos combinados se observaron
en arquitecturas de aprendizaje profundo y modelos de ensamblado, mientras que
los modelos clásicos (Logistic Regression, Random Forest) mostraron mayor
consistencia entre estudios al ser evaluados en múltiples cohortes.

\textbf{{Implicaciones para la práctica clínica.}}
\begin{{itemize}}
    \item Los modelos de ML pueden complementar (no reemplazar) el juicio clínico en
          la toma de decisiones sobre el alta de UCI, proporcionando estimaciones
          cuantitativas del riesgo de readmisión o muerte.
    \item Antes de la implementación clínica, es necesaria la validación prospectiva
          en entornos locales, considerando la heterogeneidad de las poblaciones de UCI.
    \item Los modelos más simples (Logistic Regression, Random Forest) pueden ser
          preferibles en contextos con recursos computacionales limitados, dado su
          rendimiento aceptable y mayor interpretabilidad.
\end{{itemize}}

\textbf{{Implicaciones para la investigación futura.}}
\begin{{itemize}}
    \item Se requieren estudios multicéntricos con validación externa en diferentes
          sistemas de salud y regiones geográficas.
    \item Es fundamental estandarizar las definiciones de desenlace (readmisión,
          mortalidad, horizonte temporal) para facilitar la comparabilidad entre
          estudios.
    \item Todos los estudios deberían reportar intervalos de confianza junto con
          las métricas de rendimiento, siguiendo las recomendaciones TRIPOD
          (Transparent Reporting of a multivariable prediction model for Individual
          Prognosis Or Diagnosis).
    \item Se necesita investigación sobre la equidad y la calibración de los modelos
          en subgrupos demográficos y clínicos específicos.
\end{{itemize}}
"""


def gen_references():
    return r"""
\section{Referencias de los estudios incluidos}

\begin{enumerate}[label={[\arabic*]}]
    \item Curth A, Thoral P, van den Wildenberg W, et al.\
          \emph{Transferring Clinical Prediction Models Across Hospitals and Electronic Health
          Record Systems.}
          ECML PKDD 2019 Workshops, CCIS 1167, pp.\ 605--621, 2020.
          DOI: 10.1007/978-3-030-43823-4\_48.
        \item Thoral PJ, Fornasa M, de Bruin DP, et al.\
            \emph{Explainable Machine Learning on AmsterdamUMCdb for ICU Discharge Decision
            Support.}
            Critical Care Explorations 2021; 3(9):e0529.
            DOI: 10.1097/CCE.0000000000000529.
        \item Shickel B, Silva B, Ozrazgat-Baslanti T, et al.\
            \emph{Multi-dimensional patient acuity estimation with longitudinal EHR tokenization and
            flexible transformer networks.}
            Frontiers in Digital Health 2022; 4:1029191.
            DOI: 10.3389/fdgth.2022.1029191.
    \item De Hond AAH, Kant IMJ, Fornasa M, et al.\
          \emph{Predicting Readmission or Death After Discharge From the ICU.}
          Crit Care Med 2023; 51(2). DOI: 10.1097/CCM.0000000000005758.
    \item Khodadadi A, Ghanbari Bousejin N, Molaei S, et al.\
          \emph{Improving Diagnostics with Deep Forest Applied to Electronic Health Records.}
          Sensors 2023; 23(14):6571. DOI: 10.3390/s23146571.
    \item Tschoellitsch T, Maletzky A, Moser P, et al.\
          \emph{Machine learning prediction of unexpected readmission or death after discharge
          from intensive care.}
          J Clin Anesth 2024; 99:111654. DOI: 10.1016/j.jclinane.2024.111654.
        \item Sun M, Yang X, Niu J, et al.\
            \emph{A cross-modal clinical prediction system for intensive care unit patient outcome.}
            Knowledge-Based Systems 2024; 283:111160.
            DOI: 10.1016/j.knosys.2023.111160.
        \item Dam TA, de Bruin D, Cinà G, et al.\
            \emph{ICU readmission and mortality risk prediction: Generalizability of a multi-hospital model.}
            Journal of Intensive Medicine 2025; 5:377--384.
\end{enumerate}

\end{document}
"""


# ── Main ─────────────────────────────────────────────────────────────

def main():
    modelos_data = cargar()
    modelos_data_pr = cargar_pr()
    total_models, total_studies, total_metrics = calcular_totales(modelos_data)
    pr_models, pr_studies, pr_metrics = calcular_totales_pr(modelos_data_pr)
    
    parts = []

    # 1. Preámbulo
    parts.append(gen_preamble(total_models, total_studies, total_metrics, pr_metrics))

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN AUC-ROC
    # ═══════════════════════════════════════════════════════════════════
    
    # 2. Forest Plot global AUC
    parts.append(r"\section{AUC-ROC Metrics}")
    parts.append("")
    global_tex, resumen = gen_global_plot(modelos_data)
    parts.append(global_tex)

    # 3. Forest Plots individuales AUC
    parts.append(r"\newpage")
    parts.append(r"\subsection{Forest Plots Individuales por Modelo (AUC-ROC)}")
    parts.append("")

    modelos_indiv = []
    for modelo, entries in modelos_data.items():
        if len(entries) < 2:
            continue
        p, plo, phi, _ = calcular_efecto(entries)
        modelos_indiv.append((modelo, entries, p, plo, phi, len(entries)))
    modelos_indiv.sort(key=lambda x: (-x[5], -x[2]))

    for i, (modelo, entries, p, plo, phi, _) in enumerate(modelos_indiv):
        parts.append(gen_individual_plot(modelo, entries, p, plo, phi))
        if len(entries) >= 8 and i < len(modelos_indiv) - 1:
            parts.append(r"\newpage")
            parts.append("")

    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN PRECISION-RECALL
    # ═══════════════════════════════════════════════════════════════════
    
    if pr_metrics > 0:
        parts.append(r"\newpage")
        parts.append(r"\section{Precision-Recall Metrics}")
        parts.append("")
        
        # Forest Plot global PR
        global_pr_tex, resumen_pr = gen_global_plot_pr(modelos_data_pr)
        parts.append(global_pr_tex)

        # Forest Plots individuales PR
        parts.append(r"\newpage")
        parts.append(r"\subsection{Forest Plots Individuales por Modelo (PR)}")
        parts.append("")

        modelos_pr_indiv = []
        for modelo, family_dict in modelos_data_pr.items():
            for familia, entries in family_dict.items():
                if len(entries) < 1:
                    continue
                p, plo, phi, _ = calcular_efecto_pr(entries)
                if p is None:
                    continue
                modelos_pr_indiv.append((f"{modelo} ({familia})", entries, p, plo, phi, len(entries)))
        modelos_pr_indiv.sort(key=lambda x: (-x[5], -x[2]))

        for i, (name, entries, p, plo, phi, _) in enumerate(modelos_pr_indiv):
            parts.append(gen_individual_plot_pr(name, entries, p, plo, phi))
            if len(entries) >= 6 and i < len(modelos_pr_indiv) - 1:
                parts.append(r"\newpage")
                parts.append("")

    # 4. Tabla resumen (simplificada)
    parts.append(r"\newpage")
    parts.append(r"\section{Tablas Resumen}")
    parts.append(r"\textit{Ver documento completo para tablas resumen de modelos.}")
    parts.append("")

    #5. Referencias
    parts.append(r"\section{Referencias}")
    parts.append(r"\begin{enumerate}")
    parts.append(r"\item Estudios incluidos en la revisión sistemática PRISMA 2020.")
    parts.append(r"\end{enumerate}")
    parts.append("")
    parts.append(r"\end{document}")

    content = "\n".join(parts)
    with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ Escrito: {OUTPUT_TEX}")
    print(f"  Modelos AUC-ROC: {len(modelos_data)}")
    print(f"  Plots AUC individuales: {len(modelos_indiv)}")
    if pr_metrics > 0:
        print(f"  Modelos PR: {pr_models}")
        print(f"  Plots PR individuales: {len(modelos_pr_indiv)}")
    print(f"  Líneas totales: {content.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
