"""Analizador de completitud de documentación en DXF.

Analiza qué documentación falta en un plano y genera sugerencias
de mejora priorizadas.
"""

from __future__ import annotations

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import (
    DetectedDimension,
    DetectedOpening,
    DetectedSpace,
    DetectedWall,
    Suggestion,
    SuggestionKind,
    SuggestionReport,
)


def _has_title_block(doc: Drawing) -> bool:
    """Detecta si el DXF tiene una cartela/caratula."""
    msp = doc.modelspace()

    # Buscar por bloques con nombre de cartela
    for entity in msp:
        if entity.dxftype() == "INSERT":
            name = entity.dxf.name.lower()
            if any(
                kw in name
                for kw in ("cartela", "caratula", "titleblock", "title_block", "rotulo")
            ):
                return True

    # Buscar por textos típicos de cartela
    cartela_keywords = {"profesional", "propietario", "domicilio", "matricula"}
    found_keywords = set()
    for entity in msp:
        if entity.dxftype() in ("TEXT", "MTEXT"):
            text = (
                entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
            ).lower()
            for kw in cartela_keywords:
                if kw in text:
                    found_keywords.add(kw)

    # Si encontramos al menos 2 keywords de cartela
    return len(found_keywords) >= 2


def _has_north_arrow(doc: Drawing) -> bool:
    """Detecta si el DXF tiene flecha de norte."""
    msp = doc.modelspace()
    for entity in msp:
        if entity.dxftype() == "INSERT":
            name = entity.dxf.name.lower()
            if any(kw in name for kw in ("norte", "north", "sym_north")):
                return True
    return False


def _find_walls_without_dimensions(
    walls: list[DetectedWall],
    dimensions: list[DetectedDimension],
    tolerance: float = 0.5,
) -> list[DetectedWall]:
    """Encuentra muros que no tienen una cota cercana."""
    undimensioned: list[DetectedWall] = []

    for wall in walls:
        has_dim = False
        wall_mx = (wall.start[0] + wall.end[0]) / 2
        wall_my = (wall.start[1] + wall.end[1]) / 2

        for dim in dimensions:
            dim_mx = (dim.start[0] + dim.end[0]) / 2
            dim_my = (dim.start[1] + dim.end[1]) / 2
            dist = ((wall_mx - dim_mx) ** 2 + (wall_my - dim_my) ** 2) ** 0.5

            if dist < wall.length + tolerance:
                has_dim = True
                break

        if not has_dim:
            undimensioned.append(wall)

    return undimensioned


def _find_spaces_without_area(spaces: list[DetectedSpace]) -> list[DetectedSpace]:
    """Encuentra espacios detectados que no tienen etiqueta de área."""
    return [s for s in spaces if s.area == 0.0]


def analyze_completeness(
    doc: Drawing,
    walls: list[DetectedWall],
    openings: list[DetectedOpening],
    spaces: list[DetectedSpace],
    dimensions: list[DetectedDimension],
) -> SuggestionReport:
    """Analiza la completitud de documentación de un DXF.

    Args:
        doc: Documento ezdxf.
        walls: Muros detectados.
        openings: Aberturas detectadas.
        spaces: Espacios detectados.
        dimensions: Cotas detectadas.

    Returns:
        SuggestionReport con sugerencias priorizadas.
    """
    suggestions: list[Suggestion] = []

    # 1. Cartela
    has_tb = _has_title_block(doc)
    if not has_tb:
        suggestions.append(
            Suggestion(
                kind=SuggestionKind.missing_title_block,
                description="El plano no tiene cartela/caratula profesional",
                priority=1,
            )
        )

    # 2. Flecha norte
    has_north = _has_north_arrow(doc)
    if not has_north:
        suggestions.append(
            Suggestion(
                kind=SuggestionKind.missing_north_arrow,
                description="Falta la flecha de norte",
                priority=2,
            )
        )

    # 3. Muros sin cotar
    undimensioned = _find_walls_without_dimensions(walls, dimensions)
    walls_with_dims = len(walls) - len(undimensioned)
    for wall in undimensioned:
        suggestions.append(
            Suggestion(
                kind=SuggestionKind.missing_dimension,
                description=f"Muro {wall.id} sin cota (largo={wall.length:.2f}m)",
                element_id=wall.id,
                priority=2,
            )
        )

    # 4. Espacios sin área
    spaces_no_area = _find_spaces_without_area(spaces)
    spaces_with_area = len(spaces) - len(spaces_no_area)
    for space in spaces_no_area:
        suggestions.append(
            Suggestion(
                kind=SuggestionKind.missing_area_label,
                description=f"Espacio '{space.name}' sin etiqueta de superficie",
                element_id=space.id,
                priority=2,
            )
        )

    # 5. Tabla de normas (buscamos tabla o referencias normativas)
    has_norm = False
    for entity in doc.modelspace():
        if entity.dxftype() in ("TEXT", "MTEXT"):
            text = (
                entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
            ).lower()
            if "verificaci" in text and "norma" in text:
                has_norm = True
                break
            if "cumple" in text and ("iluminaci" in text or "ventilaci" in text):
                has_norm = True
                break
    if not has_norm:
        suggestions.append(
            Suggestion(
                kind=SuggestionKind.missing_norm_table,
                description="Falta tabla de verificación normativa",
                priority=3,
            )
        )

    return SuggestionReport(
        suggestions=suggestions,
        total_walls=len(walls),
        walls_with_dimensions=walls_with_dims,
        total_spaces=len(spaces),
        spaces_with_area_labels=spaces_with_area,
        has_title_block=has_tb,
        has_norm_table=has_norm,
        has_north_arrow=has_north,
    )
