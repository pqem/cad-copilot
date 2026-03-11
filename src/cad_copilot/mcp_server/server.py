"""MCP Server para cad-copilot — expone herramientas CAD a Claude Code.

Herramientas disponibles:
- generate_dxf: Genera un archivo DXF desde un JSON semántico de FloorPlan.
- validate_floor_plan: Valida el JSON de un FloorPlan sin generar el DXF.
- list_available_blocks: Lista todos los bloques paramétricos disponibles.
- get_floor_plan_schema: Devuelve el JSON Schema del modelo FloorPlan.
- calculate_norms: Calcula verificaciones normativas CUMPLE/NO CUMPLE.
- generate_norm_table_dxf: Genera tabla DXF con verificaciones para el municipio.
"""

from __future__ import annotations

import json
import tempfile

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from cad_copilot.engine.norm_table import generate_norm_table_dxf as _generate_norm_table_dxf
from cad_copilot.engine.renderer import render_floor_plan
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.terrain import Terrain
from cad_copilot.standards.norms import calcular_normas, formatear_resultado_texto

mcp = FastMCP(
    "cad-copilot",
    instructions=(
        "Servidor CAD arquitectónico para Argentina. "
        "Genera planos 2D DXF profesionales desde JSON semántico. "
        "Unidades en metros. DXF R2013. Normas IRAM/AIA."
    ),
)

# ---------------------------------------------------------------------------
# Tool: generate_dxf
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_dxf(floor_plan_json: str, output_path: str) -> str:
    """Genera un archivo DXF desde un JSON semántico de FloorPlan.

    Flujo completo: valida el JSON con Pydantic, dibuja muros, puertas,
    ventanas, etiquetas de ambientes, cotas y cartela CPTN en Paper Space.

    Args:
        floor_plan_json: JSON del FloorPlan como string. Debe incluir al menos
            el campo "walls". Campos opcionales: spaces, annotations,
            title_block, paper_config.
        output_path: Ruta absoluta donde guardar el archivo DXF generado.
            Si los directorios no existen, se crean automáticamente.

    Returns:
        Ruta absoluta del archivo DXF generado, o mensaje de error con detalle.
    """
    try:
        data = json.loads(floor_plan_json)
    except json.JSONDecodeError as exc:
        return f"ERROR: JSON inválido — {exc}"

    try:
        floor_plan = FloorPlan.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        lines = [f"ERROR: {len(errors)} error(s) de validación:"]
        for err in errors:
            loc = " → ".join(str(p) for p in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        return "\n".join(lines)

    try:
        result = render_floor_plan(floor_plan, output_path)
        return f"DXF generado exitosamente: {result}"
    except Exception as exc:
        return f"ERROR al generar DXF: {exc}"


# ---------------------------------------------------------------------------
# Tool: generate_dxf_temp
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_dxf_temp(floor_plan_json: str) -> str:
    """Genera un archivo DXF en un directorio temporal y devuelve la ruta.

    Útil cuando no se conoce la ruta de destino de antemano. El archivo se
    guarda en /tmp con un nombre único.

    Args:
        floor_plan_json: JSON del FloorPlan como string.

    Returns:
        Ruta absoluta del archivo DXF temporal generado, o mensaje de error.
    """
    try:
        data = json.loads(floor_plan_json)
    except json.JSONDecodeError as exc:
        return f"ERROR: JSON inválido — {exc}"

    try:
        floor_plan = FloorPlan.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        lines = [f"ERROR: {len(errors)} error(s) de validación:"]
        for err in errors:
            loc = " → ".join(str(p) for p in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        return "\n".join(lines)

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        output_path = tmp.name

    try:
        result = render_floor_plan(floor_plan, output_path)
        return f"DXF generado en directorio temporal: {result}"
    except Exception as exc:
        return f"ERROR al generar DXF: {exc}"


# ---------------------------------------------------------------------------
# Tool: validate_floor_plan
# ---------------------------------------------------------------------------

@mcp.tool()
def validate_floor_plan(floor_plan_json: str) -> str:
    """Valida el JSON de un FloorPlan sin generar el DXF.

    Permite verificar que el JSON es correcto antes de generar el archivo.
    Devuelve un resumen de lo que contiene el plano si es válido.

    Args:
        floor_plan_json: JSON del FloorPlan como string.

    Returns:
        Resumen del plano si es válido, o lista de errores de validación.
    """
    try:
        data = json.loads(floor_plan_json)
    except json.JSONDecodeError as exc:
        return f"ERROR: JSON inválido — {exc}"

    try:
        fp = FloorPlan.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        lines = [f"INVÁLIDO: {len(errors)} error(s) de validación:"]
        for err in errors:
            loc = " → ".join(str(p) for p in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        return "\n".join(lines)

    # Generar resumen del plano
    total_openings = sum(len(w.openings) for w in fp.walls)
    doors = sum(
        1 for w in fp.walls for o in w.openings if o.type.value == "door"
    )
    windows = sum(
        1 for w in fp.walls for o in w.openings if o.type.value == "window"
    )

    lines = [
        "VÁLIDO ✓ — Resumen del plano:",
        f"  Muros: {len(fp.walls)}",
        f"  Aberturas: {total_openings} ({doors} puertas, {windows} ventanas)",
        f"  Ambientes: {len(fp.spaces)}",
        f"  Papel: {fp.paper_config.size} {fp.paper_config.orientation} 1:{fp.paper_config.scale}",
    ]

    if fp.title_block:
        lines.append(f"  Cartela: {fp.title_block.project} — {fp.title_block.drawing_name}")
    else:
        lines.append("  Cartela: no incluida")

    if fp.spaces:
        names = ", ".join(s.name for s in fp.spaces)
        lines.append(f"  Ambientes: {names}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: list_available_blocks
# ---------------------------------------------------------------------------

@mcp.tool()
def list_available_blocks() -> str:
    """Lista todos los bloques paramétricos disponibles en cad-copilot.

    Devuelve los bloques de puertas, ventanas y artefactos sanitarios
    con sus dimensiones estándar, naming convention y parámetros disponibles.

    Returns:
        Lista formateada de bloques disponibles con descripción y uso.
    """
    blocks = {
        "PUERTAS": [
            {
                "tipo": "hinged",
                "mecanismo": "abatible",
                "naming": "DOOR_HINGED_{width*100:03d}",
                "ejemplo": "DOOR_HINGED_090",
                "ancho_tipico": "0.70, 0.80, 0.90, 1.00 m",
                "descripcion": "Puerta con hoja abatible, marco y arco de 90°",
                "uso_json": '{"type": "door", "mechanism": "hinged", "width": 0.90}',
            },
            {
                "tipo": "sliding",
                "mecanismo": "corrediza",
                "naming": "DOOR_SLIDING_{width*100:03d}",
                "ejemplo": "DOOR_SLIDING_080",
                "ancho_tipico": "0.80, 0.90, 1.00 m",
                "descripcion": "Puerta corrediza con flecha de dirección",
                "uso_json": '{"type": "door", "mechanism": "sliding", "width": 0.80}',
            },
            {
                "tipo": "double_hinged",
                "mecanismo": "doble abatible",
                "naming": "DOOR_DOUBLE_{width*100:03d}",
                "ejemplo": "DOOR_DOUBLE_160",
                "ancho_tipico": "1.20, 1.40, 1.60 m",
                "descripcion": "Puerta doble con 2 hojas simétricas y 2 arcos",
                "uso_json": '{"type": "door", "mechanism": "double_hinged", "width": 1.60}',
            },
        ],
        "VENTANAS": [
            {
                "tipo": "sliding",
                "mecanismo": "corrediza",
                "naming": "WIN_SLIDING_{width*100:03d}",
                "ejemplo": "WIN_SLIDING_150",
                "ancho_tipico": "0.90, 1.00, 1.20, 1.50 m",
                "descripcion": "Ventana corrediza con 2 vidrios y división central",
                "uso_json": '{"type": "window", "mechanism": "sliding", "width": 1.50}',
            },
            {
                "tipo": "hinged",
                "mecanismo": "batiente",
                "naming": "WIN_HINGED_{width*100:03d}",
                "ejemplo": "WIN_HINGED_120",
                "ancho_tipico": "0.60, 0.90, 1.00, 1.20 m",
                "descripcion": "Ventana batiente con diagonales de apertura",
                "uso_json": '{"type": "window", "mechanism": "hinged", "width": 1.20}',
            },
            {
                "tipo": "fixed",
                "mecanismo": "paño fijo",
                "naming": "WIN_FIXED_{width*100:03d}",
                "ejemplo": "WIN_FIXED_120",
                "ancho_tipico": "0.60, 1.00, 1.20, 1.50, 2.00 m",
                "descripcion": "Ventana paño fijo con cruz indicativa",
                "uso_json": '{"type": "window", "mechanism": "fixed", "width": 1.20}',
            },
        ],
        "ARTEFACTOS_SANITARIOS": [
            {
                "nombre": "FIX_TOILET",
                "dimensiones": "0.37 x 0.60 m",
                "descripcion": "Inodoro en planta (tanque + asiento elíptico)",
                "parametros": "sin parámetros",
            },
            {
                "nombre": "FIX_SINK",
                "dimensiones": "0.45 x 0.55 m",
                "descripcion": "Lavabo/pileta de manos con pileta elíptica",
                "parametros": "sin parámetros",
            },
            {
                "nombre": "FIX_SHOWER_{size*100:03d}",
                "dimensiones": "0.80 x 0.80 m (default)",
                "descripcion": "Ducha cuadrada con diagonales de pendiente y desagüe",
                "parametros": "size: 0.80, 0.90 m",
            },
            {
                "nombre": "FIX_BIDET",
                "dimensiones": "0.37 x 0.55 m",
                "descripcion": "Bidet en planta (forma elíptica completa)",
                "parametros": "sin parámetros",
            },
            {
                "nombre": "FIX_KITCHEN_SINK",
                "dimensiones": "0.60 x 0.50 m",
                "descripcion": "Pileta de cocina en mesada con pileta circular",
                "parametros": "sin parámetros",
            },
        ],
        "SIMBOLOS": [
            {
                "nombre": "SYM_NORTH",
                "descripcion": "Flecha de norte para orientación del plano",
            },
            {
                "nombre": "SYM_LEVEL",
                "descripcion": "Marca de nivel de piso terminado",
            },
        ],
    }

    lines = ["BLOQUES PARAMÉTRICOS DISPONIBLES EN CAD-COPILOT", "=" * 50]

    for categoria, items in blocks.items():
        lines.append(f"\n## {categoria}")
        for item in items:
            if "naming" in item:
                lines.append(f"\n  [{item['tipo']}] {item['mecanismo'].upper()}")
                lines.append(f"    Nombre: {item['naming']}")
                lines.append(f"    Ejemplo: {item['ejemplo']}")
                lines.append(f"    Anchos típicos: {item['ancho_tipico']}")
                lines.append(f"    Descripción: {item['descripcion']}")
                lines.append(f"    JSON: {item['uso_json']}")
            else:
                lines.append(f"\n  [{item['nombre']}]")
                lines.append(f"    Dimensiones: {item.get('dimensiones', 'N/A')}")
                lines.append(f"    Descripción: {item['descripcion']}")
                if "parametros" in item:
                    lines.append(f"    Parámetros: {item['parametros']}")

    lines.append("\n" + "=" * 50)
    lines.append("NOTA: Los artefactos sanitarios se insertan via 'spaces' en el JSON.")
    lines.append("Las puertas y ventanas se insertan via 'openings' dentro de cada muro.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: get_floor_plan_schema
# ---------------------------------------------------------------------------

@mcp.tool()
def get_floor_plan_schema() -> str:
    """Devuelve el JSON Schema completo del modelo FloorPlan.

    Útil para conocer todos los campos disponibles, tipos y restricciones
    antes de construir un JSON de plano arquitectónico.

    Returns:
        JSON Schema formateado del modelo FloorPlan (Pydantic v2).
    """
    schema = FloorPlan.model_json_schema()
    return json.dumps(schema, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: get_example_floor_plan
# ---------------------------------------------------------------------------

@mcp.tool()
def get_example_floor_plan() -> str:
    """Devuelve un JSON de ejemplo de FloorPlan listo para usar.

    El ejemplo corresponde a una vivienda simple de 6x4m con:
    - 5 muros (4 exteriores + 1 medianero interior)
    - 2 puertas y 2 ventanas
    - 2 ambientes (living-comedor y dormitorio)
    - Cartela CPTN completa
    - Papel A3 apaisado 1:50

    Returns:
        JSON de ejemplo formateado como string.
    """
    example = {
        "walls": [
            {
                "id": "w1",
                "start": [0, 0],
                "end": [6, 0],
                "thickness": 0.30,
                "classification": "exterior_portante",
                "openings": [
                    {
                        "type": "door",
                        "mechanism": "hinged",
                        "width": 0.90,
                        "height": 2.10,
                        "position_along_wall": 1.0,
                    },
                    {
                        "type": "window",
                        "mechanism": "sliding",
                        "width": 1.50,
                        "height": 1.10,
                        "sill_height": 0.90,
                        "position_along_wall": 3.5,
                    },
                ],
            },
            {
                "id": "w2",
                "start": [6, 0],
                "end": [6, 4],
                "thickness": 0.30,
                "classification": "exterior_portante",
                "openings": [
                    {
                        "type": "window",
                        "mechanism": "sliding",
                        "width": 1.20,
                        "height": 1.10,
                        "sill_height": 0.90,
                        "position_along_wall": 1.4,
                    }
                ],
            },
            {
                "id": "w3",
                "start": [6, 4],
                "end": [0, 4],
                "thickness": 0.30,
                "classification": "exterior_portante",
                "openings": [],
            },
            {
                "id": "w4",
                "start": [0, 4],
                "end": [0, 0],
                "thickness": 0.30,
                "classification": "exterior_portante",
                "openings": [],
            },
            {
                "id": "w5",
                "start": [3, 0],
                "end": [3, 4],
                "thickness": 0.15,
                "classification": "interior",
                "openings": [
                    {
                        "type": "door",
                        "mechanism": "hinged",
                        "width": 0.80,
                        "height": 2.10,
                        "position_along_wall": 0.5,
                    }
                ],
            },
        ],
        "spaces": [
            {
                "name": "LIVING-COMEDOR",
                "function": "living",
                "bounded_by": ["w1", "w5", "w3", "w4"],
            },
            {
                "name": "DORMITORIO",
                "function": "dormitorio",
                "bounded_by": ["w5", "w2", "w3"],
            },
        ],
        "paper_config": {
            "size": "A3",
            "orientation": "landscape",
            "scale": 50,
            "margins": [25, 10, 10, 10],
        },
        "title_block": {
            "project": "VIVIENDA UNIFAMILIAR",
            "drawing_name": "PLANTA BAJA",
            "location": "PLOTTIER, NEUQUEN",
            "professional": "ARQ. PABLO QUEVEDO",
            "license_number": "CPTN 1234",
            "date": "2026-03-10",
            "sheet": "1/1",
        },
    }
    return json.dumps(example, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: calculate_norms
# ---------------------------------------------------------------------------

@mcp.tool()
def calculate_norms(floor_plan_json: str, terrain_json: str | None = None) -> str:
    """Calcula las verificaciones normativas del proyecto (CUMPLE/NO CUMPLE).

    Verifica el cumplimiento del Código de Edificación de Neuquén/Plottier:
    - Iluminación natural por ambiente (relación vidrio/piso)
    - Ventilación natural por ambiente (superficie practicable/piso)
    - Superficie mínima por función de local
    - FOS y FOT del terreno (si se proveen datos de terreno)

    Args:
        floor_plan_json: JSON del FloorPlan como string. Debe incluir 'walls'
            y 'spaces' para calcular iluminación/ventilación/área.
        terrain_json: JSON del Terrain como string (opcional). Si se provee,
            calcula FOS y FOT. Campos: superficie, frente, fondo, zonificacion,
            fos_max, fot_max, retiros (frente, lateral_izq, lateral_der, fondo).
            Ejemplo: {"superficie": 300, "frente": 10, "fondo": 30, "fos_max": 0.60,
            "fot_max": 1.20, "retiros": {"frente": 3, "fondo": 3}}

    Returns:
        Tabla de verificación normativa formateada como texto con CUMPLE/NO CUMPLE.
    """
    # Parsear FloorPlan
    try:
        fp_data = json.loads(floor_plan_json)
    except json.JSONDecodeError as exc:
        return f"ERROR: floor_plan_json inválido — {exc}"

    try:
        floor_plan = FloorPlan.model_validate(fp_data)
    except ValidationError as exc:
        errors = exc.errors()
        lines = [f"ERROR: {len(errors)} error(s) en floor_plan_json:"]
        for err in errors:
            loc = " → ".join(str(p) for p in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        return "\n".join(lines)

    # Parsear Terrain (opcional)
    terrain: Terrain | None = None
    if terrain_json:
        try:
            t_data = json.loads(terrain_json)
        except json.JSONDecodeError as exc:
            return f"ERROR: terrain_json inválido — {exc}"

        try:
            terrain = Terrain.model_validate(t_data)
        except ValidationError as exc:
            errors = exc.errors()
            lines = [f"ERROR: {len(errors)} error(s) en terrain_json:"]
            for err in errors:
                loc = " → ".join(str(p) for p in err["loc"])
                lines.append(f"  • {loc}: {err['msg']}")
            return "\n".join(lines)

    # Calcular normas
    try:
        resultado = calcular_normas(floor_plan, terrain)
        return formatear_resultado_texto(resultado)
    except Exception as exc:
        return f"ERROR al calcular normas: {exc}"


# ---------------------------------------------------------------------------
# Tool: generate_norm_table_dxf
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_norm_table_dxf_tool(
    floor_plan_json: str,
    output_path: str,
    terrain_json: str | None = None,
) -> str:
    """Genera una tabla DXF con verificaciones normativas para el municipio.

    La tabla incluye todos los ítems de verificación (iluminación, ventilación,
    superficies, FOS/FOT) con resultado CUMPLE/NO CUMPLE, lista para insertar
    en el Paper Space del plano municipal.

    Args:
        floor_plan_json: JSON del FloorPlan como string.
        output_path: Ruta absoluta donde guardar el DXF de la tabla normativa.
        terrain_json: JSON del Terrain como string (opcional). Si se provee,
            incluye verificación FOS/FOT en la tabla.

    Returns:
        Ruta del DXF generado, o mensaje de error.
    """
    # Parsear FloorPlan
    try:
        fp_data = json.loads(floor_plan_json)
    except json.JSONDecodeError as exc:
        return f"ERROR: floor_plan_json inválido — {exc}"

    try:
        floor_plan = FloorPlan.model_validate(fp_data)
    except ValidationError as exc:
        errors = exc.errors()
        lines = [f"ERROR: {len(errors)} error(s) en floor_plan_json:"]
        for err in errors:
            loc = " → ".join(str(p) for p in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        return "\n".join(lines)

    # Parsear Terrain (opcional)
    terrain: Terrain | None = None
    if terrain_json:
        try:
            t_data = json.loads(terrain_json)
        except json.JSONDecodeError as exc:
            return f"ERROR: terrain_json inválido — {exc}"

        try:
            terrain = Terrain.model_validate(t_data)
        except ValidationError as exc:
            errors = exc.errors()
            lines = [f"ERROR: {len(errors)} error(s) en terrain_json:"]
            for err in errors:
                loc = " → ".join(str(p) for p in err["loc"])
                lines.append(f"  • {loc}: {err['msg']}")
            return "\n".join(lines)

    # Calcular normas y generar DXF
    try:
        resultado = calcular_normas(floor_plan, terrain)
        path = _generate_norm_table_dxf(resultado, output_path)
        estado = "CUMPLE" if resultado.cumple_todo else "NO CUMPLE"
        return f"Tabla normativa DXF generada: {path} | Estado: {estado}"
    except Exception as exc:
        return f"ERROR al generar tabla normativa DXF: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point para el MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
