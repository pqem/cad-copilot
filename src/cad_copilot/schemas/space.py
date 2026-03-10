"""Schema de espacios (locales/ambientes)."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class SpaceFunction(StrEnum):
    """Función/uso del espacio según programa arquitectónico."""

    dormitorio = "dormitorio"
    living = "living"
    cocina = "cocina"
    comedor = "comedor"
    bano = "bano"
    lavadero = "lavadero"
    garage = "garage"
    pasillo = "pasillo"
    hall = "hall"
    estar = "estar"
    escritorio = "escritorio"
    deposito = "deposito"
    otro = "otro"


class Space(BaseModel):
    """Espacio/ambiente delimitado por muros."""

    id: str = Field(
        default="",
        description="Identificador único del espacio, ej: 'S1'. Se auto-genera si no se provee.",
    )
    name: str = Field(
        description="Nombre descriptivo del espacio, ej: 'LIVING-COMEDOR'",
    )
    function: SpaceFunction = Field(
        description="Función o uso del espacio",
    )
    bounded_by: list[str] = Field(
        description="IDs de los muros que delimitan este espacio",
    )
    level: float = Field(
        default=0.0,
        description="Nivel del piso terminado en metros, referido a vereda",
    )

    @model_validator(mode="after")
    def _auto_id(self) -> "Space":
        """Genera un ID desde el nombre si no se provee."""
        if not self.id:
            self.id = self.name.lower().replace(" ", "_").replace("-", "_")
        return self
