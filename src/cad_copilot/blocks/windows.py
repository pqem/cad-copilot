"""Bloques parametricos de ventanas para planos en planta.

Todas las entidades van en layer "0" para heredar el layer del INSERT.
Punto de insercion (0,0) en un extremo, centradas en Y sobre el eje del muro.
"""

from __future__ import annotations

from ezdxf.document import Drawing


def create_sliding_window(doc: Drawing, width: float) -> str:
    """Ventana corrediza: 2 vidrios paralelos dentro del espesor del muro.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho de la ventana en metros.

    Returns:
        Nombre del bloque creado.
    """
    name = f"WIN_SLIDING_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    glass_offset = 0.03  # distancia entre vidrios y eje del muro

    # Vidrio 1
    block.add_line(
        (0, -glass_offset), (width, -glass_offset), dxfattribs={"layer": "0"}
    )
    # Vidrio 2
    block.add_line(
        (0, glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Marco en los extremos
    block.add_line(
        (0, -glass_offset), (0, glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (width, -glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Division central (indica corrediza)
    block.add_line(
        (width / 2, -glass_offset),
        (width / 2, glass_offset),
        dxfattribs={"layer": "0"},
    )

    return name


def create_hinged_window(doc: Drawing, width: float) -> str:
    """Ventana abatible: vidrio + lineas diagonales indicando apertura.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho de la ventana en metros.

    Returns:
        Nombre del bloque creado.
    """
    name = f"WIN_HINGED_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    glass_offset = 0.03

    # Vidrios
    block.add_line(
        (0, -glass_offset), (width, -glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (0, glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Marco en los extremos
    block.add_line(
        (0, -glass_offset), (0, glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (width, -glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Diagonales indicando apertura
    block.add_line(
        (0, 0), (width / 2, glass_offset * 3), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (width, 0), (width / 2, glass_offset * 3), dxfattribs={"layer": "0"}
    )

    return name


def create_fixed_window(doc: Drawing, width: float) -> str:
    """Ventana pano fijo: vidrio + cruz indicando fijo.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        width: Ancho de la ventana en metros.

    Returns:
        Nombre del bloque creado.
    """
    name = f"WIN_FIXED_{int(width * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    glass_offset = 0.03

    # Vidrios
    block.add_line(
        (0, -glass_offset), (width, -glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (0, glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Marco en los extremos
    block.add_line(
        (0, -glass_offset), (0, glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (width, -glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    # Cruz
    block.add_line(
        (0, -glass_offset), (width, glass_offset), dxfattribs={"layer": "0"}
    )
    block.add_line(
        (0, glass_offset), (width, -glass_offset), dxfattribs={"layer": "0"}
    )

    return name
