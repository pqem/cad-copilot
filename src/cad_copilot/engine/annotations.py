"""Motor de anotaciones: cotas y dimensiones.

Genera DIMENSION entities para acotar muros y aberturas.
"""

from __future__ import annotations

import math

from ezdxf.layouts import BaseLayout

from cad_copilot.schemas.wall import Wall


def add_aligned_dimension(
    msp: BaseLayout,
    p1: tuple[float, float],
    p2: tuple[float, float],
    distance: float = 0.5,
    dimstyle: str = "IRAM_ARQ",
) -> None:
    """Agrega una cota aligned entre dos puntos.

    Args:
        msp: Model Space.
        p1: Primer punto de la cota.
        p2: Segundo punto de la cota.
        distance: Distancia de la línea de cota al segmento (en metros).
        dimstyle: Nombre del estilo de cota.
    """
    dim = msp.add_aligned_dim(
        p1=p1,
        p2=p2,
        distance=distance,
        dimstyle=dimstyle,
        override={"layer": "A-ANNO-DIMS"},
    )
    dim.render()


def add_linear_dimension(
    msp: BaseLayout,
    p1: tuple[float, float],
    p2: tuple[float, float],
    distance: float = 0.5,
    angle: float = 0.0,
    dimstyle: str = "IRAM_ARQ",
) -> None:
    """Agrega una cota linear (horizontal o vertical).

    Args:
        msp: Model Space.
        p1: Primer punto.
        p2: Segundo punto.
        distance: Distancia de la línea de cota.
        angle: 0 para horizontal, 90 para vertical.
        dimstyle: Nombre del estilo de cota.
    """
    dim = msp.add_linear_dim(
        base=(p1[0], p1[1] + distance) if angle == 0 else (p1[0] + distance, p1[1]),
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle=dimstyle,
        override={"layer": "A-ANNO-DIMS"},
    )
    dim.render()


def add_wall_dimensions(
    msp: BaseLayout,
    walls: list[Wall],
    offset: float = 0.8,
    dimstyle: str = "IRAM_ARQ",
) -> None:
    """Genera cadena de cotas exteriores para un conjunto de muros.

    Acota cada muro individualmente con una cota aligned
    a una distancia offset del muro.

    Args:
        msp: Model Space.
        walls: Lista de muros a acotar.
        offset: Distancia de las cotas al muro (metros).
        dimstyle: Estilo de cota.
    """
    for wall in walls:
        length = math.hypot(
            wall.end[0] - wall.start[0],
            wall.end[1] - wall.start[1],
        )
        # Saltar muros de longitud cero para evitar ZeroDivisionError
        if length == 0:
            continue

        # Cota del muro completo (start a end)
        add_aligned_dimension(
            msp,
            p1=wall.start,
            p2=wall.end,
            distance=offset,
            dimstyle=dimstyle,
        )

        # Cotas de las aberturas dentro del muro
        if wall.openings:

            # Dirección unitaria del muro
            dx = (wall.end[0] - wall.start[0]) / length
            dy = (wall.end[1] - wall.start[1]) / length

            # Acotar segmentos entre aberturas
            sorted_openings = sorted(wall.openings, key=lambda o: o.position_along_wall)

            prev_pos = 0.0
            inner_offset = offset + 0.4  # segunda línea de cotas

            for opening in sorted_openings:
                op_start = opening.position_along_wall
                op_end = op_start + opening.width

                # Segmento antes de la abertura
                if op_start - prev_pos > 0.01:
                    p_a = (
                        wall.start[0] + dx * prev_pos,
                        wall.start[1] + dy * prev_pos,
                    )
                    p_b = (
                        wall.start[0] + dx * op_start,
                        wall.start[1] + dy * op_start,
                    )
                    add_aligned_dimension(
                        msp, p1=p_a, p2=p_b,
                        distance=inner_offset, dimstyle=dimstyle,
                    )

                # Cota de la abertura misma
                p_c = (
                    wall.start[0] + dx * op_start,
                    wall.start[1] + dy * op_start,
                )
                p_d = (
                    wall.start[0] + dx * op_end,
                    wall.start[1] + dy * op_end,
                )
                add_aligned_dimension(
                    msp, p1=p_c, p2=p_d,
                    distance=inner_offset, dimstyle=dimstyle,
                )

                prev_pos = op_end

            # Segmento después de la última abertura
            if length - prev_pos > 0.01:
                p_e = (
                    wall.start[0] + dx * prev_pos,
                    wall.start[1] + dy * prev_pos,
                )
                add_aligned_dimension(
                    msp, p1=p_e, p2=wall.end,
                    distance=inner_offset, dimstyle=dimstyle,
                )
