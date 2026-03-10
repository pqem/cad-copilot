"""Tipos base y enums comunes para CAD Copilot."""

from enum import StrEnum

from pydantic import Field
from typing import Annotated


# Coordenadas x, y en metros
Point2D = tuple[float, float]

# Alias con anotación para documentar en schemas JSON
AnnotatedPoint2D = Annotated[
    Point2D,
    Field(description="Coordenadas (x, y) en metros"),
]


class Unit(StrEnum):
    """Unidades de medida del dibujo."""

    meters = "meters"
    millimeters = "millimeters"
    centimeters = "centimeters"
