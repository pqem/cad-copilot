"""Agrega o actualiza cartela CPTN en un DXF existente.

Reutiliza el motor de layout.py existente para la definición del bloque
y la inserción con atributos.
"""

from __future__ import annotations

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Paperspace

from cad_copilot.engine.layout import (
    add_title_block,
    create_layout,
)
from cad_copilot.schemas.layout import PaperConfig, TitleBlock
from cad_copilot.standards.layers import setup_layers


def add_title_block_to_existing(
    doc: Drawing,
    title_block: TitleBlock,
    paper_config: PaperConfig | None = None,
    layout_name: str = "Documentacion",
) -> Paperspace:
    """Agrega cartela CPTN a un DXF existente.

    Si el DXF no tiene un layout con ese nombre, lo crea.
    Si ya existe, usa el existente.

    Args:
        doc: Documento ezdxf a modificar.
        title_block: Datos de la cartela.
        paper_config: Config del papel. Si es None, usa A3 landscape 1:50.
        layout_name: Nombre del layout donde insertar.

    Returns:
        El layout donde se insertó la cartela.
    """
    setup_layers(doc)

    if paper_config is None:
        from cad_copilot.schemas.layout import Orientation, PaperSize
        paper_config = PaperConfig(
            size=PaperSize.A3,
            orientation=Orientation.landscape,
            scale=50,
        )

    # Obtener o crear layout
    layout = None
    try:
        layout = doc.layouts.get(layout_name)
    except (ezdxf.DXFKeyError, KeyError):
        pass

    if layout is None:
        # Calcular centro de la vista desde el bounding box del Model Space
        msp = doc.modelspace()
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for entity in msp:
            try:
                if entity.dxftype() == "LINE":
                    for pt in (entity.dxf.start, entity.dxf.end):
                        min_x = min(min_x, pt.x)
                        min_y = min(min_y, pt.y)
                        max_x = max(max_x, pt.x)
                        max_y = max(max_y, pt.y)
            except (AttributeError, TypeError):
                continue

        if min_x == float("inf"):
            view_center = (0.0, 0.0)
        else:
            view_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)

        layout = create_layout(doc, paper_config, layout_name, view_center)

    add_title_block(doc, layout, title_block, paper_config)
    return layout
