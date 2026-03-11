"""Agrega cotas faltantes a muros detectados en un DXF existente.

Reutiliza el motor de annotations.py existente, aplicando cotas solo
a muros que no tienen cota asociada. Usa dimstyle IRAM_ARQ y layer
A-ANNO-DIMS (convención profesional AIA).
"""

from __future__ import annotations

import math

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import DetectedDimension, DetectedWall
from cad_copilot.standards.dimstyles import setup_dimstyles
from cad_copilot.standards.layers import setup_layers


def _wall_has_dimension(
    wall: DetectedWall,
    dimensions: list[DetectedDimension],
    tolerance: float = 0.5,
) -> bool:
    """Verifica si un muro ya tiene una cota cercana."""
    wall_mx = (wall.start[0] + wall.end[0]) / 2
    wall_my = (wall.start[1] + wall.end[1]) / 2

    for dim in dimensions:
        dim_mx = (dim.start[0] + dim.end[0]) / 2
        dim_my = (dim.start[1] + dim.end[1]) / 2
        dist = math.sqrt((wall_mx - dim_mx) ** 2 + (wall_my - dim_my) ** 2)

        if dist < wall.length + tolerance:
            return True

    return False


def add_missing_dimensions(
    doc: Drawing,
    walls: list[DetectedWall],
    existing_dimensions: list[DetectedDimension],
    *,
    offset: float = 0.8,
    dimstyle: str = "IRAM_ARQ",
    scale: int = 50,
    min_wall_length: float = 0.5,
) -> int:
    """Agrega cotas a muros detectados que no tienen cota existente.

    Args:
        doc: Documento ezdxf a modificar.
        walls: Muros detectados del DXF.
        existing_dimensions: Cotas ya presentes en el DXF.
        offset: Distancia de la cota al muro (metros).
        dimstyle: Nombre del dimstyle a usar.
        scale: Escala del plano (para DIMSCALE).
        min_wall_length: Longitud mínima de muro para acotar.

    Returns:
        Cantidad de cotas agregadas.
    """
    # Asegurar que existan layers y dimstyles profesionales
    setup_layers(doc)
    if dimstyle == "IRAM_ARQ":
        setup_dimstyles(doc, scale=scale)

    msp = doc.modelspace()
    count = 0

    for wall in walls:
        if wall.length < min_wall_length:
            continue

        if _wall_has_dimension(wall, existing_dimensions):
            continue

        # Agregar cota aligned
        dim = msp.add_aligned_dim(
            p1=wall.start,
            p2=wall.end,
            distance=offset,
            dimstyle=dimstyle,
            override={"layer": "A-ANNO-DIMS"},
        )
        dim.render()
        count += 1

    return count
