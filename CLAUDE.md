# CLAUDE.md — CAD Copilot

## Qué es este proyecto
Copiloto CAD arquitectónico que genera planos 2D DXF profesionales desde JSON semántico.
El usuario es un **arquitecto matriculado argentino (CPTN Neuquén)** que necesita acelerar el dibujo de planos municipales y ejecutivos.

**Flujo principal:** JSON con vocabulario arquitectónico → Pydantic v2 validation → ezdxf → DXF R2013

## Stack
- **Python 3.12** con **uv** como package manager
- **ezdxf >=1.4** — generación DXF sin AutoCAD (MIT, headless)
- **Pydantic v2** — validación de schemas con defaults inteligentes
- **Shapely >=2.0** — cálculos geométricos 2D (áreas, centroides)
- **pytest + ruff** — testing y linting (dev dependencies)
- **Build system:** hatchling con src layout

## Comandos esenciales
```bash
uv sync                    # Instalar dependencias
uv run python -m cad_copilot.engine.renderer templates/vivienda_simple.json output/test.dxf  # Test E2E
uv run pytest              # Tests (pendientes de crear)
uv run ruff check src/     # Lint
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

### `src/cad_copilot/standards/` — Normas IRAM/AIA
| Archivo | Función | Qué configura |
|---------|---------|---------------|
| `layers.py` | `setup_layers(doc)` | 17 layers AIA (A-WALL, A-DOOR, A-GLAZ, A-ANNO-DIMS...) |
| `dimstyles.py` | `setup_dimstyles(doc, scale)` | Estilo IRAM_ARQ con DIMSCALE según escala |
| `textstyles.py` | `setup_textstyles(doc)` | 4 estilos: Standard, Titulo, Cotas, Notas |
| `linetypes.py` | `verify_linetypes(doc)` | CENTER, DASHED, PHANTOM, DASHDOT + aliases |

### `src/cad_copilot/blocks/` — 14 bloques paramétricos
| Archivo | Bloques | Naming |
|---------|---------|--------|
| `doors.py` | hinged, sliding, double_hinged | `DOOR_HINGED_090`, `DOOR_SLIDING_080`... |
| `windows.py` | sliding, hinged, fixed | `WIN_SLIDING_150`, `WIN_FIXED_120`... |
| `fixtures.py` | toilet, sink, shower, bidet, kitchen_sink | `FIX_TOILET`, `FIX_SHOWER_090`... |
| `symbols.py` | north_arrow, level_mark | `SYM_NORTH`, `SYM_LEVEL` |

Todos los bloques usan layer "0" para heredar del INSERT. Guard: `if name in doc.blocks: return name`.

### `src/cad_copilot/engine/` — Motor de generación
| Archivo | Función principal | Qué hace |
|---------|-------------------|----------|
| `document.py` | `create_document(scale=50)` | Crea doc DXF R2013, INSUNITS=6 (metros), aplica standards |
| `walls.py` | `draw_walls(msp, walls)` | LWPOLYLINE cerrado + HATCH (SOLID exterior, ANSI31 medianera) |
| `openings.py` | `draw_openings(doc, msp, walls)` | Posiciona bloques rotados según ángulo del muro |
| `spaces.py` | `add_space_labels(msp, spaces, walls)` | MTEXT con nombre + superficie m² en centroide (Shapely) |
| `annotations.py` | `add_wall_dimensions(msp, walls)` | Cadena de cotas aligned + cotas internas de aberturas |
| `layout.py` | `create_layout()` + `add_title_block()` | Paper Space con viewport escalado + cartela CPTN 8 atributos |
| `renderer.py` | `render_floor_plan(floor_plan, path)` | **Orquestador**: JSON→doc→walls→openings→spaces→dims→layout→save |

### `templates/` — JSON de prueba
- `vivienda_simple.json` — Casa 6x4m, 5 muros, 2 puertas, 2 ventanas, 2 ambientes, cartela CPTN

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
2. **JSON semántico** — vocabulario arquitectónico (wall/space/opening), NO geometría cruda
3. **Bloques paramétricos** — width como parámetro, el bloque se crea a medida
4. **Defaults inteligentes** — puertas default 2.10m alto, ventanas 1.10m alto y 0.90m antepecho
5. **Dual backend futuro** — ezdxf headless (Linux) + COM/pyautocad (Windows) planificado

## Estado actual (Fase 1 completada)
- Todos los módulos implementados y funcionando
- Test E2E: `vivienda_simple.json` genera DXF con 31 entidades correctamente
- **Pendiente:** tests unitarios en `tests/`, verificación visual en LibreCAD/AutoCAD

## Fases futuras (referencia)
- **Fase 2:** MCP Server — conectar con Claude Code como herramienta
- **Fase 3:** Motor de normas IRAM — cálculos de iluminación, ventilación, FOS/FOT
- **Fase 4:** Aprendizaje de DXF existentes — extraer convenciones del usuario
- **Fase 5:** Conexión Windows — COM/pyautocad para AutoCAD en vivo

## Documentación de referencia
- `PRD.md` — PRD completo (96/100) con 29 requerimientos funcionales
- `debate/SINTESIS-DEBATE.md` — Síntesis del debate 3-IA sobre arquitectura
- `research/mcp-cad-servers-analysis.md` — Análisis de MCP servers CAD existentes
- `.claude/session-plan.md` — Plan de ejecución de 10 pasos (Fase 1)
- `.claude/session-intent.md` — Contrato de intención del proyecto
