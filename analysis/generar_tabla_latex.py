#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de tabla LaTeX consolidada para meta-análisis PRISMA.

Lee todos los archivos de resumen (_resumen.txt y _resumen_ML.txt) en el
directorio de trabajo, extrae modelos ML y métricas AUC-ROC, y genera
una tabla LaTeX lista para insertar en el artículo de revisión sistemática.

Uso:
    python generar_tabla_latex.py

Salida:
    tabla_subanalisis_ml.tex  — Tabla LaTeX con subanálisis por tipo de modelo
    tabla_detalle_estudios.tex — Tabla detallada estudio × modelo × AUC
"""

import glob
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

from metadata_muestras import aggregate_outcomes, format_aggregate_cell, format_outcome_cell, table_footnote

# ─────────────────────────── Configuración ───────────────────────────

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))

# Datos manuales de respaldo: se usan cuando los archivos de resumen no están
# disponibles localmente (ej. Google Drive cloud-only) o como suplemento
# cuando el parser automático no extrae correctamente todos los modelos.
# Formato: lista de tuplas (estudio_id, estudio_nombre, modelo, tarea, auc, ci_low, ci_up)
DATOS_MANUALES = [
    # ── Estudio 2016: Curth et al. (2020) ──
    ("2016", "Curth et al. (2020)", "Logistic Regression", "Readmisión/Mortalidad (VUmc Epic)", 0.800, None, None),
    ("2016", "Curth et al. (2020)", "Gradient Boosting", "Readmisión/Mortalidad (VUmc Epic)", 0.746, None, None),
    ("2016", "Curth et al. (2020)", "Logistic Regression", "Readmisión/Mortalidad (ETZ)", 0.745, None, None),
    ("2016", "Curth et al. (2020)", "Gradient Boosting", "Readmisión/Mortalidad (ETZ)", 0.751, None, None),

    # ── Estudio 2216: Shickel et al. (2022) ──
    ("2216", "Shickel et al. (2022)", "Transformer", "Mortalidad Intrahospitalaria", 0.978, None, None),
    ("2216", "Shickel et al. (2022)", "GRU", "Mortalidad Intrahospitalaria", 0.960, None, None),
    ("2216", "Shickel et al. (2022)", "GRU + Attention", "Mortalidad Intrahospitalaria", 0.965, None, None),
    ("2216", "Shickel et al. (2022)", "CatBoost", "Mortalidad Intrahospitalaria", 0.901, None, None),
    ("2216", "Shickel et al. (2022)", "XGBoost", "Mortalidad Intrahospitalaria", 0.867, None, None),
    ("2216", "Shickel et al. (2022)", "Transformer", "Readmisión UCI", 0.843, None, None),
    ("2216", "Shickel et al. (2022)", "GRU", "Readmisión UCI", 0.750, None, None),
    ("2216", "Shickel et al. (2022)", "GRU + Attention", "Readmisión UCI", 0.770, None, None),
    ("2216", "Shickel et al. (2022)", "CatBoost", "Readmisión UCI", 0.759, None, None),
    ("2216", "Shickel et al. (2022)", "XGBoost", "Readmisión UCI", 0.762, None, None),
    ("2216", "Shickel et al. (2022)", "Transformer", "Mortalidad a 7 días", 0.983, None, None),
    ("2216", "Shickel et al. (2022)", "Transformer", "Mortalidad a 30 días", 0.953, None, None),
    ("2216", "Shickel et al. (2022)", "Transformer", "Mortalidad a 90 días", 0.923, None, None),
    ("2216", "Shickel et al. (2022)", "Transformer", "Mortalidad a 1 año", 0.892, None, None),

    # ── Estudio 2313: De Hond et al. (2023) ──
    ("2313", "De Hond et al. (2023)", "Gradient Boosting", "Readmisión/Mortalidad", 0.72, 0.67, 0.76),
    ("2313", "De Hond et al. (2023)", "Gradient Boosting", "Readmisión/Mortalidad (retrained)", 0.79, 0.75, 0.82),

    # ── Estudio 2421: Sun et al. (2024) ──
    ("2421", "Sun et al. (2024)", "Logistic Regression", "Mortalidad (eICU)", 0.848, None, None),
    ("2421", "Sun et al. (2024)", "Random Forest", "Mortalidad (eICU)", 0.872, None, None),
    ("2421", "Sun et al. (2024)", "Transformer", "Mortalidad (eICU)", 0.879, None, None),
    ("2421", "Sun et al. (2024)", "Neural Network", "Mortalidad (eICU)", 0.885, None, None),
    ("2421", "Sun et al. (2024)", "CTCL", "Mortalidad (eICU)", 0.894, None, None),
    ("2421", "Sun et al. (2024)", "Logistic Regression", "Readmisión (eICU)", 0.808, None, None),
    ("2421", "Sun et al. (2024)", "Random Forest", "Readmisión (eICU)", 0.822, None, None),
    ("2421", "Sun et al. (2024)", "Transformer", "Readmisión (eICU)", 0.822, None, None),
    ("2421", "Sun et al. (2024)", "Neural Network", "Readmisión (eICU)", 0.822, None, None),
    ("2421", "Sun et al. (2024)", "CTCL", "Readmisión (eICU)", 0.853, None, None),
]

# Archivos de salida
SALIDA_SUBANALISIS = os.path.join(DIRECTORIO, "tabla_subanalisis_ml.tex")
SALIDA_SUBANALISIS_PR = os.path.join(DIRECTORIO, "tabla_subanalisis_pr.tex")
SALIDA_DETALLE = os.path.join(DIRECTORIO, "tabla_detalle_estudios.tex")
SALIDA_DETALLE_PR = os.path.join(DIRECTORIO, "tabla_detalle_estudios_pr.tex")

# Mapeo de IDs de estudio a citas
ESTUDIO_CITAS = {
    "2016": "Curth et al. (2020)",
    "2110": "Thoral et al. (2021)",
    "2216": "Shickel et al. (2022)",
    "2313": "De Hond et al. (2023)",
    "2314": "Khodadadi et al. (2023)",
    "2420": "Tschoellitsch et al. (2024)",
    "2421": "Sun et al. (2024)",
    "2025": "Dam et al. (2025)",
}

# Mapeo de nombres de modelos normalizados
MODELO_NORMALIZACION = {
    "random forest": "Random Forest",
    "rf": "Random Forest",
    "logistic regression": "Logistic Regression",
    "lr": "Logistic Regression",
    "regresión logística": "Logistic Regression",
    "lstm": "LSTM",
    "long short-term memory": "LSTM",
    "lightgbm": "LightGBM",
    "light gradient boosting": "LightGBM",
    "light gradient boosting machine": "LightGBM",
    "xgboost": "XGBoost",
    "extreme gradient boosting": "XGBoost",
    "catboost": "CatBoost",
    "gradient boosting": "Gradient Boosting",
    "gradient boosted": "Gradient Boosting",
    "gru": "GRU",
    "gru con atención": "GRU + Attention",
    "gru con atención (eventos tokenizados + valores continuos)": "GRU + Attention",
    "gru con atención (series temporales multivariadas remuestreadas)": "GRU + Attention",
    "gru (series temporales multivariadas remuestreadas)": "GRU",
    "transformer": "Transformer",
    "transformer (eventos tokenizados + valores continuos)": "Transformer",
    "transformer (solo eventos tokenizados discretos)": "Transformer",
    "ctcl": "CTCL",
    "contrastive learning": "CTCL",
    "code-text cross-modal contrastive learning": "CTCL",
    "patient forest": "Patient Forest",
    "deep forest": "Deep Forest",
    "neural network": "Neural Network",
    "neural networks": "Neural Network",
    "redes neuronales": "Neural Network",
    "nn": "Neural Network",
    "svm": "SVM",
    "support vector machine": "SVM",
}


# ─────────────────────────── Data classes ────────────────────────────

@dataclass
class MetricaModelo:
    """Almacena las métricas de un modelo en un estudio."""
    estudio_id: str
    estudio_nombre: str
    modelo: str
    tarea: str  # mortalidad, reingreso, descompensación, etc.
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
    precision: Optional[float] = None
    f1_score: Optional[float] = None
    caracteristicas: str = ""
    cohorte: str = ""


# ────────────────────── Funciones de parsing ─────────────────────────

def extraer_id_estudio(filename: str) -> str:
    """Extrae el ID numérico del estudio desde el nombre del archivo."""
    match = re.match(r"(\d{4})", os.path.basename(filename))
    return match.group(1) if match else "????"


def normalizar_modelo(nombre_raw: str) -> str:
    """Normaliza el nombre de un modelo ML."""
    nombre_lower = nombre_raw.strip().lower()
    nombre_lower = re.sub(r"\*+", "", nombre_lower).strip()
    if nombre_lower in MODELO_NORMALIZACION:
        return MODELO_NORMALIZACION[nombre_lower]
    # Intentar coincidencia parcial
    for key, value in MODELO_NORMALIZACION.items():
        if key in nombre_lower:
            return value
    return nombre_raw.strip()


def parse_float(valor: str) -> Optional[float]:
    """Intenta parsear un valor numérico, retorna None si no es posible."""
    if not valor or valor.strip().upper() in ("N/A", "NO REPORTADO", "-", "—", ""):
        return None
    valor_clean = re.sub(r"\*+", "", valor).strip()
    # Extraer el primer número decimal
    match = re.search(r"(\d+\.?\d*)", valor_clean)
    if match:
        return float(match.group(1))
    return None


def parse_ci(texto: str) -> tuple[Optional[float], Optional[float]]:
    """Extrae intervalo de confianza de un texto como '0.91 (0.9-0.91)' o '95% CI 0.67–0.76'."""
    # Patrón: (lower–upper) o (lower-upper)
    match = re.search(r"[\(\[]?\s*(\d+\.?\d*)\s*[–\-]\s*(\d+\.?\d*)\s*[\)\]]?", texto)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def parsear_tabla_markdown(lineas: list[str], inicio: int) -> list[dict]:
    """Parsea una tabla en formato markdown a partir de un índice de inicio."""
    filas = []
    headers = []

    # Buscar la línea de encabezado
    if inicio < len(lineas) and "|" in lineas[inicio]:
        headers = [h.strip() for h in lineas[inicio].split("|") if h.strip()]
        inicio += 1

    # Saltar la línea separadora (| --- | --- |)
    if inicio < len(lineas) and re.match(r"^\s*\|[\s\-:]+\|", lineas[inicio]):
        inicio += 1

    # Leer filas de datos
    for i in range(inicio, len(lineas)):
        linea = lineas[i].strip()
        if not linea or "|" not in linea:
            break
        celdas = [c.strip() for c in linea.split("|") if c.strip()]
        if celdas and len(celdas) >= 2:
            fila = {}
            for j, header in enumerate(headers):
                if j < len(celdas):
                    fila[header] = celdas[j]
            filas.append(fila)

    return filas


def extraer_metricas_de_resumen(filepath: str) -> list[MetricaModelo]:
    """Extrae todas las métricas de modelos ML de un archivo de resumen."""
    metricas = []
    estudio_id = extraer_id_estudio(filepath)
    estudio_nombre = ESTUDIO_CITAS.get(estudio_id, f"Estudio {estudio_id}")

    with open(filepath, "r", encoding="utf-8") as f:
        contenido = f.read()
    lineas = contenido.split("\n")

    # Buscar tablas markdown con métricas
    for i, linea in enumerate(lineas):
        if "|" in linea and re.search(
            r"(modelo|model|AUC|ROC|tarea|coorte|cohorte)", linea, re.IGNORECASE
        ):
            tabla = parsear_tabla_markdown(lineas, i)
            if tabla:
                metricas.extend(
                    _procesar_tabla_generica(tabla, estudio_id, estudio_nombre)
                )
                break  # Solo la primera tabla relevante por resumen

    # Si no se encontraron tablas, intentar extracción por regex del texto
    if not metricas:
        metricas.extend(_extraer_metricas_por_regex(contenido, estudio_id, estudio_nombre))

    return metricas


def _procesar_tabla_generica(
    tabla: list[dict], estudio_id: str, estudio_nombre: str
) -> list[MetricaModelo]:
    """Procesa una tabla genérica de métricas y extrae MetricaModelo."""
    metricas = []

    for fila in tabla:
        # Intentar identificar columnas clave
        modelo_raw = (
            fila.get("Modelo", "")
            or fila.get("Model", "")
            or fila.get("Modelo ML", "")
            or ""
        )
        modelo = normalizar_modelo(modelo_raw) if modelo_raw else None
        if not modelo:
            continue

        # AUC-ROC
        auc_str = (
            fila.get("AUC-ROC", "")
            or fila.get("AUC-ROC (95% CI)", "")
            or fila.get("AUROC", "")
            or fila.get("AUC", "")
            or fila.get("Media", "")
            or ""
        )
        auc_val = parse_float(auc_str)
        ci_lower, ci_upper = parse_ci(auc_str)

        # Tarea / Cohorte
        tarea = (
            fila.get("Tarea", "")
            or fila.get("Task", "")
            or ""
        )
        cohorte = fila.get("Coorte", "") or fila.get("Cohorte", "") or ""
        caracteristicas = fila.get("Características", "") or ""

        # Mortalidad Intrahospitalaria
        mort_inhosp = fila.get("Mortalidad Intrahospitalaria", "")
        if mort_inhosp:
            auc_mort = parse_float(mort_inhosp)
            if auc_mort:
                metricas.append(MetricaModelo(
                    estudio_id=estudio_id,
                    estudio_nombre=estudio_nombre,
                    modelo=modelo,
                    tarea="Mortalidad Intrahospitalaria",
                    auc_roc=auc_mort,
                ))

        # Readmisión UCI
        readm = fila.get("Readmisión UCI", "")
        if readm:
            auc_readm = parse_float(readm)
            if auc_readm:
                metricas.append(MetricaModelo(
                    estudio_id=estudio_id,
                    estudio_nombre=estudio_nombre,
                    modelo=modelo,
                    tarea="Readmisión UCI",
                    auc_roc=auc_readm,
                ))

        # Mortalidad multi-horizonte (columnas específicas)
        for col_name in [
            "Mortalidad a 7 días", "Mortalidad a 30 días",
            "Mortalidad a 90 días", "Mortalidad a 1 año",
        ]:
            val = fila.get(col_name, "")
            if val:
                auc_multi = parse_float(val)
                if auc_multi:
                    metricas.append(MetricaModelo(
                        estudio_id=estudio_id,
                        estudio_nombre=estudio_nombre,
                        modelo=modelo,
                        tarea=col_name,
                        auc_roc=auc_multi,
                    ))

        # Si hay AUC genérico (no de columnas multi-horizonte) y tarea
        if auc_val and tarea:
            metricas.append(MetricaModelo(
                estudio_id=estudio_id,
                estudio_nombre=estudio_nombre,
                modelo=modelo,
                tarea=tarea.strip("*").strip(),
                auc_roc=auc_val,
                auc_roc_ci_lower=ci_lower,
                auc_roc_ci_upper=ci_upper,
                caracteristicas=caracteristicas,
                cohorte=cohorte,
            ))
        elif auc_val and not tarea and cohorte:
            metricas.append(MetricaModelo(
                estudio_id=estudio_id,
                estudio_nombre=estudio_nombre,
                modelo=modelo,
                tarea=f"General ({cohorte})",
                auc_roc=auc_val,
                auc_roc_ci_lower=ci_lower,
                auc_roc_ci_upper=ci_upper,
                cohorte=cohorte,
            ))
        elif auc_val and not tarea and not any(
            fila.get(c) for c in [
                "Mortalidad Intrahospitalaria", "Readmisión UCI",
                "Mortalidad a 7 días", "Mortalidad a 30 días",
                "Mortalidad a 90 días", "Mortalidad a 1 año",
            ]
        ):
            metricas.append(MetricaModelo(
                estudio_id=estudio_id,
                estudio_nombre=estudio_nombre,
                modelo=modelo,
                tarea="General",
                auc_roc=auc_val,
                auc_roc_ci_lower=ci_lower,
                auc_roc_ci_upper=ci_upper,
                caracteristicas=caracteristicas,
            ))

    # AUC-PR y otras métricas opcionales
    for fila in tabla:
        modelo_raw = fila.get("Modelo", "") or fila.get("Model", "") or ""
        modelo = normalizar_modelo(modelo_raw) if modelo_raw else None
        if not modelo:
            continue

        auc_pr_str = fila.get("AUC-PR", "")
        accuracy_str = fila.get("Accuracy", "") or fila.get("Exactitud", "")
        sens_str = fila.get("Sensitivity", "") or fila.get("Sensibilidad", "")
        spec_str = fila.get("Specificity", "") or fila.get("Especificidad", "")
        prec_str = fila.get("Precision", "") or fila.get("Precisión", "")
        f1_str = fila.get("F1-Score", "") or fila.get("F1", "")

        # Actualizar métricas existentes de este modelo
        for m in metricas:
            if m.modelo == modelo and m.estudio_id == estudio_id:
                if auc_pr_str:
                    m.auc_pr = m.auc_pr or parse_float(auc_pr_str)
                if accuracy_str:
                    m.accuracy = m.accuracy or parse_float(accuracy_str)
                if sens_str:
                    m.sensitivity = m.sensitivity or parse_float(sens_str)
                if spec_str:
                    m.specificity = m.specificity or parse_float(spec_str)
                if prec_str:
                    m.precision = m.precision or parse_float(prec_str)
                if f1_str:
                    m.f1_score = m.f1_score or parse_float(f1_str)

    return metricas


def _extraer_metricas_por_regex(
    contenido: str, estudio_id: str, estudio_nombre: str
) -> list[MetricaModelo]:
    """Extrae métricas buscando patrones de texto como 'AUC: 0.XX' o 'AUROC 0.XX'."""
    metricas = []

    # Patrón: "AUC-ROC: 0.XX" o "AUROC: 0.XX" o "AUC: 0.XX (95% CI x.xx-x.xx)"
    pattern = re.compile(
        r"(?:AUC[-\s]?ROC|AUROC|AUC)\s*[:=]?\s*(\d+\.?\d*)"
        r"(?:\s*\(?\s*(?:95%?\s*CI)?\s*[:\s]?\s*(\d+\.?\d*)\s*[–\-]\s*(\d+\.?\d*)\s*\)?)?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(contenido):
        auc_val = float(match.group(1))
        ci_lower = float(match.group(2)) if match.group(2) else None
        ci_upper = float(match.group(3)) if match.group(3) else None
        if 0.4 <= auc_val <= 1.0:
            metricas.append(MetricaModelo(
                estudio_id=estudio_id,
                estudio_nombre=estudio_nombre,
                modelo="No identificado",
                tarea="General",
                auc_roc=auc_val,
                auc_roc_ci_lower=ci_lower,
                auc_roc_ci_upper=ci_upper,
            ))

    return metricas


# ────────────────────── Cálculos meta-análisis ───────────────────────

def calcular_efecto_combinado(metricas: list[MetricaModelo]) -> tuple[float, float, float, float]:
    """
    Calcula un efecto combinado con modelo de efectos aleatorios (DerSimonian-Laird).

    Si una métrica no reporta IC 95%, se aproxima un error estándar conservador
    equivalente a un semiancho de 0.0588 (SE ≈ 0.03), consistente con los forest plots.

    Retorna: (efecto_combinado, ci_lower, ci_upper, i_squared)
    """
    if not metricas:
        return 0.0, 0.0, 0.0, 0.0

    if len(metricas) == 1:
        auc = metricas[0].auc_roc or 0.0
        if metricas[0].auc_roc_ci_lower is not None and metricas[0].auc_roc_ci_upper is not None:
            return auc, metricas[0].auc_roc_ci_lower, metricas[0].auc_roc_ci_upper, 0.0
        half_width = 1.96 * 0.03
        return auc, max(0.0, auc - half_width), min(1.0, auc + half_width), 0.0

    pesos = []
    efectos = []
    for metrica in metricas:
        auc = metrica.auc_roc or 0.0
        ci_low = metrica.auc_roc_ci_lower
        ci_up = metrica.auc_roc_ci_upper
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
    pooled_fixed = sum(efecto * peso for efecto, peso in zip(efectos, pesos)) / total_peso
    q = sum(peso * ((efecto - pooled_fixed) ** 2) for efecto, peso in zip(efectos, pesos))
    df = len(efectos) - 1
    c = total_peso - (sum(peso ** 2 for peso in pesos) / total_peso) if total_peso > 0 else 0.0
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    pesos_re = [1.0 / ((1.0 / peso) + tau2) for peso in pesos]
    total_peso_re = sum(pesos_re)
    pooled = sum(efecto * peso for efecto, peso in zip(efectos, pesos_re)) / total_peso_re
    se_pooled = math.sqrt(1.0 / total_peso_re)
    ci_low = max(0.0, pooled - 1.96 * se_pooled)
    ci_up = min(1.0, pooled + 1.96 * se_pooled)
    i_squared = max(0.0, (q - df) / q * 100) if q > 0 else 0.0

    return pooled, ci_low, ci_up, i_squared


def _familia_metrica_pr(metric_name: str) -> str:
    """Normaliza el tipo de métrica PR para evitar mezclar AP con AUPR/AUPRC."""
    nombre = (metric_name or "AUC-PR").strip().upper()
    if nombre == "AP":
        return "AP"
    return "AUPR/AUPRC"


def calcular_efecto_combinado_pr(metricas: list[MetricaModelo]) -> tuple[float, float, float, float]:
    """Calcula un efecto combinado PR con modelo de efectos aleatorios (DerSimonian-Laird)."""
    if not metricas:
        return 0.0, 0.0, 0.0, 0.0

    if len(metricas) == 1:
        auc = metricas[0].auc_pr or 0.0
        if metricas[0].auc_pr_ci_lower is not None and metricas[0].auc_pr_ci_upper is not None:
            return auc, metricas[0].auc_pr_ci_lower, metricas[0].auc_pr_ci_upper, 0.0
        half_width = 1.96 * 0.03
        return auc, max(0.0, auc - half_width), min(1.0, auc + half_width), 0.0

    pesos = []
    efectos = []
    for metrica in metricas:
        auc = metrica.auc_pr or 0.0
        ci_low = metrica.auc_pr_ci_lower
        ci_up = metrica.auc_pr_ci_upper
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
    pooled_fixed = sum(efecto * peso for efecto, peso in zip(efectos, pesos)) / total_peso
    q = sum(peso * ((efecto - pooled_fixed) ** 2) for efecto, peso in zip(efectos, pesos))
    df = len(efectos) - 1
    c = total_peso - (sum(peso ** 2 for peso in pesos) / total_peso) if total_peso > 0 else 0.0
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    pesos_re = [1.0 / ((1.0 / peso) + tau2) for peso in pesos]
    total_peso_re = sum(pesos_re)
    pooled = sum(efecto * peso for efecto, peso in zip(efectos, pesos_re)) / total_peso_re
    se_pooled = math.sqrt(1.0 / total_peso_re)
    ci_low = max(0.0, pooled - 1.96 * se_pooled)
    ci_up = min(1.0, pooled + 1.96 * se_pooled)
    i_squared = max(0.0, (q - df) / q * 100) if q > 0 else 0.0

    return pooled, ci_low, ci_up, i_squared


# ──────────────────── Generación de tablas LaTeX ─────────────────────

def generar_tabla_subanalisis(metricas: list[MetricaModelo]) -> str:
    """Genera la tabla LaTeX de subanálisis por tipo de modelo ML."""

    # Agrupar por modelo normalizado → lista de AUC-ROC
    modelo_aucs: dict[str, list[float]] = defaultdict(list)
    modelo_estudios: dict[str, set] = defaultdict(set)

    for m in metricas:
        if m.auc_roc and m.auc_roc >= 0.5:
            modelo_aucs[m.modelo].append(m.auc_roc)
            modelo_estudios[m.modelo].add(m.estudio_id)

    if not modelo_aucs:
        return "% No se encontraron métricas AUC-ROC para generar la tabla.\n"

    # Ordenar por número de estudios (descendente), luego por efecto combinado
    modelos_ordenados = sorted(
        modelo_aucs.keys(),
        key=lambda m: (-len(modelo_estudios[m]), -sum(modelo_aucs[m]) / len(modelo_aucs[m])),
    )

    # Construir tabla LaTeX
    filas = []
    for modelo in modelos_ordenados:
        entries = [m for m in metricas if m.modelo == modelo and m.auc_roc and m.auc_roc >= 0.5]
        outcome_summary = aggregate_outcomes(entries)
        n_estudios = len(modelo_estudios[modelo])
        n_entradas = len(entries)
        efecto, ci_low, ci_up, i2 = calcular_efecto_combinado(entries)

        fila = (
            f"    {modelo} & {n_estudios} & {n_entradas} & "
            f"{format_aggregate_cell(outcome_summary['readmission'])} & "
            f"{format_aggregate_cell(outcome_summary['mortality'])} & "
            f"{format_aggregate_cell(outcome_summary['composite'])} & "
            f"{efecto:.3f} & {ci_low:.3f}--{ci_up:.3f} & {i2:.1f}\\% \\\\" 
        )
        filas.append(fila)

    filas_str = "\n".join(filas)

    tabla = "\n".join([
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Subanálisis del AUC por tipo de modelo de aprendizaje automático.}\\label{tab:subgroup_ml}",
        "\\small",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{lcccccccc}",
        "\\toprule",
        "\\textbf{Modelo} & \\textbf{N Estudios} & \\textbf{N Entr.} & \\textbf{Readm. (ev/N)} & \\textbf{Mort. (ev/N)} & \\textbf{Comp. (ev/N)} & \\textbf{Efecto combinado} & \\textbf{IC 95\\%} & \\textbf{I\\textsuperscript{2}} " + r"\\",
        "\\midrule",
        filas_str,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}",
        "\\end{table}",
    ])

    return tabla


def generar_tabla_subanalisis_pr(metricas: list[MetricaModelo]) -> str:
    """Genera una tabla LaTeX de subanálisis para métricas precision-recall."""

    familias_modelo_metricas: dict[tuple[str, str], list[MetricaModelo]] = defaultdict(list)
    familias_modelo_estudios: dict[tuple[str, str], set[str]] = defaultdict(set)

    for m in metricas:
        if m.auc_pr is None or m.auc_pr <= 0:
            continue
        familia = _familia_metrica_pr(m.pr_metric_name)
        key = (familia, m.modelo)
        familias_modelo_metricas[key].append(m)
        familias_modelo_estudios[key].add(m.estudio_id)

    if not familias_modelo_metricas:
        return "% No se encontraron métricas PR para generar la tabla.\n"

    claves_ordenadas = sorted(
        familias_modelo_metricas.keys(),
        key=lambda key: (key[0], -len(familias_modelo_estudios[key]), -sum(m.auc_pr or 0 for m in familias_modelo_metricas[key]) / len(familias_modelo_metricas[key])),
    )

    filas = []
    for familia, modelo in claves_ordenadas:
        entries = familias_modelo_metricas[(familia, modelo)]
        outcome_summary = aggregate_outcomes(entries)
        n_estudios = len(familias_modelo_estudios[(familia, modelo)])
        n_entradas = len(entries)
        efecto, ci_low, ci_up, i2 = calcular_efecto_combinado_pr(entries)

        fila = (
            f"    {familia} & {modelo} & {n_estudios} & {n_entradas} & "
            f"{format_aggregate_cell(outcome_summary['readmission'])} & "
            f"{format_aggregate_cell(outcome_summary['mortality'])} & "
            f"{format_aggregate_cell(outcome_summary['composite'])} & "
            f"{efecto:.3f} & {ci_low:.3f}--{ci_up:.3f} & {i2:.1f}\\% \\\\" 
        )
        filas.append(fila)

    filas_str = "\n".join(filas)

    tabla = "\n".join([
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Subanálisis de métricas basadas en precision-recall, separando AP de la familia AUPR/AUPRC (modelo de efectos aleatorios).}\\label{tab:subgroup_pr}",
        "\\small",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{llcccccccc}",
        "\\toprule",
        "\\textbf{Tipo PR} & \\textbf{Modelo} & \\textbf{N Estudios} & \\textbf{N Entr.} & \\textbf{Readm. (ev/N)} & \\textbf{Mort. (ev/N)} & \\textbf{Comp. (ev/N)} & \\textbf{Efecto combinado} & \\textbf{IC 95\\%} & \\textbf{I\\textsuperscript{2}} " + r"\\",
        "\\midrule",
        filas_str,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        "\\par\\vspace{0.4em}\\footnotesize La familia AUPR/AUPRC agrupa etiquetas equivalentes de área bajo la curva precision-recall. AP se mantiene por separado por no ser directamente intercambiable con AUPR en todos los contextos. " + table_footnote(),
        "\\end{table}",
    ])

    return tabla


def generar_tabla_detalle(metricas: list[MetricaModelo]) -> str:
    """Genera una tabla LaTeX detallada con estudio × modelo × tarea × AUC."""

    # Filtrar solo entradas con AUC-ROC válido y seleccionar la mejor config por modelo-estudio-tarea
    mejores: dict[tuple, MetricaModelo] = {}
    for m in metricas:
        if m.auc_roc and m.auc_roc >= 0.5:
            key = (m.estudio_id, m.modelo, m.tarea)
            if key not in mejores or (m.auc_roc > (mejores[key].auc_roc or 0)):
                mejores[key] = m

    if not mejores:
        return "% No se encontraron métricas para la tabla de detalle.\n"

    # Ordenar por estudio, luego por modelo
    entradas = sorted(mejores.values(), key=lambda m: (m.estudio_id, m.modelo, m.tarea))

    filas = []
    for m in entradas:
        ci_str = ""
        if m.auc_roc_ci_lower and m.auc_roc_ci_upper:
            ci_str = f" ({m.auc_roc_ci_lower:.2f}--{m.auc_roc_ci_upper:.2f})"

        fila = (
            f"    {m.estudio_nombre} & {m.modelo} & "
            f"{_abreviar_tarea(m.tarea)} & "
            f"{format_outcome_cell(m)} & "
            f"{m.auc_roc:.3f}{ci_str} \\\\"
        )
        filas.append(fila)

    filas_str = "\n".join(filas)

    tabla = "\n".join([
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Detalle de AUC-ROC por estudio, modelo y tarea predictiva.}\\label{tab:detalle_auc}",
        "\\small",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{lllll}",
        "\\toprule",
        "\\textbf{Estudio} & \\textbf{Modelo} & \\textbf{Tarea} & \\textbf{Eventos/N} & \\textbf{AUC-ROC (IC 95\\%)} " + r"\\",
        "\\midrule",
        filas_str,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}",
        "\\end{table}",
    ])

    return tabla


def generar_tabla_detalle_pr(metricas: list[MetricaModelo]) -> str:
    """Genera una tabla LaTeX detallada con métricas tipo precision-recall."""

    entradas = sorted(
        [m for m in metricas if m.auc_pr is not None and m.auc_pr > 0],
        key=lambda m: (m.estudio_id, m.modelo, m.tarea),
    )

    if not entradas:
        return "% No se encontraron métricas PR para la tabla de detalle.\n"

    filas = []
    for m in entradas:
        ci_str = ""
        if m.auc_pr_ci_lower is not None and m.auc_pr_ci_upper is not None:
            ci_str = f" ({m.auc_pr_ci_lower:.2f}--{m.auc_pr_ci_upper:.2f})"

        fila = (
            f"    {m.estudio_nombre} & {m.modelo} & "
            f"{_abreviar_tarea(m.tarea)} & "
            f"{format_outcome_cell(m)} & "
            f"{m.pr_metric_name or 'AUC-PR'} & "
            f"{m.auc_pr:.3f}{ci_str} \\\\" 
        )
        filas.append(fila)

    filas_str = "\n".join(filas)

    tabla = "\n".join([
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Detalle de métricas basadas en precision-recall por estudio, modelo y tarea predictiva.}\\label{tab:detalle_pr}",
        "\\small",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{llllll}",
        "\\toprule",
        "\\textbf{Estudio} & \\textbf{Modelo} & \\textbf{Tarea} & \\textbf{Eventos/N} & \\textbf{Tipo PR} & \\textbf{Valor (IC 95\\%)} " + r"\\",
        "\\midrule",
        filas_str,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        f"\\par\\vspace{{0.4em}}\\footnotesize {table_footnote()}",
        "\\end{table}",
    ])

    return tabla


def _abreviar_tarea(tarea: str) -> str:
    """Abrevia nombres de tareas para la tabla."""
    abreviaturas = {
        "Mortalidad Intrahospitalaria": "Mort. InH",
        "Mortalidad a 7 días": "Mort. 7d",
        "Mortalidad a 30 días": "Mort. 30d",
        "Mortalidad a 90 días": "Mort. 90d",
        "Mortalidad a 1 año": "Mort. 1a",
        "Readmisión UCI": "Readm. UCI",
        "Readmisión/Mortalidad": "Readm./Mort.",
        "Readmisión/Mortalidad (VUmc Epic)": "Readm./Mort. (Epic)",
        "Readmisión/Mortalidad (ETZ)": "Readm./Mort. (ETZ)",
        "Readmisión/Mortalidad (retrained)": "Readm./Mort. (retr.)",
        "Readmisión/Mortalidad (AUMC)": "Readm./Mort. (AUMC)",
        "Readmisión/Mortalidad (OLVG)": "Readm./Mort. (OLVG)",
        "Readmisión/Mortalidad (MSZ)": "Readm./Mort. (MSZ)",
        "Readmisión/Mortalidad (pooled)": "Readm./Mort. (pooled)",
        "Readmisión/Mortalidad (ext.)": "Readm./Mort. (ext.)",
        "Descompensación Fisiológica": "Descomp.",
        "Alta segura UCI": "Alta segura",
        "Alta segura UCI (val.)": "Alta segura (val.)",
    }
    return abreviaturas.get(tarea, tarea[:25])


# ──────────────────────────── Main ────────────────────────────────────

def main():
    print("=" * 60)
    print("  Generador de Tablas LaTeX - Meta-análisis PRISMA")
    print("=" * 60)

    json_path = os.path.join(DIRECTORIO, "modelos_extraidos.json")
    if os.path.exists(json_path):
        print(f"\n▶ Cargando datos canónicos desde: {os.path.basename(json_path)}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        todas_metricas = [
            MetricaModelo(
                estudio_id=d["estudio_id"],
                estudio_nombre=ESTUDIO_CITAS.get(d["estudio_id"], f"Estudio {d['estudio_id']}"),
                modelo=d["modelo"],
                tarea=d.get("tarea", "General"),
                auc_roc=d.get("auc_roc"),
                auc_roc_ci_lower=d.get("auc_roc_ci_lower"),
                auc_roc_ci_upper=d.get("auc_roc_ci_upper"),
                auc_pr=d.get("auc_pr"),
                auc_pr_ci_lower=d.get("auc_pr_ci_lower"),
                auc_pr_ci_upper=d.get("auc_pr_ci_upper"),
                pr_metric_name=d.get("pr_metric_name", ""),
                accuracy=d.get("accuracy"),
                sensitivity=d.get("sensitivity"),
                specificity=d.get("specificity"),
                precision=d.get("precision"),
                f1_score=d.get("f1_score"),
                cohorte=d.get("cohort_label", ""),
            )
            for d in data
            if d.get("modelo")
        ]

        print(f"  Métricas cargadas: {len(todas_metricas)}")

        tabla_sub = generar_tabla_subanalisis(todas_metricas)
        with open(SALIDA_SUBANALISIS, "w", encoding="utf-8") as f:
            f.write(tabla_sub)
        print(f"  ✓ Guardada en: {os.path.basename(SALIDA_SUBANALISIS)}")

        tabla_sub_pr = generar_tabla_subanalisis_pr(todas_metricas)
        with open(SALIDA_SUBANALISIS_PR, "w", encoding="utf-8") as f:
            f.write(tabla_sub_pr)
        print(f"  ✓ Guardada en: {os.path.basename(SALIDA_SUBANALISIS_PR)}")

        tabla_det = generar_tabla_detalle(todas_metricas)
        with open(SALIDA_DETALLE, "w", encoding="utf-8") as f:
            f.write(tabla_det)
        print(f"  ✓ Guardada en: {os.path.basename(SALIDA_DETALLE)}")

        tabla_pr = generar_tabla_detalle_pr(todas_metricas)
        with open(SALIDA_DETALLE_PR, "w", encoding="utf-8") as f:
            f.write(tabla_pr)
        print(f"  ✓ Guardada en: {os.path.basename(SALIDA_DETALLE_PR)}")
        return

    # ── Paso 1: Cargar datos manuales (fuente principal, siempre disponible) ──
    todas_metricas: list[MetricaModelo] = []
    estudios_manuales: set[str] = set()

    print(f"\n▶ Cargando {len(DATOS_MANUALES)} entradas de datos manuales...")
    for (eid, enombre, modelo, tarea, auc, ci_low, ci_up) in DATOS_MANUALES:
        todas_metricas.append(MetricaModelo(
            estudio_id=eid,
            estudio_nombre=enombre,
            modelo=modelo,
            tarea=tarea,
            auc_roc=auc,
            auc_roc_ci_lower=ci_low,
            auc_roc_ci_upper=ci_up,
        ))
        estudios_manuales.add(eid)
    print(f"  Estudios con datos manuales: {sorted(estudios_manuales)}")

    # ── Paso 2: Buscar archivos de resumen para estudios SIN datos manuales ──
    pattern_resumen = os.path.join(DIRECTORIO, "*_resumen*.txt")
    archivos_resumen = sorted(glob.glob(pattern_resumen))
    print(f"\nArchivos de resumen encontrados: {len(archivos_resumen)}")

    for archivo in archivos_resumen:
        eid = extraer_id_estudio(archivo)
        basename = os.path.basename(archivo)
        if eid in estudios_manuales:
            print(f"  ⏩ {basename} — datos manuales ya cargados, omitido.")
            continue
        print(f"\n▶ Procesando: {basename}")
        if not os.path.exists(archivo):
            print(f"  ⚠ Archivo no disponible localmente. Omitido.")
            continue
        try:
            metricas = extraer_metricas_de_resumen(archivo)
            print(f"  Métricas extraídas: {len(metricas)}")
            for m in metricas:
                print(f"    - {m.modelo} | {m.tarea} | AUC: {m.auc_roc}")
            todas_metricas.extend(metricas)
        except Exception as e:
            print(f"  ✗ Error procesando archivo: {e}")
            continue

    print(f"\n{'=' * 60}")
    print(f"Total de métricas extraídas: {len(todas_metricas)}")

    # Generar tabla de subanálisis
    print(f"\n▶ Generando tabla de subanálisis...")
    tabla_sub = generar_tabla_subanalisis(todas_metricas)
    with open(SALIDA_SUBANALISIS, "w", encoding="utf-8") as f:
        f.write(tabla_sub)
    print(f"  ✓ Guardada en: {os.path.basename(SALIDA_SUBANALISIS)}")

    # Generar tabla de detalle
    print(f"\n▶ Generando tabla de detalle por estudio...")
    tabla_det = generar_tabla_detalle(todas_metricas)
    with open(SALIDA_DETALLE, "w", encoding="utf-8") as f:
        f.write(tabla_det)
    print(f"  ✓ Guardada en: {os.path.basename(SALIDA_DETALLE)}")

    # Mostrar tablas en consola
    print(f"\n{'=' * 60}")
    print("TABLA 1: Subanálisis por tipo de modelo")
    print("=" * 60)
    print(tabla_sub)
    print(f"\n{'=' * 60}")
    print("TABLA 2: Detalle por estudio")
    print("=" * 60)
    print(tabla_det)


if __name__ == "__main__":
    main()
