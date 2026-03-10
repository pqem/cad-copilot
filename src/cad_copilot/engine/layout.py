"""Motor de Paper Space: layouts, viewports y cartela.

Configura Paper Space para impresión con viewport escalado
y cartela CPTN con atributos.
"""

from __future__ import annotations

from ezdxf.document import Drawing
from ezdxf.layouts import Paperspace

from cad_copilot.schemas.layout import PaperConfig, PaperSize, Orientation, TitleBlock


# Dimensiones de papel ISO en mm (ancho x alto en portrait)
PAPER_SIZES_MM: dict[PaperSize, tuple[float, float]] = {
    PaperSize.A4: (210, 297),
    PaperSize.A3: (297, 420),
    PaperSize.A2: (420, 594),
    PaperSize.A1: (594, 841),
    PaperSize.A0: (841, 1189),
}


def _get_paper_dimensions(config: PaperConfig) -> tuple[float, float]:
    """Retorna ancho x alto del papel en mm según tamaño y orientación."""
    w, h = PAPER_SIZES_MM[config.size]
    if config.orientation == Orientation.landscape:
        return (h, w)
    return (w, h)


def create_layout(
    doc: Drawing,
    config: PaperConfig,
    layout_name: str = "Plano",
    view_center: tuple[float, float] = (3.0, 2.0),
) -> Paperspace:
    """Crea un layout en Paper Space con viewport escalado.

    Args:
        doc: Documento ezdxf.
        config: Configuración del papel (tamaño, orientación, escala, márgenes).
        layout_name: Nombre del layout.
        view_center: Centro de la vista en Model Space (metros).

    Returns:
        El layout creado.
    """
    paper_w, paper_h = _get_paper_dimensions(config)
    margin_left, margin_top, margin_right, margin_bottom = config.margins

    # Área útil para el viewport (descontando márgenes)
    vp_w = paper_w - margin_left - margin_right
    vp_h = paper_h - margin_top - margin_bottom

    # Centro del viewport en Paper Space (en mm)
    vp_center_x = margin_left + vp_w / 2
    vp_center_y = margin_bottom + vp_h / 2

    # Altura visible en Model Space (metros) para lograr la escala deseada
    # Escala 1:N → 1mm en papel = N mm en realidad
    # vp_h (mm) → vp_h * N (mm en model) → vp_h * N / 1000 (m en model)
    view_height = vp_h * config.scale / 1000

    # Crear layout
    layout = doc.layouts.new(layout_name)

    # Agregar viewport
    layout.add_viewport(
        center=(vp_center_x, vp_center_y),
        size=(vp_w, vp_h),
        view_center_point=view_center,
        view_height=view_height,
    )

    return layout


def _create_title_block_definition(doc: Drawing) -> str:
    """Crea el bloque de cartela CPTN si no existe. Retorna nombre del bloque."""
    name = "CARTELA_CPTN"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Cartela estándar: 170mm x 55mm (tamaño en mm de Paper Space)
    w = 170
    h = 55

    # Marco exterior
    block.add_lwpolyline(
        [(0, 0), (w, 0), (w, h), (0, h), (0, 0)],
        close=True,
        dxfattribs={"layer": "0"},
    )

    # Divisiones horizontales
    block.add_line((0, 11), (w, 11), dxfattribs={"layer": "0"})  # línea inferior
    block.add_line((0, 22), (w, 22), dxfattribs={"layer": "0"})
    block.add_line((0, 33), (w, 33), dxfattribs={"layer": "0"})
    block.add_line((0, 44), (w, 44), dxfattribs={"layer": "0"})

    # División vertical central
    block.add_line((85, 0), (85, 33), dxfattribs={"layer": "0"})

    # Labels fijos (texto pequeño)
    label_h = 2.0
    block.add_text("PROYECTO:", dxfattribs={"layer": "0", "height": label_h, "insert": (2, 46)})
    block.add_text("PLANO:", dxfattribs={"layer": "0", "height": label_h, "insert": (2, 35)})
    block.add_text("UBICACIÓN:", dxfattribs={"layer": "0", "height": label_h, "insert": (2, 24)})
    block.add_text("PROFESIONAL:", dxfattribs={"layer": "0", "height": label_h, "insert": (2, 13)})
    block.add_text("MATRÍCULA:", dxfattribs={"layer": "0", "height": label_h, "insert": (87, 13)})
    block.add_text("ESCALA:", dxfattribs={"layer": "0", "height": label_h, "insert": (2, 2)})
    block.add_text("FECHA:", dxfattribs={"layer": "0", "height": label_h, "insert": (87, 2)})
    block.add_text("LÁMINA:", dxfattribs={"layer": "0", "height": label_h, "insert": (140, 2)})

    # Atributos editables
    attr_h = 3.5
    block.add_attdef(tag="PROYECTO", insert=(2, 49), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="PLANO", insert=(2, 38), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="UBICACION", insert=(2, 27), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="PROFESIONAL", insert=(2, 16), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="MATRICULA", insert=(87, 16), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="ESCALA", insert=(2, 5), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="FECHA", insert=(87, 5), dxfattribs={"layer": "0", "height": attr_h})
    block.add_attdef(tag="LAMINA", insert=(140, 5), dxfattribs={"layer": "0", "height": attr_h})

    return name


def add_title_block(
    doc: Drawing,
    layout: Paperspace,
    title_block: TitleBlock,
    paper_config: PaperConfig,
) -> None:
    """Inserta la cartela CPTN en el Paper Space.

    Se coloca en la esquina inferior derecha del papel.

    Args:
        doc: Documento ezdxf.
        layout: Layout de Paper Space donde insertar.
        title_block: Datos de la cartela.
        paper_config: Configuración del papel (para calcular posición).
    """
    block_name = _create_title_block_definition(doc)
    paper_w, paper_h = _get_paper_dimensions(paper_config)

    # Cartela en esquina inferior derecha (con margen derecho de 5mm)
    cartela_w = 170
    insert_x = paper_w - cartela_w - paper_config.margins[2]
    insert_y = paper_config.margins[3]

    # Mapeo de datos a atributos
    attribs = {
        "PROYECTO": title_block.project,
        "PLANO": title_block.drawing_name,
        "UBICACION": title_block.location,
        "PROFESIONAL": title_block.professional,
        "MATRICULA": title_block.license_number,
        "ESCALA": f"1:{paper_config.scale}",
        "FECHA": title_block.date,
        "LAMINA": title_block.sheet,
    }

    layout.add_blockref(
        block_name,
        insert=(insert_x, insert_y),
        dxfattribs={"layer": "A-ANNO-TTLB"},
    ).add_auto_attribs(attribs)
