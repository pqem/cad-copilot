"""Estilos de texto estándar para planos arquitectónicos.

Define los estilos de texto usados en cotas, títulos, notas y texto general.
Los nombres de fuente usan el archivo TTF correspondiente.
"""

from __future__ import annotations

from typing import Any

from ezdxf.document import Drawing

# Mapeo de nombre legible -> archivo TTF
_FONT_MAP: dict[str, str] = {
    "Arial": "arial.ttf",
    "Arial Narrow": "arialn.ttf",
    "Arial Bold": "arialbd.ttf",
}

TEXT_STYLES: dict[str, dict[str, Any]] = {
    "Standard": {
        "font": "Arial",
        "height": 0,       # Altura variable (se define al usar)
    },
    "Titulo": {
        "font": "Arial",
        "height": 0,       # Altura variable
        "width": 1.0,
    },
    "Cotas": {
        "font": "Arial Narrow",
        "height": 0,       # Altura variable
    },
    "Notas": {
        "font": "Arial",
        "height": 0,       # Altura variable
    },
}


def setup_textstyles(doc: Drawing) -> None:
    """Crea todos los estilos de texto estándar en el documento DXF.

    Si un estilo ya existe, se omite sin error.
    Los nombres de fuente se convierten a archivos TTF para compatibilidad DXF.

    Args:
        doc: Documento ezdxf donde crear los estilos de texto.
    """
    for name, props in TEXT_STYLES.items():
        if name in doc.styles:
            continue

        ttf_file = _FONT_MAP.get(props["font"], "arial.ttf")

        dxfattribs: dict[str, Any] = {
            "font": ttf_file,
        }

        if props.get("height", 0) != 0:
            dxfattribs["height"] = props["height"]

        if "width" in props:
            dxfattribs["width"] = props["width"]

        doc.styles.new(name, dxfattribs=dxfattribs)
