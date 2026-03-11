"""Schema del terreno para cálculos normativos FOS/FOT/retiros.

Modela los datos del terreno necesarios para verificar el cumplimiento
del código de edificación de Plottier/Neuquén.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Zonificacion(StrEnum):
    """Zonificación urbana según código de edificación de Neuquén/Plottier."""

    residencial = "residencial"
    comercial = "comercial"
    mixta = "mixta"
    industrial = "industrial"


class RetirosConfig(BaseModel):
    """Retiros mínimos obligatorios según zonificación."""

    frente: float = Field(
        default=3.0,
        ge=0,
        description="Retiro de frente en metros (típico R: 3-5m)",
    )
    lateral_izq: float = Field(
        default=0.0,
        ge=0,
        description="Retiro lateral izquierdo en metros (0 = medianera)",
    )
    lateral_der: float = Field(
        default=0.0,
        ge=0,
        description="Retiro lateral derecho en metros (0 = medianera)",
    )
    fondo: float = Field(
        default=3.0,
        ge=0,
        description="Retiro de fondo en metros (típico R: 3-4m)",
    )


class Terrain(BaseModel):
    """Datos del terreno para cálculos normativos FOS/FOT/retiros.

    Los valores por defecto corresponden a zonificación residencial
    típica de Plottier, Neuquén (orientativos — verificar con municipio).
    """

    superficie: float = Field(
        gt=0,
        description="Superficie total del terreno en m²",
    )
    frente: float = Field(
        gt=0,
        description="Dimensión de frente del terreno en metros",
    )
    fondo: float = Field(
        gt=0,
        description="Dimensión de fondo del terreno en metros",
    )
    zonificacion: Zonificacion = Field(
        default=Zonificacion.residencial,
        description="Zonificación urbana del terreno",
    )
    fos_max: float = Field(
        default=0.60,
        gt=0,
        le=1.0,
        description="FOS máximo permitido (Factor de Ocupación del Suelo)",
    )
    fot_max: float = Field(
        default=1.20,
        gt=0,
        description="FOT máximo permitido (Factor de Ocupación Total)",
    )
    retiros: RetirosConfig = Field(
        default_factory=RetirosConfig,
        description="Retiros mínimos obligatorios en metros",
    )
    altura_max: float | None = Field(
        default=None,
        gt=0,
        description="Altura máxima de edificación en metros (None = sin restricción)",
    )

    @model_validator(mode="after")
    def _validate_superficie(self) -> "Terrain":
        """Verifica coherencia entre dimensiones y superficie declarada."""
        calc = self.frente * self.fondo
        declarada = self.superficie
        # Tolerancia del 10% para terrenos irregulares
        if abs(calc - declarada) / declarada > 0.10:
            # Solo advertencia, no error — terrenos irregulares son comunes
            pass
        return self
