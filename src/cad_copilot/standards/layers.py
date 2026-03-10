"""Definición de layers estándar IRAM/AIA para arquitectura 2D.

Cada layer tiene:
- name: nombre según convención AIA (A-XXXX)
- color: índice ACI de AutoCAD
- lineweight: peso de línea en centésimas de mm (50 = 0.50mm)
- linetype: tipo de línea DXF
- description: descripción en español
"""

from __future__ import annotations

from typing import Any

from ezdxf.document import Drawing

# Colores ACI estándar de referencia:
# 1=rojo, 2=amarillo, 3=verde, 4=cyan, 5=azul, 6=magenta, 7=blanco, 8=gris, 9=gris claro
# lineweight -3 = Default en DXF

LAYERS: dict[str, dict[str, Any]] = {
    "A-WALL": {
        "color": 7,
        "lineweight": 50,
        "linetype": "Continuous",
        "description": "Muros",
    },
    "A-WALL-PATT": {
        "color": 8,
        "lineweight": 13,
        "linetype": "Continuous",
        "description": "Relleno de muros",
    },
    "A-DOOR": {
        "color": 2,
        "lineweight": 25,
        "linetype": "Continuous",
        "description": "Puertas",
    },
    "A-GLAZ": {
        "color": 3,
        "lineweight": 25,
        "linetype": "Continuous",
        "description": "Ventanas/vidrios",
    },
    "A-FURN": {
        "color": 6,
        "lineweight": 13,
        "linetype": "Continuous",
        "description": "Mobiliario",
    },
    "A-PLMB-FIXT": {
        "color": 1,
        "lineweight": 18,
        "linetype": "Continuous",
        "description": "Sanitarios",
    },
    "A-STRS": {
        "color": 4,
        "lineweight": 25,
        "linetype": "Continuous",
        "description": "Escaleras",
    },
    "A-COLS": {
        "color": 5,
        "lineweight": 35,
        "linetype": "Continuous",
        "description": "Columnas",
    },
    "A-ANNO-DIMS": {
        "color": 3,
        "lineweight": 18,
        "linetype": "Continuous",
        "description": "Cotas",
    },
    "A-ANNO-TEXT": {
        "color": 3,
        "lineweight": 18,
        "linetype": "Continuous",
        "description": "Textos",
    },
    "A-ANNO-SYMB": {
        "color": 3,
        "lineweight": 18,
        "linetype": "Continuous",
        "description": "Símbolos",
    },
    "A-ANNO-TTLB": {
        "color": 7,
        "lineweight": 50,
        "linetype": "Continuous",
        "description": "Cartela",
    },
    "A-FLOR": {
        "color": 9,
        "lineweight": 13,
        "linetype": "Continuous",
        "description": "Pisos",
    },
    "A-GRID": {
        "color": 8,
        "lineweight": 13,
        "linetype": "CENTER",
        "description": "Ejes",
    },
    "A-ELEV": {
        "color": 4,
        "lineweight": 25,
        "linetype": "Continuous",
        "description": "Fachadas",
    },
    "A-ROOF": {
        "color": 5,
        "lineweight": 25,
        "linetype": "Continuous",
        "description": "Techos",
    },
    "DEFPOINTS": {
        "color": 7,
        "lineweight": -3,
        "linetype": "Continuous",
        "description": "Puntos de definición (no imprime)",
    },
}


def setup_layers(doc: Drawing) -> None:
    """Crea todos los layers estándar IRAM/AIA en el documento DXF.

    Si un layer ya existe, se omite sin error.

    Args:
        doc: Documento ezdxf donde crear los layers.
    """
    for name, props in LAYERS.items():
        if name in doc.layers:
            continue
        layer = doc.layers.new(
            name=name,
            dxfattribs={
                "color": props["color"],
                "lineweight": props["lineweight"],
                "linetype": props["linetype"],
            },
        )
        # La descripción se guarda como XDATA en el layer
        if props.get("description"):
            layer.description = props["description"]
