"""Analizador general de archivos DXF existentes.

Lee un DXF y extrae metadata, layers, bloques, dimstyles, textstyles,
estadísticas de entidades y bounding box.
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

from cad_copilot.schemas.detection import (
    BlockInfo,
    BoundingBox,
    DxfAnalysis,
    DxfMetadata,
    EntityStats,
    LayerInfo,
)


def read_dxf(path: str | Path) -> Drawing:
    """Lee un archivo DXF y devuelve el documento ezdxf."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo DXF no encontrado: {path}")
    if not path.suffix.lower() == ".dxf":
        raise ValueError(f"El archivo no es DXF: {path}")
    return ezdxf.readfile(str(path))


def _extract_metadata(doc: Drawing, path: str | Path) -> DxfMetadata:
    """Extrae metadata del documento DXF."""
    path = Path(path)
    return DxfMetadata(
        file_path=str(path),
        dxf_version=doc.dxfversion,
        encoding=doc.encoding,
        insunits=doc.header.get("$INSUNITS", 0),
        file_size_bytes=os.path.getsize(path) if path.exists() else 0,
    )


def _extract_layers(doc: Drawing, msp: Modelspace) -> list[LayerInfo]:
    """Extrae información de todos los layers con conteo de entidades."""
    entity_counts: Counter[str] = Counter(e.dxf.layer for e in msp)

    layers = []
    for layer in doc.layers:
        name = layer.dxf.name
        layers.append(
            LayerInfo(
                name=name,
                color=layer.dxf.color,
                lineweight=getattr(layer.dxf, "lineweight", -3),
                entity_count=entity_counts.get(name, 0),
                is_frozen=layer.is_frozen(),
                is_off=layer.is_off(),
            )
        )

    return sorted(layers, key=lambda l: l.name)


def _extract_blocks(doc: Drawing, msp: Modelspace) -> list[BlockInfo]:
    """Extrae información de bloques definidos (excluyendo internos *Model_Space, etc.)."""
    insert_counts: Counter[str] = Counter(
        e.dxf.name for e in msp if e.dxftype() == "INSERT"
    )

    blocks = []
    for block in doc.blocks:
        if block.name.startswith("*"):
            continue
        entity_count = len(list(block))
        if entity_count == 0 and insert_counts.get(block.name, 0) == 0:
            continue
        blocks.append(
            BlockInfo(
                name=block.name,
                entity_count=entity_count,
                insert_count=insert_counts.get(block.name, 0),
            )
        )

    return sorted(blocks, key=lambda b: b.name)


def _extract_entity_stats(msp: Modelspace) -> tuple[list[EntityStats], int]:
    """Extrae conteo de entidades por tipo en Model Space."""
    counts: Counter[str] = Counter(e.dxftype() for e in msp)
    total = sum(counts.values())
    stats = [
        EntityStats(entity_type=t, count=c)
        for t, c in counts.most_common()
    ]
    return stats, total


def _extract_dimstyles(doc: Drawing) -> list[str]:
    """Extrae nombres de dimstyles definidos."""
    return sorted(ds.dxf.name for ds in doc.dimstyles)


def _extract_textstyles(doc: Drawing) -> list[str]:
    """Extrae nombres de textstyles definidos."""
    return sorted(ts.dxf.name for ts in doc.styles)


def _calculate_bounding_box(msp: Modelspace) -> BoundingBox:
    """Calcula el bounding box de todas las entidades en Model Space."""
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    found = False
    for entity in msp:
        try:
            dxftype = entity.dxftype()

            if dxftype == "LINE":
                for pt in (entity.dxf.start, entity.dxf.end):
                    min_x = min(min_x, pt.x)
                    min_y = min(min_y, pt.y)
                    max_x = max(max_x, pt.x)
                    max_y = max(max_y, pt.y)
                    found = True

            elif dxftype == "LWPOLYLINE":
                for x, y, *_ in entity.get_points(format="xy"):
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    found = True

            elif dxftype == "CIRCLE":
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                min_x = min(min_x, cx - r)
                min_y = min(min_y, cy - r)
                max_x = max(max_x, cx + r)
                max_y = max(max_y, cy + r)
                found = True

            elif dxftype == "ARC":
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                min_x = min(min_x, cx - r)
                min_y = min(min_y, cy - r)
                max_x = max(max_x, cx + r)
                max_y = max(max_y, cy + r)
                found = True

            elif dxftype == "INSERT":
                ix, iy = entity.dxf.insert.x, entity.dxf.insert.y
                min_x = min(min_x, ix)
                min_y = min(min_y, iy)
                max_x = max(max_x, ix)
                max_y = max(max_y, iy)
                found = True

            elif dxftype in ("TEXT", "MTEXT"):
                pt = entity.dxf.insert
                min_x = min(min_x, pt.x)
                min_y = min(min_y, pt.y)
                max_x = max(max_x, pt.x)
                max_y = max(max_y, pt.y)
                found = True

            elif dxftype == "DIMENSION":
                pt = entity.dxf.defpoint
                min_x = min(min_x, pt.x)
                min_y = min(min_y, pt.y)
                max_x = max(max_x, pt.x)
                max_y = max(max_y, pt.y)
                found = True

            elif dxftype == "POINT":
                pt = entity.dxf.location
                min_x = min(min_x, pt.x)
                min_y = min(min_y, pt.y)
                max_x = max(max_x, pt.x)
                max_y = max(max_y, pt.y)
                found = True

        except (AttributeError, TypeError):
            continue

    if not found:
        return BoundingBox()

    return BoundingBox(
        min_point=(min_x, min_y),
        max_point=(max_x, max_y),
    )


def analyze_dxf(path: str | Path) -> DxfAnalysis:
    """Analiza un archivo DXF y devuelve un reporte estructurado.

    Args:
        path: Ruta al archivo .dxf

    Returns:
        DxfAnalysis con metadata, layers, bloques, estadísticas, etc.
    """
    doc = read_dxf(path)
    msp = doc.modelspace()

    metadata = _extract_metadata(doc, path)
    layers = _extract_layers(doc, msp)
    blocks = _extract_blocks(doc, msp)
    entity_stats, total = _extract_entity_stats(msp)
    dimstyles = _extract_dimstyles(doc)
    textstyles = _extract_textstyles(doc)
    bbox = _calculate_bounding_box(msp)

    return DxfAnalysis(
        metadata=metadata,
        layers=layers,
        blocks=blocks,
        entity_stats=entity_stats,
        dimstyles=dimstyles,
        textstyles=textstyles,
        total_entities=total,
        bounding_box=bbox,
    )
