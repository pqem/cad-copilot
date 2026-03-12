# CAD Copilot

> **En desarrollo activo** — Este proyecto es experimental y open source. Las APIs, schemas y herramientas pueden cambiar. Contribuciones, ideas y feedback son bienvenidos via [issues](https://github.com/pqem/cad-copilot/issues).

Asistente de documentación CAD para arquitectura argentina. Lee planos DXF existentes y agrega documentación profesional: cotas IRAM, tablas de verificación normativa, y cartela CPTN. También puede generar planos 2D desde JSON.

No requiere AutoCAD ni licencias comerciales — funciona 100% headless con [ezdxf](https://ezdxf.mozman.at/).

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)

## Instalación

```bash
git clone git@github.com:pqem/cad-copilot.git
cd cad-copilot
uv sync
```

## Uso

### 1. Generar un plano DXF desde JSON

```bash
# Usar el template de ejemplo incluido
uv run cad-copilot templates/vivienda_simple.json output/plano.dxf

# O crear tu propio JSON (ver sección Schema más abajo)
uv run cad-copilot mi_plano.json output/mi_plano.dxf
```

### 2. Como MCP Server (integración con Claude Code)

```bash
# Agregar el server a Claude Code
claude mcp add cad-copilot -- uv run --directory /ruta/a/cad-copilot cad-copilot-mcp

# O desde el directorio del proyecto, Claude Code detecta .mcp.json automáticamente
```

El MCP server expone 15 herramientas:

| Herramienta | Descripción |
|-------------|-------------|
| `generate_dxf` | Genera DXF completo desde JSON |
| `generate_dxf_temp` | Genera DXF en directorio temporal |
| `validate_floor_plan` | Valida JSON sin generar |
| `list_available_blocks` | Lista bloques paramétricos disponibles |
| `get_floor_plan_schema` | Devuelve el JSON Schema completo |
| `get_example_floor_plan` | Devuelve un JSON de ejemplo funcional |
| `calculate_norms` | Verifica cumplimiento normativo |
| `generate_norm_table_dxf_tool` | Genera tabla de normas como DXF |
| `read_dxf` | Analiza un DXF existente (metadata, layers, stats) |
| `detect_elements` | Detecta muros, aberturas y espacios en un DXF |
| `suggest_missing` | Identifica documentación faltante |
| `add_dimensions_tool` | Agrega cadenas de cotas IRAM a muros |
| `add_norm_table_tool` | Agrega tabla de verificación normativa |
| `add_title_block_tool` | Agrega cartela CPTN |
| `document_dxf` | Documentación completa de un DXF (detect + cotas + tabla + cartela) |

### 3. Documentar un DXF existente (flujo principal)

Usando el MCP server desde Claude Code:

1. **Analizar**: `read_dxf` para ver qué tiene el plano
2. **Detectar**: `detect_elements` para identificar muros/aberturas/espacios
3. **Evaluar**: `suggest_missing` para ver qué documentación le falta
4. **Documentar**: `document_dxf` para agregar todo de una vez, o usar las herramientas individuales (`add_dimensions_tool`, `add_norm_table_tool`, `add_title_block_tool`)

## Schema del JSON

El JSON de entrada sigue el modelo `FloorPlan`:

```json
{
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
          "position_along_wall": 1.0
        }
      ]
    }
  ],
  "spaces": [
    {
      "name": "LIVING",
      "function": "living",
      "bounded_by": ["w1"]
    }
  ],
  "paper_config": {
    "size": "A3",
    "orientation": "landscape",
    "scale": 50
  },
  "title_block": {
    "project": "VIVIENDA UNIFAMILIAR",
    "drawing_name": "PLANTA BAJA",
    "professional": "ARQ. NOMBRE",
    "license_number": "CPTN 1234"
  }
}
```

### Clasificaciones de muro
`exterior_portante`, `exterior_no_portante`, `interior`, `medianero`

### Tipos de abertura
- **type**: `door`, `window`
- **mechanism**: `hinged`, `sliding`, `fixed`, `double_hinged`

### Funciones de espacio
`living`, `comedor`, `dormitorio`, `cocina`, `bano`, `lavadero`, `garage`, `pasillo`, `hall`, `estar`, `escritorio`, `deposito`, `otro`

## Para ver los DXF generados

Cualquier visor DXF compatible con R2013 (AC1027):
- [QCAD](https://qcad.org) (Linux/Mac/Windows)
- [LibreCAD](https://librecad.org)
- AutoCAD / BricsCAD
- Visor online: [ShareCAD](https://sharecad.org)

## Tests

```bash
uv run pytest              # 494 tests
uv run pytest -x -q        # Quick (para en el primer error)
uv run ruff check src/     # Lint
```

## Convenciones técnicas

- **Unidades Model Space**: metros (INSUNITS=6)
- **Unidades Paper Space**: milímetros
- **Escala por defecto**: 1:50
- **Layers**: convención AIA (`A-WALL`, `A-DOOR`, `A-GLAZ`, `A-ANNO-DIMS`, etc.)
- **Cotas**: estilo `IRAM_ARQ` (flechas oblicuas, texto sobre línea)
- **14 bloques paramétricos**: puertas (3), ventanas (3), artefactos sanitarios (5), símbolos (2)

## Stack

| Dependencia | Versión | Para qué |
|-------------|---------|----------|
| [ezdxf](https://ezdxf.mozman.at/) | >=1.4 | Lectura/escritura DXF sin AutoCAD |
| [Pydantic](https://docs.pydantic.dev/) | v2 | Validación de schemas JSON |
| [Shapely](https://shapely.readthedocs.io/) | >=2.0 | Cálculos geométricos (áreas, centroides) |
| [FastMCP](https://github.com/jlowin/fastmcp) | >=1.0 | MCP server para Claude Code |

## Estado del proyecto

El proyecto tiene 4 fases completadas y 494 tests pasando:

| Fase | Qué incluye | Estado |
|------|-------------|--------|
| 1 | Motor DXF (muros, aberturas, espacios, cotas, layout, bloques) | Completa |
| 2 | MCP Server (6 tools de generación) | Completa |
| 3 | Motor de normas municipales (iluminación, ventilación, FOS/FOT) | Completa |
| 4 | Lector de DXF existentes + documentador automático (7 tools) | Completa |

### Roadmap abierto

- Plugin para AutoCAD (ver abajo)
- Soporte para más tipos de planos (cortes, fachadas)
- Detección de artefactos sanitarios en DXF existentes
- Aprendizaje incremental del estilo del usuario
- Integración con más normativas municipales argentinas

Si tenés ideas o encontrás bugs, abrí un [issue](https://github.com/pqem/cad-copilot/issues).

## Uso con AutoCAD

### Flujo actual (sin plugin)

Los DXF generados son formato R2013 (AC1027), compatibles con AutoCAD 2013+:

1. Diseñás en AutoCAD como siempre
2. **Guardar como → DXF**
3. cad-copilot documenta el archivo (cotas, tabla de normas, cartela)
4. Abrís el resultado en AutoCAD — todo queda editable con layers AIA

### Plugin para AutoCAD (pendiente)

Todavía no existe un plugin que permita usar cad-copilot desde dentro de AutoCAD. Estas son las opciones técnicas para quien quiera contribuir:

| Opción | Cómo funciona | Requisitos | Complejidad |
|--------|---------------|------------|-------------|
| **AutoLISP** | Script `.lsp` que exporta DXF, llama a cad-copilot via shell, y recarga el resultado | AutoCAD + Python instalado en la misma máquina | Baja |
| **pyautocad (COM)** | Python controla AutoCAD abierto via COM Automation — puede leer/escribir entidades en vivo | Windows + AutoCAD + [pyautocad](https://pypi.org/project/pyautocad/) | Media |
| **Plugin .NET** | Plugin compilado con ObjectARX/C# que corre dentro de AutoCAD como comando nativo | Windows + Visual Studio + AutoCAD SDK | Alta |
| **HTTP bridge** | cad-copilot corre como servidor HTTP local; un script AutoLISP/PyAutoCAD le envía requests | Cualquier OS con AutoCAD | Media |

#### Ejemplo: integración mínima con AutoLISP

Un `.lsp` que exporta el dibujo actual, lo documenta, y lo recarga:

```lisp
(defun c:CADCOPILOT ()
  ; Exportar dibujo actual como DXF temporal
  (setq dxf_path (strcat (getenv "TEMP") "\\cadcopilot_input.dxf"))
  (setq out_path (strcat (getenv "TEMP") "\\cadcopilot_output.dxf"))
  (command "_.SAVEAS" "DXF" dxf_path)

  ; Llamar a cad-copilot para documentar
  (startapp "cmd" (strcat "/c uv run --directory C:\\ruta\\cad-copilot cad-copilot-mcp"))
  ;; TODO: invocar document_dxf via MCP o CLI directo

  ; Abrir resultado
  (command "_.OPEN" out_path)
  (princ "\nCAD Copilot: documentación aplicada.")
  (princ)
)
```

> Este es un esqueleto ilustrativo. Si querés implementar la integración con AutoCAD, abrí un [issue](https://github.com/pqem/cad-copilot/issues) para coordinar.

## Contribuir

```bash
git clone git@github.com:pqem/cad-copilot.git
cd cad-copilot
uv sync
uv run pytest          # verificar que todo pasa
uv run ruff check src/ # lint
```

El código fuente está en `src/cad_copilot/`. Los tests en `tests/`. PRs bienvenidos.

## Licencia

MIT
