"""Bloques parametricos de puertas para planos en planta.

Todas las entidades van en layer "0" para heredar el layer del INSERT.
Punto de insercion (0,0) en la bisagra. Muro en direccion X+, apertura en Y+.
"""

from __future__ import annotations

from ezdxf.document import Drawing


def create_hinged_door(doc: Drawing, width: float) -> str:
    """Puerta abatible: marco + hoja + arco 90 grados.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho de la puerta en metros (ej: 0.80, 0.90).

    Returns:
        Nombre del bloque creado.
    """
    name = f"DOOR_HINGED_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    marco = 0.04

    # Marco: 2 lineas cortas perpendiculares al muro
    block.add_line((0, 0), (0, marco), dxfattribs={"layer": "0"})
    block.add_line((width, 0), (width, marco), dxfattribs={"layer": "0"})

    # Hoja: linea vertical desde la bisagra
    block.add_line((0, 0), (0, width), dxfattribs={"layer": "0"})

    # Arco de giro 90 grados: centro en bisagra
    block.add_arc(
        center=(0, 0),
        radius=width,
        start_angle=0,
        end_angle=90,
        dxfattribs={"layer": "0"},
    )

    return name


def create_sliding_door(doc: Drawing, width: float) -> str:
    """Puerta corrediza: marco + hoja paralela al muro + flecha de direccion.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho de la puerta en metros.

    Returns:
        Nombre del bloque creado.
    """
    name = f"DOOR_SLIDING_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    marco = 0.04

    # Marco
    block.add_line((0, 0), (0, marco), dxfattribs={"layer": "0"})
    block.add_line((width, 0), (width, marco), dxfattribs={"layer": "0"})

    # Hoja paralela al muro (a media altura del marco)
    block.add_line(
        (0, marco / 2), (width, marco / 2), dxfattribs={"layer": "0"}
    )

    # Flecha de direccion
    arrow_y = marco + 0.05
    block.add_line(
        (width * 0.3, arrow_y), (width * 0.7, arrow_y), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (width * 0.6, arrow_y - 0.03),
        (width * 0.7, arrow_y),
        dxfattribs={"layer": "0"},
    )
    block.add_line(
        (width * 0.6, arrow_y + 0.03),
        (width * 0.7, arrow_y),
        dxfattribs={"layer": "0"},
    )

    return name


def create_double_door(doc: Drawing, width: float) -> str:
    """Puerta doble abatible: 2 hojas simetricas con 2 arcos de 90 grados.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho total de la puerta en metros.

    Returns:
        Nombre del bloque creado.
    """
    name = f"DOOR_DOUBLE_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    half = width / 2
    block = doc.blocks.new(name=name)
    marco = 0.04

    # Marco
    block.add_line((0, 0), (0, marco), dxfattribs={"layer": "0"})
    block.add_line((width, 0), (width, marco), dxfattribs={"layer": "0"})

    # Hoja izquierda: bisagra en (0,0), abre hacia Y+
    block.add_line((0, 0), (0, half), dxfattribs={"layer": "0"})
    block.add_arc(
        center=(0, 0),
        radius=half,
        start_angle=0,
        end_angle=90,
        dxfattribs={"layer": "0"},
    )

    # Hoja derecha: bisagra en (width,0), abre hacia Y+
    block.add_line((width, 0), (width, half), dxfattribs={"layer": "0"})
    block.add_arc(
        center=(width, 0),
        radius=half,
        start_angle=90,
        end_angle=180,
        dxfattribs={"layer": "0"},
    )

    return name
