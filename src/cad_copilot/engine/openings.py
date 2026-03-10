"""Motor de aberturas: puertas y ventanas en muros.

Calcula la posición y rotación del bloque según la orientación del muro,
y corta el muro (gap) donde va la abertura.
"""

from __future__ import annotations

import math

from ezdxf.document import Drawing
from ezdxf.layouts import BaseLayout

from cad_copilot.schemas.opening import Opening, OpeningType, OpeningMechanism
from cad_copilot.schemas.wall import Wall
from cad_copilot.blocks.doors import create_hinged_door, create_sliding_door, create_double_door
from cad_copilot.blocks.windows import (
    create_sliding_window,
    create_hinged_window,
    create_fixed_window,
)


def _get_wall_angle(wall: Wall) -> float:
    """Calcula el ángulo del muro en grados (dirección start→end)."""
    dx = wall.end[0] - wall.start[0]
    dy = wall.end[1] - wall.start[1]
    return math.degrees(math.atan2(dy, dx))


def _get_wall_length(wall: Wall) -> float:
    """Calcula la longitud del muro."""
    dx = wall.end[0] - wall.start[0]
    dy = wall.end[1] - wall.start[1]
    return math.hypot(dx, dy)


def _position_on_wall(
    wall: Wall, position_along: float
) -> tuple[float, float]:
    """Calcula la coordenada absoluta de un punto a lo largo del muro.

    Args:
        wall: El muro.
        position_along: Distancia en metros desde wall.start.

    Returns:
        Coordenada (x, y) sobre la línea del muro.
    """
    length = _get_wall_length(wall)
    if length == 0:
        return wall.start
    t = position_along / length
    x = wall.start[0] + t * (wall.end[0] - wall.start[0])
    y = wall.start[1] + t * (wall.end[1] - wall.start[1])
    return (x, y)


def _ensure_block(doc: Drawing, opening: Opening) -> str:
    """Crea el bloque para la abertura si no existe. Retorna el nombre del bloque."""
    width = opening.width

    if opening.type == OpeningType.door:
        if opening.mechanism == OpeningMechanism.hinged:
            return create_hinged_door(doc, width)
        elif opening.mechanism == OpeningMechanism.sliding:
            return create_sliding_door(doc, width)
        elif opening.mechanism == OpeningMechanism.double_hinged:
            return create_double_door(doc, width)
        else:
            return create_hinged_door(doc, width)
    else:  # window
        if opening.mechanism == OpeningMechanism.sliding:
            return create_sliding_window(doc, width)
        elif opening.mechanism == OpeningMechanism.hinged:
            return create_hinged_window(doc, width)
        elif opening.mechanism == OpeningMechanism.fixed:
            return create_fixed_window(doc, width)
        else:
            return create_sliding_window(doc, width)


def draw_opening(
    doc: Drawing,
    msp: BaseLayout,
    wall: Wall,
    opening: Opening,
) -> None:
    """Dibuja una abertura (puerta o ventana) en un muro.

    Inserta el bloque correspondiente con la posición y rotación
    calculadas a partir de la orientación del muro.

    Args:
        doc: Documento ezdxf (para crear bloques si no existen).
        msp: Model Space donde insertar.
        wall: El muro que contiene la abertura.
        opening: La abertura a dibujar.
    """
    # Crear/obtener el bloque
    block_name = _ensure_block(doc, opening)

    # Calcular posición de inserción
    insert_point = _position_on_wall(wall, opening.position_along_wall)

    # Ángulo del muro
    angle = _get_wall_angle(wall)

    # Layer según tipo
    layer = "A-DOOR" if opening.type == OpeningType.door else "A-GLAZ"

    # Insertar bloque
    msp.add_blockref(
        block_name,
        insert=insert_point,
        dxfattribs={
            "layer": layer,
            "rotation": angle,
        },
    )


def draw_openings(
    doc: Drawing,
    msp: BaseLayout,
    walls: list[Wall],
) -> None:
    """Dibuja todas las aberturas de todos los muros.

    Args:
        doc: Documento ezdxf.
        msp: Model Space.
        walls: Lista de muros con sus aberturas.
    """
    for wall in walls:
        for opening in wall.openings:
            draw_opening(doc, msp, wall, opening)
