# Investigacion Exhaustiva: MCP Servers para CAD
**Fecha:** 2026-03-10
**Proyecto:** cad-copilot - Copiloto CAD Arquitectonico
**Objetivo:** Evaluar repos existentes como base/inspiracion para conectar Claude Code con AutoCAD para planos 2D

---

## Tabla de Resumen Comparativo

| Repo | Lenguaje | Conexion CAD | Tools MCP | Multi-CAD | Linux | Estado | Utilidad para nosotros |
|------|----------|-------------|-----------|-----------|-------|--------|----------------------|
| AnCode666/multiCAD-mcp | Python | COM (Windows) | ~46 | Si (4 CADs) | No | Activo | ALTA - mejor base |
| puran-water/autocad-mcp | Python | File IPC + ezdxf | 8 consolidados | No (solo AutoCAD LT) | Si (ezdxf) | Activo | ALTA - backend ezdxf |
| ngk0/autocad-mcp | Python | File IPC + ezdxf | 19 | No (solo AutoCAD LT) | Si (ezdxf) | Activo | ALTA - fork mejorado |
| ahmetcemkaraca/AutoCAD_MCP | Python | COM API | 7 production + 25 dev | No | No | Semi-activo | MEDIA - ideas avanzadas |
| daobataotie/CAD-MCP | Python | COM | Basicos (linea, circulo, arco, rectangulo, polylinea) | Si (3 CADs) | No | Activo | BAJA - muy basico |
| zh19980811/Easy-MCP-AutoCad | Python | COM | Basicos + SQLite | No | No | Abandonado | BAJA - concepto DB interesante |
| vigneshpbmenon/autocad-mcp-server | Python | Python automation | Basicos (linea, polilinea, rect, circulo, elipse, arco) | No | No | v0.1 alpha | BAJA - muy temprano |
| contextform/freecad-mcp | Python | FreeCAD API | Multiples | No (FreeCAD) | Si | Activo | MEDIA - patrones MCP |
| lgradisar/archicad-mcp | Python | Tapir JSON API | 4 (script-first) | No (ArchiCAD) | Parcial | Activo | MEDIA - arquitectura elegante |
| reclosedev/pyautocad | Python | COM (ActiveX) | N/A (libreria) | No | No | Abandonado | BAJA - referencia COM |
| ezdxf (mozman) | Python | DXF directo | N/A (libreria) | N/A | Si | Activo, v1.4.3 | CRITICA - dependencia clave |

---

## 1. AnCode666/multiCAD-mcp

**URL:** https://github.com/AnCode666/multiCAD-mcp
**Autor:** Andres Corbal (Espana)
**Lenguaje:** Python
**Licencia:** No especificada

### Que hace
MCP server que permite controlar software CAD a traves de asistentes IA como Claude Desktop o Cursor. Soporta multiples plataformas CAD.

### CADs soportados
- AutoCAD
- ZWCAD
- GstarCAD
- BricsCAD

### Conexion con CAD
- **Tecnologia COM** (Windows Component Object Model)
- Requiere Windows OS
- Usa `pywin32` para acceso a Windows API
- Arquitectura COM-based para control en tiempo real

### Tools MCP (~46 tools)
Organizados en categorias:
- **Drawing tools**: Dibujo de lineas, circulos, arcos, rectangulos, polilineas, etc.
- **Layer management**: Crear, modificar, eliminar capas, cambiar propiedades
- **Entity tools**: Manipulacion de entidades (mover, copiar, rotar, escalar, etc.)
- **File management**: Abrir, guardar, exportar archivos
- **Block tools**: Insercion y gestion de bloques
- **Annotation**: Texto, dimensiones, cotas

### Dependencias
- Python 3.10+
- pywin32 (COM access)
- pydantic (validacion de datos)
- mcp (SDK del protocolo)
- Modulo NLP custom con regex y keyword mapping

### Tecnologias clave
- Type hints completos
- Error handling comprehensivo
- NLP basico con regex para interpretar comandos en lenguaje natural

### Plataforma
- **Solo Windows** (depende de COM)
- No funciona en Linux/Mac

### Estado
- Activo, mantenido por el autor
- Documentacion buena en README

### Evaluacion para nuestro proyecto
**Utilidad: ALTA como inspiracion y posible base**
- La mejor cobertura de tools MCP para CAD 2D que existe
- Soporte multi-CAD es un patron excelente
- Limitacion critica: solo Windows/COM, no sirve directamente para Linux
- La estructura de tools (46 categorized) es el mejor modelo a seguir
- Podriamos replicar su API de tools pero con backend ezdxf para Linux

---

## 2. puran-water/autocad-mcp

**URL:** https://github.com/puran-water/autocad-mcp
**Autor:** Puran Water LLC
**Lenguaje:** Python
**Version:** v3.1

### Que hace
MCP server para AutoCAD LT con doble backend: File IPC para Windows y ezdxf headless para cualquier plataforma. Especializado en diagramas P&ID (Piping and Instrumentation).

### Conexion con CAD
**Dos backends:**

1. **File IPC Backend** (Windows):
   - Envia keystrokes a la ventana MDIClient de AutoCAD via `PostMessageW(WM_CHAR)`
   - Ejecuta comando AutoLISP `(c:mcp-dispatch)`
   - No roba foco de ventana (focus-free dispatch)
   - Requiere AutoCAD LT 2024+ (soporte AutoLISP agregado en LT 2024)

2. **ezdxf Headless Backend** (multiplataforma):
   - Funciona en Linux, macOS, WSL
   - Genera archivos DXF sin AutoCAD instalado
   - Generacion offline

### Configuracion de backend
Variable `AUTOCAD_MCP_BACKEND`:
- `auto` (default): intenta File IPC, fallback a ezdxf
- `file_ipc`: requiere AutoCAD
- `ezdxf`: solo headless

### Tools MCP (8 consolidados)
1. **drawing** - Dibujo de entidades
2. **entity** - Manipulacion de entidades
3. **layer** - Gestion de capas
4. **block** - Gestion de bloques
5. **annotation** - Texto y anotaciones
6. **pid** - Simbolos P&ID (600+ simbolos ISA 5.1-2009)
7. **view** - Control de vista
8. **system** - Operaciones del sistema (undo/redo)

### Funciones P&ID especializadas
- setup_layers, insert_symbol, list_symbols
- draw_process_line, connect_equipment
- add_flow_arrow, add_equipment_tag, add_line_number
- insert_valve, insert_instrument, insert_pump, insert_tank

### Features adicionales
- `execute_lisp`: ejecuta AutoLISP arbitrario (solo File IPC)
- Undo/redo
- ESC prefix y UTF-8 fallback para IPC robusto

### Testing
232 tests cubriendo backend ezdxf, protocolo IPC, busqueda de equipos, etc.

### Plataforma
- Windows (File IPC backend)
- **Linux/macOS/WSL** (ezdxf backend)

### Estado
- Muy activo, bien documentado
- Companion agent skill: puran-water/autocad-drafting
- Releases frecuentes

### Evaluacion para nuestro proyecto
**Utilidad: ALTA - especialmente el backend ezdxf**
- El patron de doble backend (File IPC + ezdxf) es exactamente lo que necesitamos
- El backend ezdxf prueba que se puede generar DXF sin AutoCAD en Linux
- La arquitectura es la mas madura del ecosistema
- Limitacion: esta muy orientado a P&ID, no a arquitectura
- Podriamos tomar su patron de backend y reemplazar P&ID con tools arquitectonicos
- El sistema de 232 tests es un buen modelo de testing

---

## 3. ngk0/autocad-mcp

**URL:** https://github.com/ngk0/autocad-mcp
**Lenguaje:** Python

### Que hace
Fork/variante de puran-water/autocad-mcp con mas tools. MCP server para AutoCAD LT automation y generacion headless de DXF.

### Tools MCP (19 consolidados)
1. drawing, entity, layer, block, annotation, pid, view, system (iguales a puran-water)
2. **query** - Consultas sobre entidades
3. **search** - Busqueda de entidades
4. **geometry** - Operaciones geometricas
5. **select** - Seleccion de entidades
6. **modify** - Modificacion avanzada
7. **validate** - Validacion de dibujos
8. **export** - Exportacion
9. **xref** - Referencias externas
10. **layout** - Gestion de layouts/espacios de papel
11. **electrical** - Diagramas electricos

### Backend
Mismo doble backend que puran-water: File IPC + ezdxf headless

### Testing
232 tests (misma base)

### Evaluacion para nuestro proyecto
**Utilidad: ALTA - version extendida de puran-water**
- 19 tools vs 8, mas completo
- Los tools adicionales (query, search, geometry, modify, validate, export, xref, layout) son muy relevantes para arquitectura
- El tool "layout" es especialmente importante para planos (Paper Space)
- El tool "xref" es critico para proyectos arquitectonicos
- Mejor candidato como base directa para fork

---

## 4. ahmetcemkaraca/AutoCAD_MCP

**URL:** https://github.com/ahmetcemkaraca/AutoCAD_MCP
**Autor:** Ahmet Cem Karaca
**Lenguaje:** Python

### Que hace
MCP server para AutoCAD 2025. Se describe como "first-of-its-kind". Tiene 7 tools production-ready y 25+ features en desarrollo.

### Conexion con CAD
- AutoCAD COM API
- Requiere AutoCAD 2025 (no LT)

### Tools MCP (7 production-ready)
No se detallan individualmente en la documentacion publica, pero cubren operaciones basicas de dibujo y manipulacion.

### Features avanzados en desarrollo (25+)
Organizados por dominio:
- **Manufactura**: Algoritmos de optimizacion de patrones para reducir desperdicio de material
- **Arquitectura**: Framework de modelado asistido por IA para iteracion de diseno acelerada
- **Educacion**: Sistema de instruccion en lenguaje natural para transformar aprendizaje CAD
- **Ingenieria**: Herramientas de automatizacion para eliminar tareas repetitivas de drafting

### Dependencias
- Python
- AutoCAD COM API
- SciPy y NumPy (procesamiento matematico avanzado)
- Flask (framework web)

### Plataforma
- Solo Windows
- Compatible con Claude Code CLI en WSL/VS Code

### Estado
- Semi-activo (desarrollo en progreso)
- Ambicioso pero muchas features son WIP

### Evaluacion para nuestro proyecto
**Utilidad: MEDIA**
- Las ideas de optimizacion para arquitectura son interesantes
- SciPy/NumPy para calculo matematico es un buen patron
- Demasiado WIP para usar como base
- Las 25 features avanzadas podrian ser inspiracion para roadmap
- Limitado a Windows/COM

---

## 5. daobataotie/CAD-MCP

**URL:** https://github.com/daobataotie/CAD-MCP
**Lenguaje:** Python

### Que hace
Servicio de control CAD que permite dibujar mediante instrucciones en lenguaje natural. Combina NLP y automatizacion CAD.

### CADs soportados
- AutoCAD
- GstarCAD (GCAD)
- ZWCAD

### Conexion con CAD
- COM (Windows)

### Tools/Funcionalidades
- Dibujo basico: linea, circulo, arco, rectangulo, polilinea
- Gestion de capas
- Guardado de dibujos
- NLP para parseo de comandos y reconocimiento de colores

### Estructura del proyecto
- CAD controller
- Configuration file
- Natural language processor
- Server implementation

### Estado
- Activo pero basico
- Orientado a demo/prueba de concepto

### Evaluacion para nuestro proyecto
**Utilidad: BAJA**
- Muy basico, solo operaciones primitivas
- El NLP custom es interesante pero innecesario con LLMs modernos
- No agrega valor significativo sobre multiCAD-mcp

---

## 6. zh19980811/Easy-MCP-AutoCad

**URL:** https://github.com/zh19980811/Easy-MCP-AutoCad
**Lenguaje:** Python

### Que hace
MCP server con integracion SQLite para almacenar y consultar elementos CAD. Enfocado en convertir dibujos en datos.

### Conexion con CAD
- COM (Windows)
- AutoCAD 2018+

### Features
- Control de dibujo por lenguaje natural
- Tools basicos (linea, circulo)
- Gestion de capas
- Auto-generacion de diagramas PMC
- Analisis de elementos de dibujo
- Resaltado de patrones de texto
- **Base de datos SQLite embebida** para almacenar elementos CAD

### Estado
- **Abandonado** - el creador dice que no tiene tiempo
- Abierto a colaboracion

### Evaluacion para nuestro proyecto
**Utilidad: BAJA (concepto DB interesante)**
- La idea de SQLite para metadatos de elementos CAD es valiosa
- Podria ser util para busquedas y analisis de planos
- Pero el codigo esta abandonado y es basico

---

## 7. vigneshpbmenon/autocad-mcp-server

**URL:** https://github.com/vigneshpbmenon/autocad-mcp-server
**Lenguaje:** Python

### Que hace
MCP server basico para AutoCAD. Version 0.1 foundational release.

### Tools
- Lineas, polilineas, rectangulos, circulos, elipses, arcos

### Estado
- v0.1 alpha, muy temprano

### Evaluacion para nuestro proyecto
**Utilidad: BAJA** - demasiado basico

---

## 8. contextform/freecad-mcp

**URL:** https://github.com/contextform/freecad-mcp
**Lenguaje:** Python

### Que hace
MCP server open-source para FreeCAD. Copiloto IA para modelado 3D parametrico.

### Compatibilidad con clientes MCP
- Claude Code, Gemini CLI, VS Code Copilot, OpenCode, Codex CLI

### Features
- Instalador automatico
- Automatizacion de workflows CAD
- Creacion de modelos 3D via lenguaje natural

### Plataforma
- **Multiplataforma** (FreeCAD es cross-platform)

### Estado
- Activo, bien mantenido

### Evaluacion para nuestro proyecto
**Utilidad: MEDIA - patrones MCP**
- Buen ejemplo de integracion con multiples clientes MCP
- FreeCAD es 3D, no directamente aplicable a planos 2D
- El instalador automatico es un buen patron UX
- La compatibilidad con Claude Code y Gemini CLI es relevante

---

## 9. lgradisar/archicad-mcp

**URL:** https://github.com/lgradisar/archicad-mcp
**Lenguaje:** Python

### Que hace
MCP server para ArchiCAD usando Tapir add-on con comandos JSON. Arquitectura "script-first" muy elegante.

### Arquitectura (MUY relevante)
```
AI Agent (Claude) -> MCP Client -> MCP Server (4 tools) -> multiconn_archicad -> ArchiCAD + Tapir
```

### Filosofia: Script-First
- Solo 4 tools MCP expuestos
- En lugar de wrappear cada comando como tool separado, expone `execute_script`
- El AI escribe Python para operaciones complejas
- Loops, filtrado, file I/O - todo en scripts Python

### Tools MCP (4)
1. **execute_script** - Ejecuta Python async con acceso completo a comandos ArchiCAD
2. **discover** - Descubre comandos disponibles
3. Y 2 mas de gestion

### Features
- Control multi-instancia (multiples ArchiCADs simultaneos)
- Requiere Python 3.12+ con uv
- ArchiCAD debe estar corriendo con JSON API oficial
- Tapir Add-On para acceso completo

### Evaluacion para nuestro proyecto
**Utilidad: MEDIA-ALTA - la arquitectura es brillante**
- El patron "script-first" con pocos tools es muy elegante
- En vez de 46 tools individuales, 1 tool de ejecucion de scripts
- El LLM puede generar scripts ezdxf completos y ejecutarlos
- Este patron reduce drasticamente la complejidad del MCP server
- Podriamos combinar: pocos tools de alto nivel + execute_script con ezdxf

---

## 10. reclosedev/pyautocad

**URL:** https://github.com/reclosedev/pyautocad
**Lenguaje:** Python
**Stars:** 568
**Forks:** 147

### Que hace
Libreria Python para simplificar scripts de ActiveX Automation para AutoCAD.

### Conexion
- COM / ActiveX (Windows only)
- Wrapper sobre la interfaz COM de AutoCAD

### Features
- Iteracion sobre objetos
- Busqueda de objetos
- Seleccion de usuario
- Mensajes

### Estado
- **Efectivamente abandonado**
- Issues reportan problemas con AutoCAD 2025 (COM errors)
- No se actualiza regularmente

### Evaluacion para nuestro proyecto
**Utilidad: BAJA** - obsoleta, solo Windows, no MCP

---

## 11. ezdxf (mozman/ezdxf) - DEPENDENCIA CRITICA

**URL:** https://github.com/mozman/ezdxf
**Lenguaje:** Python/C extensions
**Version:** 1.4.3
**Licencia:** MIT

### Que hace
Libreria Python para crear, leer, modificar y escribir archivos DXF. La libreria DXF mas madura y completa del ecosistema Python.

### Versiones DXF soportadas
- Read/Write: R12, R2000, R2004, R2007, R2010, R2013, R2018
- Read-only: R13/R14 y versiones mas antiguas

### Plataforma
- **Multiplataforma completa**: Windows, Linux, macOS
- Binarios pre-compilados en PyPI para todas las plataformas
- C-extensions opcionales para CPython (rendimiento)

### Requisitos
- Python 3.10+
- Sin dependencia de AutoCAD
- Sin dependencia de Windows

### Limitaciones importantes
- **No es un conversor de formatos** - no convierte DXF a DWG
- **No es un CAD kernel** - no provee funcionalidad de alto nivel para construccion
- No renderiza graficos (pero tiene modulo de visualizacion basica)

### Evaluacion para nuestro proyecto
**Utilidad: CRITICA - es nuestra dependencia principal**
- Es la unica forma viable de generar planos DXF en Linux sin AutoCAD
- Madura, bien testeada, activamente mantenida
- MIT license permite uso comercial
- La limitacion DXF-only (no DWG) es aceptable: DXF es el formato de intercambio estandar
- AutoCAD abre DXF sin problemas
- Todos los MCP servers que soportan Linux (puran-water, ngk0) usan ezdxf como backend

---

## 12. Repos adicionales encontrados

### archicad-mcp (boti-ormandi)
- Otra implementacion para ArchiCAD en LobeHub
- Similar a lgradisar pero con enfoque diferente

### SzamosiMate/tapir-archicad-MCP
- Expone TODOS los comandos Tapir como tools MCP auto-generados
- Enfoque opuesto al script-first de lgradisar

### revit-mcp (multiples repos)
- oakplank/RevitMCP: pyRevit Routes + endpoints
- PiggyAndrew/revit_mcp: Named Pipe entre Python MCP y C# Revit Add-in
- revit-mcp/revit-mcp: TypeScript, actualizado ene 2026
- Arquitectura: MCP Server (Python) -> Named Pipe -> Revit Add-in (C#) -> Revit API
- Patron interesante para comunicacion entre procesos

### cadquery-mcp-server (rishigundakaram)
- MCP server para CadQuery (modelado 3D parametrico)
- Tools: verify_cad_query, generate_cad_query
- Export STL/STEP
- Mas orientado a 3D printing

### spkane/freecad-addon-robust-mcp-server
- Version "robusta" del FreeCAD MCP
- FreeCAD Addon + MCP Bridge Workbench

---

## Analisis de Patrones Arquitectonicos

### Patron 1: COM Direct (Windows-only)
**Usado por:** multiCAD-mcp, AutoCAD_MCP, CAD-MCP, Easy-MCP-AutoCad, pyautocad
- Ventaja: Control total sobre AutoCAD en tiempo real
- Desventaja: Solo Windows, requiere AutoCAD instalado y corriendo

### Patron 2: File IPC + AutoLISP (Windows)
**Usado por:** puran-water/autocad-mcp, ngk0/autocad-mcp
- Envia keystrokes via PostMessageW al MDIClient de AutoCAD
- Ejecuta AutoLISP remotamente
- No roba foco de ventana
- Ventaja: Funciona con AutoCAD LT (mas barato)
- Desventaja: Solo Windows, depende de ventana de AutoCAD

### Patron 3: ezdxf Headless (Multiplataforma)
**Usado por:** puran-water, ngk0 como backend alternativo
- Genera DXF puro sin AutoCAD
- Funciona en Linux, macOS, WSL
- Ventaja: Sin dependencias de software propietario
- Desventaja: No hay preview en tiempo real, solo genera archivos

### Patron 4: Script-First (Pocos tools + scripting)
**Usado por:** archicad-mcp
- 4 tools MCP, el AI genera scripts completos
- Ventaja: Maximo flexibilidad, minima complejidad del server
- Desventaja: Depende mas de la capacidad del LLM

### Patron 5: JSON API (Aplicacion con servidor HTTP)
**Usado por:** archicad-mcp (via Tapir), Revit MCP (via pyRevit Routes)
- El CAD software expone una API HTTP/JSON
- El MCP server se conecta como cliente HTTP
- Ventaja: Desacoplado, potencialmente multiplataforma
- Desventaja: Requiere add-on en el CAD software

---

## Recomendacion para cad-copilot

### Arquitectura propuesta (hibrida)

Combinando los mejores patrones encontrados:

```
Claude Code (orquestador)
    |
    v
MCP Server Python (cad-copilot-mcp)
    |
    +-- Backend 1: ezdxf headless (Linux - principal)
    |   - Genera archivos DXF directamente
    |   - Funciona sin AutoCAD
    |   - Ideal para generacion automatizada de planos
    |
    +-- Backend 2: COM/File IPC (Windows - opcional futuro)
    |   - Control directo de AutoCAD
    |   - Para edicion interactiva en tiempo real
    |
    +-- Backend 3: LibreCAD CLI (Linux - opcional futuro)
        - Visualizacion de DXF generados
```

### Tools MCP recomendados (inspirados en multiCAD-mcp + ngk0)

**Fase 1 - MVP:**
1. **drawing** - Muros, puertas, ventanas, lineas, rectangulos, arcos
2. **layer** - Capas arquitectonicas estandar (muros, cotas, mobiliario, etc.)
3. **annotation** - Cotas, textos, etiquetas de ambiente
4. **layout** - Paper space, cajetin, escala
5. **export** - Generar DXF, preview SVG

**Fase 2 - Completo:**
6. **block** - Bloques arquitectonicos (sanitarios, mobiliario, puertas)
7. **query** - Consultar areas, perimetros, mediciones
8. **modify** - Mover, copiar, rotar, escalar, mirror
9. **validate** - Verificar normativas basicas
10. **xref** - Referencias externas

**Fase 3 - Avanzado:**
11. **template** - Templates de planos tipo (planta, corte, fachada)
12. **calculate** - Calculos de superficies, FOT, FOS
13. **script** - execute_script estilo archicad-mcp para operaciones complejas

### Repos a clonar/estudiar en detalle
1. **ngk0/autocad-mcp** - Base principal (19 tools, doble backend)
2. **AnCode666/multiCAD-mcp** - Referencia de tools completos
3. **lgradisar/archicad-mcp** - Patron script-first
4. **mozman/ezdxf** - Dependencia critica, estudiar API a fondo

### Stack tecnologico recomendado
- **Python 3.12+** (todos los repos usan Python)
- **ezdxf 1.4.3** (generacion DXF)
- **mcp SDK Python** (protocolo MCP)
- **pydantic** (validacion de datos)
- **uv** (package manager, usado por archicad-mcp)

---

## Gaps identificados en el ecosistema

1. **Nadie ha hecho un MCP server especifico para arquitectura 2D** - todos son genericos
2. **No existe un MCP server ezdxf-first** - todos ponen ezdxf como fallback, no como backend principal
3. **No hay libreria de bloques arquitectonicos** integrada en ningun MCP server
4. **No hay validacion de normativas** en ningun repo
5. **No hay generacion de cajetin/rotulo** automatizada
6. **No hay calculo de superficies/FOT/FOS** integrado
7. **No hay soporte para escala de plano** adecuado

Estos gaps son exactamente nuestra oportunidad de diferenciacion.
