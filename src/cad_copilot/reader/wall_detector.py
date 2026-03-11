"""Detector de muros en archivos DXF existentes.

Estrategias de detección:
1. LWPOLYLINE rectangulares (4 vértices, cerrados) → muros como polígonos
2. Pares de LINE paralelas cercanas → muros como dos líneas
3. Heurísticas por layer: layers con lineweight grueso suelen contener muros

Los espesores se miden del DXF, NO se asumen valores fijos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

from cad_copilot.schemas.detection import DetectedWall


# --- Constantes de detección ---

# Espesor mínimo/máximo razonable para un muro (metros)
MIN_WALL_THICKNESS = 0.05
MAX_WALL_THICKNESS = 0.60

# Longitud mínima de un segmento para considerarse muro (metros)
MIN_WALL_LENGTH = 0.30

# Tolerancia para considerar dos líneas como paralelas (radianes)
PARALLEL_ANGLE_TOLERANCE = 0.05  # ~3 grados

# Tolerancia para considerar que un LWPOLYLINE es rectangular
RECTANGLE_ANGLE_TOLERANCE = 0.1  # ~6 grados

# Layers que generalmente NO contienen muros
EXCLUDE_LAYER_PATTERNS = {
    "defpoints", "cotas", "texto", "caratula", "hatch",
    "cota", "hierro", "referencia", "det", "cloacas",
    "proyecci", "punta", "blocks",
}

# Layers numéricos (pen width) que son pluma fina → no son muros.
# En planos argentinos, los layers 0.01-0.10 son líneas de detalle/cotas.
# Los muros reales están en layers >= 0.15 (pluma gruesa).
THIN_PEN_LAYERS = {"0", "0.01", "0.05", "0.07", "0.1", "0.10", "005", "01"}


@dataclass
class _Line:
    """Línea interna para procesamiento."""

    x1: float
    y1: float
    x2: float
    y2: float
    layer: str
    handle: str
    angle: float = 0.0
    length: float = 0.0

    def __post_init__(self):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        self.angle = math.atan2(dy, dx) % math.pi  # 0 a pi
        self.length = math.sqrt(dx * dx + dy * dy)

    @property
    def midpoint(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


def _should_skip_layer(layer_name: str) -> bool:
    """Determina si un layer probablemente NO contiene muros."""
    if layer_name in THIN_PEN_LAYERS:
        return True
    name_lower = layer_name.lower()
    return any(pattern in name_lower for pattern in EXCLUDE_LAYER_PATTERNS)


def _distance_point_to_line(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    """Distancia perpendicular de un punto a una línea definida por dos puntos."""
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


def _lines_overlap_projection(line_a: _Line, line_b: _Line) -> float:
    """Calcula cuánto se solapan dos líneas paralelas en su eje principal.

    Devuelve la longitud del solapamiento (0 si no hay).
    """
    angle = line_a.angle
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # Proyectar los 4 puntos sobre el eje de la línea A
    proj_a1 = line_a.x1 * cos_a + line_a.y1 * sin_a
    proj_a2 = line_a.x2 * cos_a + line_a.y2 * sin_a
    proj_b1 = line_b.x1 * cos_a + line_b.y1 * sin_a
    proj_b2 = line_b.x2 * cos_a + line_b.y2 * sin_a

    min_a, max_a = min(proj_a1, proj_a2), max(proj_a1, proj_a2)
    min_b, max_b = min(proj_b1, proj_b2), max(proj_b1, proj_b2)

    overlap = min(max_a, max_b) - max(min_a, min_b)
    return max(0.0, overlap)


def _detect_walls_from_parallel_lines(
    lines: list[_Line],
) -> list[DetectedWall]:
    """Detecta muros como pares de líneas paralelas cercanas."""
    if len(lines) < 2:
        return []

    # Ordenar por ángulo para buscar paralelas eficientemente
    sorted_lines = sorted(lines, key=lambda l: (l.angle, l.midpoint[0], l.midpoint[1]))

    walls: list[DetectedWall] = []
    used: set[str] = set()

    for i, line_a in enumerate(sorted_lines):
        if line_a.handle in used or line_a.length < MIN_WALL_LENGTH:
            continue

        best_match: _Line | None = None
        best_dist = float("inf")

        for j in range(i + 1, len(sorted_lines)):
            line_b = sorted_lines[j]
            if line_b.handle in used or line_b.length < MIN_WALL_LENGTH:
                continue

            # Verificar paralelismo
            angle_diff = abs(line_a.angle - line_b.angle)
            if angle_diff > PARALLEL_ANGLE_TOLERANCE:
                # Si la diferencia de ángulo ya es grande, los siguientes
                # (ordenados por ángulo) serán peores
                if angle_diff > PARALLEL_ANGLE_TOLERANCE * 3:
                    break
                continue

            # Verificar que estén en el mismo layer
            if line_a.layer != line_b.layer:
                continue

            # Calcular distancia perpendicular
            dist = _distance_point_to_line(
                line_b.midpoint[0], line_b.midpoint[1],
                line_a.x1, line_a.y1, line_a.x2, line_a.y2,
            )

            if MIN_WALL_THICKNESS <= dist <= MAX_WALL_THICKNESS:
                # Verificar solapamiento mínimo (al menos 50% de la línea más corta)
                overlap = _lines_overlap_projection(line_a, line_b)
                min_len = min(line_a.length, line_b.length)
                if overlap >= min_len * 0.5:
                    if dist < best_dist:
                        best_dist = dist
                        best_match = line_b

        if best_match is not None:
            used.add(line_a.handle)
            used.add(best_match.handle)

            # Usar la línea más larga como referencia para el eje del muro,
            # desplazada al centro entre las dos líneas
            ref = line_a if line_a.length >= best_match.length else best_match
            other = best_match if ref is line_a else line_a

            # Desplazar la referencia hacia el centro (mitad del espesor)
            dx_perp = -(ref.y2 - ref.y1)
            dy_perp = ref.x2 - ref.x1
            perp_len = math.sqrt(dx_perp * dx_perp + dy_perp * dy_perp)
            if perp_len > 0:
                dx_perp /= perp_len
                dy_perp /= perp_len

            # Determinar dirección: el otro lado debe quedar hacia el otro
            to_other_x = other.midpoint[0] - ref.midpoint[0]
            to_other_y = other.midpoint[1] - ref.midpoint[1]
            sign = 1 if (to_other_x * dx_perp + to_other_y * dy_perp) > 0 else -1

            half_t = best_dist / 2
            cx1 = ref.x1 + sign * half_t * dx_perp
            cy1 = ref.y1 + sign * half_t * dy_perp
            cx2 = ref.x2 + sign * half_t * dx_perp
            cy2 = ref.y2 + sign * half_t * dy_perp

            wall_length = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)

            walls.append(
                DetectedWall(
                    id=f"wall_L_{len(walls)}",
                    start=(cx1, cy1),
                    end=(cx2, cy2),
                    thickness=round(best_dist, 4),
                    layer=line_a.layer,
                    entity_handles=[line_a.handle, best_match.handle],
                    length=round(wall_length, 4),
                )
            )

    return walls


def _detect_walls_from_polylines(msp: Modelspace) -> list[DetectedWall]:
    """Detecta muros como LWPOLYLINE rectangulares (4 vértices).

    Un rectángulo largo y estrecho es probablemente un muro.
    """
    walls: list[DetectedWall] = []

    for entity in msp:
        if entity.dxftype() != "LWPOLYLINE":
            continue

        if _should_skip_layer(entity.dxf.layer):
            continue

        points = list(entity.get_points(format="xy"))
        if len(points) < 4:
            continue

        # Para polígonos cerrados con 4 puntos (rectángulos)
        is_closed = entity.is_closed or (
            len(points) >= 4
            and math.sqrt(
                (points[0][0] - points[-1][0]) ** 2
                + (points[0][1] - points[-1][1]) ** 2
            )
            < 0.01
        )

        if not is_closed:
            continue

        # Usar los puntos únicos (sin repetir el cierre)
        pts = points[:4] if len(points) >= 4 else points
        if len(points) > 4 and is_closed and len(points) <= 5:
            pts = points[:4]
        elif len(points) > 5:
            continue  # Polígonos complejos no son muros simples

        if len(pts) != 4:
            continue

        # Calcular las 4 longitudes de lados
        sides = []
        for k in range(4):
            p1 = pts[k]
            p2 = pts[(k + 1) % 4]
            sides.append(math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))

        # Un muro rectangular tiene 2 lados largos y 2 cortos
        sorted_sides = sorted(sides)
        short_sides = sorted_sides[:2]
        long_sides = sorted_sides[2:]

        avg_thickness = sum(short_sides) / 2
        avg_length = sum(long_sides) / 2

        # Verificar proporciones de muro
        if avg_thickness < MIN_WALL_THICKNESS or avg_thickness > MAX_WALL_THICKNESS:
            continue
        if avg_length < MIN_WALL_LENGTH:
            continue
        if avg_length / avg_thickness < 2.0:
            continue  # Demasiado cuadrado para ser muro

        # Verificar que los ángulos sean ~90 grados
        is_rectangular = True
        for k in range(4):
            p0 = pts[(k - 1) % 4]
            p1 = pts[k]
            p2 = pts[(k + 1) % 4]
            dx1, dy1 = p1[0] - p0[0], p1[1] - p0[1]
            dx2, dy2 = p2[0] - p1[0], p2[1] - p1[1]
            len1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
            len2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
            if len1 == 0 or len2 == 0:
                is_rectangular = False
                break
            dot = (dx1 * dx2 + dy1 * dy2) / (len1 * len2)
            if abs(dot) > RECTANGLE_ANGLE_TOLERANCE:
                is_rectangular = False
                break

        if not is_rectangular:
            continue

        # Calcular eje central del muro (centro de los lados largos)
        # Encontrar qué par de lados opuestos son los largos
        if sides[0] + sides[2] > sides[1] + sides[3]:
            # lados 0,2 son los largos → eje entre lados 1,3
            mid_start = (
                (pts[0][0] + pts[3][0]) / 2,
                (pts[0][1] + pts[3][1]) / 2,
            )
            mid_end = (
                (pts[1][0] + pts[2][0]) / 2,
                (pts[1][1] + pts[2][1]) / 2,
            )
        else:
            # lados 1,3 son los largos → eje entre lados 0,2
            mid_start = (
                (pts[0][0] + pts[1][0]) / 2,
                (pts[0][1] + pts[1][1]) / 2,
            )
            mid_end = (
                (pts[2][0] + pts[3][0]) / 2,
                (pts[2][1] + pts[3][1]) / 2,
            )

        handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""

        walls.append(
            DetectedWall(
                id=f"wall_P_{len(walls)}",
                start=mid_start,
                end=mid_end,
                thickness=round(avg_thickness, 4),
                layer=entity.dxf.layer,
                entity_handles=[handle],
                length=round(avg_length, 4),
            )
        )

    return walls


def detect_walls(
    doc: Drawing,
    *,
    layers: list[str] | None = None,
    include_polylines: bool = True,
    include_line_pairs: bool = True,
) -> list[DetectedWall]:
    """Detecta muros en un DXF existente.

    Args:
        doc: Documento ezdxf ya leido.
        layers: Lista de layers donde buscar. Si es None, busca en todos
                (excluyendo layers obviamente no-muros).
        include_polylines: Buscar LWPOLYLINE rectangulares.
        include_line_pairs: Buscar pares de LINE paralelas.

    Returns:
        Lista de DetectedWall con posición, espesor y handles de entidades.
    """
    msp = doc.modelspace()
    all_walls: list[DetectedWall] = []

    # 1. Detectar muros como LWPOLYLINE rectangulares
    if include_polylines:
        poly_walls = _detect_walls_from_polylines(msp)
        all_walls.extend(poly_walls)

    # 2. Detectar muros como pares de LINE paralelas
    if include_line_pairs:
        # Recopilar líneas del Model Space
        lines: list[_Line] = []
        for entity in msp:
            if entity.dxftype() != "LINE":
                continue

            layer = entity.dxf.layer
            if layers is not None and layer not in layers:
                continue
            if layers is None and _should_skip_layer(layer):
                continue

            s = entity.dxf.start
            e = entity.dxf.end
            handle = entity.dxf.handle if hasattr(entity.dxf, "handle") else ""
            line = _Line(s.x, s.y, e.x, e.y, layer, handle)

            if line.length >= MIN_WALL_LENGTH:
                lines.append(line)

        line_walls = _detect_walls_from_parallel_lines(lines)
        all_walls.extend(line_walls)

    # Re-numerar IDs
    for i, wall in enumerate(all_walls):
        wall.id = f"wall_{i}"

    return all_walls
