"""Agrega tabla de verificación normativa a un DXF existente.

Reutiliza el motor de norms.py y norm_table.py existentes,
alimentándolos con los espacios detectados del DXF.
"""

from __future__ import annotations

from ezdxf.document import Drawing
from ezdxf.layouts import Paperspace

from cad_copilot.engine.norm_table import _draw_cell, _ensure_layers
from cad_copilot.engine.norm_table import (
    COL_W_DESCRIPCION,
    COL_W_ESTADO,
    COL_W_MINIMO,
    COL_W_VALOR,
    FONT_HEIGHT,
    FONT_HEIGHT_TITLE,
    ROW_H,
    ROW_H_HEADER,
    TOTAL_W,
)
from cad_copilot.schemas.detection import DetectedSpace, SpaceCategory
from cad_copilot.standards.norms import (
    ResultadoNormas,
    calcular_normas,
)
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.wall import Wall


# Mapeo de SpaceCategory detectada → SpaceFunction del motor de normas
_CATEGORY_TO_FUNCTION: dict[SpaceCategory, SpaceFunction] = {
    SpaceCategory.dormitorio: SpaceFunction.dormitorio,
    SpaceCategory.living: SpaceFunction.living,
    SpaceCategory.comedor: SpaceFunction.living,  # comedor usa mismo mínimo
    SpaceCategory.cocina: SpaceFunction.cocina,
    SpaceCategory.bano: SpaceFunction.bano,
    SpaceCategory.lavadero: SpaceFunction.lavadero,
    SpaceCategory.garage: SpaceFunction.garage,
    SpaceCategory.pasillo: SpaceFunction.pasillo,
    SpaceCategory.hall: SpaceFunction.hall,
    SpaceCategory.estar: SpaceFunction.estar,
    SpaceCategory.escritorio: SpaceFunction.escritorio,
    SpaceCategory.deposito: SpaceFunction.deposito,
    SpaceCategory.otro: SpaceFunction.otro,
}


def _detected_spaces_to_schema(
    spaces: list[DetectedSpace],
) -> tuple[list[Space], list[Wall]]:
    """Convierte espacios detectados a los schemas del motor de normas.

    Crea muros ficticios cuadrados para que el motor pueda calcular
    superficies de iluminación/ventilación (se marca como 0 porque
    no tenemos datos de aberturas por espacio).
    """
    schema_spaces: list[Space] = []
    schema_walls: list[Wall] = []

    for detected in spaces:
        if detected.area <= 0:
            continue

        function = _CATEGORY_TO_FUNCTION.get(detected.category, SpaceFunction.otro)

        # Crear un espacio con un muro ficticio (cuadrado)
        import math
        side = math.sqrt(detected.area)
        wall_id = f"_auto_{detected.id}"

        wall = Wall(
            id=wall_id,
            start=(0, 0),
            end=(side, 0),
            thickness=0.15,
        )
        schema_walls.append(wall)

        space = Space(
            id=detected.id,
            name=detected.name,
            function=function,
            bounded_by=[wall_id],
        )
        schema_spaces.append(space)

    return schema_spaces, schema_walls


def calculate_norms_from_detected(
    spaces: list[DetectedSpace],
    project_name: str = "",
) -> ResultadoNormas | None:
    """Calcula verificación normativa a partir de espacios detectados.

    Args:
        spaces: Espacios detectados del DXF.
        project_name: Nombre del proyecto.

    Returns:
        ResultadoNormas o None si no hay espacios con área.
    """
    schema_spaces, schema_walls = _detected_spaces_to_schema(spaces)
    if not schema_spaces:
        return None

    floor_plan = FloorPlan(
        walls=schema_walls,
        spaces=schema_spaces,
    )
    # Inyectar nombre de proyecto en el resultado
    result = calcular_normas(floor_plan)
    result.proyecto = project_name
    return result


def add_norm_table_to_layout(
    doc: Drawing,
    layout: Paperspace,
    resultado: ResultadoNormas,
    insert_x: float = 10.0,
    insert_y: float = 280.0,
) -> None:
    """Agrega la tabla normativa directamente en un layout de Paper Space existente.

    Args:
        doc: Documento ezdxf.
        layout: Layout de Paper Space donde insertar.
        resultado: Resultado de la verificación normativa.
        insert_x: Coordenada X (mm en Paper Space).
        insert_y: Coordenada Y (mm en Paper Space).
    """
    _ensure_layers(doc)

    x = insert_x
    y = insert_y

    # Título
    titulo = "VERIFICACIÓN NORMATIVA — CÓD. EDIFICACIÓN NEUQUÉN/PLOTTIER"
    _draw_cell(
        layout, x, y, TOTAL_W, ROW_H_HEADER + 2,
        titulo,
        layer="A-ANNO-TTLB",
        text_height=FONT_HEIGHT_TITLE,
        bold=True,
        align="CENTER",
    )
    y -= ROW_H_HEADER + 2

    estado = "CUMPLE" if resultado.cumple_todo else "NO CUMPLE"
    sub = f"Proyecto: {resultado.proyecto or '(sin nombre)'}    Estado: {estado}"
    _draw_cell(layout, x, y, TOTAL_W, ROW_H, sub, align="LEFT")
    y -= ROW_H

    # Encabezados
    y -= 2
    headers = ["ÍTEM", "CALCULADO", "MÍN/MÁX", "ESTADO"]
    col_widths = [COL_W_DESCRIPCION, COL_W_VALOR, COL_W_MINIMO, COL_W_ESTADO]

    cx = x
    for header, cw in zip(headers, col_widths):
        _draw_cell(layout, cx, y, cw, ROW_H_HEADER, header, bold=True, align="CENTER")
        cx += cw
    y -= ROW_H_HEADER

    # Filas de ambientes
    for amb in resultado.ambientes:
        area_str = f"{amb.area_m2:.2f} m²"
        _draw_cell(
            layout, x, y, TOTAL_W, ROW_H,
            f"{amb.space_name} ({amb.function}) — Área: {area_str}",
            bold=True, align="LEFT",
        )
        y -= ROW_H

        for item in amb.items:
            if item.valor_minimo == 0.0 and item.cumple:
                continue
            cx = x
            estado_txt = "CUMPLE" if item.cumple else "NO CUMPLE"

            _draw_cell(layout, cx, y, COL_W_DESCRIPCION, ROW_H, f"  {item.descripcion}")
            cx += COL_W_DESCRIPCION
            _draw_cell(layout, cx, y, COL_W_VALOR, ROW_H, f"{item.valor_calculado:.3f}", align="RIGHT")
            cx += COL_W_VALOR
            _draw_cell(layout, cx, y, COL_W_MINIMO, ROW_H, f"{item.valor_minimo:.3f}", align="RIGHT")
            cx += COL_W_MINIMO
            _draw_cell(layout, cx, y, COL_W_ESTADO, ROW_H, estado_txt, align="CENTER")
            y -= ROW_H

    # Nota al pie
    y -= 2
    _draw_cell(
        layout, x, y, TOTAL_W, ROW_H,
        "Verificación orientativa. Confirmar con municipio.",
        text_height=FONT_HEIGHT - 0.5,
        align="LEFT",
    )
