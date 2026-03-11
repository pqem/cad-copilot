"""Schemas Pydantic v2 para detección de elementos en DXF existentes.

Estos modelos representan elementos detectados (no definidos por el usuario)
a partir de la lectura y análisis de un archivo DXF real.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from cad_copilot.schemas.base import Point2D


# --- Enums ---


class OpeningKind(StrEnum):
    """Tipo de abertura detectada."""

    door = "door"
    window = "window"
    unknown = "unknown"


class SpaceCategory(StrEnum):
    """Categoría funcional de un espacio detectado."""

    dormitorio = "dormitorio"
    living = "living"
    comedor = "comedor"
    cocina = "cocina"
    bano = "bano"
    lavadero = "lavadero"
    garage = "garage"
    pasillo = "pasillo"
    hall = "hall"
    estar = "estar"
    escritorio = "escritorio"
    deposito = "deposito"
    otro = "otro"


# --- Layer info ---


class LayerInfo(BaseModel):
    """Información de un layer del DXF."""

    name: str
    color: int = 7
    lineweight: int = -3
    entity_count: int = 0
    is_frozen: bool = False
    is_off: bool = False


# --- Block info ---


class BlockInfo(BaseModel):
    """Información de un bloque definido en el DXF."""

    name: str
    entity_count: int = 0
    insert_count: int = 0


# --- Entity stats ---


class EntityStats(BaseModel):
    """Conteo de entidades por tipo."""

    entity_type: str
    count: int


# --- DXF Analysis (Paso 1) ---


class DxfMetadata(BaseModel):
    """Metadata general del archivo DXF."""

    file_path: str
    dxf_version: str = ""
    encoding: str = "utf-8"
    insunits: int = 0
    file_size_bytes: int = 0


class BoundingBox(BaseModel):
    """Bounding box del dibujo en Model Space."""

    min_point: Point2D = (0.0, 0.0)
    max_point: Point2D = (0.0, 0.0)

    @property
    def width(self) -> float:
        return self.max_point[0] - self.min_point[0]

    @property
    def height(self) -> float:
        return self.max_point[1] - self.min_point[1]


class DxfAnalysis(BaseModel):
    """Resultado completo del análisis de un archivo DXF."""

    metadata: DxfMetadata
    layers: list[LayerInfo] = Field(default_factory=list)
    blocks: list[BlockInfo] = Field(default_factory=list)
    entity_stats: list[EntityStats] = Field(default_factory=list)
    dimstyles: list[str] = Field(default_factory=list)
    textstyles: list[str] = Field(default_factory=list)
    total_entities: int = 0
    bounding_box: BoundingBox = Field(default_factory=BoundingBox)

    @property
    def layer_names(self) -> list[str]:
        return [layer.name for layer in self.layers]


# --- Detected elements (Pasos 2-5) ---


class DetectedWall(BaseModel):
    """Muro detectado en el DXF."""

    id: str = ""
    start: Point2D
    end: Point2D
    thickness: float = 0.0
    layer: str = ""
    entity_handles: list[str] = Field(default_factory=list)
    length: float = 0.0


class DetectedOpening(BaseModel):
    """Abertura detectada en el DXF."""

    id: str = ""
    kind: OpeningKind = OpeningKind.unknown
    position: Point2D = (0.0, 0.0)
    width: float = 0.0
    block_name: str = ""
    layer: str = ""
    entity_handle: str = ""
    wall_id: str = ""


class DetectedSpace(BaseModel):
    """Espacio/ambiente detectado en el DXF."""

    id: str = ""
    name: str = ""
    category: SpaceCategory = SpaceCategory.otro
    area: float = 0.0
    centroid: Point2D = (0.0, 0.0)
    label_handle: str = ""
    layer: str = ""
    boundary_handles: list[str] = Field(default_factory=list)


class DetectedDimension(BaseModel):
    """Cota existente detectada en el DXF."""

    id: str = ""
    value: float = 0.0
    start: Point2D = (0.0, 0.0)
    end: Point2D = (0.0, 0.0)
    layer: str = ""
    dimstyle: str = ""
    entity_handle: str = ""
    associated_wall_id: str = ""


# --- Detection result ---


class DetectionResult(BaseModel):
    """Resultado completo de la detección de elementos."""

    analysis: DxfAnalysis
    walls: list[DetectedWall] = Field(default_factory=list)
    openings: list[DetectedOpening] = Field(default_factory=list)
    spaces: list[DetectedSpace] = Field(default_factory=list)
    dimensions: list[DetectedDimension] = Field(default_factory=list)


# --- Suggestions (Paso 6) ---


class SuggestionKind(StrEnum):
    """Tipo de sugerencia de documentación."""

    missing_dimension = "missing_dimension"
    missing_area_label = "missing_area_label"
    missing_title_block = "missing_title_block"
    missing_norm_table = "missing_norm_table"
    inconsistent_dimension = "inconsistent_dimension"
    missing_north_arrow = "missing_north_arrow"


class Suggestion(BaseModel):
    """Sugerencia de mejora de documentación."""

    kind: SuggestionKind
    description: str
    element_id: str = ""
    priority: int = Field(default=1, ge=1, le=3)


class SuggestionReport(BaseModel):
    """Reporte de sugerencias de documentación faltante."""

    suggestions: list[Suggestion] = Field(default_factory=list)
    total_walls: int = 0
    walls_with_dimensions: int = 0
    total_spaces: int = 0
    spaces_with_area_labels: int = 0
    has_title_block: bool = False
    has_norm_table: bool = False
    has_north_arrow: bool = False

    @property
    def completeness_score(self) -> float:
        """Score de 0 a 100 indicando qué tan documentado está el plano."""
        checks = [
            self.has_title_block,
            self.has_north_arrow,
            self.walls_with_dimensions >= self.total_walls if self.total_walls > 0 else True,
            self.spaces_with_area_labels >= self.total_spaces
            if self.total_spaces > 0
            else True,
        ]
        return round(sum(checks) / max(len(checks), 1) * 100, 1)
