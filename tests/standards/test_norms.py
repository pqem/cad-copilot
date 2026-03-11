"""Tests para el motor de normas — standards/norms.py.

Verifica los cálculos de iluminación, ventilación, superficie mínima,
FOS, FOT y la función principal calcular_normas().
"""

from __future__ import annotations

import pytest

from cad_copilot.schemas.opening import Opening, OpeningMechanism, OpeningType
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.terrain import RetirosConfig, Terrain, Zonificacion
from cad_copilot.schemas.wall import Wall
from cad_copilot.standards.norms import (
    AREA_MIN,
    ILUMINACION_MIN,
    VENTILACION_MIN,
    TipoLocal,
    _calcular_superficie_ventilacion,
    _calcular_superficie_vidrio,
    _get_tipo_local,
    calcular_normas,
    formatear_resultado_texto,
    verificar_area_minima,
    verificar_fos_fot,
    verificar_iluminacion,
    verificar_ventilacion,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_wall(
    wall_id: str,
    start: tuple[float, float],
    end: tuple[float, float],
    openings: list[Opening] | None = None,
    thickness: float = 0.15,
) -> Wall:
    return Wall(
        id=wall_id,
        start=list(start),
        end=list(end),
        thickness=thickness,
        openings=openings or [],
    )


def make_window(
    width: float = 1.20,
    height: float = 1.10,
    mechanism: OpeningMechanism = OpeningMechanism.sliding,
    position: float = 0.5,
) -> Opening:
    return Opening(
        type=OpeningType.window,
        width=width,
        height=height,
        mechanism=mechanism,
        position_along_wall=position,
    )


def make_door(width: float = 0.90, position: float = 0.5) -> Opening:
    return Opening(
        type=OpeningType.door,
        width=width,
        mechanism=OpeningMechanism.hinged,
        position_along_wall=position,
    )


@pytest.fixture
def simple_room_walls() -> list[Wall]:
    """Habitación cuadrada 4x4m con ventana corrediza 1.20x1.10m en w1."""
    window = make_window(width=1.20, height=1.10, mechanism=OpeningMechanism.sliding)
    return [
        make_wall("w1", (0, 0), (4, 0), openings=[window]),
        make_wall("w2", (4, 0), (4, 4)),
        make_wall("w3", (4, 4), (0, 4)),
        make_wall("w4", (0, 4), (0, 0)),
    ]


@pytest.fixture
def simple_room_space(simple_room_walls: list[Wall]) -> Space:
    """Dormitorio 4x4m."""
    return Space(
        id="s1",
        name="DORMITORIO PRINCIPAL",
        function=SpaceFunction.dormitorio,
        bounded_by=["w1", "w2", "w3", "w4"],
    )


@pytest.fixture
def simple_floor_plan(simple_room_walls: list[Wall], simple_room_space: Space) -> FloorPlan:
    """FloorPlan mínimo con 1 habitación."""
    return FloorPlan(walls=simple_room_walls, spaces=[simple_room_space])


@pytest.fixture
def simple_terrain() -> Terrain:
    """Terreno residencial 10x30m = 300 m²."""
    return Terrain(
        superficie=300.0,
        frente=10.0,
        fondo=30.0,
        zonificacion=Zonificacion.residencial,
        fos_max=0.60,
        fot_max=1.20,
    )


# ---------------------------------------------------------------------------
# Tests: _get_tipo_local
# ---------------------------------------------------------------------------

class TestGetTipoLocal:
    def test_dormitorio_es_habitable(self):
        assert _get_tipo_local(SpaceFunction.dormitorio) == TipoLocal.habitable

    def test_living_es_habitable(self):
        assert _get_tipo_local(SpaceFunction.living) == TipoLocal.habitable

    def test_comedor_es_habitable(self):
        assert _get_tipo_local(SpaceFunction.comedor) == TipoLocal.habitable

    def test_estar_es_habitable(self):
        assert _get_tipo_local(SpaceFunction.estar) == TipoLocal.habitable

    def test_cocina_es_servicio(self):
        assert _get_tipo_local(SpaceFunction.cocina) == TipoLocal.servicio

    def test_bano_es_servicio(self):
        assert _get_tipo_local(SpaceFunction.bano) == TipoLocal.servicio

    def test_lavadero_es_servicio(self):
        assert _get_tipo_local(SpaceFunction.lavadero) == TipoLocal.servicio

    def test_garage_es_no_computable(self):
        assert _get_tipo_local(SpaceFunction.garage) == TipoLocal.no_computable

    def test_pasillo_es_no_computable(self):
        assert _get_tipo_local(SpaceFunction.pasillo) == TipoLocal.no_computable


# ---------------------------------------------------------------------------
# Tests: _calcular_superficie_vidrio
# ---------------------------------------------------------------------------

class TestCalcularSuperficieVidrio:
    def test_ventana_simple(self, simple_room_space: Space, simple_room_walls: list[Wall]):
        """1 ventana 1.20x1.10 = 1.32 m²."""
        sup = _calcular_superficie_vidrio(simple_room_space, simple_room_walls)
        assert sup == pytest.approx(1.20 * 1.10, abs=1e-6)

    def test_sin_ventanas(self):
        """Habitación sin ventanas → superficie 0."""
        walls = [
            make_wall("w1", (0, 0), (3, 0)),
            make_wall("w2", (3, 0), (3, 3)),
            make_wall("w3", (3, 3), (0, 3)),
            make_wall("w4", (0, 3), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        assert _calcular_superficie_vidrio(space, walls) == 0.0

    def test_puertas_no_cuentan_como_vidrio(self):
        """Las puertas no se suman a superficie de vidrio."""
        door = make_door()
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[door]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        assert _calcular_superficie_vidrio(space, walls) == 0.0

    def test_multiples_ventanas(self):
        """Suma de múltiples ventanas en distintos muros."""
        w1 = make_window(1.20, 1.10, OpeningMechanism.sliding)
        w2 = make_window(0.90, 1.10, OpeningMechanism.hinged)
        walls = [
            make_wall("w1", (0, 0), (5, 0), openings=[w1]),
            make_wall("w2", (5, 0), (5, 4), openings=[w2]),
            make_wall("w3", (5, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        expected = 1.20 * 1.10 + 0.90 * 1.10
        assert _calcular_superficie_vidrio(space, walls) == pytest.approx(expected, abs=1e-6)

    def test_solo_cuenta_muros_del_espacio(self):
        """Solo ventanas en muros del space.bounded_by se cuentan."""
        window_in = make_window(1.20, 1.10)
        window_out = make_window(0.90, 1.10)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window_in]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
            make_wall("w5", (0, 4), (0, 8), openings=[window_out]),  # fuera del espacio
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        assert _calcular_superficie_vidrio(space, walls) == pytest.approx(1.20 * 1.10, abs=1e-6)


# ---------------------------------------------------------------------------
# Tests: _calcular_superficie_ventilacion
# ---------------------------------------------------------------------------

class TestCalcularSuperficieVentilacion:
    def test_sliding_es_50_porciento(self):
        """Ventana corrediza = 50% del vano."""
        window = make_window(1.20, 1.10, OpeningMechanism.sliding)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        expected = 1.20 * 1.10 * 0.50
        assert _calcular_superficie_ventilacion(space, walls) == pytest.approx(expected, abs=1e-6)

    def test_hinged_es_100_porciento(self):
        """Ventana batiente = 100% del vano."""
        window = make_window(1.20, 1.10, OpeningMechanism.hinged)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        expected = 1.20 * 1.10 * 1.00
        assert _calcular_superficie_ventilacion(space, walls) == pytest.approx(expected, abs=1e-6)

    def test_fixed_es_cero(self):
        """Paño fijo = 0% (no ventila)."""
        window = make_window(1.50, 1.10, OpeningMechanism.fixed)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        assert _calcular_superficie_ventilacion(space, walls) == 0.0

    def test_double_hinged_es_100_porciento(self):
        """Doble batiente = 100% del vano."""
        window = make_window(1.20, 1.10, OpeningMechanism.double_hinged)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(
            id="s1", name="X", function=SpaceFunction.dormitorio,
            bounded_by=["w1", "w2", "w3", "w4"],
        )
        expected = 1.20 * 1.10 * 1.00
        assert _calcular_superficie_ventilacion(space, walls) == pytest.approx(expected, abs=1e-6)


# ---------------------------------------------------------------------------
# Tests: verificar_iluminacion
# ---------------------------------------------------------------------------

class TestVerificarIluminacion:
    def test_cumple_habitacion_con_ventana_suficiente(self):
        """Dormitorio 4x4=16m², ventana 1.20x1.10=1.32m² → ratio=0.0825 < 1/6=0.167 → NO CUMPLE."""
        # Necesita 1/6 * 16 = 2.67 m² de vidrio mínimo
        # 1.32 < 2.67 → no cumple
        window = make_window(1.20, 1.10, OpeningMechanism.sliding)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=["w1", "w2", "w3", "w4"])
        result = verificar_iluminacion(space, walls, area_m2=16.0)
        assert result.cumple is False
        assert result.valor_calculado == pytest.approx(1.32 / 16.0, abs=1e-6)

    def test_cumple_con_ventana_grande(self):
        """Dormitorio 4x4=16m², ventana 3.0x1.10=3.3m² → ratio=0.206 > 1/6 → CUMPLE."""
        window = make_window(3.0, 1.10, OpeningMechanism.hinged)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=["w1", "w2", "w3", "w4"])
        result = verificar_iluminacion(space, walls, area_m2=16.0)
        assert result.cumple is True

    def test_minimo_servicio_es_menor(self):
        """Baño: mínimo es 1/8, no 1/6."""
        window = make_window(0.60, 1.10, OpeningMechanism.sliding)
        walls = [
            make_wall("w1", (0, 0), (2, 0), openings=[window]),
            make_wall("w2", (2, 0), (2, 2)),
            make_wall("w3", (2, 2), (0, 2)),
            make_wall("w4", (0, 2), (0, 0)),
        ]
        space = Space(id="s1", name="BAÑO", function=SpaceFunction.bano, bounded_by=["w1", "w2", "w3", "w4"])
        result = verificar_iluminacion(space, walls, area_m2=4.0)
        # 0.60 * 1.10 / 4.0 = 0.165 > 0.125 → CUMPLE
        assert result.cumple is True
        assert result.valor_minimo == pytest.approx(1 / 8, abs=1e-6)

    def test_no_computable_siempre_cumple(self):
        """Local no computable (garage) siempre cumple."""
        space = Space(id="s1", name="GARAGE", function=SpaceFunction.garage, bounded_by=[])
        result = verificar_iluminacion(space, [], area_m2=0.0)
        assert result.cumple is True

    def test_area_cero_no_cumple(self):
        """Si no se puede calcular el área, retorna NO CUMPLE para habitables."""
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=[])
        result = verificar_iluminacion(space, [], area_m2=0.0)
        assert result.cumple is False


# ---------------------------------------------------------------------------
# Tests: verificar_ventilacion
# ---------------------------------------------------------------------------

class TestVerificarVentilacion:
    def test_sliding_50pct_cumple_ventilacion(self):
        """Habitación 4x4=16m², ventana sliding 1.20x1.10 → efectivo=0.66m², ratio=0.041 < 1/12=0.083 → NO CUMPLE."""
        window = make_window(1.20, 1.10, OpeningMechanism.sliding)
        walls = [
            make_wall("w1", (0, 0), (4, 0), openings=[window]),
            make_wall("w2", (4, 0), (4, 4)),
            make_wall("w3", (4, 4), (0, 4)),
            make_wall("w4", (0, 4), (0, 0)),
        ]
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=["w1", "w2", "w3", "w4"])
        result = verificar_ventilacion(space, walls, area_m2=16.0)
        efectivo = 1.20 * 1.10 * 0.50
        assert result.valor_calculado == pytest.approx(efectivo / 16.0, abs=1e-6)

    def test_hinged_mayor_efectivo(self):
        """Batiente tiene mayor superficie efectiva que corrediza del mismo tamaño."""
        w_sliding = make_window(1.20, 1.10, OpeningMechanism.sliding)
        w_hinged = make_window(1.20, 1.10, OpeningMechanism.hinged)

        def make_space_walls(window: Opening) -> tuple[Space, list[Wall]]:
            walls = [
                make_wall("w1", (0, 0), (4, 0), openings=[window]),
                make_wall("w2", (4, 0), (4, 4)),
                make_wall("w3", (4, 4), (0, 4)),
                make_wall("w4", (0, 4), (0, 0)),
            ]
            space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=["w1", "w2", "w3", "w4"])
            return space, walls

        s, walls = make_space_walls(w_sliding)
        r_sliding = verificar_ventilacion(s, walls, area_m2=16.0)

        s2, walls2 = make_space_walls(w_hinged)
        r_hinged = verificar_ventilacion(s2, walls2, area_m2=16.0)

        assert r_hinged.valor_calculado > r_sliding.valor_calculado


# ---------------------------------------------------------------------------
# Tests: verificar_area_minima
# ---------------------------------------------------------------------------

class TestVerificarAreaMinima:
    def test_dormitorio_cumple_9m2(self):
        """Dormitorio 10m² cumple mínimo de 9m²."""
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=[])
        result = verificar_area_minima(space, 10.0)
        assert result.cumple is True
        assert result.valor_minimo == 9.0

    def test_dormitorio_no_cumple_8m2(self):
        """Dormitorio 8m² NO cumple mínimo de 9m²."""
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=[])
        result = verificar_area_minima(space, 8.0)
        assert result.cumple is False

    def test_living_cumple_15m2(self):
        """Living 16m² cumple mínimo de 15m²."""
        space = Space(id="s1", name="X", function=SpaceFunction.living, bounded_by=[])
        result = verificar_area_minima(space, 16.0)
        assert result.cumple is True

    def test_cocina_minimo_5m2(self):
        """Cocina mínimo 5m²."""
        space = Space(id="s1", name="X", function=SpaceFunction.cocina, bounded_by=[])
        result = verificar_area_minima(space, 5.0)
        assert result.cumple is True
        assert result.valor_minimo == 5.0

    def test_bano_minimo_3m2(self):
        """Baño mínimo 3m²."""
        space = Space(id="s1", name="X", function=SpaceFunction.bano, bounded_by=[])
        result = verificar_area_minima(space, 2.5)
        assert result.cumple is False

    def test_lavadero_minimo_2_5m2(self):
        space = Space(id="s1", name="X", function=SpaceFunction.lavadero, bounded_by=[])
        result = verificar_area_minima(space, 2.5)
        assert result.cumple is True

    def test_pasillo_sin_requisito(self):
        """Pasillo sin requisito mínimo → siempre cumple."""
        space = Space(id="s1", name="X", function=SpaceFunction.pasillo, bounded_by=[])
        result = verificar_area_minima(space, 0.5)
        assert result.cumple is True
        assert result.valor_minimo == 0.0

    def test_override_minimos(self):
        """Permite override del mínimo."""
        from cad_copilot.schemas.space import SpaceFunction
        space = Space(id="s1", name="X", function=SpaceFunction.dormitorio, bounded_by=[])
        result = verificar_area_minima(space, 11.0, area_min={SpaceFunction.dormitorio: 12.0})
        assert result.cumple is False
        assert result.valor_minimo == 12.0


# ---------------------------------------------------------------------------
# Tests: verificar_fos_fot
# ---------------------------------------------------------------------------

class TestVerificarFosFot:
    def test_fos_cumple(self, simple_floor_plan: FloorPlan, simple_terrain: Terrain):
        """Habitación 4x4=16m² en terreno 300m² → FOS=0.053 < 0.60 → CUMPLE."""
        resultado = verificar_fos_fot(simple_floor_plan, simple_terrain)
        assert resultado.fos_calculado == pytest.approx(16.0 / 300.0, abs=1e-4)
        assert resultado.items[0].cumple is True

    def test_fos_no_cumple_terreno_pequeno(self, simple_floor_plan: FloorPlan):
        """Habitación 4x4=16m² en terreno 20m² → FOS=0.80 > 0.60 → NO CUMPLE."""
        terrain = Terrain(superficie=20.0, frente=4.0, fondo=5.0, fos_max=0.60, fot_max=1.20)
        resultado = verificar_fos_fot(simple_floor_plan, terrain)
        assert resultado.items[0].cumple is False

    def test_sin_espacios_fos_cero(self, simple_terrain: Terrain):
        """Sin espacios definidos, FOS=0 → siempre cumple."""
        fp = FloorPlan(walls=[make_wall("w1", (0, 0), (4, 0))])
        resultado = verificar_fos_fot(fp, simple_terrain)
        assert resultado.fos_calculado == 0.0
        assert resultado.items[0].cumple is True

    def test_resultado_tiene_dos_items(self, simple_floor_plan: FloorPlan, simple_terrain: Terrain):
        """Resultado FOS/FOT tiene siempre 2 ítems."""
        resultado = verificar_fos_fot(simple_floor_plan, simple_terrain)
        assert len(resultado.items) == 2


# ---------------------------------------------------------------------------
# Tests: calcular_normas (función principal)
# ---------------------------------------------------------------------------

class TestCalcularNormas:
    def test_resultado_tiene_un_ambiente_por_espacio(
        self, simple_floor_plan: FloorPlan
    ):
        resultado = calcular_normas(simple_floor_plan)
        assert len(resultado.ambientes) == len(simple_floor_plan.spaces)

    def test_sin_terreno_no_hay_resultado_terreno(self, simple_floor_plan: FloorPlan):
        resultado = calcular_normas(simple_floor_plan)
        assert resultado.terreno is None

    def test_con_terreno_hay_resultado_terreno(
        self, simple_floor_plan: FloorPlan, simple_terrain: Terrain
    ):
        resultado = calcular_normas(simple_floor_plan, simple_terrain)
        assert resultado.terreno is not None

    def test_cada_ambiente_tiene_3_items(self, simple_floor_plan: FloorPlan):
        """Cada ambiente tiene items de iluminación, ventilación y área."""
        resultado = calcular_normas(simple_floor_plan)
        for amb in resultado.ambientes:
            assert len(amb.items) == 3

    def test_proyecto_se_toma_del_title_block(self, simple_floor_plan: FloorPlan):
        from cad_copilot.schemas.layout import TitleBlock
        simple_floor_plan.title_block = TitleBlock(
            project="TEST PROJECT",
            drawing_name="PLANTA BAJA",
            location="PLOTTIER",
            professional="ARQ. TEST",
            license_number="CPTN 0000",
            date="2026-01-01",
        )
        resultado = calcular_normas(simple_floor_plan)
        assert resultado.proyecto == "TEST PROJECT"

    def test_observacion_sin_espacios(self):
        """Sin espacios, agrega observación general."""
        fp = FloorPlan(walls=[make_wall("w1", (0, 0), (4, 0))])
        resultado = calcular_normas(fp)
        assert any("ambient" in obs.lower() for obs in resultado.observaciones_generales)

    def test_observacion_sin_terreno(self, simple_floor_plan: FloorPlan):
        """Sin terreno, agrega observación sobre FOS/FOT."""
        resultado = calcular_normas(simple_floor_plan)
        assert any("terreno" in obs.lower() for obs in resultado.observaciones_generales)

    def test_override_iluminacion_min(self, simple_floor_plan: FloorPlan):
        """Override de mínimos de iluminación funciona."""
        from cad_copilot.standards.norms import TipoLocal
        # Establecer mínimo muy bajo para forzar CUMPLE
        resultado = calcular_normas(
            simple_floor_plan,
            iluminacion_min={TipoLocal.habitable: 0.001, TipoLocal.servicio: 0.001, TipoLocal.no_computable: 0.0},
        )
        item_ilum = resultado.ambientes[0].items[0]
        assert item_ilum.cumple is True

    def test_cumple_todo_property(self, simple_floor_plan: FloorPlan, simple_terrain: Terrain):
        """cumple_todo es False si algún ítem no cumple."""
        resultado = calcular_normas(simple_floor_plan, simple_terrain)
        # Al menos la iluminación de un dormitorio 4x4 con ventana 1.20x1.10 NO cumple
        assert isinstance(resultado.cumple_todo, bool)


# ---------------------------------------------------------------------------
# Tests: formatear_resultado_texto
# ---------------------------------------------------------------------------

class TestFormatearResultadoTexto:
    def test_incluye_nombre_proyecto(self, simple_floor_plan: FloorPlan):
        from cad_copilot.schemas.layout import TitleBlock
        simple_floor_plan.title_block = TitleBlock(
            project="VIVIENDA TEST",
            drawing_name="PLANTA",
            location="PLOTTIER",
            professional="ARQ.",
            license_number="CPTN 0",
            date="2026-01-01",
        )
        resultado = calcular_normas(simple_floor_plan)
        texto = formatear_resultado_texto(resultado)
        assert "VIVIENDA TEST" in texto

    def test_incluye_cumple_no_cumple(self, simple_floor_plan: FloorPlan):
        resultado = calcular_normas(simple_floor_plan)
        texto = formatear_resultado_texto(resultado)
        assert "CUMPLE" in texto or "NO CUMPLE" in texto

    def test_incluye_nombres_de_ambientes(self, simple_floor_plan: FloorPlan):
        resultado = calcular_normas(simple_floor_plan)
        texto = formatear_resultado_texto(resultado)
        assert "DORMITORIO PRINCIPAL" in texto

    def test_incluye_seccion_terreno_si_existe(
        self, simple_floor_plan: FloorPlan, simple_terrain: Terrain
    ):
        resultado = calcular_normas(simple_floor_plan, simple_terrain)
        texto = formatear_resultado_texto(resultado)
        assert "FOS" in texto
        assert "FOT" in texto

    def test_nota_al_pie(self, simple_floor_plan: FloorPlan):
        resultado = calcular_normas(simple_floor_plan)
        texto = formatear_resultado_texto(resultado)
        assert "NOTA" in texto or "municipio" in texto.lower()


# ---------------------------------------------------------------------------
# Tests: Terrain schema
# ---------------------------------------------------------------------------

class TestTerrain:
    def test_terreno_minimo(self):
        t = Terrain(superficie=300.0, frente=10.0, fondo=30.0)
        assert t.zonificacion == Zonificacion.residencial
        assert t.fos_max == 0.60
        assert t.fot_max == 1.20

    def test_retiros_default(self):
        t = Terrain(superficie=300.0, frente=10.0, fondo=30.0)
        assert t.retiros.frente == 3.0
        assert t.retiros.fondo == 3.0
        assert t.retiros.lateral_izq == 0.0
        assert t.retiros.lateral_der == 0.0

    def test_retiros_custom(self):
        retiros = RetirosConfig(frente=5.0, lateral_izq=2.0, lateral_der=0.0, fondo=4.0)
        t = Terrain(superficie=300.0, frente=10.0, fondo=30.0, retiros=retiros)
        assert t.retiros.frente == 5.0
        assert t.retiros.lateral_izq == 2.0

    def test_fos_max_validacion(self):
        """FOS no puede ser mayor a 1."""
        with pytest.raises(Exception):
            Terrain(superficie=300.0, frente=10.0, fondo=30.0, fos_max=1.5)

    def test_superficie_negativa_invalida(self):
        with pytest.raises(Exception):
            Terrain(superficie=-100.0, frente=10.0, fondo=30.0)

    def test_zonificacion_enum(self):
        t = Terrain(superficie=200.0, frente=8.0, fondo=25.0, zonificacion="comercial")
        assert t.zonificacion == Zonificacion.comercial


# ---------------------------------------------------------------------------
# Tests: constantes normativas
# ---------------------------------------------------------------------------

class TestConstantesNormativas:
    def test_iluminacion_habitable_es_1_sobre_6(self):
        assert ILUMINACION_MIN[TipoLocal.habitable] == pytest.approx(1 / 6, abs=1e-6)

    def test_iluminacion_servicio_es_1_sobre_8(self):
        assert ILUMINACION_MIN[TipoLocal.servicio] == pytest.approx(1 / 8, abs=1e-6)

    def test_ventilacion_habitable_es_1_sobre_12(self):
        assert VENTILACION_MIN[TipoLocal.habitable] == pytest.approx(1 / 12, abs=1e-6)

    def test_area_min_dormitorio_es_9(self):
        assert AREA_MIN[SpaceFunction.dormitorio] == 9.0

    def test_area_min_living_es_15(self):
        assert AREA_MIN[SpaceFunction.living] == 15.0

    def test_area_min_bano_es_3(self):
        assert AREA_MIN[SpaceFunction.bano] == 3.0
