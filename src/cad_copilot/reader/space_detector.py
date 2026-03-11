"""Detector de espacios/ambientes en archivos DXF existentes.

Estrategias de detección:
1. Buscar TEXT/MTEXT con nombres de ambientes conocidos
2. Buscar HATCH entities que delimitan áreas
3. Calcular área si hay polígonos cerrados asociados
"""

from __future__ import annotations

import re

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import DetectedSpace, SpaceCategory

# Patrones de nombres de ambientes (español + inglés)
SPACE_PATTERNS: dict[SpaceCategory, list[re.Pattern]] = {
    SpaceCategory.dormitorio: [
        re.compile(r"(?i)dormitorio"),
        re.compile(r"(?i)bedroom"),
        re.compile(r"(?i)dorm\.?\s*\d*"),
        re.compile(r"(?i)habitaci[oó]n"),
    ],
    SpaceCategory.living: [
        re.compile(r"(?i)living"),
        re.compile(r"(?i)sala"),
    ],
    SpaceCategory.comedor: [
        re.compile(r"(?i)comedor"),
        re.compile(r"(?i)dining"),
    ],
    SpaceCategory.cocina: [
        re.compile(r"(?i)cocina"),
        re.compile(r"(?i)kitchen"),
    ],
    SpaceCategory.bano: [
        re.compile(r"(?i)ba[ñn]o"),
        re.compile(r"(?i)bathroom"),
        re.compile(r"(?i)toilette"),
        re.compile(r"(?i)sanitario"),
    ],
    SpaceCategory.lavadero: [
        re.compile(r"(?i)lavadero"),
        re.compile(r"(?i)laundry"),
    ],
    SpaceCategory.garage: [
        re.compile(r"(?i)garage"),
        re.compile(r"(?i)cochera"),
    ],
    SpaceCategory.pasillo: [
        re.compile(r"(?i)pasillo"),
        re.compile(r"(?i)circulaci[oó]n"),
        re.compile(r"(?i)hallway"),
    ],
    SpaceCategory.hall: [
        re.compile(r"(?i)\bhall\b"),
        re.compile(r"(?i)recibidor"),
        re.compile(r"(?i)vest[ií]bulo"),
    ],
    SpaceCategory.estar: [
        re.compile(r"(?i)\bestar\b"),
        re.compile(r"(?i)family\s*room"),
    ],
    SpaceCategory.escritorio: [
        re.compile(r"(?i)escritorio"),
        re.compile(r"(?i)estudio"),
        re.compile(r"(?i)office"),
    ],
    SpaceCategory.deposito: [
        re.compile(r"(?i)dep[oó]sito"),
        re.compile(r"(?i)storage"),
        re.compile(r"(?i)bodega"),
    ],
}


def _classify_space_name(text: str) -> tuple[SpaceCategory, str]:
    """Clasifica un texto como nombre de ambiente.

    Returns:
        (categoría, nombre limpio) o (otro, "") si no se reconoce.
    """
    clean = text.strip()
    if not clean or len(clean) < 3:
        return SpaceCategory.otro, ""

    for category, patterns in SPACE_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(clean):
                return category, clean

    return SpaceCategory.otro, ""


def _extract_area_from_text(text: str) -> float | None:
    """Intenta extraer un valor de área de un texto (ej: "12.50 m²" o "12.50m2")."""
    patterns = [
        re.compile(r"(\d+[\.,]\d+)\s*m[²2]", re.IGNORECASE),
        re.compile(r"(\d+[\.,]\d+)\s*m\s*2", re.IGNORECASE),
        re.compile(r"sup[.\s]*=?\s*(\d+[\.,]\d+)", re.IGNORECASE),
        re.compile(r"[áa]rea[.\s]*=?\s*(\d+[\.,]\d+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group(1).replace(",", ".")
            try:
                return float(value)
            except ValueError:
                continue
    return None


def detect_spaces(doc: Drawing) -> list[DetectedSpace]:
    """Detecta espacios/ambientes en un DXF existente.

    Args:
        doc: Documento ezdxf ya leído.

    Returns:
        Lista de DetectedSpace con nombre, categoría, posición y área si disponible.
    """
    msp = doc.modelspace()
    spaces: list[DetectedSpace] = []

    for entity in msp:
        dxftype = entity.dxftype()
        if dxftype not in ("TEXT", "MTEXT"):
            continue

        # Extraer texto
        if dxftype == "TEXT":
            text = entity.dxf.text
        else:
            text = entity.text  # MTEXT usa .text property

        if not text:
            continue

        # Clasificar
        category, name = _classify_space_name(text)
        if category == SpaceCategory.otro:
            continue

        # Posición
        insert = entity.dxf.insert
        handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""

        # Intentar extraer área del mismo texto o de textos cercanos
        area = _extract_area_from_text(text) or 0.0

        spaces.append(
            DetectedSpace(
                id=f"space_{len(spaces)}",
                name=name,
                category=category,
                area=area,
                centroid=(insert.x, insert.y),
                label_handle=handle,
                layer=entity.dxf.layer,
            )
        )

    return spaces
