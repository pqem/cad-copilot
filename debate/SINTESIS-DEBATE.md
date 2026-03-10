# Síntesis del Debate: Arquitectura del Copiloto CAD

**Fecha:** 2026-03-10
**Participantes:** Claude (opus-4.6), Gemini (3.1-pro), Codex (gpt-5.3-codex)

---

## Matriz de Posiciones por Eje

### 1. CONEXIÓN CON AUTOCAD

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Mecanismo | MCP Server en Windows | MCP Server en Windows | **ACUERDO** |
| Transporte | Implícito (HTTP?) | WebSocket bidireccional | **Claude gana**: necesitamos notificaciones push desde AutoCAD |
| Ejecución en AutoCAD | SendStringToExecute / .NET | COM (pyautocad) + LISP como capa interna | **Complementarios** |
| Plugin nativo | Descartado | Descartado | **ACUERDO** |
| BricsCAD Linux | No mencionado | Camino futuro viable | **Buena previsión** |

Codex agrega: protocolo **idempotente** con `job_id`, cola persistente, ACK/reintentos. Comandos atómicos (`create_layer`, `draw_wall`, `annotate_dim`).

**DECISIÓN: MCP Server Python en Windows con WebSocket bidireccional. COM/pyautocad como interfaz con AutoCAD. Protocolo idempotente (aporte Codex). BricsCAD Linux como plan B futuro.**

---

### 2. GENERACIÓN DXF

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Motor principal | ezdxf offline | ezdxf offline | **ACUERDO total** |
| COM en vivo | Para modificaciones puntuales | Para queries + modificaciones | **ACUERDO** |
| Flujo | Genera DXF → inserta en AutoCAD | Genera DXF → DXFIN/INSERT → usuario ajusta | **ACUERDO** |
| Performance | "Celeron sufrirá con COM" | "<100ms con ezdxf vs 5-10s COM" | **Datos sólidos de Claude** |

Codex agrega: flujo **"plan → diff → apply"** con snapshot DXF antes/después y reconciliación por handles/capas para evitar divergencia entre lo generado y el estado real del dibujo.

**DECISIÓN: ezdxf en Linux genera DXF completos. COM solo para queries y modificaciones puntuales. Workflow atómico + reconciliación por diff (aporte Codex).**

---

### 3. FORMATO INTERMEDIO

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Formato | JSON con schema estricto | JSON con Pydantic | **ACUERDO** |
| Vocabulario | `wall`, `function: exterior` | `wall`, `classification: exterior_portante` | **Claude más detallado** |
| Spaces | No explícito | Entidad de primer nivel | **Claude gana**: fundamental para normas |
| Openings | Entidad independiente | Anidados en walls | **Claude gana**: semánticamente correcto |
| Validación | Pydantic | Pydantic + Shapely topológico | **Claude más robusto** |
| DSL propio | No mencionado | Descartado explícitamente | **ACUERDO** |
| Python directo | No mencionado | Descartado (seguridad) | **ACUERDO** |

**DECISIÓN: JSON con Pydantic v2. Vocabulario arquitectónico con `wall`, `space`, `opening`. Spaces como entidades de primer nivel. Openings anidados en walls. Validación topológica con Shapely.**

---

### 4. APRENDIZAJE DE PLANOS

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Enfoque | RAG + LanceDB vectorial | Análisis determinístico + filesystem | **DESACUERDO principal** |
| Layers/estilos | Extraer de DXF | Extraer de DXF (igual) | **ACUERDO** |
| Bloques | En base vectorial | Archivos DXF individuales en filesystem | **Claude más pragmático** |
| Templates | "Template de Contexto" | Jinja2 parametrizados por tipología | **Claude más concreto** |
| Búsqueda futura | LanceDB | FTS (Tantivy/SQLite) si hace falta | **Claude más apropiado para datos estructurados** |

Codex agrega: **score de calidad por archivo** para no contaminar con planos legacy, clustering por tipo de proyecto, y "style profile" con revisión humana y reglas bloqueantes.

**DECISIÓN: Enfoque de Claude + filtro de Codex. Análisis determinístico de DXF existentes → `user_conventions.json`. Bloques exportados a filesystem. Templates Jinja2 por tipología. Score de calidad para filtrar planos legacy (aporte Codex). RAG vectorial solo si escala a 200+ planos (futuro lejano).**

Razón: los datos de un plano CAD son estructurados (layers, bloques, estilos), no texto libre. Un JSON con convenciones es más preciso, reproducible y debuggeable que embeddings vectoriales.

---

### 5. STACK Y UX

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Interfaz principal | CLI (Claude Code) | CLI (Claude Code) | **ACUERDO** |
| Preview | SVG en browser | Canvas 2D interactivo (Vite) | **Claude gana**: zoom/pan/click es esencial |
| Next.js | No | No (SSR innecesario, Celeron sufre) | **ACUERDO** |
| Interactividad | Abrir imagen/browser | WebSocket push + click → referencia ID | **Claude más rico** |

**DECISIÓN: Claude Code como interfaz principal. Preview web con Vite + Canvas 2D (zoom, pan, click para referenciar). Sin Next.js. El preview es borrador, AutoCAD es el plano final.**

---

### 6. NORMAS Y CÁLCULOS

| Aspecto | Gemini | Claude | Consenso |
|---------|--------|--------|----------|
| Principio | LLM NO calcula, Python calcula | LLM NO calcula, Python calcula | **ACUERDO total** |
| Estructura | `normas_neuquen.json` | Módulos Python por jurisdicción/norma | **Claude más escalable** |
| Geometría | Shapely | Shapely | **ACUERDO** |
| Tests | No detallado | Tests con planos reales aprobados | **Claude excelente idea** |
| Trazabilidad | No detallado | Cada verificación cita artículo/norma | **Fundamental para responsabilidad profesional** |
| Versionado | No detallado | Fecha de vigencia por norma | **Necesario** |

**DECISIÓN: Motor de normas 100% Python determinístico. Módulos por jurisdicción (Neuquén) y norma (IRAM). Shapely para geometría. Trazabilidad con cita de artículo/norma. Tests con planos reales ya aprobados como ground truth.**

---

## ARQUITECTURA FINAL CONSENSUADA

```
╔══════════════════════════════════════════════════════════╗
║                    LINUX (NUC)                           ║
║                                                          ║
║  ┌──────────────────────────────────────────────────┐   ║
║  │  Claude Code (orquestador / lenguaje natural)     │   ║
║  └──────────────┬───────────────────────────────────┘   ║
║                 │                                        ║
║                 ▼                                        ║
║  ┌──────────────────────────────────────────────────┐   ║
║  │  JSON Semántico (Pydantic v2 validated)           │   ║
║  │  Vocabulario: wall, space, opening, annotation    │   ║
║  └──────┬──────────┬──────────────┬─────────────────┘   ║
║         │          │              │                      ║
║         ▼          ▼              ▼                      ║
║  ┌──────────┐ ┌──────────┐ ┌─────────────────────┐     ║
║  │Motor     │ │Motor     │ │Preview Server       │     ║
║  │Normas    │ │Dibujo    │ │(uvicorn+WebSocket)  │     ║
║  │(Shapely) │ │(ezdxf)   │ │                     │     ║
║  └──────────┘ └────┬─────┘ └──────────┬──────────┘     ║
║                    │                   │                 ║
║                    ▼                   ▼                 ║
║              archivo.dxf      Browser (Canvas 2D)       ║
║                    │          zoom/pan/click             ║
╚════════════════════╪════════════════════════════════════╝
                     │  WebSocket bidireccional (LAN)
                     ▼
╔══════════════════════════════════════════════════════════╗
║                    WINDOWS                               ║
║                                                          ║
║  ┌──────────────────────────────────────────────────┐   ║
║  │  MCP Server Python                                │   ║
║  │  ├── DXFIN / INSERT (importar DXF generados)     │   ║
║  │  ├── Query (leer selección, medidas)              │   ║
║  │  ├── Modify (mover, cambiar layer)                │   ║
║  │  └── Watch (notificar cambios del usuario)        │   ║
║  └──────────────────┬───────────────────────────────┘   ║
║                     │ COM / pyautocad                    ║
║                     ▼                                    ║
║               ┌──────────┐                               ║
║               │ AutoCAD  │                               ║
║               └──────────┘                               ║
╚══════════════════════════════════════════════════════════╝
```

## STACK TECNOLÓGICO DEFINITIVO

| Componente | Tecnología | Justificación |
|-----------|-----------|---------------|
| Orquestador | Claude Code + MCP | Nativo, ya instalado |
| Formato intermedio | JSON + Pydantic v2 | Tipado, validable, LLMs lo generan bien |
| Generación DXF | Python 3.12 + ezdxf 1.4 | MIT, maduro, <100ms por plano |
| Geometría/cálculos | Shapely | Estándar 2D, áreas, intersecciones |
| Motor de normas | Python puro + JSON params | Determinístico, testeable |
| Preview backend | uvicorn + websockets | Mínimo, async |
| Preview frontend | Vite + Canvas 2D | <50KB, sin framework pesado |
| MCP Server (Win) | Python + pyautocad + mcp | Bridge COM ↔ MCP |
| Templates | Jinja2 | Planos parametrizados por tipología |
| Convenciones | JSON extraído de DXF del usuario | Determinístico, editable |
| Bloques | Archivos DXF en filesystem | Simples, versionables en git |
| Tests | pytest + planos reales aprobados | Ground truth del municipio |

## FASES DE IMPLEMENTACIÓN

### Fase 1: Motor de Dibujo (semana 1-2)
- Setup proyecto Python con ezdxf
- Definir JSON Schema con Pydantic (wall, space, opening)
- Motor que traduce JSON → DXF con layers IRAM
- Bloques básicos: puerta abatible, ventana, sanitarios
- Cartela con datos CPTN

### Fase 2: Integración Claude Code (semana 3-4)
- MCP Server local (Linux) como tool de Claude Code
- Claude interpreta lenguaje natural → genera JSON → motor genera DXF
- Preview web con Canvas 2D

### Fase 3: Motor de Normas (semana 5-6)
- Cálculo de superficies con Shapely
- FOS/FOT según zona de Neuquén
- Tabla de iluminación/ventilación automática
- Tests con planos reales

### Fase 4: Aprendizaje (semana 7-8)
- Extractor de convenciones de DXF existentes
- Exportar bloques del usuario a biblioteca
- Templates Jinja2 por tipología

### Fase 5: Conexión AutoCAD (semana 9-10)
- MCP Server en Windows con pyautocad
- WebSocket bridge Linux ↔ Windows
- Import DXF en AutoCAD, queries, modificaciones

### Fase 6: Refinamiento continuo
- Más tipologías y normas IRAM
- Más bloques paramétricos
- Optimización del flujo de trabajo
