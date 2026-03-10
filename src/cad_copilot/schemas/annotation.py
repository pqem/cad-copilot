"""Schema de anotaciones y acotaciones."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DimensionType(StrEnum):
    """Tipo de acotación."""

    linear = "linear"
    aligned = "aligned"
    angular = "angular"


class AnnotationType(StrEnum):
    """Tipo de anotación gráfica."""

    level_mark = "level_mark"
    section_cut = "section_cut"
    north = "north"
    scale_bar = "scale_bar"


class DimensionConfig(BaseModel):
    """Configuración de acotaciones del plano."""

    type: DimensionType = Field(
        default=DimensionType.linear,
        description="Tipo de acotación: lineal, alineada o angular",
    )
    offset: float = Field(
        default=0.5,
        description="Distancia en metros de la línea de cota al muro",
    )


class AnnotationConfig(BaseModel):
    """Configuración general de anotaciones del plano."""

    north_angle: float = Field(
        default=0.0,
        description="Ángulo del norte en grados (0 = arriba)",
    )
    scale: str = Field(
        default="1:50",
        description="Escala de representación, ej: '1:50', '1:100'",
    )
    dimensions: DimensionConfig | None = Field(
        default=None,
        description="Configuración de acotaciones; None si no se acotan",
    )
