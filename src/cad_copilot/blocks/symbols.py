"""Bloques de simbolos arquitectonicos para planos.

Todas las entidades van en layer "0" para heredar el layer del INSERT.
"""

from __future__ import annotations

from ezdxf.document import Drawing


def create_north_arrow(doc: Drawing) -> str:
    """Flecha de norte: triangulo apuntando hacia arriba + letra N.

    El tamano base es 0.5m, se escala con el factor de INSERT.

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "SYM_NORTH"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    size = 0.5  # tamano en metros (se escalara con INSERT)

    # Triangulo
    block.add_lwpolyline(
        [(0, 0), (size / 2, size), (-size / 2, size), (0, 0)],
        close=True,
        dxfattribs={"layer": "0"},
    )

    # Linea central (mitad rellena)
    block.add_line((0, 0), (0, size), dxfattribs={"layer": "0"})

    # Letra N
    block.add_text(
        "N",
        dxfattribs={
            "layer": "0",
            "height": size * 0.3,
            "insert": (-size * 0.15, size * 1.1),
        },
    )

    return name


def create_level_mark(doc: Drawing) -> str:
    """Simbolo de nivel: triangulo pequeno + atributo para el valor de nivel.

    Args:
        doc: Documento ezdxf donde crear el bloque.

    Returns:
        Nombre del bloque creado.
    """
    name = "SYM_LEVEL"
    if name in doc.blocks:
        return name

    block = doc.blocks.new(name=name)
    s = 0.15  # tamano del triangulo

    # Triangulo equilatero
    block.add_lwpolyline(
        [(-s / 2, 0), (s / 2, 0), (0, s * 0.866)],
        close=True,
        dxfattribs={"layer": "0"},
    )

    # Atributo para el nivel (ATTDEF)
    block.add_attdef(
        tag="NIVEL",
        insert=(s, s * 0.3),
        dxfattribs={"layer": "0", "height": 0.10, "prompt": "Nivel"},
    )

    return name
