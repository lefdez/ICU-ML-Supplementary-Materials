#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class OutcomeMetadata:
    sample_size: int
    event_count: Optional[int]
    event_kind: str
    cohort_label: str = ""
    estimated: bool = False
    note: str = ""


@dataclass(frozen=True)
class OutcomeAggregate:
    entry_count: int = 0
    sample_total: int = 0
    event_total: int = 0
    missing_event_entries: int = 0
    estimated_entries: int = 0


OUTCOME_LABELS = {
    "readmission": "Readmisión",
    "mortality": "Mortalidad",
    "composite": "Compuesto",
}


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = " ".join(text.strip().lower().split())
    return text


def _task_key(study_id: str, task: str) -> tuple[str, str]:
    return str(study_id), _normalize_text(task)


ENTRY_METADATA: dict[tuple[str, str], OutcomeMetadata] = {
    # 2016: Curth et al. (2020)
    _task_key("2016", "Readmisión/Mortalidad (VUmc Epic)"): OutcomeMetadata(2847, 208, "composite", "VUmc Epic", True, "Eventos estimados a partir de incidencia 7.3%"),
    _task_key("2016", "Readmisión/Mortalidad (ETZ)"): OutcomeMetadata(13300, 811, "composite", "ETZ", True, "Eventos estimados a partir de incidencia 6.1%"),
    _task_key("2016", "Mortalidad"): OutcomeMetadata(2847, 208, "composite", "VUmc Epic", True, "Alias histórico del desenlace compuesto"),
    _task_key("2016", "Mortalidad (ETZ)"): OutcomeMetadata(13300, 811, "composite", "ETZ", True, "Alias histórico del desenlace compuesto"),

    # 2110: Thoral et al. (2021) — datos exactos confirmados en Tabla S5 del suplemento
    _task_key("2110", "Readmisión/Mortalidad"): OutcomeMetadata(3929, 263, "composite", "Cohorte de validación", False, "263 eventos exactos (6.7%); Tabla S5 suplemento"),
    _task_key("2110", "Mortalidad"): OutcomeMetadata(3929, 74, "mortality", "Cohorte de validación", False, "74 muertes dentro de 7 días post-alta (1.9%); Tabla S5 suplemento"),
    _task_key("2110", "Readmisión"): OutcomeMetadata(3929, 189, "readmission", "Cohorte de validación", False, "189 readmisiones dentro de 7 días post-alta (4.8%); Tabla S5 suplemento"),

    # 2216: Shickel et al. (2022), cohorte de validación (n=12,674)
    _task_key("2216", "Readmisión"): OutcomeMetadata(12674, 613, "readmission", "Cohorte de validación", False),
    _task_key("2216", "Readmisión UCI"): OutcomeMetadata(12674, 613, "readmission", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad Intrahospitalaria"): OutcomeMetadata(12674, 1131, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad a 7 días"): OutcomeMetadata(12674, 1022, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad 7d"): OutcomeMetadata(12674, 1022, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad a 30 días"): OutcomeMetadata(12674, 1380, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad 30d"): OutcomeMetadata(12674, 1380, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad a 90 días"): OutcomeMetadata(12674, 1785, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad 90d"): OutcomeMetadata(12674, 1785, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad a 1 año"): OutcomeMetadata(12674, 2288, "mortality", "Cohorte de validación", False),
    _task_key("2216", "Mortalidad 1a"): OutcomeMetadata(12674, 2288, "mortality", "Cohorte de validación", False),

    # 2313: De Hond et al. (2023)
    _task_key("2313", "Readmisión/Mortalidad"): OutcomeMetadata(10052, 577, "composite", "Leiden UMC", False),
    _task_key("2313", "Readmisión/Mortalidad (retr.)"): OutcomeMetadata(10052, 577, "composite", "Leiden UMC", False),
    _task_key("2313", "Readmisión/Mortalidad (retrained)"): OutcomeMetadata(10052, 577, "composite", "Leiden UMC", False),

    # 2314: Khodadadi et al. (2023)
    _task_key("2314", "Mortalidad (MIMIC)"): OutcomeMetadata(50391, 5377, "mortality", "MIMIC-III", False),
    _task_key("2314", "Mortalidad (eICU)"): OutcomeMetadata(41026, 2983, "mortality", "eICU", False),
    _task_key("2314", "Readmisión (eICU)"): OutcomeMetadata(41026, 7051, "readmission", "eICU", False),

    # 2420: Tschoellitsch et al. (2024)
    _task_key("2420", "Readmisión/Mortalidad"): OutcomeMetadata(16405, 310, "composite", "Cohorte interna", False),
    _task_key("2420", "Readmisión/Mortalidad (ext.)"): OutcomeMetadata(58434, 2873, "composite", "Validación externa MIMIC-IV", False),

    # 2421: Sun et al. (2024)
    _task_key("2421", "Mortalidad (eICU)"): OutcomeMetadata(24600, None, "mortality", "eICU-CRD", False, "El artículo reporta el tamaño muestral pero no el número de eventos"),
    _task_key("2421", "Readmisión (eICU)"): OutcomeMetadata(15360, None, "readmission", "eICU-CRD", False, "El artículo reporta el tamaño muestral pero no el número de eventos"),

    # 2025: Dam et al. (2025)
    _task_key("2025", "Readmisión/Mortalidad (AUMC)"): OutcomeMetadata(15328, 904, "composite", "AUMC", True, "Eventos estimados a partir de incidencia 5.9%"),
    _task_key("2025", "Readmisión/Mortalidad (OLVG)"): OutcomeMetadata(19417, 1340, "composite", "OLVG", True, "Eventos estimados a partir de incidencia 6.9%"),
    _task_key("2025", "Readmisión/Mortalidad (MSZ)"): OutcomeMetadata(10092, 717, "composite", "MSZ", True, "Eventos estimados a partir de incidencia 7.1%"),
    _task_key("2025", "Readmisión/Mortalidad (pooled)"): OutcomeMetadata(29509, 2057, "composite", "MSZ + OLVG", True, "Eventos estimados sumando incidencias reportadas"),
    _task_key("2025", "Readmisión/Mortalidad (ext.)"): OutcomeMetadata(15328, 904, "composite", "AUMC", True, "Eventos estimados a partir de incidencia 5.9%"),
}


def metadata_for_entry(entry: Any) -> Optional[OutcomeMetadata]:
    if isinstance(entry, dict):
        study_id = str(entry.get("estudio_id", ""))
        task = entry.get("tarea", "")
    else:
        study_id = str(getattr(entry, "estudio_id", ""))
        task = getattr(entry, "tarea", "")
    return ENTRY_METADATA.get(_task_key(study_id, task))


def apply_metadata(entry: Any) -> Any:
    meta = metadata_for_entry(entry)
    sample_size = meta.sample_size if meta else None
    event_count = meta.event_count if meta else None
    event_kind = meta.event_kind if meta else None
    cohort_label = meta.cohort_label if meta else ""
    estimated = meta.estimated if meta else False
    note = meta.note if meta else ""

    if isinstance(entry, dict):
        entry["sample_size"] = sample_size
        entry["event_count"] = event_count
        entry["event_kind"] = event_kind
        entry["cohort_label"] = cohort_label
        entry["event_count_estimated"] = estimated
        entry["outcome_note"] = note
        return entry

    setattr(entry, "sample_size", sample_size)
    setattr(entry, "event_count", event_count)
    setattr(entry, "event_kind", event_kind)
    setattr(entry, "cohort_label", cohort_label)
    setattr(entry, "event_count_estimated", estimated)
    setattr(entry, "outcome_note", note)
    return entry


def aggregate_outcomes(entries: list[Any]) -> dict[str, OutcomeAggregate]:
    base = {
        "readmission": OutcomeAggregate(),
        "mortality": OutcomeAggregate(),
        "composite": OutcomeAggregate(),
    }
    accum = {key: base[key].__dict__.copy() for key in base}

    for entry in entries:
        meta = metadata_for_entry(entry)
        if not meta:
            continue
        bucket = accum[meta.event_kind]
        bucket["entry_count"] += 1
        bucket["sample_total"] += meta.sample_size
        if meta.event_count is None:
            bucket["missing_event_entries"] += 1
        else:
            bucket["event_total"] += meta.event_count
        if meta.estimated:
            bucket["estimated_entries"] += 1

    return {key: OutcomeAggregate(**values) for key, values in accum.items()}


def format_outcome_cell(entry: Any) -> str:
    meta = metadata_for_entry(entry)
    if not meta:
        return "NR"
    event_text = "NR" if meta.event_count is None else f"{meta.event_count:,}"
    if meta.estimated and meta.event_count is not None:
        event_text += "*"
    return f"{event_text}/{meta.sample_size:,}"


def format_aggregate_cell(aggregate: OutcomeAggregate) -> str:
    if aggregate.sample_total == 0:
        return "---"

    if aggregate.event_total == 0 and aggregate.missing_event_entries == aggregate.entry_count:
        event_text = "NR"
    else:
        event_text = f"{aggregate.event_total:,}"
        if aggregate.estimated_entries:
            event_text += "*"

    suffix = ""
    if aggregate.missing_event_entries:
        suffix = f" [NR={aggregate.missing_event_entries}]"

    return f"{event_text}/{aggregate.sample_total:,}{suffix}"


def table_footnote() -> str:
    return "* eventos estimados a partir de incidencias reportadas; NR = no reportado en el artículo original."