# Resumen: MCP Servers CAD existentes — Qué sirve y qué no

## Los 3 repos más útiles

### 1. puran-water/autocad-mcp (170 stars) — PATRÓN DE BACKEND
- **Doble backend**: File IPC (Windows) + **ezdxf headless (Linux)**
- 8 tools consolidados, 232 tests
- Especializado en P&ID pero la arquitectura es excelente
- **Lo que nos sirve**: El patrón de dual backend es exactamente nuestro diseño. Podemos estudiar cómo implementaron el switch auto/file_ipc/ezdxf

### 2. AnCode666/multiCAD-mcp — REFERENCIA DE API
- **46 tools MCP** organizados en categorías
- Soporta 4 CADs: AutoCAD, ZWCAD, GstarCAD, BricsCAD
- Python + COM (solo Windows)
- **Lo que nos sirve**: La mejor referencia de API de tools. Copiar la estructura de categorías (drawing, layer, entity, block, annotation, file)

### 3. thepiruthvirajan/autocad-mcp-server (27 stars) — INSPIRACIÓN ARQUITECTÓNICA
- Crea muros, puertas, ventanas, habitaciones directamente
- Gestión inteligente de layers (WALLS, DOORS, WINDOWS, ANNOTATION)
- Etiquetado automático
- **Lo que nos sirve**: Es el único que piensa en "muros" y "puertas", no solo en "líneas". Validar su approach de grosor dinámico para muros

## Patrón brillante descubierto

### lgradisar/archicad-mcp — SCRIPT-FIRST
- Solo **4 tools MCP**, pero uno es `execute_script`
- El LLM genera Python completo y lo ejecuta
- Máxima flexibilidad, mínima complejidad del server
- **Idea para nosotros**: Combinar tools de alto nivel (draw_wall, add_door) + un `execute_ezdxf_script` para operaciones complejas que no encajan en tools predefinidos

## Lo que NO sirve directamente

| Repo | Por qué no |
|------|-----------|
| pyautocad | Abandonado, COM failures con AutoCAD 2025 |
| daobataotie/CAD-MCP | Muy básico, solo primitivas |
| Easy-MCP-AutoCad | Abandonado |
| ahmetcemkaraca/AutoCAD_MCP | 7 tools production, 25 WIP, demasiado inmaduro |

## Hallazgo clave: EL GAP ES ENORME

Ningún repo existente tiene:
- Bloques arquitectónicos (puertas, ventanas, sanitarios)
- Cartela/rótulo automatizado
- Cálculo de superficies, FOS/FOT
- Validación de normas IRAM
- Templates de planos (planta, corte, fachada)
- Capas arquitectónicas estándar
- Escala de plano configurada

**Nadie ha hecho un MCP server específico para arquitectura 2D.**
