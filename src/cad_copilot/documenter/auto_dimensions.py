"""Agrega cotas faltantes a muros detectados en un DXF existente.

Reutiliza el motor de annotations.py existente, aplicando cotas solo
a muros que no tienen cota asociada. Usa dimstyle IRAM_ARQ y layer
A-ANNO-DIMS (convención profesional AIA).

Cuando se trabaja sobre un DXF existente, se intenta detectar el dimstyle
del plano para que las cotas nuevas tengan el mismo tamaño.
"""

from __future__ import annotations

import math

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import DetectedDimension, DetectedWall
from cad_copilot.standards.layers import setup_layers


def _wall_has_dimension(
    wall: DetectedWall,
    dimensions: list[DetectedDimension],
    tolerance: float = 0.5,
) -> bool:
    """Verifica si un muro ya tiene una cota cercana."""
    wall_mx = (wall.start[0] + wall.end[0]) / 2
    wall_my = (wall.start[1] + wall.end[1]) / 2

    for dim in dimensions:
        dim_mx = (dim.start[0] + dim.end[0]) / 2
        dim_my = (dim.start[1] + dim.end[1]) / 2
        dist = math.sqrt((wall_mx - dim_mx) ** 2 + (wall_my - dim_my) ** 2)

        if dist < wall.length + tolerance:
            return True

    return False


def _setup_matching_dimstyle(doc: Drawing) -> str:
    """Crea un dimstyle IRAM_ARQ que se adapta al DXF existente.

    Si el DXF ya tiene cotas, copia las proporciones de tamaño del dimstyle
    existente más usado. Si no, usa valores por defecto para metros (DIMSCALE=1).
    """
    name = "IRAM_ARQ"
    if name in doc.dimstyles:
        return name

    # Detectar dimstyle más usado en cotas existentes
    msp = doc.modelspace()
    existing_styles: dict[str, int] = {}
    for entity in msp:
        if entity.dxftype() == "DIMENSION":
            ds = getattr(entity.dxf, "dimstyle", "Standard")
            existing_styles[ds] = existing_styles.get(ds, 0) + 1

    # Copiar proporciones del dimstyle más usado
    ref_dimtxt = 0.3  # default para metros
    ref_dimasz = 0.15
    ref_dimscale = 1.0

    if existing_styles:
        most_used = max(existing_styles, key=existing_styles.get)
        try:
            ref_ds = doc.dimstyles.get(most_used)
            ref_dimtxt = getattr(ref_ds.dxf, "dimtxt", ref_dimtxt)
            ref_dimasz = getattr(ref_ds.dxf, "dimasz", ref_dimasz)
            ref_dimscale = getattr(ref_ds.dxf, "dimscale", ref_dimscale)
        except Exception:
            pass

    ds = doc.dimstyles.new(name)
    ds.dxf.dimtxt = ref_dimtxt
    ds.dxf.dimasz = ref_dimasz
    ds.dxf.dimscale = ref_dimscale
    ds.dxf.dimexe = ref_dimtxt * 0.5
    ds.dxf.dimexo = ref_dimtxt * 0.25
    ds.dxf.dimgap = ref_dimtxt * 0.25
    ds.dxf.dimdec = 2
    ds.dxf.dimtad = 1  # texto arriba
    ds.dxf.dimtih = 0
    ds.dxf.dimtoh = 0
    ds.dxf.dimclrd = 3  # verde
    ds.dxf.dimclre = 3
    ds.dxf.dimclrt = 3
    ds.dxf.dimlunit = 2  # decimal

    return name


def add_missing_dimensions(
    doc: Drawing,
    walls: list[DetectedWall],
    existing_dimensions: list[DetectedDimension],
    *,
    offset: float = 0.8,
    dimstyle: str = "IRAM_ARQ",
    scale: int = 50,
    min_wall_length: float = 0.5,
) -> int:
    """Agrega cotas a muros detectados que no tienen cota existente.

    Args:
        doc: Documento ezdxf a modificar.
        walls: Muros detectados del DXF.
        existing_dimensions: Cotas ya presentes en el DXF.
        offset: Distancia de la cota al muro (metros).
        dimstyle: Nombre del dimstyle a usar.
        scale: Escala del plano (para DIMSCALE).
        min_wall_length: Longitud mínima de muro para acotar.

    Returns:
        Cantidad de cotas agregadas.
    """
    setup_layers(doc)
    actual_dimstyle = _setup_matching_dimstyle(doc)

    msp = doc.modelspace()
    count = 0

    for wall in walls:
        if wall.length < min_wall_length:
            continue

        if _wall_has_dimension(wall, existing_dimensions):
            continue

        dim = msp.add_aligned_dim(
            p1=wall.start,
            p2=wall.end,
            distance=offset,
            dimstyle=actual_dimstyle,
            override={"layer": "A-ANNO-DIMS"},
        )
        dim.render()
        count += 1

    return count
