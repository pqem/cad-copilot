"""Estilo de cota IRAM para arquitectura.

Define el estilo de acotado IRAM_ARQ con las variables DXF estándar
para planos arquitectónicos en sistema métrico.
"""

from __future__ import annotations

from typing import Any

from ezdxf.document import Drawing

# Configuración base del estilo de cota IRAM para arquitectura.
# Los valores están en unidades de dibujo (mm en papel a escala 1:1).
# DIMSCALE se calcula según la escala del plano.
DIMSTYLE_IRAM: dict[str, Any] = {
    "name": "IRAM_ARQ",
    "dimasz": 2.5,       # Tamaño de flecha (mm a escala)
    "dimtxt": 2.5,       # Altura texto de cota
    "dimexe": 1.25,      # Extensión línea auxiliar más allá de la línea de cota
    "dimexo": 0.625,     # Offset línea auxiliar desde el punto de referencia
    "dimdec": 2,         # 2 decimales (metros)
    "dimgap": 0.625,     # Gap entre texto y línea de cota
    "dimtad": 1,         # Texto arriba de la línea
    "dimtih": 0,         # Texto NO siempre horizontal dentro
    "dimtoh": 0,         # Texto NO siempre horizontal fuera
    "dimtsz": 0,         # Sin tick (usar flecha)
    "dimclrd": 3,        # Color línea de cota (verde)
    "dimclre": 3,        # Color línea auxiliar
    "dimclrt": 3,        # Color texto
    "dimlunit": 2,       # Unidades decimales
    "dimscale": 1.0,     # Se ajusta según escala del plano
}


def setup_dimstyles(doc: Drawing, scale: int = 50) -> None:
    """Crea el estilo de cota IRAM_ARQ en el documento DXF.

    El DIMSCALE se calcula a partir de la escala del plano:
    - Escala 1:50  -> DIMSCALE = 50
    - Escala 1:100 -> DIMSCALE = 100
    - Escala 1:25  -> DIMSCALE = 25

    Esto garantiza que textos y flechas se vean correctamente en papel.

    Args:
        doc: Documento ezdxf donde crear el dimstyle.
        scale: Denominador de la escala del plano (50 para 1:50, 100 para 1:100).
    """
    name = DIMSTYLE_IRAM["name"]

    if name in doc.dimstyles:
        return

    dimstyle = doc.dimstyles.new(name)

    # Setear todas las variables DXF del estilo de cota
    for key, value in DIMSTYLE_IRAM.items():
        if key == "name":
            continue
        if key == "dimscale":
            # DIMSCALE se calcula según la escala del plano
            setattr(dimstyle.dxf, key, float(scale))
        else:
            setattr(dimstyle.dxf, key, value)
