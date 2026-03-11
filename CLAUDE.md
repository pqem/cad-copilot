# CLAUDE.md — CAD Copilot

## Qué es este proyecto
**Cadista IA** — asistente de documentación CAD para arquitectura argentina.
El usuario es un **arquitecto matriculado argentino (CPTN Neuquén)** en Plottier, Neuquén.

### Flujo principal (PIVOTE — no genera planos desde cero)
1. El arquitecto **diseña manualmente** en AutoCAD (o software CAD)
2. Exporta/convierte a DXF
3. **cad-copilot LEE el DXF** y lo analiza (muros, espacios, aberturas)
4. **AGREGA documentación**: cotas, tablas de normas, referencias, cartela
5. La herramienta **crece incrementalmente** — el usuario le enseña tareas nuevas

### Importante
- NO copiar layers/nombres del plano del usuario — usar convención profesional (AIA/IRAM)
- Los espesores de muro varían según cada obra — no asumir valores fijos
- El tipo de obra (casa, comercio, etc.) no cambia el flujo de trabajo
- El módulo de generación desde JSON (Fases 1-3) sigue siendo útil como motor auxiliar

## Stack
- **Python 3.12** con **uv** como package manager
- **ezdxf >=1.4** — lectura/escritura DXF sin AutoCAD (MIT, headless)
- **Pydantic v2** — validación de schemas con defaults inteligentes
- **Shapely >=2.0** — cálculos geométricos 2D (áreas, centroides)
- **FastMCP** — MCP server para integración con Claude Code
- **pytest + ruff** — testing y linting (dev dependencies)
- **Build system:** hatchling con src layout

## Comandos esenciales
```bash
uv sync                    # Instalar dependencias
uv run pytest              # 294 tests
uv run pytest -x -q        # Quick test
uv run ruff check src/     # Lint
uv run python -m cad_copilot.engine.renderer templates/vivienda_simple.json output/test.dxf
```

## Arquitectura del código

### `src/cad_copilot/schemas/` — Modelos Pydantic v2
| Archivo | Modelo principal | Descripción |
|---------|-----------------|-------------|
| `base.py` | `Point2D`, `Unit` | Tipos base (tuple[float,float], enum metros/mm) |
| `wall.py` | `Wall`, `WallClassification` | Muro con start/end/thickness/openings, 4 clasificaciones |
| `opening.py` | `Opening`, `OpeningType`, `OpeningMechanism` | Puerta/ventana con defaults condicionales por tipo |
| `space.py` | `Space`, `SpaceFunction` | Ambiente con bounded_by (list de wall IDs), 13 funciones |
| `annotation.py` | `DimensionConfig`, `AnnotationConfig` | Configuración de cotas y anotaciones |
| `layout.py` | `PaperConfig`, `TitleBlock`, `PaperSize`, `Orientation` | Papel A0-A4, márgenes, cartela CPTN |
| `project.py` | `FloorPlan` | Modelo raíz que compone todo |
| `terrain.py` | `Terrain` | FOS/FOT, retiros, zonificación, alturas |

### `src/cad_copilot/standards/` — Normas IRAM/AIA
| Archivo | Función | Qué configura |
|---------|---------|---------------|
| `layers.py` | `setup_layers(doc)` | 17 layers AIA (A-WALL, A-DOOR, A-GLAZ, A-ANNO-DIMS...) |
| `dimstyles.py` | `setup_dimstyles(doc, scale)` | Estilo IRAM_ARQ con DIMSCALE según escala |
| `textstyles.py` | `setup_textstyles(doc)` | 4 estilos: Standard, Titulo, Cotas, Notas |
| `linetypes.py` | `verify_linetypes(doc)` | CENTER, DASHED, PHANTOM, DASHDOT + aliases |
| `norms.py` | Motor normativo | Iluminación, ventilación, áreas mínimas, FOS/FOT (Ord. 7811/456) |

### `src/cad_copilot/blocks/` — 14 bloques paramétricos
| Archivo | Bloques | Naming |
|---------|---------|--------|
| `doors.py` | hinged, sliding, double_hinged | `DOOR_HINGED_090`, `DOOR_SLIDING_080`... |
| `windows.py` | sliding, hinged, fixed | `WIN_SLIDING_150`, `WIN_FIXED_120`... |
| `fixtures.py` | toilet, sink, shower, bidet, kitchen_sink | `FIX_TOILET`, `FIX_SHOWER_090`... |
| `symbols.py` | north_arrow, level_mark | `SYM_NORTH`, `SYM_LEVEL` |

### `src/cad_copilot/engine/` — Motor de generación
| Archivo | Función principal | Qué hace |
|---------|-------------------|----------|
| `document.py` | `create_document(scale=50)` | Crea doc DXF R2013, INSUNITS=6 (metros), aplica standards |
| `walls.py` | `draw_walls(msp, walls)` | LWPOLYLINE cerrado + HATCH |
| `openings.py` | `draw_openings(doc, msp, walls)` | Posiciona bloques rotados según ángulo del muro |
| `spaces.py` | `add_space_labels(msp, spaces, walls)` | MTEXT con nombre + superficie m² en centroide (Shapely) |
| `annotations.py` | `add_wall_dimensions(msp, walls)` | Cadena de cotas aligned + cotas internas de aberturas |
| `layout.py` | `create_layout()` + `add_title_block()` | Paper Space con viewport escalado + cartela CPTN |
| `norm_table.py` | Tabla DXF formateada | Tabla de verificación normativa en Paper Space |
| `renderer.py` | `render_floor_plan(floor_plan, path)` | Orquestador: JSON→doc→walls→openings→spaces→dims→layout→save |

### `src/cad_copilot/mcp_server/` — FastMCP Server
- Config: `.mcp.json` → `uv run cad-copilot-mcp` (stdio)
- 15 tools total:
  - Generación: generate_dxf, generate_dxf_temp, validate_floor_plan, list_available_blocks, get_floor_plan_schema, get_example_floor_plan, calculate_norms, generate_norm_table_dxf_tool
  - Lectura (Fase 4): read_dxf, detect_elements, suggest_missing, add_dimensions_tool, add_norm_table_tool, add_title_block_tool, document_dxf

## Convenciones de código
- Unidades en Model Space: **metros** (INSUNITS=6)
- Unidades en Paper Space: **milímetros**
- Escala por defecto: 1:50
- DXF version: R2013 (AC1027) para máxima compatibilidad con AutoCAD
- Layers siguen convención AIA: `A-WALL`, `A-DOOR`, `A-GLAZ`, `A-ANNO-DIMS`, `A-ANNO-TEXT`, `A-ANNO-TTLB`
- Dimstyle: `IRAM_ARQ` (flechas oblicuas, texto sobre línea, factor 1000 para mostrar mm)
- Idioma del código: inglés (variables, funciones). Docstrings y comentarios: español
- Ruff line-length: 100

## Principios de diseño
1. **LLM NUNCA calcula** — Python + Shapely hacen todos los cálculos determinísticos
2. **Leer antes de escribir** — analizar el DXF existente antes de modificar
3. **Convenciones profesionales** — layers AIA/IRAM, no copiar arbitrariamente del usuario
4. **Bloques paramétricos** — width como parámetro, el bloque se crea a medida
5. **Defaults inteligentes** — puertas default 2.10m alto, ventanas 1.10m alto y 0.90m antepecho
6. **Crecimiento incremental** — el usuario enseña tareas nuevas progresivamente

## Estado actual (Fases 1-4 completadas, 494 tests)
- Fase 1: Motor DXF completo ✅
- Fase 2: MCP Server (6 tools) ✅ — PR #1 merged
- Fase 3: Motor de normas municipales ✅ — PR #2 merged
- Fase 4: Lector de DXF + documentador ✅ — 200 tests nuevos

## Fase 4: Lector de DXF y Documentador (COMPLETADA)

### `reader/` — Lector/analizador de DXF existentes
| Archivo | Función | Qué hace |
|---------|---------|----------|
| `analyzer.py` | `analyze_dxf(path)` | Metadata, layers, bloques, stats, bounding box |
| `wall_detector.py` | `detect_walls(doc)` | LWPOLYLINE rectangulares + pares LINE paralelas |
| `opening_detector.py` | `detect_openings(doc)` | INSERTs por nombre + bloques con ARC |
| `space_detector.py` | `detect_spaces(doc)` | TEXT/MTEXT con nombres de ambientes |
| `dimension_detector.py` | `detect_dimensions(doc)` | DIMENSION entities con valores |

### `documenter/` — Motor de documentación sobre DXF existente
| Archivo | Función | Qué hace |
|---------|---------|----------|
| `suggestions.py` | `analyze_completeness()` | Score de documentación + sugerencias |
| `auto_dimensions.py` | `add_missing_dimensions()` | Cotas IRAM_ARQ a muros no cotados |
| `norm_compliance.py` | `calculate_norms_from_detected()` | Tabla normas desde espacios detectados |
| `title_block.py` | `add_title_block_to_existing()` | Cartela CPTN en Paper Space |

### `schemas/detection.py` — Modelos Pydantic para detección
- DxfAnalysis, DetectedWall, DetectedOpening, DetectedSpace, DetectedDimension
- DetectionResult, SuggestionReport, Suggestion

## Herramientas CAD en el NUC (Linux)
- **QCAD 3.32.6**: `/opt/qcad-3.32.6-trial-linux-x86_64/` — DWG→DXF, visualización
- **FreeCAD 1.0.2**: flatpak — Python-scriptable, Draft 2D
- Conversión DWG→DXF: vía QCAD con script ECMAScript custom

## Samples
- `samples/Figueroa.dxf` — 7.6MB, 30,514 entidades, convertido desde DWG del usuario
- `templates/vivienda_simple.json` — Casa 6x4m de ejemplo para el motor generador

## Documentación de referencia
- `PRD.md` — PRD completo (96/100) con 29 requerimientos funcionales
- `debate/SINTESIS-DEBATE.md` — Síntesis del debate 3-IA sobre arquitectura
- `research/mcp-cad-servers-analysis.md` — Análisis de MCP servers CAD existentes
