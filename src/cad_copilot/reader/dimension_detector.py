"""Detector de cotas existentes en archivos DXF.

Lee entidades DIMENSION del Model Space y extrae sus valores, puntos
y dimstyle asociado.
"""

from __future__ import annotations

import math

from ezdxf.document import Drawing

from cad_copilot.schemas.detection import DetectedDimension


def _calculate_dimension_value(entity) -> float:
    """Calcula el valor de una cota a partir de sus puntos de definición."""
    try:
        # Primero intentar obtener el valor medido almacenado
        if hasattr(entity.dxf, "actual_measurement"):
            val = entity.dxf.actual_measurement
            if val > 0:
                return round(val, 4)

        # Si no, calcular desde los puntos de definición
        defpoint = entity.dxf.defpoint
        if hasattr(entity.dxf, "defpoint2"):
            defpoint2 = entity.dxf.defpoint2
        elif hasattr(entity.dxf, "defpoint3"):
            defpoint2 = entity.dxf.defpoint3
        else:
            return 0.0

        dx = defpoint2.x - defpoint.x
        dy = defpoint2.y - defpoint.y
        return round(math.sqrt(dx * dx + dy * dy), 4)

    except (AttributeError, TypeError):
        return 0.0


def _get_dimension_endpoints(entity) -> tuple[tuple[float, float], tuple[float, float]]:
    """Extrae los endpoints de definición de una cota."""
    try:
        defpoint = entity.dxf.defpoint
        start = (defpoint.x, defpoint.y)

        for attr in ("defpoint2", "defpoint3"):
            if hasattr(entity.dxf, attr):
                pt = getattr(entity.dxf, attr)
                return start, (pt.x, pt.y)

        return start, start

    except (AttributeError, TypeError):
        return (0.0, 0.0), (0.0, 0.0)


def detect_dimensions(doc: Drawing) -> list[DetectedDimension]:
    """Detecta cotas existentes en un DXF.

    Args:
        doc: Documento ezdxf ya leído.

    Returns:
        Lista de DetectedDimension con valor, puntos, layer y dimstyle.
    """
    msp = doc.modelspace()
    dimensions: list[DetectedDimension] = []

    for entity in msp:
        if entity.dxftype() != "DIMENSION":
            continue

        value = _calculate_dimension_value(entity)
        start, end = _get_dimension_endpoints(entity)

        handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""
        dimstyle = getattr(entity.dxf, "dimstyle", "Standard")

        dimensions.append(
            DetectedDimension(
                id=f"dim_{len(dimensions)}",
                value=value,
                start=start,
                end=end,
                layer=entity.dxf.layer,
                dimstyle=dimstyle,
                entity_handle=handle,
            )
        )

    return dimensions
