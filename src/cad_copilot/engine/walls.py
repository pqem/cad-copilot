"""Motor de dibujo de muros arquitectónicos.

Traduce entidades Wall del schema a LWPOLYLINE + HATCH en el Model Space.
Los muros se dibujan como rectángulos con espesor (offset perpendicular)
y opcionalmente con relleno (HATCH) según su clasificación.
"""

from __future__ import annotations

import math

from ezdxf.layouts import BaseLayout

from cad_copilot.schemas.wall import Wall, WallClassification


def _perpendicular_offset(
    start: tuple[float, float],
    end: tuple[float, float],
    thickness: float,
) -> list[tuple[float, float]]:
    """Calcula los 4 vértices del rectángulo del muro.

    El muro se expande hacia el lado izquierdo de la dirección start→end.

    Returns:
        Lista de 4 puntos [p1, p2, p3, p4] formando el contorno cerrado.
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return []

    # Vector normal unitario (perpendicular izquierda)
    nx = -dy / length
    ny = dx / length

    # Offset completo del espesor
    ox = nx * thickness
    oy = ny * thickness

    # 4 esquinas del muro (rectángulo)
    p1 = (start[0], start[1])
    p2 = (end[0], end[1])
    p3 = (end[0] + ox, end[1] + oy)
    p4 = (start[0] + ox, start[1] + oy)

    return [p1, p2, p3, p4]


def _get_hatch_pattern(classification: WallClassification) -> str | None:
    """Retorna el patrón de hatch según la clasificación del muro."""
    patterns = {
        WallClassification.exterior_portante: "SOLID",
        WallClassification.medianera: "ANSI31",
        WallClassification.interior: None,
        WallClassification.tabique: None,
    }
    return patterns.get(classification)


def draw_wall(msp: BaseLayout, wall: Wall) -> None:
    """Dibuja un muro individual en el Model Space.

    Genera:
    - LWPOLYLINE cerrada con el contorno del muro (layer A-WALL)
    - HATCH según clasificación (layer A-WALL-PATT) si corresponde

    Args:
        msp: Model Space del documento ezdxf.
        wall: Entidad Wall del schema.
    """
    vertices = _perpendicular_offset(wall.start, wall.end, wall.thickness)
    if not vertices:
        return

    # Dibujar contorno del muro
    msp.add_lwpolyline(
        vertices,
        close=True,
        dxfattribs={"layer": "A-WALL"},
    )

    # Agregar hatch si corresponde
    pattern = _get_hatch_pattern(wall.classification)
    if pattern is not None:
        hatch = msp.add_hatch(
            color=256,  # BYLAYER
            dxfattribs={"layer": "A-WALL-PATT"},
        )
        if pattern == "SOLID":
            hatch.set_solid_fill()
        else:
            hatch.set_pattern_fill(pattern, scale=0.01)

        # Crear boundary path con los vértices del muro
        hatch.paths.add_polyline_path(
            [(v[0], v[1]) for v in vertices],
            is_closed=True,
        )


def draw_walls(msp: BaseLayout, walls: list[Wall]) -> None:
    """Dibuja todos los muros en el Model Space.

    Args:
        msp: Model Space del documento ezdxf.
        walls: Lista de entidades Wall del schema.
    """
    for wall in walls:
        draw_wall(msp, wall)
