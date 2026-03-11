"""Detector de aberturas (puertas y ventanas) en archivos DXF existentes.

Estrategias de detección:
1. INSERT de bloques con nombres que contengan "puerta", "door", "ventana", "window"
2. INSERT de bloques con arcos (ARC) internos → puertas batientes
3. INSERT de bloques sanitarios se excluyen
"""

from __future__ import annotations

import math
import re

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import DetectedOpening, OpeningKind


# Patrones de nombres de bloques
DOOR_PATTERNS = [
    re.compile(r"(?i)puerta"),
    re.compile(r"(?i)door"),
    re.compile(r"(?i)porta"),
    re.compile(r"(?i)^P[\d_]"),  # P1, P_090, etc.
]

WINDOW_PATTERNS = [
    re.compile(r"(?i)ventana"),
    re.compile(r"(?i)window"),
    re.compile(r"(?i)^V[\d_]"),
    re.compile(r"(?i)^WIN"),
]

# Bloques que NO son aberturas
EXCLUDE_PATTERNS = [
    re.compile(r"(?i)inodoro"),
    re.compile(r"(?i)lavamanos"),
    re.compile(r"(?i)bidet"),
    re.compile(r"(?i)cocina"),
    re.compile(r"(?i)ducha"),
    re.compile(r"(?i)shower"),
    re.compile(r"(?i)sink"),
    re.compile(r"(?i)toilet"),
    re.compile(r"(?i)tanque"),
    re.compile(r"(?i)norte"),
    re.compile(r"(?i)north"),
    re.compile(r"(?i)cota"),
    re.compile(r"(?i)nivel"),
    re.compile(r"(?i)level"),
    re.compile(r"(?i)_ArchTick"),
    re.compile(r"(?i)^A\$C"),  # bloques internos AutoCAD
]


def _classify_block_name(name: str) -> OpeningKind:
    """Clasifica un bloque por su nombre."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(name):
            return OpeningKind.unknown

    for pattern in DOOR_PATTERNS:
        if pattern.search(name):
            return OpeningKind.door

    for pattern in WINDOW_PATTERNS:
        if pattern.search(name):
            return OpeningKind.window

    return OpeningKind.unknown


def _block_has_arc(doc: Drawing, block_name: str) -> bool:
    """Verifica si la definición del bloque contiene entidades ARC (indicador de puerta)."""
    try:
        block = doc.blocks.get(block_name)
        if block is None:
            return False
        return any(e.dxftype() == "ARC" for e in block)
    except Exception:
        return False


def _estimate_block_width(doc: Drawing, block_name: str) -> float:
    """Estima el ancho de un bloque basándose en su geometría."""
    try:
        block = doc.blocks.get(block_name)
        if block is None:
            return 0.0

        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for entity in block:
            dxftype = entity.dxftype()
            if dxftype == "LINE":
                for pt in (entity.dxf.start, entity.dxf.end):
                    min_x = min(min_x, pt.x)
                    max_x = max(max_x, pt.x)
                    min_y = min(min_y, pt.y)
                    max_y = max(max_y, pt.y)
            elif dxftype == "ARC":
                cx = entity.dxf.center.x
                cy = entity.dxf.center.y
                r = entity.dxf.radius
                min_x = min(min_x, cx - r)
                max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r)
                max_y = max(max_y, cy + r)
            elif dxftype == "LWPOLYLINE":
                for x, y in entity.get_points(format="xy"):
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        if min_x == float("inf"):
            return 0.0

        # El ancho es la dimensión mayor del bounding box del bloque
        return max(max_x - min_x, max_y - min_y)

    except Exception:
        return 0.0


def detect_openings(doc: Drawing) -> list[DetectedOpening]:
    """Detecta aberturas (puertas y ventanas) en un DXF existente.

    Args:
        doc: Documento ezdxf ya leído.

    Returns:
        Lista de DetectedOpening con tipo, posición, ancho y bloque.
    """
    msp = doc.modelspace()
    openings: list[DetectedOpening] = []
    block_width_cache: dict[str, float] = {}

    for entity in msp:
        if entity.dxftype() != "INSERT":
            continue

        block_name = entity.dxf.name

        # Clasificar por nombre
        kind = _classify_block_name(block_name)

        # Si no se clasificó por nombre, verificar si tiene arco (puerta batiente)
        if kind == OpeningKind.unknown:
            if _block_has_arc(doc, block_name):
                kind = OpeningKind.door
            else:
                continue

        # Estimar ancho del bloque
        if block_name not in block_width_cache:
            block_width_cache[block_name] = _estimate_block_width(doc, block_name)
        width = block_width_cache[block_name]

        # Considerar escala del insert
        scale_x = getattr(entity.dxf, "xscale", 1.0)
        scale_y = getattr(entity.dxf, "yscale", 1.0)
        max_scale = max(abs(scale_x), abs(scale_y))
        if max_scale > 0:
            width *= max_scale

        insert = entity.dxf.insert
        handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""

        openings.append(
            DetectedOpening(
                id=f"opening_{len(openings)}",
                kind=kind,
                position=(insert.x, insert.y),
                width=round(width, 4),
                block_name=block_name,
                layer=entity.dxf.layer,
                entity_handle=handle,
            )
        )

    return openings


def detect_openings_from_arcs(doc: Drawing) -> list[DetectedOpening]:
    """Detecta puertas a partir de entidades ARC sueltas en Model Space.

    Un ARC de ~90 grados con radio entre 0.5m y 1.5m es probablemente
    el barrido de una puerta batiente.
    """
    msp = doc.modelspace()
    openings: list[DetectedOpening] = []

    for entity in msp:
        if entity.dxftype() != "ARC":
            continue

        radius = entity.dxf.radius
        if radius < 0.5 or radius > 1.5:
            continue

        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        sweep = (end_angle - start_angle) % 360

        # Un barrido de puerta es ~90 grados (tolerancia amplia)
        if not (70 <= sweep <= 110):
            continue

        center = entity.dxf.center
        handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""

        openings.append(
            DetectedOpening(
                id=f"opening_arc_{len(openings)}",
                kind=OpeningKind.door,
                position=(center.x, center.y),
                width=round(radius, 4),
                block_name="",
                layer=entity.dxf.layer,
                entity_handle=handle,
            )
        )

    return openings
