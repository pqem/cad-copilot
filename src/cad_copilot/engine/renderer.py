"""Renderer principal: orquesta la generación completa de un DXF desde un FloorPlan JSON.

Flujo: JSON → Pydantic validation → ezdxf document → DXF file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cad_copilot.schemas.project import FloorPlan
from cad_copilot.engine.document import create_document
from cad_copilot.engine.walls import draw_walls
from cad_copilot.engine.openings import draw_openings
from cad_copilot.engine.spaces import add_space_labels
from cad_copilot.engine.annotations import add_wall_dimensions
from cad_copilot.engine.layout import create_layout, add_title_block


def render_floor_plan(floor_plan: FloorPlan, output_path: str) -> str:
    """Genera un archivo DXF completo desde un FloorPlan.

    Args:
        floor_plan: Modelo FloorPlan validado con Pydantic.
        output_path: Ruta donde guardar el DXF.

    Returns:
        Ruta absoluta del archivo generado.
    """
    # 1. Crear documento con escala configurada
    scale = floor_plan.paper_config.scale
    doc = create_document(scale=scale)
    msp = doc.modelspace()

    # 2. Dibujar muros
    draw_walls(msp, floor_plan.walls)

    # 3. Dibujar aberturas (puertas y ventanas)
    draw_openings(doc, msp, floor_plan.walls)

    # 4. Agregar textos de ambientes con superficie
    if floor_plan.spaces:
        add_space_labels(msp, floor_plan.spaces, floor_plan.walls)

    # 5. Agregar cotas exteriores
    add_wall_dimensions(msp, floor_plan.walls)

    # 6. Crear Paper Space con viewport
    if floor_plan.title_block is not None or True:
        # Calcular centro de la vista (centroide de todos los muros)
        all_x = []
        all_y = []
        for w in floor_plan.walls:
            all_x.extend([w.start[0], w.end[0]])
            all_y.extend([w.start[1], w.end[1]])
        if all_x and all_y:
            view_cx = (min(all_x) + max(all_x)) / 2
            view_cy = (min(all_y) + max(all_y)) / 2
        else:
            view_cx, view_cy = 3.0, 2.0

        layout = create_layout(
            doc,
            floor_plan.paper_config,
            layout_name=floor_plan.title_block.drawing_name if floor_plan.title_block else "Plano",
            view_center=(view_cx, view_cy),
        )

        # 7. Insertar cartela
        if floor_plan.title_block is not None:
            add_title_block(doc, layout, floor_plan.title_block, floor_plan.paper_config)

    # 8. Guardar
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output))

    return str(output.resolve())


def render_from_json(json_path: str, output_path: str) -> str:
    """Carga un JSON, lo valida con Pydantic y genera el DXF.

    Args:
        json_path: Ruta al archivo JSON con el FloorPlan.
        output_path: Ruta donde guardar el DXF.

    Returns:
        Ruta absoluta del archivo generado.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    floor_plan = FloorPlan.model_validate(data)
    return render_floor_plan(floor_plan, output_path)


def main() -> None:
    """Entry point CLI: cad-copilot input.json output.dxf"""
    if len(sys.argv) < 3:
        print("Uso: cad-copilot <input.json> <output.dxf>")
        print("  o: python -m cad_copilot.engine.renderer <input.json> <output.dxf>")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2]

    result = render_from_json(json_path, output_path)
    print(f"DXF generado: {result}")


if __name__ == "__main__":
    main()
