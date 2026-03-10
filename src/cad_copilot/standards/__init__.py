"""Módulo de estándares CAD para arquitectura.

Exporta las constantes y funciones de configuración para layers, dimstyles,
textstyles y linetypes según normas IRAM/AIA.
"""

from .dimstyles import DIMSTYLE_IRAM, setup_dimstyles
from .layers import LAYERS, setup_layers
from .linetypes import LINETYPES, setup_linetypes
from .textstyles import TEXT_STYLES, setup_textstyles

__all__ = [
    "LAYERS",
    "setup_layers",
    "DIMSTYLE_IRAM",
    "setup_dimstyles",
    "TEXT_STYLES",
    "setup_textstyles",
    "LINETYPES",
    "setup_linetypes",
]
