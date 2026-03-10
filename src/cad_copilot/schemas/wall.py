"""Schema de muros."""

from enum import StrEnum

from pydantic import BaseModel, Field

from cad_copilot.schemas.base import AnnotatedPoint2D
from cad_copilot.schemas.opening import Opening


class WallClassification(StrEnum):
    """Clasificación constructiva del muro."""

    exterior_portante = "exterior_portante"
    interior = "interior"
    medianera = "medianera"
    tabique = "tabique"


class Wall(BaseModel):
    """Muro definido por dos puntos extremos, espesor y clasificación."""

    id: str = Field(
        description="Identificador único del muro, ej: 'W1'",
    )
    start: AnnotatedPoint2D = Field(
        description="Coordenada (x, y) del punto de inicio en metros",
    )
    end: AnnotatedPoint2D = Field(
        description="Coordenada (x, y) del punto final en metros",
    )
    thickness: float = Field(
        gt=0,
        default=0.15,
        description="Espesor del muro en metros",
    )
    classification: WallClassification = Field(
        default=WallClassification.interior,
        description="Clasificación constructiva del muro",
    )
    openings: list[Opening] = Field(
        default_factory=list,
        description="Lista de aberturas (puertas/ventanas) en este muro",
    )
