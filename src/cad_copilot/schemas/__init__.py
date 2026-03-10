"""Schemas Pydantic para CAD Copilot — re-exporta todos los modelos públicos."""

from cad_copilot.schemas.annotation import (
    AnnotationConfig,
    AnnotationType,
    DimensionConfig,
    DimensionType,
)
from cad_copilot.schemas.base import AnnotatedPoint2D, Point2D, Unit
from cad_copilot.schemas.layout import (
    Orientation,
    PaperConfig,
    PaperSize,
    TitleBlock,
)
from cad_copilot.schemas.opening import Opening, OpeningMechanism, OpeningType
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.wall import Wall, WallClassification

__all__ = [
    # Base
    "AnnotatedPoint2D",
    "Point2D",
    "Unit",
    # Aberturas
    "Opening",
    "OpeningMechanism",
    "OpeningType",
    # Muros
    "Wall",
    "WallClassification",
    # Espacios
    "Space",
    "SpaceFunction",
    # Anotaciones
    "AnnotationConfig",
    "AnnotationType",
    "DimensionConfig",
    "DimensionType",
    # Layout
    "Orientation",
    "PaperConfig",
    "PaperSize",
    "TitleBlock",
    # Proyecto
    "FloorPlan",
]
