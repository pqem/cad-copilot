"""Schema raíz del proyecto — FloorPlan es el modelo principal."""

from pydantic import BaseModel, Field

from cad_copilot.schemas.annotation import AnnotationConfig
from cad_copilot.schemas.layout import PaperConfig, TitleBlock
from cad_copilot.schemas.space import Space
from cad_copilot.schemas.wall import Wall


class FloorPlan(BaseModel):
    """Planta arquitectónica completa — modelo raíz del JSON de entrada."""

    walls: list[Wall] = Field(
        description="Lista de muros que componen la planta",
    )
    spaces: list[Space] = Field(
        default_factory=list,
        description="Lista de espacios/ambientes delimitados por muros",
    )
    annotations: AnnotationConfig = Field(
        default_factory=AnnotationConfig,
        description="Configuración de anotaciones y acotaciones",
    )
    title_block: TitleBlock | None = Field(
        default=None,
        description="Carátula de la lámina; None si no se incluye",
    )
    paper_config: PaperConfig = Field(
        default_factory=PaperConfig,
        description="Configuración de la lámina (papel, escala, márgenes)",
    )
