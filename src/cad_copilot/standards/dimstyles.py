"""Estilo de cota IRAM para arquitectura.

Define el estilo de acotado IRAM_ARQ con las variables DXF estándar
para planos arquitectónicos en sistema métrico.
"""

from __future__ import annotations

from typing import Any

from ezdxf.document import Drawing

# Configuración base del estilo de cota IRAM para arquitectura.
# IMPORTANTE: El Model Space usa metros (INSUNITS=6).
# Los valores se expresan en metros para que se vean correctamente.
# Se calculan como: valor_mm_papel × escala / 1000
# Ejemplo 1:50 → 2.5mm texto × 50 / 1000 = 0.125m en Model Space.
# DIMSCALE=1 siempre (los valores ya están escalados).
#
# Valores base en mm de papel (antes de escalar):
_DIMTXT_MM = 2.5       # Altura texto de cota (mm en papel)
_DIMASZ_MM = 2.5       # Tamaño de flecha (mm en papel)
_DIMEXE_MM = 1.25      # Extensión línea auxiliar
_DIMEXO_MM = 0.625     # Offset línea auxiliar
_DIMGAP_MM = 0.625     # Gap texto-línea

# Diccionario de referencia (valores base en mm, escala por defecto 50)
DIMSTYLE_IRAM: dict[str, Any] = {
    "name": "IRAM_ARQ",
    "dimscale": 1,
    "dimtxt": _DIMTXT_MM,
    "dimasz": _DIMASZ_MM,
    "dimexe": _DIMEXE_MM,
    "dimexo": _DIMEXO_MM,
    "dimgap": _DIMGAP_MM,
    "dimdec": 2,
    "dimtad": 1,
    "dimtih": 0,
    "dimtoh": 0,
    "dimtsz": 0,
    "dimclrd": 3,
    "dimclre": 3,
    "dimclrt": 3,
    "dimlunit": 2,
}


def _mm_to_model(mm: float, scale: int) -> float:
    """Convierte mm en papel a metros en Model Space según la escala."""
    return mm * scale / 1000


def setup_dimstyles(doc: Drawing, scale: int = 50) -> None:
    """Crea el estilo de cota IRAM_ARQ en el documento DXF.

    Los tamaños se calculan para que en Model Space (metros) se vean
    proporcionados a la escala del plano. En Paper Space a 1:N
    el texto medirá 2.5mm.

    Args:
        doc: Documento ezdxf donde crear el dimstyle.
        scale: Denominador de la escala del plano (50 para 1:50, 100 para 1:100).
    """
    name = "IRAM_ARQ"

    if name in doc.dimstyles:
        return

    dimstyle = doc.dimstyles.new(name)

    dimstyle.dxf.dimscale = 1.0  # Siempre 1 — valores ya escalados
    dimstyle.dxf.dimtxt = _mm_to_model(_DIMTXT_MM, scale)
    dimstyle.dxf.dimasz = _mm_to_model(_DIMASZ_MM, scale)
    dimstyle.dxf.dimexe = _mm_to_model(_DIMEXE_MM, scale)
    dimstyle.dxf.dimexo = _mm_to_model(_DIMEXO_MM, scale)
    dimstyle.dxf.dimgap = _mm_to_model(_DIMGAP_MM, scale)
    dimstyle.dxf.dimdec = 2         # 2 decimales
    dimstyle.dxf.dimtad = 1         # Texto arriba de la línea
    dimstyle.dxf.dimtih = 0         # Texto NO siempre horizontal dentro
    dimstyle.dxf.dimtoh = 0         # Texto NO siempre horizontal fuera
    dimstyle.dxf.dimtsz = 0         # Sin tick (usar flecha)
    dimstyle.dxf.dimclrd = 3        # Color línea de cota (verde)
    dimstyle.dxf.dimclre = 3        # Color línea auxiliar
    dimstyle.dxf.dimclrt = 3        # Color texto
    dimstyle.dxf.dimlunit = 2       # Unidades decimales
