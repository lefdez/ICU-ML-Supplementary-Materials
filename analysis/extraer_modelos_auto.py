#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor automático de modelos ML y métricas AUC desde PDFs.

Procesa TODOS los PDFs en el directorio, extrae texto con PyPDF2,
busca modelos ML y métricas AUC-ROC mediante regex, y genera
archivos de resumen + actualiza las tablas LaTeX.

NO requiere API externa (Gemini). Todo es local.

Uso:
    python extraer_modelos_auto.py
"""

import glob
import math
import os
import re
import json
from dataclasses import dataclass, asdict
from typing import Optional

import PyPDF2

from metadata_muestras import apply_metadata, aggregate_outcomes, format_aggregate_cell, format_outcome_cell, table_footnote

# ─────────────────────────── Configuración ───────────────────────────

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIRECTORIO, "data")
ORIGINALES_DIR = os.path.join(DATA_DIR, "originales")
SALIDA_JSON = os.path.join(DIRECTORIO, "modelos_extraidos.json")

# ─────────────────────────── Data classes ────────────────────────────

@dataclass
class ModeloExtraido:
    estudio_id: str
    pdf_nombre: str
    modelo: str
    tarea: str
    auc_roc: Optional[float] = None
    auc_roc_ci_lower: Optional[float] = None
    auc_roc_ci_upper: Optional[float] = None
    auc_pr: Optional[float] = None
    auc_pr_ci_lower: Optional[float] = None
    auc_pr_ci_upper: Optional[float] = None
    pr_metric_name: str = ""
    accuracy: Optional[float] = None
    sensitivity: Optional[float] = None
    specificity: Optional[float] = None
    f1_score: Optional[float] = None
    contexto: str = ""
    sample_size: Optional[int] = None
    event_count: Optional[int] = None
    event_kind: Optional[str] = None
    cohort_label: str = ""
    event_count_estimated: bool = False
    outcome_note: str = ""


# ─────────────────────── Extracción de PDF ───────────────────────────

def extraer_texto_pdf(filepath: str) -> str:
    """Extrae todo el texto de un PDF."""
    paginas = []
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    paginas.append(txt)
    except Exception as e:
        print(f"  ✗ Error leyendo PDF: {e}")
        return ""
    texto = "\n".join(paginas)
    print(f"  Páginas: {len(paginas)}, Tokens: {len(texto.split())}")
    return texto


FILENAME_TO_ID = {}


def extraer_id_estudio(filename: str) -> str:
    basename = os.path.basename(filename)
    # Check special mappings first
    for key, eid in FILENAME_TO_ID.items():
        if key in basename:
            return eid
    match = re.match(r"(\d{4})", basename)
    return match.group(1) if match else "????"


# ────────────────── Patrones de modelos ML conocidos ─────────────────

# Patrones regex para identificar modelos ML en texto científico
MODELO_PATTERNS = {
    "Logistic Regression": [
        r"logistic\s+regression",
        r"\bLR\b(?=\s*[\(,\.])",
        r"log[ií]stic[ao]?\s+regres",
    ],
    "Random Forest": [
        r"random\s+forest",
        r"\bRF\b(?=\s*[\(,\.])",
    ],
    "Gradient Boosting": [
        r"gradient\s+boost(?:ing|ed)",
        r"\bGBM\b",
        r"\bGBDT\b",
        r"gradient\s+tree",
    ],
    "XGBoost": [
        r"\bXGBoost\b",
        r"\bxgb\b",
        r"\bXGB\b",
        r"extreme\s+gradient\s+boost(?:ing|ed)",
    ],
    "LightGBM": [
        r"\bLightGBM\b",
        r"\bLGBM\b",
        r"light\s+gradient\s+boost",
    ],
    "CatBoost": [
        r"\bCatBoost\b",
    ],
    "AdaBoost": [
        r"\bAdaBoost\b",
        r"\bada[-\s]?boost\b",
    ],
    "SVM": [
        r"support\s+vector\s+machine",
        r"\bSVM\b",
        r"\bSVR\b",
    ],
    "Decision Tree": [
        r"decision\s+tree",
        r"\bCART\b",
    ],
    "Naive Bayes": [
        r"na[ïi]ve\s+bayes",
        r"\bNB\b(?=\s*[\(,\.])",
    ],
    "K-Nearest Neighbors": [
        r"k-?\s*nearest\s+neighbor",
        r"\bKNN\b",
        r"\bk-?NN\b",
        r"\bK-?NN\b",
    ],
    "Neural Network": [
        r"neural\s+network",
        r"\bNN\b(?=\s*[\(,\.])",
        r"\bANN\b",
        r"\bMLP\b",
        r"multi[-\s]?layer\s+perceptron",
    ],
    "LSTM": [
        r"\bLSTM\b",
        r"long\s+short[-\s]term\s+memory",
    ],
    "GRU": [
        r"\bGRU\b",
        r"gated\s+recurrent\s+unit",
    ],
    "Transformer": [
        r"\btransformer\b",
        r"\bBERT\b",
        r"\bGPT\b",
        r"\battention\s+mechanism\b",
        r"\bLongformer\b",
    ],
    "Patient Forest": [
        r"patient\s+forest",
    ],
    "Deep Forest": [
        r"deep\s+forest",
        r"\bgcForest\b",
        r"gc[-\s]?forest",
        r"multi[-\s]?grained\s+cascade",
    ],
    "Convolutional Neural Network": [
        r"\bCNN\b",
        r"convolutional\s+neural",
    ],
    "Recurrent Neural Network": [
        r"\bRNN\b(?!.*GRU|.*LSTM)",
        r"recurrent\s+neural\s+network",
    ],
    "Ensemble": [
        r"\bensemble\b(?!\s+(?:of|method))",
        r"\bstacking\b",
        r"\bbagging\b",
    ],
    "LASSO": [
        r"\bLASSO\b",
        r"least\s+absolute\s+shrinkage",
    ],
    "Ridge Regression": [
        r"\bridge\s+regression\b",
    ],
    "Elastic Net": [
        r"\belastic\s*net\b",
    ],
    "Cox Regression": [
        r"\bcox\b.*\bregression\b",
        r"\bcox\b.*\bmodel\b",
        r"proportional\s+hazard",
    ],
}


# ────────────────── Patrones de métricas AUC ─────────────────────────

def buscar_auc_valores(texto: str) -> list[dict]:
    """Busca todos los valores AUC/AUROC en el texto con su contexto."""
    resultados = []

    # Patrón principal: AUC/AUROC seguido de valor numérico con posible IC
    patterns = [
        # "AUC of 0.85" / "AUC = 0.85" / "AUC: 0.85" / "AUROC 0.85"
        r"(?:AUC[-\s]?ROC|AUROC|AUC|[Cc]-statistic|[Cc]-index)"
        r"[\s:=]*(?:of\s+)?(\d+\.?\d*)"
        r"(?:\s*\(?\s*(?:95%?\s*CI)?[:\s,]*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*\)?)?",

        # "0.85 (95% CI 0.80-0.90)" sin prefijo AUC directo
        r"(\d\.\d{2,3})\s*\(\s*(?:95%?\s*CI)?[:\s,]*(\d\.\d{2,3})\s*[-–]\s*(\d\.\d{2,3})\s*\)",
    ]

    for pat in patterns:
        for m in re.finditer(pat, texto, re.IGNORECASE):
            try:
                auc = float(m.group(1))
                ci_low = float(m.group(2)) if m.group(2) else None
                ci_up = float(m.group(3)) if m.group(3) else None

                # Filtrar valores válidos de AUC (entre 0.5 y 1.0)
                if 0.5 <= auc <= 1.0:
                    # Extraer contexto (100 chars antes y después)
                    start = max(0, m.start() - 150)
                    end = min(len(texto), m.end() + 150)
                    contexto = texto[start:end].replace("\n", " ").strip()

                    resultados.append({
                        "auc": auc,
                        "ci_lower": ci_low,
                        "ci_upper": ci_up,
                        "contexto": contexto,
                        "pos": m.start(),
                    })
            except (ValueError, IndexError):
                continue

    # Deduplicar por posición cercana
    if resultados:
        resultados.sort(key=lambda x: x["pos"])
        dedup = [resultados[0]]
        for r in resultados[1:]:
            if r["pos"] - dedup[-1]["pos"] > 10:
                dedup.append(r)
        return dedup

    return resultados


def identificar_modelos_en_texto(texto: str) -> dict[str, list[int]]:
    """Identifica qué modelos ML se mencionan y sus posiciones en el texto."""
    encontrados = {}
    texto_lower = texto.lower()

    for modelo, patterns in MODELO_PATTERNS.items():
        posiciones = []
        for pat in patterns:
            for m in re.finditer(pat, texto_lower):
                posiciones.append(m.start())
        if posiciones:
            encontrados[modelo] = sorted(set(posiciones))

    return encontrados


def asociar_auc_a_modelos(
    texto: str,
    modelos: dict[str, list[int]],
    aucs: list[dict],
) -> list[tuple[str, dict]]:
    """Asocia cada valor AUC al modelo ML más cercano en el texto."""
    asociaciones = []

    for auc_info in aucs:
        pos_auc = auc_info["pos"]
        mejor_modelo = None
        mejor_dist = float("inf")

        for modelo, posiciones in modelos.items():
            for pos_mod in posiciones:
                dist = abs(pos_auc - pos_mod)
                if dist < mejor_dist:
                    mejor_dist = dist
                    mejor_modelo = modelo

        # Solo asociar si el modelo está razonablemente cerca (< 2000 chars)
        if mejor_modelo and mejor_dist < 2000:
            asociaciones.append((mejor_modelo, auc_info))
        else:
            asociaciones.append(("No identificado", auc_info))

    return asociaciones


def detectar_tareas(texto: str) -> list[str]:
    """Detecta qué tareas predictivas aborda el artículo."""
    tareas = []
    texto_lower = texto.lower()

    task_patterns = {
        "Mortalidad": [r"mortality", r"mortalidad", r"death", r"survival"],
        "Readmisión": [r"readmission", r"re-?admission", r"reingreso", r"readmit"],
        "LOS (Estancia)": [r"length\s+of\s+stay", r"\bLOS\b", r"estancia"],
        "Alta UCI": [r"discharge", r"alta", r"safe\s+discharge", r"ready.*discharge"],
        "Diagnóstico": [r"diagnos", r"classification", r"disease\s+predict"],
    }

    for tarea, pats in task_patterns.items():
        for pat in pats:
            if re.search(pat, texto_lower):
                tareas.append(tarea)
                break

    return tareas if tareas else ["General"]


# ──────────────── Extracción de tablas numéricas del PDF ─────────────

def buscar_tablas_con_auc(texto: str) -> list[dict]:
    """
    Busca patrones tabulares en el texto extraído del PDF.
    Detecta filas con formato: Modelo ... 0.XXX ... 0.XXX
    """
    resultados = []

    # Buscar líneas con múltiples valores decimales (posibles filas de tabla)
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        # Buscar líneas que contienen al menos un valor AUC-like
        valores = re.findall(r"\b(0\.\d{2,4})\b", linea)
        if len(valores) >= 1:
            # Verificar si algún valor es un AUC plausible
            aucs_plausibles = [float(v) for v in valores if 0.5 <= float(v) <= 1.0]
            if aucs_plausibles:
                contexto_lines = lineas[max(0, i - 2):min(len(lineas), i + 3)]
                resultados.append({
                    "linea": linea.strip(),
                    "valores_auc": aucs_plausibles,
                    "contexto": "\n".join(contexto_lines),
                    "pos_linea": i,
                })

    return resultados


# ──────────────────────── Procesamiento principal ────────────────────

def procesar_pdf(filepath: str) -> list[ModeloExtraido]:
    """Procesa un PDF completo: extrae texto, identifica modelos y métricas."""
    estudio_id = extraer_id_estudio(filepath)
    nombre_pdf = os.path.basename(filepath)
    pdf_dir = os.path.dirname(filepath)  # Directorio real del PDF
    print(f"\n{'='*60}")
    print(f"▶ [{estudio_id}] {nombre_pdf}")
    print(f"{'='*60}")

    # 1. Extraer texto
    texto = extraer_texto_pdf(filepath)
    if not texto or len(texto.split()) < 100:
        print(f"  ✗ Texto insuficiente para análisis")
        return []

    # Guardar texto original
    originales_dir = os.path.join(pdf_dir, "originales")
    os.makedirs(originales_dir, exist_ok=True)
    nombre_base = os.path.splitext(nombre_pdf)[0]
    try:
        orig_path = os.path.join(originales_dir, nombre_base + "_original.txt")
        with open(orig_path, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"  Texto guardado en: originales/{nombre_base}_original.txt")
    except OSError as e:
        print(f"  ⚠ No se pudo guardar texto original: {e}")
        # Continuar sin guardar

    # 2. Identificar modelos ML
    modelos = identificar_modelos_en_texto(texto)
    print(f"  Modelos ML detectados: {list(modelos.keys())}")

    # 3. Buscar valores AUC
    aucs = buscar_auc_valores(texto)
    print(f"  Valores AUC encontrados: {len(aucs)}")
    for a in aucs:
        ci_str = ""
        if a["ci_lower"] and a["ci_upper"]:
            ci_str = f" (CI: {a['ci_lower']}-{a['ci_upper']})"
        print(f"    AUC={a['auc']}{ci_str}")

    # 4. Detectar tareas
    tareas = detectar_tareas(texto)
    print(f"  Tareas detectadas: {tareas}")

    # 5. Asociar AUCs a modelos
    asociaciones = asociar_auc_a_modelos(texto, modelos, aucs)

    # 6. Construir resultados
    resultados = []
    tarea_principal = tareas[0] if tareas else "General"

    for modelo, auc_info in asociaciones:
        # Detectar tarea específica del contexto
        tarea_ctx = tarea_principal
        ctx_lower = auc_info["contexto"].lower()
        if "mortality" in ctx_lower or "mortalidad" in ctx_lower or "death" in ctx_lower:
            tarea_ctx = "Mortalidad"
        elif "readmission" in ctx_lower or "reingreso" in ctx_lower or "readmit" in ctx_lower:
            tarea_ctx = "Readmisión"
        elif "discharge" in ctx_lower or "alta" in ctx_lower:
            tarea_ctx = "Alta UCI"
        elif "decompensation" in ctx_lower or "descomp" in ctx_lower:
            tarea_ctx = "Descompensación"
        elif "diagnos" in ctx_lower:
            tarea_ctx = "Diagnóstico"

        resultados.append(ModeloExtraido(
            estudio_id=estudio_id,
            pdf_nombre=nombre_pdf,
            modelo=modelo,
            tarea=tarea_ctx,
            auc_roc=auc_info["auc"],
            auc_roc_ci_lower=auc_info.get("ci_lower"),
            auc_roc_ci_upper=auc_info.get("ci_upper"),
            contexto=auc_info["contexto"][:200],
        ))

    # Si no se encontraron AUCs pero sí modelos, registrar los modelos sin métricas
    if not aucs and modelos:
        print(f"  ⚠ Se encontraron modelos pero sin valores AUC explícitos")
        for modelo in modelos:
            resultados.append(ModeloExtraido(
                estudio_id=estudio_id,
                pdf_nombre=nombre_pdf,
                modelo=modelo,
                tarea=tarea_principal,
                contexto="AUC no encontrado en texto extraído",
            ))

    # 7. Guardar resumen individual
    resumen_path = os.path.join(pdf_dir, nombre_base + "_resumen_ML.txt")
    guardar_resumen_ml(resultados, modelos, tareas, aucs, resumen_path, estudio_id, nombre_pdf)

    return resultados


def guardar_resumen_ml(
    resultados: list[ModeloExtraido],
    modelos: dict,
    tareas: list,
    aucs: list,
    filepath: str,
    estudio_id: str,
    nombre_pdf: str,
):
    """Guarda un archivo de resumen ML para el estudio."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"## Extracción Automática de Modelos ML — Estudio {estudio_id}\n\n")
            f.write(f"**Archivo:** {nombre_pdf}\n\n")

            f.write("### Modelos ML Detectados\n\n")
            for modelo in modelos:
                f.write(f"- {modelo}\n")

            f.write(f"\n### Tareas Predictivas\n\n")
            for tarea in tareas:
                f.write(f"- {tarea}\n")

            f.write(f"\n### Métricas AUC-ROC Extraídas\n\n")
            if resultados:
                f.write("| Modelo | Tarea | AUC-ROC | IC 95% | Métrica PR | IC 95% PR |\n")
                f.write("| :-- | :-- | :-- | :-- | :-- | :-- |\n")
                for r in resultados:
                    ci = ""
                    if r.auc_roc_ci_lower and r.auc_roc_ci_upper:
                        ci = f"{r.auc_roc_ci_lower}–{r.auc_roc_ci_upper}"
                    pr_ci = ""
                    if r.auc_pr_ci_lower is not None and r.auc_pr_ci_upper is not None:
                        pr_ci = f"{r.auc_pr_ci_lower}–{r.auc_pr_ci_upper}"
                    auc_str = f"{r.auc_roc:.3f}" if r.auc_roc else "N/A"
                    pr_str = f"{r.auc_pr:.3f}" if r.auc_pr is not None else "N/A"
                    pr_label = r.pr_metric_name or "AUC-PR"
                    f.write(f"| {r.modelo} | {r.tarea} | {auc_str} | {ci or 'N/A'} | {pr_label}: {pr_str} | {pr_ci or 'N/A'} |\n")
            else:
                f.write("No se encontraron métricas AUC-ROC en el texto extraído.\n")

            f.write(f"\n### Contextos de Métricas\n\n")
            for r in resultados:
                if r.auc_roc:
                    f.write(f"**{r.modelo}** (AUC={r.auc_roc}):\n")
                    f.write(f"> {r.contexto}\n\n")

        print(f"  ✓ Resumen guardado: {os.path.basename(filepath)}")
    except OSError as e:
        print(f"  ⚠ No se pudo guardar resumen: {e}")


# ──────────────────────── Generación LaTeX ───────────────────────────

def generar_latex_desde_resultados(todos_resultados: list[ModeloExtraido], output_dir: str = ""):
    """Genera las tablas LaTeX directamente desde los resultados extraídos."""
    if not output_dir:
        output_dir = DIRECTORIO
    from collections import defaultdict

    for resultado in todos_resultados:
        apply_metadata(resultado)

    # ── Tabla 1: Subanálisis por modelo ──
    modelo_aucs = defaultdict(list)
    modelo_estudios = defaultdict(set)

    for r in todos_resultados:
        if r.auc_roc and r.auc_roc >= 0.5:
            modelo_aucs[r.modelo].append(r.auc_roc)
            modelo_estudios[r.modelo].add(r.estudio_id)

    modelos_ord = sorted(
        modelo_aucs.keys(),
        key=lambda m: (-len(modelo_estudios[m]), -sum(modelo_aucs[m]) / len(modelo_aucs[m])),
    )

    def calcular_efecto_inv_var(entries: list[ModeloExtraido]) -> tuple[float, float, float, float]:
        if not entries:
            return 0.0, 0.0, 0.0, 0.0

        if len(entries) == 1:
            auc = entries[0].auc_roc or 0.0
            if entries[0].auc_roc_ci_lower is not None and entries[0].auc_roc_ci_upper is not None:
                return auc, entries[0].auc_roc_ci_lower, entries[0].auc_roc_ci_upper, 0.0
            half_width = 1.96 * 0.03
            return auc, max(0.0, auc - half_width), min(1.0, auc + half_width), 0.0

        pesos = []
        efectos = []
        for entry in entries:
            auc = entry.auc_roc or 0.0
            ci_low = entry.auc_roc_ci_lower
            ci_up = entry.auc_roc_ci_upper
            if ci_low is not None and ci_up is not None and ci_up > ci_low:
                se = (ci_up - ci_low) / (2 * 1.96)
            else:
                se = 0.03
            if se <= 0:
                se = 0.03
            peso = 1.0 / (se ** 2)
            pesos.append(peso)
            efectos.append(auc)

        total_peso = sum(pesos)
        pooled = sum(efecto * peso for efecto, peso in zip(efectos, pesos)) / total_peso
        se_pooled = math.sqrt(1.0 / total_peso)
        ci_low = max(0.0, pooled - 1.96 * se_pooled)
        ci_up = min(1.0, pooled + 1.96 * se_pooled)

        q = sum(peso * ((efecto - pooled) ** 2) for efecto, peso in zip(efectos, pesos))
        df = len(efectos) - 1
        i2 = max(0.0, (q - df) / q * 100) if q > 0 else 0.0
        return pooled, ci_low, ci_up, i2

    def calcular_efecto_inv_var_pr(entries: list[ModeloExtraido]) -> tuple[float, float, float, float]:
        if not entries:
            return 0.0, 0.0, 0.0, 0.0

        if len(entries) == 1:
            auc = entries[0].auc_pr or 0.0
            if entries[0].auc_pr_ci_lower is not None and entries[0].auc_pr_ci_upper is not None:
                return auc, entries[0].auc_pr_ci_lower, entries[0].auc_pr_ci_upper, 0.0
            half_width = 1.96 * 0.03
            return auc, max(0.0, auc - half_width), min(1.0, auc + half_width), 0.0

        pesos = []
        efectos = []
        for entry in entries:
            auc = entry.auc_pr or 0.0
            ci_low = entry.auc_pr_ci_lower
            ci_up = entry.auc_pr_ci_upper
            if ci_low is not None and ci_up is not None and ci_up > ci_low:
                se = (ci_up - ci_low) / (2 * 1.96)
            else:
                se = 0.03
            if se <= 0:
                se = 0.03
            peso = 1.0 / (se ** 2)
            pesos.append(peso)
            efectos.append(auc)

        total_peso = sum(pesos)
        pooled = sum(efecto * peso for efecto, peso in zip(efectos, pesos)) / total_peso
        se_pooled = math.sqrt(1.0 / total_peso)
        ci_low = max(0.0, pooled - 1.96 * se_pooled)
        ci_up = min(1.0, pooled + 1.96 * se_pooled)

        q = sum(peso * ((efecto - pooled) ** 2) for efecto, peso in zip(efectos, pesos))
        df = len(efectos) - 1
        i2 = max(0.0, (q - df) / q * 100) if q > 0 else 0.0
        return pooled, ci_low, ci_up, i2

    def familia_metrica_pr(metric_name: str) -> str:
        nombre = (metric_name or "AUC-PR").strip().upper()
        if nombre == "AP":
            return "AP"
        return "AUPR/AUPRC"

    filas_sub = []
    for modelo in modelos_ord:
        entries = [r for r in todos_resultados if r.modelo == modelo and r.auc_roc and r.auc_roc >= 0.5]
        outcome_summary = aggregate_outcomes(entries)
        n_est = len(modelo_estudios[modelo])
        n_ent = len(entries)
        media, ci_low, ci_up, i2 = calcular_efecto_inv_var(entries)
        filas_sub.append(
            f"    {modelo} & {n_est} & {n_ent} & "
            f"{format_aggregate_cell(outcome_summary['readmission'])} & "
            f"{format_aggregate_cell(outcome_summary['mortality'])} & "
            f"{format_aggregate_cell(outcome_summary['composite'])} & "
            f"{media:.3f} & {ci_low:.3f}--{ci_up:.3f} & {i2:.1f}\\% \\\\" 
        )

    tabla_sub = (
        "\\begin{table}[H]\n\\centering\n"
        "\\caption{Subanálisis del AUC por tipo de modelo de aprendizaje automático, incorporando el volumen evaluado por desenlace.}"
        "\\label{tab:subgroup_ml}\n\\small\n"
        "\\begin{adjustbox}{max width=\\textwidth}\n"
        "\\begin{tabular}{lcccccccc}\n\\toprule\n"
        "\\textbf{Modelo} & \\textbf{N Estudios} & \\textbf{N Entr.} & \\textbf{Readm. (ev/N)} & "
        "\\textbf{Mort. (ev/N)} & \\textbf{Comp. (ev/N)} & \\textbf{Efecto combinado} & "
        "\\textbf{IC 95\\%} & \\textbf{I\\textsuperscript{2}} \\\\\n\\midrule\n"
        + "\n".join(filas_sub) + "\n"
        "\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n"
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}\n"
        "\\end{table}"
    )

    # ── Tabla 1b: Subanálisis PR por familia de métrica ──
    pr_groups = defaultdict(list)
    pr_group_studies = defaultdict(set)
    for r in todos_resultados:
        if r.auc_pr is None or r.auc_pr <= 0:
            continue
        key = (familia_metrica_pr(r.pr_metric_name), r.modelo)
        pr_groups[key].append(r)
        pr_group_studies[key].add(r.estudio_id)

    filas_sub_pr = []
    for familia, modelo in sorted(
        pr_groups.keys(),
        key=lambda key: (key[0], -len(pr_group_studies[key]), -sum(x.auc_pr or 0 for x in pr_groups[key]) / len(pr_groups[key])),
    ):
        entries = pr_groups[(familia, modelo)]
        outcome_summary = aggregate_outcomes(entries)
        n_est = len(pr_group_studies[(familia, modelo)])
        n_ent = len(entries)
        media, ci_low, ci_up, i2 = calcular_efecto_inv_var_pr(entries)
        filas_sub_pr.append(
            f"    {familia} & {modelo} & {n_est} & {n_ent} & "
            f"{format_aggregate_cell(outcome_summary['readmission'])} & "
            f"{format_aggregate_cell(outcome_summary['mortality'])} & "
            f"{format_aggregate_cell(outcome_summary['composite'])} & "
            f"{media:.3f} & {ci_low:.3f}--{ci_up:.3f} & {i2:.1f}\\% \\\\" 
        )

    tabla_sub_pr = (
        "\\begin{table}[H]\n\\centering\n"
        "\\caption{Subanálisis descriptivo de métricas basadas en precision-recall, separando AP de la familia AUPR/AUPRC.}"
        "\\label{tab:subgroup_pr}\n\\small\n"
        "\\begin{adjustbox}{max width=\\textwidth}\n"
        "\\begin{tabular}{llcccccccc}\n\\toprule\n"
        "\\textbf{Tipo PR} & \\textbf{Modelo} & \\textbf{N Estudios} & \\textbf{N Entr.} & \\textbf{Readm. (ev/N)} & "
        "\\textbf{Mort. (ev/N)} & \\textbf{Comp. (ev/N)} & \\textbf{Efecto combinado} & \\textbf{IC 95\\%} & \\textbf{I\\textsuperscript{2}} \\\\\n\\midrule\n"
        + ("\n".join(filas_sub_pr) if filas_sub_pr else "    % Sin métricas PR disponibles\n") + "\n"
        "\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n"
        "\\par\\vspace{0.4em}\\footnotesize La familia AUPR/AUPRC agrupa etiquetas equivalentes de área bajo la curva precision-recall. AP se mantiene por separado por no ser directamente intercambiable con AUPR en todos los contextos. "
        f"{table_footnote()}\n"
        "\\end{table}"
    )

    # ── Tabla 2: Detalle por estudio ──
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

    # Seleccionar mejor AUC por (estudio, modelo, tarea)
    mejores = {}
    for r in todos_resultados:
        if r.auc_roc and r.auc_roc >= 0.5:
            key = (r.estudio_id, r.modelo, r.tarea)
            if key not in mejores or r.auc_roc > mejores[key].auc_roc:
                mejores[key] = r

    entradas = sorted(mejores.values(), key=lambda r: (r.estudio_id, r.modelo, r.tarea))

    filas_det = []
    for r in entradas:
        cite = CITAS.get(r.estudio_id, f"Estudio {r.estudio_id}")
        ci = ""
        if r.auc_roc_ci_lower and r.auc_roc_ci_upper:
            ci = f" ({r.auc_roc_ci_lower:.2f}--{r.auc_roc_ci_upper:.2f})"
        filas_det.append(
            f"    {cite} & {r.modelo} & {r.tarea} & {format_outcome_cell(r)} & {r.auc_roc:.3f}{ci} \\\\" 
        )

    tabla_det = (
        "\\begin{table}[H]\n\\centering\n"
        "\\caption{Detalle de AUC-ROC por estudio, modelo y tarea predictiva.}"
        "\\label{tab:detalle_auc}\n\\small\n"
        "\\begin{adjustbox}{max width=\\textwidth}\n"
        "\\begin{tabular}{lllll}\n\\toprule\n"
        "\\textbf{Estudio} & \\textbf{Modelo} & \\textbf{Tarea} & \\textbf{Eventos/N} & "
        "\\textbf{AUC-ROC (IC 95\\%)} \\\\\n\\midrule\n"
        + "\n".join(filas_det) + "\n"
        "\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n"
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}\n"
        "\\end{table}"
    )

    entradas_pr = sorted(
        [r for r in todos_resultados if r.auc_pr is not None and r.auc_pr > 0],
        key=lambda r: (r.estudio_id, r.modelo, r.tarea),
    )
    filas_pr = []
    for r in entradas_pr:
        cite = CITAS.get(r.estudio_id, f"Estudio {r.estudio_id}")
        pr_ci = ""
        if r.auc_pr_ci_lower is not None and r.auc_pr_ci_upper is not None:
            pr_ci = f" ({r.auc_pr_ci_lower:.2f}--{r.auc_pr_ci_upper:.2f})"
        metric_label = r.pr_metric_name or "AUC-PR"
        filas_pr.append(
            f"    {cite} & {r.modelo} & {r.tarea} & {format_outcome_cell(r)} & {metric_label} & {r.auc_pr:.3f}{pr_ci} \\\\" 
        )

    tabla_pr = (
        "\\begin{table}[H]\n\\centering\n"
        "\\caption{Detalle de métricas basadas en precision-recall por estudio, modelo y tarea predictiva.}"
        "\\label{tab:detalle_pr}\n\\small\n"
        "\\begin{adjustbox}{max width=\\textwidth}\n"
        "\\begin{tabular}{llllll}\n\\toprule\n"
        "\\textbf{Estudio} & \\textbf{Modelo} & \\textbf{Tarea} & \\textbf{Eventos/N} & \\textbf{Tipo PR} & \\textbf{Valor (IC 95\\%)} \\\\\n\\midrule\n"
        + ("\n".join(filas_pr) if filas_pr else "    % Sin métricas PR disponibles\n") + "\n"
        "\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n"
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}\n"
        "\\end{table}"
    )

    # Guardar archivos
    sub_path = os.path.join(output_dir, "tabla_subanalisis_ml.tex")
    sub_pr_path = os.path.join(output_dir, "tabla_subanalisis_pr.tex")
    det_path = os.path.join(output_dir, "tabla_detalle_estudios.tex")
    det_pr_path = os.path.join(output_dir, "tabla_detalle_estudios_pr.tex")

    try:
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(tabla_sub)
        with open(sub_pr_path, "w", encoding="utf-8") as f:
            f.write(tabla_sub_pr)
        with open(det_path, "w", encoding="utf-8") as f:
            f.write(tabla_det)
        with open(det_pr_path, "w", encoding="utf-8") as f:
            f.write(tabla_pr)
    except OSError as e:
        print(f"  ⚠ No se pudieron guardar archivos LaTeX: {e}")

    return tabla_sub, tabla_sub_pr, tabla_det, tabla_pr


# ──────────────────── Datos manuales de respaldo ─────────────────────

def cargar_datos_manuales() -> list[ModeloExtraido]:
    """
    Datos verificados manualmente de TODOS los estudios.
    Fuente principal para la generación de tablas LaTeX.
    """
    manuales = [
        # ══════════════════════════════════════════════════════════════
        # 2016: Curth et al. (2020) – Transferring clinical prediction models
        # Tabla 2: AUROC para mortalidad intrahospitalaria en UCI
        # Datos en 2 hospitales: VUmc Epic y ETZ
        # ══════════════════════════════════════════════════════════════
        ModeloExtraido("2016", "2016-transfer-clinical-models.pdf", "Logistic Regression", "Readmisión/Mortalidad (VUmc Epic)", 0.800),
        ModeloExtraido("2016", "2016-transfer-clinical-models.pdf", "Gradient Boosting", "Readmisión/Mortalidad (VUmc Epic)", 0.746),
        ModeloExtraido("2016", "2016-transfer-clinical-models.pdf", "Logistic Regression", "Readmisión/Mortalidad (ETZ)", 0.745),
        ModeloExtraido("2016", "2016-transfer-clinical-models.pdf", "Gradient Boosting", "Readmisión/Mortalidad (ETZ)", 0.751),

        # ══════════════════════════════════════════════════════════════
        # 2110: Thoral et al. (2021) – Explainable ML on AmsterdamUMCdb
        # Tabla S6 del suplemento digital — 5 algoritmos × 3 desenlaces
        # Validation cohort n=3,929; eventos exactos (Tabla S5 suplemento)
        # Nota: el artículo llama "Gradient Boosting" al algoritmo XGBoost
        # ══════════════════════════════════════════════════════════════
        # Desenlace combinado (readmisión y/o muerte a 7 días)
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "XGBoost",             "Readmisión/Mortalidad", 0.780, 0.747, 0.814, 0.189, None, None, "AUPRC"),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "SVM",                "Readmisión/Mortalidad", 0.789, 0.756, 0.822),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Random Forest",      "Readmisión/Mortalidad", 0.780, 0.746, 0.813),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Logistic Regression","Readmisión/Mortalidad", 0.783, 0.749, 0.816),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "LightGBM",           "Readmisión/Mortalidad", 0.776, 0.742, 0.809),
        # Solo mortalidad (74 muertes en validación)
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "XGBoost",             "Mortalidad", 0.834, 0.777, 0.891, 0.086, None, None, "AUPRC"),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "SVM",                "Mortalidad", 0.836, 0.779, 0.893),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Random Forest",      "Mortalidad", 0.845, 0.789, 0.901),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Logistic Regression","Mortalidad", 0.849, 0.793, 0.904),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "LightGBM",           "Mortalidad", 0.839, 0.782, 0.895),
        # Solo readmisión (189 readmisiones en validación)
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "XGBoost",             "Readmisión", 0.715, 0.673, 0.757, 0.102, None, None, "AUPRC"),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "SVM",                "Readmisión", 0.734, 0.692, 0.775),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Random Forest",      "Readmisión", 0.737, 0.695, 0.778),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "Logistic Regression","Readmisión", 0.743, 0.702, 0.784),
        ModeloExtraido("2110", "2110-explainable-icu-discharge.pdf", "LightGBM",           "Readmisión", 0.724, 0.682, 0.766),

        # ══════════════════════════════════════════════════════════════
        # 2216: Shickel et al. (2022) – Multi-dimensional Patient Acuity
        # Mejores resultados (tokenización + valores continuos)
        # ══════════════════════════════════════════════════════════════
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Mortalidad Intrahospitalaria", 0.978),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "GRU", "Mortalidad Intrahospitalaria", 0.960),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "GRU + Attention", "Mortalidad Intrahospitalaria", 0.965),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "CatBoost", "Mortalidad Intrahospitalaria", 0.901),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "XGBoost", "Mortalidad Intrahospitalaria", 0.867),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Readmisión", 0.843),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "GRU", "Readmisión", 0.750),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "GRU + Attention", "Readmisión", 0.770),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "CatBoost", "Readmisión", 0.759),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "XGBoost", "Readmisión", 0.762),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Mortalidad 7d", 0.983),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Mortalidad 30d", 0.953),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Mortalidad 90d", 0.923),
        ModeloExtraido("2216", "2216-patient-acuity-transformer.pdf", "Transformer", "Mortalidad 1a", 0.892),

        # ══════════════════════════════════════════════════════════════
        # 2313: De Hond et al. (2023) – Predicting readmission or death
        # Gradient Boosting (Pacmed Critical)
        # ══════════════════════════════════════════════════════════════
        ModeloExtraido("2313", "2313-readmission-death-retraining.pdf", "Gradient Boosting", "Readmisión/Mortalidad", 0.72, 0.67, 0.76),
        ModeloExtraido("2313", "2313-readmission-death-retraining.pdf", "Gradient Boosting", "Readmisión/Mortalidad (retr.)", 0.79, 0.75, 0.82),

        # ══════════════════════════════════════════════════════════════
        # 2314: Khodadadi et al. (2023) – Deep Forest Applied to EHR
        # Tabla 3: AUROC 75:25 split
        # ══════════════════════════════════════════════════════════════
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Patient Forest", "Mortalidad (MIMIC)", 0.801, None, None, 0.619, None, None, "AUPRC"),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Random Forest", "Mortalidad (MIMIC)", 0.763),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Neural Network", "Mortalidad (MIMIC)", 0.749),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Logistic Regression", "Mortalidad (MIMIC)", 0.773),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "SVM", "Mortalidad (MIMIC)", 0.746),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Naive Bayes", "Mortalidad (MIMIC)", 0.658),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "K-Nearest Neighbors", "Mortalidad (MIMIC)", 0.654),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "XGBoost", "Mortalidad (MIMIC)", 0.772),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Patient Forest", "Mortalidad (eICU)", 0.864, None, None, 0.5732, None, None, "AUPRC"),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Random Forest", "Mortalidad (eICU)", 0.839),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Neural Network", "Mortalidad (eICU)", 0.816),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Logistic Regression", "Mortalidad (eICU)", 0.833),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "SVM", "Mortalidad (eICU)", 0.847),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "XGBoost", "Mortalidad (eICU)", 0.813),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Patient Forest", "Readmisión (eICU)", 0.869, None, None, 0.5952, None, None, "AUPRC"),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Random Forest", "Readmisión (eICU)", 0.814),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Neural Network", "Readmisión (eICU)", 0.812),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "Logistic Regression", "Readmisión (eICU)", 0.819),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "SVM", "Readmisión (eICU)", 0.821),
        ModeloExtraido("2314", "2314-deep-forest-ehr.pdf", "XGBoost", "Readmisión (eICU)", 0.808),

        # ══════════════════════════════════════════════════════════════
        # 2420: Tschoellitsch et al. (2024) – ML prediction readmission/death
        # ══════════════════════════════════════════════════════════════
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "Random Forest", "Readmisión/Mortalidad", 0.721, None, None, 0.087, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "Ensemble", "Readmisión/Mortalidad", 0.714, None, None, 0.080, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "XGBoost", "Readmisión/Mortalidad", 0.699, None, None, 0.084, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "AdaBoost", "Readmisión/Mortalidad", 0.688, None, None, 0.067, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "Logistic Regression", "Readmisión/Mortalidad", 0.680, None, None, 0.080, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "Neural Network", "Readmisión/Mortalidad", 0.652, None, None, 0.063, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "XGBoost", "Readmisión/Mortalidad (ext.)", 0.648, None, None, 0.142, None, None, "AP"),
        ModeloExtraido("2420", "2420-icu-readmission-death.pdf", "Random Forest", "Readmisión/Mortalidad (ext.)", 0.641, None, None, 0.140, None, None, "AP"),

        # ══════════════════════════════════════════════════════════════
        # 2421: Sun et al. (2024) – Cross-modal clinical prediction (CTCL)
        # eICU-CRD database. Tables 2 & 3.
        # ══════════════════════════════════════════════════════════════
        # Mortality
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Logistic Regression", "Mortalidad (eICU)", 0.848, None, None, 0.7625, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Random Forest", "Mortalidad (eICU)", 0.872, None, None, 0.8025, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Transformer", "Mortalidad (eICU)", 0.879, None, None, 0.8114, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Neural Network", "Mortalidad (eICU)", 0.885),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "CTCL", "Mortalidad (eICU)", 0.894, None, None, 0.8372, None, None, "AUPR"),
        # Readmission
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Logistic Regression", "Readmisión (eICU)", 0.808, None, None, 0.8433, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Random Forest", "Readmisión (eICU)", 0.822, None, None, 0.8553, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Transformer", "Readmisión (eICU)", 0.822, None, None, 0.8569, None, None, "AUPR"),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "Neural Network", "Readmisión (eICU)", 0.822),
        ModeloExtraido("2421", "2421-crossmodal-icu-outcomes.pdf", "CTCL", "Readmisión (eICU)", 0.853, None, None, 0.8687, None, None, "AUPR"),

        # ══════════════════════════════════════════════════════════════
        # 2025: Dam et al. (2025) – ICU readmission & mortality risk
        # Multi-hospital Gradient Boosting (Pacmed Critical)
        # Composite readmission/mortality within 7 days
        # AUROC reported as percentages in Table 2
        # ══════════════════════════════════════════════════════════════
        # Internal validation per hospital
        ModeloExtraido("2025", "2025-multihospital-readmission-mortality.pdf", "Gradient Boosting", "Readmisión/Mortalidad (AUMC)", 0.765),
        ModeloExtraido("2025", "2025-multihospital-readmission-mortality.pdf", "Gradient Boosting", "Readmisión/Mortalidad (OLVG)", 0.740),
        ModeloExtraido("2025", "2025-multihospital-readmission-mortality.pdf", "Gradient Boosting", "Readmisión/Mortalidad (MSZ)", 0.709),
        # Pooled model
        ModeloExtraido("2025", "2025-multihospital-readmission-mortality.pdf", "Gradient Boosting", "Readmisión/Mortalidad (pooled)", 0.729),
        # External validation: pooled model on AUMC
        ModeloExtraido("2025", "2025-multihospital-readmission-mortality.pdf", "Gradient Boosting", "Readmisión/Mortalidad (ext.)", 0.698),
    ]
    return manuales


# ──────────────────────────── Main ────────────────────────────────────

def main():
    print("=" * 70)
    print("  EXTRACTOR AUTOMÁTICO DE MODELOS ML Y MÉTRICAS AUC DESDE PDFs")
    print("=" * 70)
    print(f"Directorio: {DIRECTORIO}\n")

    # Encontrar todos los PDFs en la carpeta data/
    pdfs = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    print(f"PDFs encontrados: {len(pdfs)}")
    for p in pdfs:
        print(f"  • {os.path.basename(p)}")

    if not pdfs:
        print("✗ No se encontraron PDFs.")
        return

    # Procesar cada PDF
    todos_resultados: list[ModeloExtraido] = []
    estudios_procesados: set[str] = set()

    for pdf_path in pdfs:
        eid = extraer_id_estudio(pdf_path)
        resultados = procesar_pdf(pdf_path)
        if resultados:
            todos_resultados.extend(resultados)
            estudios_procesados.add(eid)
        else:
            print(f"  ⚠ Sin resultados del PDF para estudio {eid}")

    # Complementar con datos manuales (fuente canónica para los estudios ya curados)
    datos_manuales = cargar_datos_manuales()
    estudios_manuales = {m.estudio_id for m in datos_manuales}

    # Para estudios con curación manual, descartar la extracción automática ruidosa.
    resultados_automaticos_filtrados = [
        r for r in todos_resultados if r.estudio_id not in estudios_manuales
    ]
    todos_resultados = resultados_automaticos_filtrados + datos_manuales

    # Deduplicar: para cada (estudio, modelo, tarea), quedarse con el mejor AUC
    mejores_global = {}
    for r in todos_resultados:
        if r.modelo == "No identificado":
            continue
        if r.auc_roc and r.auc_roc >= 0.5:
            key = (r.estudio_id, r.modelo, r.tarea)
            if key not in mejores_global or r.auc_roc > mejores_global[key].auc_roc:
                mejores_global[key] = r

    resultados_finales = list(mejores_global.values())

    for resultado in resultados_finales:
        apply_metadata(resultado)

    # Resumen general
    print(f"\n{'='*70}")
    print(f"  RESUMEN GENERAL")
    print(f"{'='*70}")
    print(f"  Total métricas únicas: {len(resultados_finales)}")

    estudios_unicos = set(r.estudio_id for r in resultados_finales)
    modelos_unicos = set(r.modelo for r in resultados_finales)
    print(f"  Estudios: {sorted(estudios_unicos)}")
    print(f"  Modelos: {sorted(modelos_unicos)}")

    # Guardar JSON con todos los resultados
    json_data = [asdict(r) for r in resultados_finales]
    json_path = os.path.join(DIRECTORIO, "modelos_extraidos.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"\n  ✓ Datos JSON guardados: modelos_extraidos.json")
    except OSError as e:
        print(f"\n  ⚠ No se pudo guardar JSON: {e}")

    # Generar tablas LaTeX
    print(f"\n{'='*70}")
    print(f"  GENERANDO TABLAS LATEX")
    print(f"{'='*70}")

    tabla_sub, tabla_sub_pr, tabla_det, tabla_pr = generar_latex_desde_resultados(resultados_finales, DIRECTORIO)

    print(f"\n  ✓ tabla_subanalisis_ml.tex")
    print("  ✓ tabla_subanalisis_pr.tex")
    print(f"  ✓ tabla_detalle_estudios.tex")
    print(f"  ✓ tabla_detalle_estudios_pr.tex")

    print(f"\n{'='*70}")
    print("  TABLA SUBANÁLISIS POR MODELO")
    print(f"{'='*70}")
    print(tabla_sub)

    print(f"\n{'='*70}")
    print("  TABLA SUBANÁLISIS PR")
    print(f"{'='*70}")
    print(tabla_sub_pr)

    print(f"\n{'='*70}")
    print("  TABLA DETALLE POR ESTUDIO")
    print(f"{'='*70}")
    print(tabla_det)

    print(f"\n{'='*70}")
    print("  TABLA DETALLE MÉTRICAS PR")
    print(f"{'='*70}")
    print(tabla_pr)

    print(f"\n{'='*70}")
    print("  ✓ PROCESO COMPLETADO")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
