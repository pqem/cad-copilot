"""Schema de aberturas (puertas y ventanas)."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class OpeningType(StrEnum):
    """Tipo de abertura."""

    door = "door"
    window = "window"


class OpeningMechanism(StrEnum):
    """Mecanismo de apertura de la abertura."""

    hinged = "hinged"
    sliding = "sliding"
    fixed = "fixed"
    double_hinged = "double_hinged"


class Opening(BaseModel):
    """Abertura (puerta o ventana) ubicada sobre un muro."""

    type: OpeningType = Field(
        description="Tipo de abertura: puerta o ventana",
    )
    position_along_wall: float = Field(
        ge=0,
        description="Posición en metros desde el punto de inicio del muro",
    )
    width: float = Field(
        gt=0,
        description="Ancho de la abertura en metros",
    )
    height: float = Field(
        gt=0,
        default=None,  # type: ignore[assignment]
        description="Alto de la abertura en metros (default 2.10 puertas, 1.10 ventanas)",
    )
    sill_height: float = Field(
        ge=0,
        default=None,  # type: ignore[assignment]
        description="Altura del antepecho en metros (default 0.0 puertas, 0.90 ventanas)",
    )
    mechanism: OpeningMechanism | None = Field(
        default=None,
        description="Mecanismo de apertura (default hinged para puertas, sliding para ventanas)",
    )
    block_name: str | None = Field(
        default=None,
        description="Nombre del bloque DXF, ej: 'P1', 'V1'. Se auto-genera si no se provee.",
    )

    @model_validator(mode="after")
    def _set_defaults_by_type(self) -> "Opening":
        """Asigna valores por defecto según el tipo de abertura."""
        if self.type == OpeningType.door:
            if self.height is None:
                self.height = 2.10
            if self.sill_height is None:
                self.sill_height = 0.0
            if self.mechanism is None:
                self.mechanism = OpeningMechanism.hinged
        else:  # window
            if self.height is None:
                self.height = 1.10
            if self.sill_height is None:
                self.sill_height = 0.90
            if self.mechanism is None:
                self.mechanism = OpeningMechanism.sliding
        return self
