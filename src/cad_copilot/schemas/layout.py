"""Schema de configuración de lámina y carátula."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PaperSize(StrEnum):
    """Tamaño de papel normalizado IRAM/ISO."""

    A4 = "A4"
    A3 = "A3"
    A2 = "A2"
    A1 = "A1"
    A0 = "A0"


class Orientation(StrEnum):
    """Orientación de la lámina."""

    portrait = "portrait"
    landscape = "landscape"


class PaperConfig(BaseModel):
    """Configuración de la lámina (papel, escala, márgenes)."""

    size: PaperSize = Field(
        default=PaperSize.A2,
        description="Tamaño de papel normalizado",
    )
    orientation: Orientation = Field(
        default=Orientation.landscape,
        description="Orientación de la lámina: apaisado o vertical",
    )
    scale: int = Field(
        default=50,
        gt=0,
        description="Denominador de la escala 1:N",
    )
    margins: tuple[float, float, float, float] = Field(
        default=(25.0, 5.0, 5.0, 5.0),
        description="Márgenes en mm: (izquierda, arriba, derecha, abajo)",
    )


class TitleBlock(BaseModel):
    """Carátula/rótulo de la lámina."""

    project: str = Field(
        description="Nombre del proyecto",
    )
    location: str = Field(
        description="Ubicación del proyecto (dirección o localidad)",
    )
    owner: str = Field(
        default="",
        description="Nombre del comitente/propietario",
    )
    professional: str = Field(
        description="Nombre del profesional actuante",
    )
    license_number: str = Field(
        description="Número de matrícula profesional",
    )
    date: str = Field(
        description="Fecha del plano, ej: '2026-03-10'",
    )
    sheet: str = Field(
        default="1/1",
        description="Número de lámina, ej: '1/3'",
    )
    drawing_name: str = Field(
        description="Nombre del dibujo, ej: 'PLANTA BAJA'",
    )
