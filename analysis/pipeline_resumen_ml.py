#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de extracción de modelos ML y métricas desde artículos PDF.

Escanea el directorio por archivos PDF, extrae texto con PyPDF2,
genera resúmenes ML con Google Gemini API, y guarda los resultados.

Requisitos:
    pip install PyPDF2 google-generativeai

Configuración:
    Variable de entorno GOOGLE_API_KEY con tu clave de la API de Gemini.
    O bien, editar la variable API_KEY directamente en este script.
"""

import asyncio
import glob
import os
import sys
import time
import logging

import PyPDF2
import google.generativeai as genai

# ─────────────────────────── Configuración ───────────────────────────

# Directorio de trabajo (donde están los PDFs)
DIRECTORIO = os.path.dirname(os.path.abspath(__file__))

# Subdirectorio para guardar textos originales extraídos
ORIGINALES_DIR = os.path.join(DIRECTORIO, "originales")

# Sufijo de los archivos de resumen ML generados
SUFIJO_RESUMEN_ML = "_resumen_ML.txt"
SUFIJO_ORIGINAL = "_original.txt"

# Modelo de Gemini a utilizar
GEMINI_MODEL = "gemini-2.0-flash"

# Máximo de reintentos por llamada a la API
MAX_RETRIES = 3

# Modo de procesamiento: "pendientes" solo procesa PDFs sin resumen ML,
# "todos" procesa todos los PDFs incluyendo los que ya tienen resumen.
MODO = "pendientes"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────── Prompt ML ───────────────────────────────

def get_ML_Prompt(prompt: str) -> str:
    """Genera el prompt para extracción de modelos ML y métricas."""
    return f"""🔍 **Extracción de modelos ML y métricas en artículos científicos**
✅ Objetivo Principal:
    Extraer todos los modelos de Machine Learning (ML) utilizados en el artículo y, para cada uno de ellos, presentar un recuadro con las métricas de evaluación relevantes, separadas para predicción de mortalidad y reingreso hospitalario.

    🧠 Instrucciones detalladas:
    Para cada modelo ML mencionado en el artículo, realiza lo siguiente:

    1. Identifica el tipo de modelo:
    Especifica el nombre del modelo (ej. Random Forest, SVM, XGBoost, etc.)

    2. Crea un recuadro con los siguientes campos, separados según su aplicación:
    📌 A. Si el modelo fue usado para predecir mortalidad:
    Modelo ML:

    No. de muertes / tamaño de muestra (mortality/sample size):

    AUC (Área bajo la curva ROC):

    Exactitud (Accuracy):

    Sensibilidad (Recall / SN):

    Especificidad (Specificity / SP):

    Precisión (Precision / PV):

    📌 B. Si el modelo fue usado para predecir reingresos hospitalarios:
    Modelo ML:

    No. de reingresos / tamaño de muestra (readmission/sample size):

    AUC (Área bajo la curva ROC):

    Exactitud (Accuracy):

    Sensibilidad (Recall / SN):

    Especificidad (Specificity / SP):

    Precisión (Precision / PV):

    🔎 Instrucciones adicionales:
    Si un modelo fue usado para ambos fines (mortalidad y reingreso), genera dos recuadros separados.

    En caso de que alguna métrica no se mencione explícitamente, indícalo como "No reportado".

    Si los datos están en tablas, figuras o texto, extrae la información más directamente posible.

    No omitas ningún modelo ML mencionado, aunque sea de forma secundaria.

    Mantén un formato claro, preciso y bien organizado.
---

📌 **Texto a evaluar:**
{prompt}"""


# ─────────────────────── Funciones auxiliares ────────────────────────

def extraer_texto_pdf(archivo_pdf: str) -> str:
    """Extrae todo el texto de un archivo PDF usando PyPDF2."""
    texto_paginas = []
    with open(archivo_pdf, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texto_paginas.append(page_text)
    texto_completo = " ".join(texto_paginas)
    if len(texto_completo.split()) < 50:
        logger.warning(
            f"Texto extraído muy corto ({len(texto_completo.split())} tokens): "
            f"{os.path.basename(archivo_pdf)}"
        )
    return texto_completo


def obtener_pdfs_pendientes(directorio: str, modo: str) -> list[str]:
    """Retorna la lista de archivos PDF que necesitan resumen ML."""
    pdfs = sorted(glob.glob(os.path.join(directorio, "*.pdf")))
    if modo == "todos":
        logger.info(f"Modo 'todos': se procesarán {len(pdfs)} PDFs.")
        return pdfs

    pendientes = []
    for pdf_path in pdfs:
        nombre_base = os.path.splitext(os.path.basename(pdf_path))[0]
        resumen_ml = os.path.join(directorio, nombre_base + SUFIJO_RESUMEN_ML)
        if not os.path.exists(resumen_ml):
            pendientes.append(pdf_path)
        else:
            logger.info(f"Ya existe resumen ML: {nombre_base}")
    logger.info(f"PDFs pendientes de procesar: {len(pendientes)} de {len(pdfs)}")
    return pendientes


def guardar_texto(filepath: str, contenido: str) -> None:
    """Guarda texto en un archivo, creando el directorio si es necesario."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(contenido)


# ────────────────────── Generación con Gemini ────────────────────────

async def generar_resumen_ml(archivo_pdf: str, model) -> None:
    """Extrae texto de un PDF y genera el resumen ML con Gemini."""
    nombre_base = os.path.splitext(os.path.basename(archivo_pdf))[0]
    logger.info(f"▶ Procesando: {nombre_base}")

    # 1. Extraer texto del PDF
    texto_original = extraer_texto_pdf(archivo_pdf)
    if not texto_original.strip():
        logger.error(f"✗ No se pudo extraer texto: {nombre_base}")
        return

    # 2. Guardar texto original
    archivo_original = os.path.join(ORIGINALES_DIR, nombre_base + SUFIJO_ORIGINAL)
    guardar_texto(archivo_original, texto_original)
    logger.info(f"  Texto original guardado ({len(texto_original.split())} tokens)")

    # 3. Generar resumen ML con Gemini (con reintentos)
    prompt = get_ML_Prompt(texto_original)
    resumen_texto = None

    for intento in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"  Llamando a Gemini (intento {intento}/{MAX_RETRIES})...")
            response = model.generate_content(prompt)
            resumen_texto = response.candidates[0].content.parts[0].text
            break
        except Exception as e:
            logger.warning(f"  Error en intento {intento}: {e}")
            if intento < MAX_RETRIES:
                wait_time = 2 ** intento
                logger.info(f"  Reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"✗ Falló tras {MAX_RETRIES} intentos: {nombre_base}")
                return

    # 4. Guardar resumen ML
    archivo_resumen = os.path.join(DIRECTORIO, nombre_base + SUFIJO_RESUMEN_ML)
    guardar_texto(archivo_resumen, resumen_texto)
    logger.info(f"✓ Resumen ML guardado: {nombre_base}")


async def procesar_todos(pdfs: list[str], model) -> None:
    """Procesa una lista de PDFs secuencialmente para respetar rate limits."""
    total = len(pdfs)
    for i, pdf_path in enumerate(pdfs, 1):
        logger.info(f"━━━ [{i}/{total}] ━━━")
        await generar_resumen_ml(pdf_path, model)
        # Pausa entre llamadas para respetar rate limits de la API
        if i < total:
            logger.info("  Esperando 5s antes del siguiente PDF...")
            await asyncio.sleep(5)


# ──────────────────────────── Main ────────────────────────────────────

async def main():
    # Verificar API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error(
            "No se encontró GOOGLE_API_KEY en variables de entorno.\n"
            "Configúrala con: set GOOGLE_API_KEY=tu_clave_aqui (Windows)\n"
            "                 export GOOGLE_API_KEY=tu_clave_aqui (Linux/Mac)"
        )
        sys.exit(1)

    # Configurar Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info(f"Modelo Gemini configurado: {GEMINI_MODEL}")

    # Obtener PDFs pendientes
    pdfs = obtener_pdfs_pendientes(DIRECTORIO, MODO)
    if not pdfs:
        logger.info("No hay PDFs pendientes de procesar. ¡Todo listo!")
        return

    logger.info("PDFs a procesar:")
    for pdf in pdfs:
        logger.info(f"  • {os.path.basename(pdf)}")

    # Crear directorio de originales
    os.makedirs(ORIGINALES_DIR, exist_ok=True)

    # Procesar
    inicio = time.time()
    await procesar_todos(pdfs, model)
    elapsed = time.time() - inicio
    logger.info(f"Pipeline finalizado en {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
