"""Tests para el MCP Server de cad-copilot."""

from __future__ import annotations

import json
import os
import tempfile


from cad_copilot.mcp_server.server import (
    generate_dxf,
    generate_dxf_temp,
    get_example_floor_plan,
    get_floor_plan_schema,
    list_available_blocks,
    validate_floor_plan,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_FLOOR_PLAN = {
    "walls": [
        {
            "id": "w1",
            "start": [0, 0],
            "end": [4, 0],
            "thickness": 0.20,
            "classification": "exterior_portante",
            "openings": [
                {"type": "door", "mechanism": "hinged", "width": 0.90, "position_along_wall": 0.5}
            ],
        },
        {
            "id": "w2",
            "start": [4, 0],
            "end": [4, 3],
            "thickness": 0.20,
            "classification": "exterior_portante",
            "openings": [],
        },
        {
            "id": "w3",
            "start": [4, 3],
            "end": [0, 3],
            "thickness": 0.20,
            "classification": "exterior_portante",
            "openings": [
                {
                    "type": "window",
                    "mechanism": "sliding",
                    "width": 1.20,
                    "position_along_wall": 1.0,
                }
            ],
        },
        {
            "id": "w4",
            "start": [0, 3],
            "end": [0, 0],
            "thickness": 0.20,
            "classification": "exterior_portante",
            "openings": [],
        },
    ],
}

INVALID_FLOOR_PLAN_JSON = '{"walls": "no es una lista"}'
MALFORMED_JSON = "esto no es json {"


# ---------------------------------------------------------------------------
# Tests: validate_floor_plan
# ---------------------------------------------------------------------------


def test_validate_floor_plan_valid():
    """Un FloorPlan válido devuelve confirmación con resumen."""
    result = validate_floor_plan(json.dumps(VALID_FLOOR_PLAN))
    assert "VÁLIDO ✓" in result
    assert "Muros: 4" in result
    assert "puertas" in result
    assert "ventanas" in result


def test_validate_floor_plan_invalid_json():
    """JSON mal formado devuelve error de parseo."""
    result = validate_floor_plan(MALFORMED_JSON)
    assert "ERROR" in result
    assert "JSON inválido" in result


def test_validate_floor_plan_schema_error():
    """JSON válido pero con schema incorrecto devuelve errores de validación."""
    result = validate_floor_plan(INVALID_FLOOR_PLAN_JSON)
    assert "INVÁLIDO" in result
    assert "validación" in result.lower()


def test_validate_floor_plan_missing_walls():
    """FloorPlan sin muros devuelve error de validación."""
    result = validate_floor_plan("{}")
    assert "INVÁLIDO" in result


def test_validate_floor_plan_counts_correctly():
    """El conteo de puertas y ventanas es correcto."""
    result = validate_floor_plan(json.dumps(VALID_FLOOR_PLAN))
    assert "1 puertas, 1 ventanas" in result or "1 puerta" in result or "1 ventana" in result


# ---------------------------------------------------------------------------
# Tests: generate_dxf
# ---------------------------------------------------------------------------


def test_generate_dxf_creates_file():
    """generate_dxf crea un archivo DXF en la ruta especificada."""
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        output_path = tmp.name

    try:
        result = generate_dxf(json.dumps(VALID_FLOOR_PLAN), output_path)
        assert "DXF generado exitosamente" in result
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_generate_dxf_invalid_json():
    """generate_dxf con JSON inválido devuelve error."""
    result = generate_dxf(MALFORMED_JSON, "/tmp/test.dxf")
    assert "ERROR" in result
    assert "JSON inválido" in result


def test_generate_dxf_schema_error():
    """generate_dxf con schema incorrecto devuelve errores de validación."""
    result = generate_dxf(INVALID_FLOOR_PLAN_JSON, "/tmp/test.dxf")
    assert "ERROR" in result
    assert "validación" in result.lower()


def test_generate_dxf_creates_parent_dirs():
    """generate_dxf crea los directorios padre si no existen."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "deep", "test.dxf")
        result = generate_dxf(json.dumps(VALID_FLOOR_PLAN), output_path)
        assert "DXF generado exitosamente" in result
        assert os.path.exists(output_path)


# ---------------------------------------------------------------------------
# Tests: generate_dxf_temp
# ---------------------------------------------------------------------------


def test_generate_dxf_temp_creates_file():
    """generate_dxf_temp crea un DXF en directorio temporal."""
    result = generate_dxf_temp(json.dumps(VALID_FLOOR_PLAN))
    assert "DXF generado en directorio temporal" in result
    # Extraer path del resultado y verificar que existe
    path = result.split(": ", 1)[-1]
    assert os.path.exists(path)
    assert path.endswith(".dxf")
    # Limpiar
    os.unlink(path)


def test_generate_dxf_temp_invalid_json():
    """generate_dxf_temp con JSON inválido devuelve error."""
    result = generate_dxf_temp(MALFORMED_JSON)
    assert "ERROR" in result


# ---------------------------------------------------------------------------
# Tests: list_available_blocks
# ---------------------------------------------------------------------------


def test_list_available_blocks_contains_doors():
    """list_available_blocks incluye sección de puertas."""
    result = list_available_blocks()
    assert "PUERTAS" in result
    assert "hinged" in result
    assert "sliding" in result
    assert "double_hinged" in result


def test_list_available_blocks_contains_windows():
    """list_available_blocks incluye sección de ventanas."""
    result = list_available_blocks()
    assert "VENTANAS" in result
    assert "WIN_SLIDING" in result
    assert "WIN_HINGED" in result
    assert "WIN_FIXED" in result


def test_list_available_blocks_contains_fixtures():
    """list_available_blocks incluye artefactos sanitarios."""
    result = list_available_blocks()
    assert "ARTEFACTOS_SANITARIOS" in result
    assert "FIX_TOILET" in result
    assert "FIX_SINK" in result
    assert "FIX_SHOWER" in result


def test_list_available_blocks_contains_usage_examples():
    """list_available_blocks incluye ejemplos de uso JSON."""
    result = list_available_blocks()
    assert '"type": "door"' in result
    assert '"type": "window"' in result


# ---------------------------------------------------------------------------
# Tests: get_floor_plan_schema
# ---------------------------------------------------------------------------


def test_get_floor_plan_schema_returns_valid_json():
    """get_floor_plan_schema devuelve JSON válido."""
    result = get_floor_plan_schema()
    schema = json.loads(result)  # no debe lanzar excepción
    assert isinstance(schema, dict)


def test_get_floor_plan_schema_contains_walls():
    """El schema incluye la propiedad 'walls'."""
    result = get_floor_plan_schema()
    schema = json.loads(result)
    # Buscar 'walls' en el schema (puede estar en 'properties' o en $defs)
    schema_str = json.dumps(schema)
    assert '"walls"' in schema_str


def test_get_floor_plan_schema_is_pydantic_v2():
    """El schema tiene formato Pydantic v2 (tiene '$defs' o 'properties')."""
    result = get_floor_plan_schema()
    schema = json.loads(result)
    assert "properties" in schema or "$defs" in schema


# ---------------------------------------------------------------------------
# Tests: get_example_floor_plan
# ---------------------------------------------------------------------------


def test_get_example_floor_plan_returns_valid_json():
    """get_example_floor_plan devuelve JSON válido."""
    result = get_example_floor_plan()
    data = json.loads(result)  # no debe lanzar excepción
    assert isinstance(data, dict)


def test_get_example_floor_plan_is_valid_floor_plan():
    """El ejemplo de FloorPlan pasa la validación de schema."""
    example = get_example_floor_plan()
    result = validate_floor_plan(example)
    assert "VÁLIDO ✓" in result


def test_get_example_floor_plan_has_5_walls():
    """El ejemplo tiene exactamente 5 muros."""
    result = get_example_floor_plan()
    data = json.loads(result)
    assert len(data["walls"]) == 5


def test_get_example_floor_plan_has_title_block():
    """El ejemplo incluye cartela CPTN."""
    result = get_example_floor_plan()
    data = json.loads(result)
    assert "title_block" in data
    assert data["title_block"]["professional"] == "ARQ. PABLO QUEVEDO"
