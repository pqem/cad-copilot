"""Motor de normas para planos municipales argentinos.

Implementa verificaciones del código de edificación de Neuquén/Plottier.
Todas las funciones son puras: reciben datos del FloorPlan y Terrain,
y devuelven resultados sin efectos secundarios.

Referencia normativa (orientativa):
- Código de Edificación de la Ciudad de Neuquén (Ord. 7811 y modificatorias)
- Código de Edificación de Plottier (Ord. 456/2001 y modificatorias)
- IRAM 11603 — Clasificación bioambiental de la República Argentina
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cad_copilot.engine.spaces import calculate_space_area
from cad_copilot.schemas.opening import OpeningMechanism, OpeningType
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.terrain import Terrain
from cad_copilot.schemas.wall import Wall


# ---------------------------------------------------------------------------
# Constantes normativas por defecto (Neuquén/Plottier residencial)
# Todas son sobreescribibles — NO hardcodear en lógica final.
# ---------------------------------------------------------------------------

class TipoLocal(StrEnum):
    """Clasificación del local a efectos de normas de iluminación/ventilación."""

    habitable = "habitable"       # dormitorios, living, comedor, estar, escritorio
    servicio = "servicio"         # cocina, baño, lavadero
    no_computable = "no_computable"  # garage, pasillo, depósito, hall, otro


# Mínimo de iluminación: superficie vidrio / superficie piso
ILUMINACION_MIN: dict[TipoLocal, float] = {
    TipoLocal.habitable: 1 / 6,    # ~0.167
    TipoLocal.servicio: 1 / 8,     # 0.125
    TipoLocal.no_computable: 0.0,  # sin requisito
}

# Mínimo de ventilación: superficie practicable / superficie piso
# = 1/2 del mínimo de iluminación
VENTILACION_MIN: dict[TipoLocal, float] = {
    TipoLocal.habitable: 1 / 12,   # ~0.083
    TipoLocal.servicio: 1 / 16,    # 0.0625
    TipoLocal.no_computable: 0.0,  # sin requisito
}

# Superficie mínima por función (m²)
AREA_MIN: dict[SpaceFunction, float] = {
    SpaceFunction.dormitorio: 9.0,    # secundario; principal requiere 12 m²
    SpaceFunction.living: 15.0,
    SpaceFunction.comedor: 10.0,
    SpaceFunction.cocina: 5.0,
    SpaceFunction.bano: 3.0,
    SpaceFunction.lavadero: 2.5,
    SpaceFunction.estar: 12.0,
    SpaceFunction.escritorio: 9.0,
    SpaceFunction.garage: 12.5,     # 1 auto: 2.5 x 5 m
    SpaceFunction.hall: 0.0,        # sin mínimo
    SpaceFunction.pasillo: 0.0,     # sin mínimo
    SpaceFunction.deposito: 0.0,    # sin mínimo
    SpaceFunction.otro: 0.0,        # sin mínimo
}

# Altura mínima libre (metros)
ALTURA_MIN: dict[TipoLocal, float] = {
    TipoLocal.habitable: 2.60,
    TipoLocal.servicio: 2.40,
    TipoLocal.no_computable: 2.20,
}

# Clasificación de funciones de espacio por tipo de local
TIPO_POR_FUNCION: dict[SpaceFunction, TipoLocal] = {
    SpaceFunction.dormitorio: TipoLocal.habitable,
    SpaceFunction.living: TipoLocal.habitable,
    SpaceFunction.comedor: TipoLocal.habitable,
    SpaceFunction.estar: TipoLocal.habitable,
    SpaceFunction.escritorio: TipoLocal.habitable,
    SpaceFunction.cocina: TipoLocal.servicio,
    SpaceFunction.bano: TipoLocal.servicio,
    SpaceFunction.lavadero: TipoLocal.servicio,
    SpaceFunction.garage: TipoLocal.no_computable,
    SpaceFunction.hall: TipoLocal.no_computable,
    SpaceFunction.pasillo: TipoLocal.no_computable,
    SpaceFunction.deposito: TipoLocal.no_computable,
    SpaceFunction.otro: TipoLocal.no_computable,
}


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass
class ItemVerificacion:
    """Resultado de verificación de un ítem normativo."""

    descripcion: str
    valor_calculado: float
    valor_minimo: float
    unidad: str
    cumple: bool
    observacion: str = ""

    @property
    def estado(self) -> str:
        return "CUMPLE" if self.cumple else "NO CUMPLE"


@dataclass
class ResultadoAmbiente:
    """Resultado de verificación normativa de un ambiente."""

    space_id: str
    space_name: str
    function: str
    tipo_local: str
    area_m2: float
    items: list[ItemVerificacion] = field(default_factory=list)

    @property
    def cumple_todo(self) -> bool:
        return all(item.cumple for item in self.items)


@dataclass
class ResultadoTerreno:
    """Resultado de verificación FOS/FOT del terreno."""

    superficie_terreno: float
    superficie_cubierta: float
    superficie_total: float
    fos_calculado: float
    fot_calculado: float
    fos_max: float
    fot_max: float
    items: list[ItemVerificacion] = field(default_factory=list)

    @property
    def cumple_todo(self) -> bool:
        return all(item.cumple for item in self.items)


@dataclass
class ResultadoNormas:
    """Resultado completo de verificación normativa del proyecto."""

    proyecto: str
    ambientes: list[ResultadoAmbiente] = field(default_factory=list)
    terreno: ResultadoTerreno | None = None
    observaciones_generales: list[str] = field(default_factory=list)

    @property
    def cumple_todo(self) -> bool:
        ambs = all(a.cumple_todo for a in self.ambientes)
        terr = self.terreno.cumple_todo if self.terreno else True
        return ambs and terr

    @property
    def resumen(self) -> str:
        estado = "CUMPLE" if self.cumple_todo else "NO CUMPLE"
        return f"{estado} — {self.proyecto}"


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _get_tipo_local(function: SpaceFunction) -> TipoLocal:
    """Clasifica un espacio según tipo de local (habitable/servicio/no_computable)."""
    return TIPO_POR_FUNCION.get(function, TipoLocal.no_computable)


def _calcular_superficie_vidrio(space: Space, walls: list[Wall]) -> float:
    """Calcula la superficie de vidrio (iluminación) de un ambiente.

    Suma el área de todas las ventanas en los muros que delimitan el espacio.
    El área de vidrio = ancho × alto de la abertura.

    Args:
        space: El ambiente.
        walls: Lista de muros del proyecto.

    Returns:
        Superficie de vidrio en m².
    """
    wall_map = {w.id: w for w in walls}
    superficie = 0.0

    for wall_id in space.bounded_by:
        wall = wall_map.get(wall_id)
        if wall is None:
            continue
        for opening in wall.openings:
            if opening.type == OpeningType.window:
                superficie += opening.width * opening.height

    return superficie


def _calcular_superficie_ventilacion(space: Space, walls: list[Wall]) -> float:
    """Calcula la superficie practicable de ventilación de un ambiente.

    La superficie efectiva depende del mecanismo:
    - corrediza (sliding): 50% del vano (solo un paño abre)
    - batiente (hinged): 100% del vano
    - paño fijo (fixed): 0% (no ventila)
    - doble batiente (double_hinged): 100% del vano

    Args:
        space: El ambiente.
        walls: Lista de muros del proyecto.

    Returns:
        Superficie practicable de ventilación en m².
    """
    FACTOR_VENTILACION: dict[OpeningMechanism, float] = {
        OpeningMechanism.sliding: 0.50,
        OpeningMechanism.hinged: 1.00,
        OpeningMechanism.fixed: 0.00,
        OpeningMechanism.double_hinged: 1.00,
    }

    wall_map = {w.id: w for w in walls}
    superficie = 0.0

    for wall_id in space.bounded_by:
        wall = wall_map.get(wall_id)
        if wall is None:
            continue
        for opening in wall.openings:
            if opening.type == OpeningType.window:
                factor = FACTOR_VENTILACION.get(opening.mechanism or OpeningMechanism.sliding, 0.5)
                superficie += opening.width * opening.height * factor

    return superficie


# ---------------------------------------------------------------------------
# Verificaciones por ambiente
# ---------------------------------------------------------------------------

def verificar_iluminacion(
    space: Space,
    walls: list[Wall],
    area_m2: float,
    iluminacion_min: dict[TipoLocal, float] | None = None,
) -> ItemVerificacion:
    """Verifica el requisito de iluminación natural de un ambiente.

    Args:
        space: El ambiente a verificar.
        walls: Lista de muros del proyecto.
        area_m2: Área del ambiente en m² (pre-calculada).
        iluminacion_min: Override de mínimos (usa defaults si None).

    Returns:
        ItemVerificacion con resultado CUMPLE/NO CUMPLE.
    """
    mins = iluminacion_min or ILUMINACION_MIN
    tipo = _get_tipo_local(space.function)

    if tipo == TipoLocal.no_computable:
        return ItemVerificacion(
            descripcion="Iluminación natural",
            valor_calculado=0.0,
            valor_minimo=0.0,
            unidad="ratio (vidrio/piso)",
            cumple=True,
            observacion="Local no computable — sin requisito de iluminación",
        )

    if area_m2 <= 0:
        return ItemVerificacion(
            descripcion="Iluminación natural",
            valor_calculado=0.0,
            valor_minimo=mins[tipo],
            unidad="ratio (vidrio/piso)",
            cumple=False,
            observacion="No se pudo calcular el área del local",
        )

    sup_vidrio = _calcular_superficie_vidrio(space, walls)
    ratio = sup_vidrio / area_m2
    minimo = mins[tipo]
    minimo_str = f"1/{round(1/minimo)}" if minimo > 0 else "0"

    return ItemVerificacion(
        descripcion="Iluminación natural",
        valor_calculado=ratio,
        valor_minimo=minimo,
        unidad=f"ratio vidrio/piso (mín {minimo_str})",
        cumple=ratio >= minimo,
        observacion=f"Sup. vidrio: {sup_vidrio:.2f} m² | Sup. piso: {area_m2:.2f} m²",
    )


def verificar_ventilacion(
    space: Space,
    walls: list[Wall],
    area_m2: float,
    ventilacion_min: dict[TipoLocal, float] | None = None,
) -> ItemVerificacion:
    """Verifica el requisito de ventilación natural de un ambiente.

    Args:
        space: El ambiente a verificar.
        walls: Lista de muros del proyecto.
        area_m2: Área del ambiente en m² (pre-calculada).
        ventilacion_min: Override de mínimos (usa defaults si None).

    Returns:
        ItemVerificacion con resultado CUMPLE/NO CUMPLE.
    """
    mins = ventilacion_min or VENTILACION_MIN
    tipo = _get_tipo_local(space.function)

    if tipo == TipoLocal.no_computable:
        return ItemVerificacion(
            descripcion="Ventilación natural",
            valor_calculado=0.0,
            valor_minimo=0.0,
            unidad="ratio (practicable/piso)",
            cumple=True,
            observacion="Local no computable — sin requisito de ventilación",
        )

    if area_m2 <= 0:
        return ItemVerificacion(
            descripcion="Ventilación natural",
            valor_calculado=0.0,
            valor_minimo=mins[tipo],
            unidad="ratio (practicable/piso)",
            cumple=False,
            observacion="No se pudo calcular el área del local",
        )

    sup_practicable = _calcular_superficie_ventilacion(space, walls)
    ratio = sup_practicable / area_m2
    minimo = mins[tipo]
    minimo_str = f"1/{round(1/minimo)}" if minimo > 0 else "0"

    return ItemVerificacion(
        descripcion="Ventilación natural",
        valor_calculado=ratio,
        valor_minimo=minimo,
        unidad=f"ratio practicable/piso (mín {minimo_str})",
        cumple=ratio >= minimo,
        observacion=f"Sup. practicable: {sup_practicable:.2f} m² | Sup. piso: {area_m2:.2f} m²",
    )


def verificar_area_minima(
    space: Space,
    area_m2: float,
    area_min: dict[SpaceFunction, float] | None = None,
) -> ItemVerificacion:
    """Verifica la superficie mínima requerida para el local.

    Args:
        space: El ambiente a verificar.
        area_m2: Área calculada en m².
        area_min: Override de mínimos (usa defaults si None).

    Returns:
        ItemVerificacion con resultado CUMPLE/NO CUMPLE.
    """
    mins = area_min or AREA_MIN
    minimo = mins.get(space.function, 0.0)

    if minimo <= 0:
        return ItemVerificacion(
            descripcion="Superficie mínima",
            valor_calculado=area_m2,
            valor_minimo=0.0,
            unidad="m²",
            cumple=True,
            observacion="Sin requisito de superficie mínima para este local",
        )

    obs = ""
    if space.function == SpaceFunction.dormitorio:
        obs = "Mín. dormitorio secundario. Principal: 12.00 m²"

    return ItemVerificacion(
        descripcion="Superficie mínima",
        valor_calculado=area_m2,
        valor_minimo=minimo,
        unidad="m²",
        cumple=area_m2 >= minimo,
        observacion=obs,
    )


# ---------------------------------------------------------------------------
# Verificaciones del terreno
# ---------------------------------------------------------------------------

def verificar_fos_fot(
    floor_plan: FloorPlan,
    terrain: Terrain,
) -> ResultadoTerreno:
    """Verifica FOS y FOT del proyecto contra los máximos del terreno.

    Calcula la superficie cubierta como la suma de áreas de todos los ambientes.
    En proyectos de planta múltiple, la superficie total es la suma de todas las plantas.

    Args:
        floor_plan: Plano del proyecto.
        terrain: Datos del terreno.

    Returns:
        ResultadoTerreno con verificación FOS/FOT.
    """
    # Superficie cubierta = suma de áreas de todos los ambientes
    superficie_cubierta = sum(
        calculate_space_area(s, floor_plan.walls) for s in floor_plan.spaces
    )
    # Para planta simple: total = cubierta
    # En proyectos multi-planta el usuario debe sumar manualmente
    superficie_total = superficie_cubierta

    fos = superficie_cubierta / terrain.superficie if terrain.superficie > 0 else 0.0
    fot = superficie_total / terrain.superficie if terrain.superficie > 0 else 0.0

    items = [
        ItemVerificacion(
            descripcion="FOS — Factor de Ocupación del Suelo",
            valor_calculado=fos,
            valor_minimo=terrain.fos_max,  # aquí es máximo permitido
            unidad=f"ratio (máx {terrain.fos_max:.2f})",
            cumple=fos <= terrain.fos_max,
            observacion=f"Sup. cubierta: {superficie_cubierta:.2f} m² / Terreno: {terrain.superficie:.2f} m²",
        ),
        ItemVerificacion(
            descripcion="FOT — Factor de Ocupación Total",
            valor_calculado=fot,
            valor_minimo=terrain.fot_max,  # aquí es máximo permitido
            unidad=f"ratio (máx {terrain.fot_max:.2f})",
            cumple=fot <= terrain.fot_max,
            observacion=f"Sup. total: {superficie_total:.2f} m² / Terreno: {terrain.superficie:.2f} m²",
        ),
    ]

    return ResultadoTerreno(
        superficie_terreno=terrain.superficie,
        superficie_cubierta=superficie_cubierta,
        superficie_total=superficie_total,
        fos_calculado=fos,
        fot_calculado=fot,
        fos_max=terrain.fos_max,
        fot_max=terrain.fot_max,
        items=items,
    )


# ---------------------------------------------------------------------------
# Función principal: calcular todas las normas
# ---------------------------------------------------------------------------

def calcular_normas(
    floor_plan: FloorPlan,
    terrain: Terrain | None = None,
    iluminacion_min: dict[TipoLocal, float] | None = None,
    ventilacion_min: dict[TipoLocal, float] | None = None,
    area_min: dict[SpaceFunction, float] | None = None,
) -> ResultadoNormas:
    """Calcula todas las verificaciones normativas del proyecto.

    Función principal que orquesta todos los cálculos normativos.
    Permite override de todos los mínimos para diferentes municipios.

    Args:
        floor_plan: Plano del proyecto (FloorPlan validado).
        terrain: Datos del terreno (None = omite verificación FOS/FOT).
        iluminacion_min: Override de mínimos de iluminación por tipo de local.
        ventilacion_min: Override de mínimos de ventilación por tipo de local.
        area_min: Override de superficies mínimas por función.

    Returns:
        ResultadoNormas con verificaciones completas CUMPLE/NO CUMPLE.
    """
    proyecto = ""
    if floor_plan.title_block:
        proyecto = floor_plan.title_block.project

    resultado = ResultadoNormas(proyecto=proyecto)

    # Verificar cada ambiente
    for space in floor_plan.spaces:
        tipo = _get_tipo_local(space.function)
        area = calculate_space_area(space, floor_plan.walls)

        items: list[ItemVerificacion] = []

        # Iluminación natural
        items.append(verificar_iluminacion(space, floor_plan.walls, area, iluminacion_min))

        # Ventilación natural
        items.append(verificar_ventilacion(space, floor_plan.walls, area, ventilacion_min))

        # Superficie mínima
        items.append(verificar_area_minima(space, area, area_min))

        resultado.ambientes.append(
            ResultadoAmbiente(
                space_id=space.id,
                space_name=space.name,
                function=space.function.value,
                tipo_local=tipo.value,
                area_m2=area,
                items=items,
            )
        )

    # Verificar FOS/FOT si se provee terreno
    if terrain is not None:
        resultado.terreno = verificar_fos_fot(floor_plan, terrain)

    # Observaciones generales
    if not floor_plan.spaces:
        resultado.observaciones_generales.append(
            "No se definieron ambientes en el plano. Los cálculos de iluminación y ventilación requieren ambientes."
        )

    if terrain is None:
        resultado.observaciones_generales.append(
            "No se proveyeron datos de terreno. Los cálculos FOS/FOT no están disponibles."
        )

    return resultado


# ---------------------------------------------------------------------------
# Formateo de resultados como texto tabular
# ---------------------------------------------------------------------------

def formatear_resultado_texto(resultado: ResultadoNormas) -> str:
    """Formatea el resultado normativo como tabla de texto legible.

    Genera una tabla ASCII con todos los ítems verificados, apta para
    incluir en el plano como referencia o para revisión municipal.

    Args:
        resultado: Resultado de calcular_normas().

    Returns:
        Tabla de texto formateada.
    """
    lines: list[str] = []
    SEP = "─" * 80

    lines.append("VERIFICACIÓN NORMATIVA — CÓDIGO EDIFICACIÓN NEUQUÉN/PLOTTIER")
    lines.append(f"Proyecto: {resultado.proyecto or '(sin nombre)'}")
    lines.append(f"Estado general: {'✓ CUMPLE' if resultado.cumple_todo else '✗ NO CUMPLE'}")
    lines.append(SEP)

    # Ambientes
    if resultado.ambientes:
        lines.append("\nVERIFICACIÓN POR AMBIENTE")
        lines.append(SEP)

        for amb in resultado.ambientes:
            estado = "✓" if amb.cumple_todo else "✗"
            lines.append(
                f"\n{estado} {amb.space_name.upper()} "
                f"({amb.function} — {amb.tipo_local}) "
                f"| Área: {amb.area_m2:.2f} m²"
            )

            for item in amb.items:
                estado_item = "✓" if item.cumple else "✗"
                lines.append(
                    f"   {estado_item} {item.descripcion}: "
                    f"{item.valor_calculado:.3f} {item.unidad}"
                )
                if item.observacion:
                    lines.append(f"      → {item.observacion}")

    # Terreno
    if resultado.terreno:
        lines.append(f"\n{SEP}")
        lines.append("\nVERIFICACIÓN DE TERRENO (FOS/FOT)")
        lines.append(SEP)

        t = resultado.terreno
        lines.append(f"  Superficie del terreno: {t.superficie_terreno:.2f} m²")
        lines.append(f"  Superficie cubierta:    {t.superficie_cubierta:.2f} m²")
        lines.append(f"  Superficie total:       {t.superficie_total:.2f} m²")

        for item in t.items:
            estado_item = "✓" if item.cumple else "✗"
            lines.append(
                f"\n  {estado_item} {item.descripcion}: "
                f"{item.valor_calculado:.3f} (máx {item.valor_minimo:.3f})"
            )
            if item.observacion:
                lines.append(f"     → {item.observacion}")

    # Observaciones generales
    if resultado.observaciones_generales:
        lines.append(f"\n{SEP}")
        lines.append("\nOBSERVACIONES:")
        for obs in resultado.observaciones_generales:
            lines.append(f"  • {obs}")

    lines.append(f"\n{SEP}")
    lines.append(
        "NOTA: Verificación orientativa basada en Cód. Edificación Neuquén/Plottier."
    )
    lines.append("Confirmar con municipio antes de presentar legajo.")

    return "\n".join(lines)
