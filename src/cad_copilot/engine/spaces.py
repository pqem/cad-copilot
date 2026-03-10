"""Motor de textos de ambientes.

Coloca MTEXT con el nombre del local y su superficie calculada.
"""

from __future__ import annotations

import math

from ezdxf.layouts import BaseLayout
from shapely.geometry import Polygon

from cad_copilot.schemas.space import Space
from cad_copilot.schemas.wall import Wall
from cad_copilot.engine.walls import _perpendicular_offset


def _calculate_space_polygon(
    space: Space, walls: list[Wall]
) -> Polygon | None:
    """Construye el polígono de un ambiente desde los puntos interiores de sus muros.

    Simplificación: usa los start points de los muros que limitan el espacio
    para formar el polígono (asume que están en orden y forman un contorno cerrado).
    """
    wall_map = {w.id: w for w in walls}
    points = []
    for wall_id in space.bounded_by:
        wall = wall_map.get(wall_id)
        if wall is None:
            continue
        points.append(wall.start)

    if len(points) < 3:
        return None

    return Polygon(points)


def calculate_space_area(space: Space, walls: list[Wall]) -> float:
    """Calcula la superficie de un ambiente en m².

    Args:
        space: El ambiente.
        walls: Lista completa de muros del proyecto.

    Returns:
        Superficie en m². 0.0 si no se puede calcular.
    """
    poly = _calculate_space_polygon(space, walls)
    if poly is None or not poly.is_valid:
        return 0.0
    return poly.area


def _space_centroid(space: Space, walls: list[Wall]) -> tuple[float, float]:
    """Calcula el centroide del ambiente para colocar el texto."""
    poly = _calculate_space_polygon(space, walls)
    if poly is None or not poly.is_valid:
        # Fallback: promedio de start points de los muros
        wall_map = {w.id: w for w in walls}
        points = [wall_map[wid].start for wid in space.bounded_by if wid in wall_map]
        if not points:
            return (0, 0)
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        return (cx, cy)
    centroid = poly.centroid
    return (centroid.x, centroid.y)


def add_space_labels(
    msp: BaseLayout,
    spaces: list[Space],
    walls: list[Wall],
    text_height: float = 0.10,
) -> None:
    """Agrega etiquetas de ambientes (nombre + superficie) como MTEXT.

    Args:
        msp: Model Space.
        spaces: Lista de ambientes.
        walls: Lista de muros (para calcular áreas y centroides).
        text_height: Altura del texto en metros (en Model Space).
    """
    for space in spaces:
        area = calculate_space_area(space, walls)
        cx, cy = _space_centroid(space, walls)

        # Texto: NOMBRE\Psuperficie m²
        text = f"{space.name}\\P{area:.2f} m²"

        msp.add_mtext(
            text,
            dxfattribs={
                "layer": "A-ANNO-TEXT",
                "style": "Standard",
                "char_height": text_height,
                "insert": (cx, cy),
                "attachment_point": 5,  # Middle center
            },
        )
