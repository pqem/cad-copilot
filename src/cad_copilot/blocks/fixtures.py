"""Bloques de sanitarios y artefactos para planos en planta.

Dimensiones reales en metros. Punto de insercion (0,0) en esquina inferior izquierda.
Todas las entidades van en layer "0" para heredar el layer del INSERT.
"""

from __future__ import annotations

from ezdxf.document import Drawing


def create_toilet(doc: Drawing) -> str:
    """Inodoro en planta: 0.37 x 0.60m (tanque + asiento).

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "FIX_TOILET"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Tanque (rectangulo posterior)
    points = [(0, 0), (0.37, 0), (0.37, 0.18), (0, 0.18), (0, 0)]
    block.add_lwpolyline(points, dxfattribs={"layer": "0"})

    # Asiento (elipse) — eje mayor vertical (0.21) > eje menor horizontal (0.17)
    block.add_ellipse(
        center=(0.185, 0.18 + 0.21),
        major_axis=(0, 0.21),
        ratio=0.17 / 0.21,
        dxfattribs={"layer": "0"},
    )

    return name


def create_sink(doc: Drawing) -> str:
    """Lavabo en planta: 0.45 x 0.55m.

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "FIX_SINK"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Contorno exterior
    points = [(0, 0), (0.45, 0), (0.45, 0.55), (0, 0.55), (0, 0)]
    block.add_lwpolyline(points, dxfattribs={"layer": "0"})

    # Pileta interior (elipse)
    block.add_ellipse(
        center=(0.225, 0.30),
        major_axis=(0.15, 0),
        ratio=0.67,
        dxfattribs={"layer": "0"},
    )

    return name


def create_shower(doc: Drawing, size: float = 0.80) -> str:
    """Ducha cuadrada en planta con diagonales de pendiente y desague central.

    Args:
        doc: Documento ezdxf donde crear el bloque.
        size: Lado del cuadrado en metros (default 0.80).

    Returns:
        Nombre del bloque creado.
    """
    name = f"FIX_SHOWER_{int(size * 100):03d}"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Contorno
    points = [(0, 0), (size, 0), (size, size), (0, size), (0, 0)]
    block.add_lwpolyline(points, dxfattribs={"layer": "0"})

    # Diagonales para indicar pendiente
    block.add_line((0, 0), (size, size), dxfattribs={"layer": "0"})
    block.add_line((size, 0), (0, size), dxfattribs={"layer": "0"})

    # Desague central (circulo pequeno)
    block.add_circle(
        center=(size / 2, size / 2), radius=0.03, dxfattribs={"layer": "0"}
    )

    return name


def create_bidet(doc: Drawing) -> str:
    """Bidet en planta: 0.37 x 0.55m (elipse sin tanque).

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "FIX_BIDET"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Forma eliptica completa — eje mayor vertical (0.275) > eje menor horizontal (0.17)
    block.add_ellipse(
        center=(0.185, 0.275),
        major_axis=(0, 0.275),
        ratio=0.17 / 0.275,
        dxfattribs={"layer": "0"},
    )

    return name


def create_kitchen_sink(doc: Drawing) -> str:
    """Pileta de cocina en mesada: 0.60 x 0.50m con pileta circular.

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "FIX_KITCHEN_SINK"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)

    # Mesada contorno
    points = [(0, 0), (0.60, 0), (0.60, 0.50), (0, 0.50), (0, 0)]
    block.add_lwpolyline(points, dxfattribs={"layer": "0"})

    # Pileta circular
    block.add_circle(
        center=(0.30, 0.25), radius=0.15, dxfattribs={"layer": "0"}
    )

    return name
