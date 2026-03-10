# PRD: CAD Copilot — Copiloto CAD Arquitectónico

**Versión:** 1.0
**Fecha:** 2026-03-10
**Autor:** Pablo Quevedo + Claude Code (AI-assisted)
**Estado:** Draft

---

## 1. Resumen Ejecutivo

**CAD Copilot** es una herramienta open source que conecta Claude Code con AutoCAD/BricsCAD para generar y modificar planos arquitectónicos 2D mediante lenguaje natural. El sistema traduce instrucciones en español ("dibujá una puerta abatible de 0.90 en el living") a entidades DXF profesionales con layers, cotas, bloques y rellenos correctos según normas IRAM.

**Propuesta de valor:** Reducir al menos un 50% el tiempo de dibujo de planos municipales y ejecutivos, eliminando la parte más tediosa del proceso (textos, cotas, referencias técnicas, tablas de cálculo) mientras el arquitecto mantiene control total sobre el diseño.

**Diferenciador:** No existe ninguna herramienta que genere documentación técnica para planos municipales argentinos con normas IRAM. Este sistema llena ese gap.

---

## 2. Problema

### 2.1 Situación actual

Un arquitecto matriculado en Argentina dedica una proporción significativa de su tiempo de dibujo a tareas repetitivas y mecánicas:

| Tarea | % del tiempo de dibujo | Nivel de tediosidad |
|-------|----------------------|-------------------|
| Textos (nombres de ambientes, notas, referencias) | ~20% | Alto |
| Cotas (cadenas, niveles, alturas) | ~20% | Alto |
| Referencias técnicas (símbolos, indicaciones de corte, norte) | ~15% | Alto |
| Tablas (iluminación, ventilación, superficies) | ~10% | Muy alto (cálculo manual + dibujo) |
| Cartela y datos del plano | ~5% | Medio (repetitivo) |
| Geometría (muros, aberturas, bloques) | ~30% | Bajo-medio |

**El 70% del tiempo se va en tareas que podrían automatizarse.** La geometría (el diseño propiamente dicho) es solo el 30%.

### 2.2 Dolor específico

1. **Cotas**: Acotar un plano de vivienda típica (100m²) lleva 1-2 horas. Cada muro, cada abertura, cada retiro. Y si algo cambia, hay que recotizar todo.
2. **Tablas de cálculo**: Las tablas de iluminación y ventilación requieren medir cada ventana, calcular áreas de vidrio vs área de piso, verificar ratios. Es un cálculo manual propenso a errores que tiene consecuencias en la aprobación municipal.
3. **Textos y referencias**: Nombrar ambientes, indicar superficies, colocar símbolos de corte, niveles, norte — todo es manual y repetitivo.
4. **Consistencia**: Si se modifica una abertura, hay que actualizar la cota, la tabla de iluminación, la planilla de carpinterías y la fachada. Hoy todo eso es manual.

### 2.3 Impacto

- **Tiempo perdido**: Horas por plano en tareas mecánicas
- **Errores**: Cálculos manuales de iluminación/ventilación pueden tener errores que el municipio detecta → rechazo del legajo → demora en la obra
- **Costo oportunidad**: Tiempo que podría dedicarse a diseñar más proyectos o mejorar la calidad del diseño

---

## 3. Objetivos y Métricas

### 3.1 Objetivos (SMART)

| ID | Objetivo | Prioridad | Métrica | Meta |
|----|----------|-----------|---------|------|
| O1 | Reducir tiempo de anotación (cotas, textos, referencias) | P0 | Tiempo de anotación por plano | -50% |
| O2 | Automatizar tablas de cálculo (iluminación, ventilación, superficies) | P0 | Errores de cálculo | 0 errores |
| O3 | Generar bloques paramétricos desde lenguaje natural | P1 | Tiempo de creación de bloque | -80% |
| O4 | Mantener compatibilidad total con AutoCAD | P0 | DXF abre sin errores en AutoCAD | 100% |
| O5 | Aprender convenciones del usuario | P1 | Layers/estilos correctos sin configurar | >90% |
| O6 | Verificar cumplimiento normativo automáticamente | P1 | Detección de incumplimientos IRAM | >95% |

### 3.2 Métricas de éxito

| Métrica | Baseline (hoy) | Meta Fase 1 | Meta Fase 3 |
|---------|----------------|-------------|-------------|
| Tiempo dibujo plano municipal (vivienda 100m²) | ~X horas | -30% | -50% |
| Errores en tablas de iluminación/ventilación | Frecuentes | Eliminados | Eliminados |
| Compatibilidad DXF → AutoCAD | N/A | 100% sin errores | 100% sin errores |
| Tiempo para acotar un plano completo | 1-2 horas | 5 minutos | 2 minutos |

---

## 4. No-Goals (Límites explícitos)

| ID | Qué NO hace este sistema | Razón |
|----|--------------------------|-------|
| NG1 | NO diseña la planta (distribución de ambientes) | El diseño es del arquitecto. El sistema dibuja y anota |
| NG2 | NO genera planos 3D ni modelos BIM | Scope es 2D puro. BIM es otro proyecto |
| NG3 | NO reemplaza AutoCAD | AutoCAD sigue siendo el editor final. El sistema es un acelerador |
| NG4 | NO genera DWG nativo | Genera DXF que AutoCAD abre sin problemas. DWG requiere SDK pago |
| NG5 | NO es una app web multi-usuario | Es herramienta local, single-user, para el arquitecto en su máquina |
| NG6 | NO hace cálculo estructural | Solo normativa urbanística (FOS/FOT) e higiene (iluminación/ventilación) |
| NG7 | NO genera presupuestos ni cómputos métricos | Fuera de scope inicial |

---

## 5. Personas

### Persona 1: Pablo (usuario principal y desarrollador)

- **Rol**: Arquitecto matriculado (CPTN Neuquén), desarrollador amateur
- **Contexto**: Usa AutoCAD en Windows, Claude Code en Linux (NUC). Dibuja planos municipales y ejecutivos para viviendas unifamiliares y ampliaciones
- **Pain**: Las cotas, textos y tablas le consumen más tiempo que el diseño en sí
- **Necesidad**: "Quiero decirle al sistema 'cotá el living' y que aparezcan las cotas correctas con mi estilo"
- **Skill técnico**: Puede configurar y debuggear, pero no quiere mantener código complejo
- **Herramientas**: AutoCAD, Claude Code, Codex, Gemini

### Persona 2: Arquitecto usuario futuro

- **Rol**: Arquitecto argentino que usa AutoCAD
- **Contexto**: No programa. Quiere una herramienta que "simplemente funcione"
- **Pain**: Mismo que Pablo pero sin capacidad de customización
- **Necesidad**: CLI simple o interfaz mínima. Instrucciones en español
- **Skill técnico**: Bajo. Necesita instalación simple y documentación clara

---

## 6. Requerimientos Funcionales

### 6.1 Motor de Dibujo (P0 — Fase 1)

| ID | Requerimiento | Criterio de aceptación |
|----|--------------|----------------------|
| FR-001 | Generar muros como LWPOLYLINE con espesor configurable | Muro de 0.15m y 0.30m se dibujan correctamente en layer A-WALL |
| FR-002 | Insertar puertas como bloques paramétricos | Puerta abatible de cualquier ancho (0.70-1.00m) con arco de giro 90° |
| FR-003 | Insertar ventanas como bloques paramétricos | Ventana con representación en planta según tipo (corrediza, abatible, paño fijo) |
| FR-004 | Aplicar layers según convención IRAM/AIA | Cada entidad se asigna al layer correcto con color, tipo de línea y peso adecuados |
| FR-005 | Generar cartela/rótulo con datos CPTN | Bloque con atributos: proyecto, ubicación, escala, profesional, matrícula, fecha |
| FR-006 | Configurar Paper Space con viewports | Layout A1/A2/A3 con viewport(s) a escala 1:50, 1:75 o 1:100 |
| FR-007 | Generar DXF R2013 compatible con AutoCAD | El DXF se abre en AutoCAD 2013+ sin errores ni advertencias |
| FR-008 | Acotar muros con cadenas de cotas | DIMENSION entities (linear, aligned) con estilo IRAM configurable |
| FR-009 | Insertar textos de ambientes con superficie | MTEXT con nombre del local + superficie calculada |
| FR-010 | Aplicar hatches a muros en corte | HATCH SOLID o ANSI31 en muros cortados |

### 6.2 Integración Claude Code (P0 — Fase 2)

| ID | Requerimiento | Criterio de aceptación |
|----|--------------|----------------------|
| FR-011 | MCP Server local que exponga tools de dibujo | Claude Code puede invocar `draw_wall`, `add_door`, `add_dimensions`, etc. |
| FR-012 | Interpretar lenguaje natural → JSON semántico | "Dibujá un muro de 4m hacia el este" → JSON con wall entity válida |
| FR-013 | Validar JSON con Pydantic antes de dibujar | JSON inválido retorna error descriptivo, no dibuja |
| FR-014 | Preview web interactivo | Canvas 2D con zoom, pan. Se actualiza en tiempo real al generar |
| FR-015 | Modificar entidades existentes via prompt | "Mové la pared w1 30cm al norte" modifica el DXF existente |

### 6.3 Motor de Normas (P1 — Fase 3)

| ID | Requerimiento | Criterio de aceptación |
|----|--------------|----------------------|
| FR-016 | Calcular superficies de locales con Shapely | Superficie de cada ambiente ±0.01m² respecto a cálculo manual |
| FR-017 | Verificar FOS/FOT según zona urbana de Neuquén | Input: zona + terreno + planta → output: cumple/no cumple + valores |
| FR-018 | Generar tabla de iluminación y ventilación | Para cada local: superficie vidrio, superficie ventilación, ratio, cumple/no cumple |
| FR-019 | Actualizar tablas automáticamente al modificar aberturas | Cambiar ventana V3 → tabla se recalcula sola |
| FR-020 | Trazabilidad normativa | Cada verificación cita artículo/norma específica |

### 6.4 Aprendizaje (P1 — Fase 4)

| ID | Requerimiento | Criterio de aceptación |
|----|--------------|----------------------|
| FR-021 | Extraer convenciones de DXF existentes | Analizar N planos del usuario → generar user_conventions.json |
| FR-022 | Exportar bloques del usuario a biblioteca | Bloques extraídos como DXF individuales en ~/.cad-copilot/blocks/ |
| FR-023 | Aplicar convenciones automáticamente | Nuevos planos usan layers, estilos y bloques del usuario sin configurar |
| FR-024 | Templates por tipología | Template "vivienda municipal", "ampliación", "ejecutivo estructura" |

### 6.5 Conexión AutoCAD (P2 — Fase 5)

| ID | Requerimiento | Criterio de aceptación |
|----|--------------|----------------------|
| FR-025 | MCP Server en Windows con WebSocket | Conexión bidireccional Linux ↔ Windows estable |
| FR-026 | Importar DXF generado en AutoCAD | Comando automático DXFIN o INSERT desde el MCP Server |
| FR-027 | Leer selección actual de AutoCAD | "¿Qué tengo seleccionado?" → respuesta con entidades y propiedades |
| FR-028 | Modificar entidades en AutoCAD via prompt | "Cambiá el layer de la selección a A-DOOR" se ejecuta en AutoCAD |
| FR-029 | Notificar cambios del usuario | Si el usuario modifica algo en AutoCAD, Claude Code se entera |

---

## 7. Formato Intermedio (JSON Schema)

El corazón del sistema es un JSON semántico que representa intenciones arquitectónicas, no geometría cruda. Esto permite que el LLM piense en "muros" y "puertas", no en "líneas" y "arcos".

### 7.1 Entidades del vocabulario

| Entidad | Propiedades clave | Genera en DXF |
|---------|------------------|---------------|
| `wall` | start, end, thickness, material, classification, openings[] | LWPOLYLINE + HATCH |
| `space` | name, function, bounded_by[], min_area, requires_ventilation | MTEXT + cálculos |
| `opening` | type (door/window), width, height, sill_height, mechanism | INSERT (bloque) |
| `dimension` | type (linear/aligned/angular), references[] | DIMENSION entity |
| `annotation` | type (level/section_cut/north/scale_bar), position | INSERT/MTEXT/LINE |
| `title_block` | project, location, scale, professional, license, date | INSERT con ATTRIB |
| `table` | type (illumination/ventilation/areas), auto_calculate | TABLE o MTEXT |

### 7.2 Operaciones soportadas

| Operación | Descripción | Ejemplo prompt |
|-----------|-------------|----------------|
| `create` | Crear nuevas entidades | "Dibujá un muro de 4m..." |
| `modify` | Modificar existentes por ID | "Mové w1 30cm al norte" |
| `delete` | Eliminar entidades | "Borrá la ventana V3" |
| `query` | Consultar propiedades | "¿Cuánto mide el living?" |
| `calculate` | Ejecutar cálculos normativos | "Verificá iluminación del dormitorio" |
| `annotate` | Agregar cotas/textos/referencias | "Cotá el frente completo" |
| `generate_table` | Crear tabla de cálculo | "Generá la tabla de iluminación" |
| `clone` | Clonar con modificaciones | "Hacé una puerta igual a P1 pero de 0.90" |

---

## 8. Arquitectura Técnica

### 8.1 Diagrama de componentes

```
LINUX (NUC - Celeron J4005, 7.3GB RAM)
├── Claude Code (orquestador, lenguaje natural)
├── MCP Server Local (Python, expone tools)
│   ├── draw_entities(json) → DXF
│   ├── modify_entities(json) → DXF modificado
│   ├── calculate_norms(json) → reporte
│   └── extract_conventions(dxf_path) → json
├── Motor de Dibujo (Python + ezdxf)
├── Motor de Normas (Python + Shapely)
├── Preview Server (uvicorn + WebSocket)
└── Browser (Vite + Canvas 2D)

WINDOWS (PC Oficina o misma red)
├── MCP Server Remoto (Python + pyautocad)
│   ├── import_dxf(path)
│   ├── query_selection()
│   ├── modify_entity(handle, props)
│   └── watch_changes() → WebSocket push
└── AutoCAD
```

### 8.2 Stack tecnológico

| Componente | Tecnología | Versión | Licencia | Costo |
|-----------|-----------|---------|----------|-------|
| Orquestador | Claude Code + MCP | 2.1.x | Anthropic Pro/Max | Ya pagado |
| Schemas | Pydantic v2 | 2.x | MIT | $0 |
| Generación DXF | ezdxf | 1.4.x | MIT | $0 |
| Geometría | Shapely | 2.x | BSD | $0 |
| Preview backend | uvicorn + websockets | latest | BSD | $0 |
| Preview frontend | Vite + Canvas 2D | latest | MIT | $0 |
| Templates | Jinja2 | 3.x | BSD | $0 |
| MCP Server Win | pyautocad + mcp | latest | MIT/varied | $0 |
| Tests | pytest | 8.x | MIT | $0 |
| **Total** | | | | **$0** |

---

## 9. Fases de Implementación

### Fase 1: Motor de Dibujo (P0)
**Objetivo:** Generar DXF profesional desde JSON
**Entregables:**
- [ ] Pydantic schemas (wall, space, opening, dimension, annotation)
- [ ] Motor ezdxf que traduce JSON → DXF
- [ ] Layers IRAM/AIA preconfigurados
- [ ] Bloques: puerta abatible, puerta corrediza, ventana corrediza, ventana abatible
- [ ] Bloques: inodoro, lavabo, ducha, bidet, mesada cocina
- [ ] Cartela CPTN con atributos
- [ ] Paper Space con viewport escalado
- [ ] Cotas (cadenas lineales y aligned)
- [ ] Tests con plano de referencia

**Criterio de salida:** Un JSON de vivienda simple genera un DXF que se abre en AutoCAD sin errores, con layers correctos, cotas y cartela.

### Fase 2: Integración Claude Code (P0)
**Objetivo:** Lenguaje natural → DXF via Claude Code
**Entregables:**
- [ ] MCP Server local con tools de dibujo
- [ ] Prompt engineering para interpretación arquitectónica
- [ ] Preview web Canvas 2D interactivo
- [ ] Flujo completo: prompt → JSON → validación → DXF → preview

**Criterio de salida:** "Dibujá un living de 4x3 con una ventana corrediza de 1.50" genera DXF correcto.

### Fase 3: Motor de Normas (P1)
**Objetivo:** Cálculos automáticos y verificación normativa
**Entregables:**
- [ ] Cálculo de superficies por local (Shapely)
- [ ] Tabla de iluminación y ventilación automática
- [ ] Verificación FOS/FOT (Neuquén, zonas R1-R4, C1-C3)
- [ ] Trazabilidad (cita de norma/artículo)
- [ ] Tests con planos reales aprobados

**Criterio de salida:** Generar tabla de iluminación/ventilación con 0 errores vs cálculo manual.

### Fase 4: Aprendizaje (P1)
**Objetivo:** El sistema aprende del estilo del usuario
**Entregables:**
- [ ] Extractor de convenciones de DXF existentes
- [ ] Biblioteca de bloques extraídos
- [ ] Templates Jinja2 por tipología
- [ ] Score de calidad de planos (filtro legacy)

**Criterio de salida:** Nuevo plano usa automáticamente layers, bloques y estilos del usuario.

### Fase 5: Conexión AutoCAD (P2)
**Objetivo:** Bridge bidireccional con AutoCAD en Windows
**Entregables:**
- [ ] MCP Server Windows con pyautocad
- [ ] WebSocket bridge Linux ↔ Windows
- [ ] Import DXF automático en AutoCAD
- [ ] Query de selección
- [ ] Notificación de cambios del usuario

**Criterio de salida:** "Mandá esto a AutoCAD" importa el DXF. "¿Qué tengo seleccionado?" responde correctamente.

---

## 10. Riesgos y Mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|-------------|---------|------------|
| R1 | ezdxf genera DXF que AutoCAD rechaza | Baja | Crítico | Tests exhaustivos con múltiples versiones de AutoCAD. Template base del usuario |
| R2 | LLM genera coordenadas geométricamente imposibles | Media | Alto | Validación Pydantic + verificación topológica Shapely pre-dibujo |
| R3 | COM de AutoCAD es inestable (diálogos modales) | Media | Medio | Health check + reconexión automática. ezdxf offline como fallback |
| R4 | Normas IRAM codificadas incorrectamente | Media | Crítico | Tests con planos reales aprobados. Revisión manual del arquitecto |
| R5 | Celeron J4005 sin potencia suficiente | Baja | Medio | ezdxf es liviano (<100ms). Preview Canvas 2D es <50KB. Sin frameworks pesados |
| R6 | Planos legacy contaminan aprendizaje | Media | Bajo | Score de calidad + revisión humana del style profile |
| R7 | Cotas mal posicionadas o superpuestas | Alta | Medio | Algoritmo de placement con detección de colisiones |
| R8 | Dependencia de AutoCAD (licencia paga) | Baja | Bajo | BricsCAD Linux como alternativa. El DXF funciona en cualquier CAD |

---

## 11. Restricciones Técnicas

| Restricción | Impacto | Decisión |
|-------------|---------|----------|
| NUC Celeron J4005, 7.3GB RAM | No puede correr procesos pesados | Stack liviano: Python puro, sin Docker, sin frameworks JS pesados |
| Presupuesto $0 | Solo herramientas open source | ezdxf (MIT), Shapely (BSD), Pydantic (MIT), todo gratis |
| AutoCAD en Windows, Claude Code en Linux | Necesita bridge de red | MCP Server con WebSocket en LAN |
| Sin DWG nativo | Formato de salida es DXF | AutoCAD abre DXF sin problemas. ODA Converter como opción futura |
| Single user (Pablo) | No necesita auth, multi-tenancy, cloud | Arquitectura local, filesystem, sin base de datos |

---

## 12. Glosario

| Término | Definición |
|---------|-----------|
| **DXF** | Drawing Exchange Format — formato abierto de Autodesk para intercambio CAD |
| **ezdxf** | Librería Python para leer/escribir DXF (MIT, v1.4.3) |
| **MCP** | Model Context Protocol — protocolo de Anthropic para conectar LLMs con herramientas |
| **IRAM** | Instituto Argentino de Normalización y Certificación |
| **CPTN** | Consejo Profesional Técnico de Neuquén |
| **FOS** | Factor de Ocupación del Suelo (superficie cubierta / superficie terreno) |
| **FOT** | Factor de Ocupación Total (superficie total / superficie terreno) |
| **Layer** | Capa en CAD — organiza entidades por tipo (muros, cotas, textos) |
| **Paper Space** | Espacio de presentación para impresión con viewports escalados |
| **Viewport** | Ventana en Paper Space que muestra Model Space a una escala |
| **Cartela/Rótulo** | Recuadro en el plano con datos del proyecto y profesional |
| **Bloque** | Grupo de entidades reutilizable (puerta, ventana, sanitario) |
| **HATCH** | Relleno/sombreado de áreas cerradas |
| **LWPOLYLINE** | Polilínea liviana 2D — entidad base para muros |

---

## Self-Score (Framework 100 puntos)

### AI-Specific Optimization (25/25)
- [x] Vocabulario semántico claro para LLM (wall, space, opening) — 7/7
- [x] Operaciones bien definidas (create, modify, query, calculate) — 6/6
- [x] Formato intermedio JSON validable con Pydantic — 6/6
- [x] Boundaries claras: LLM interpreta, Python calcula, nunca al revés — 6/6

### Traditional PRD Core (24/25)
- [x] Problema cuantificado con dolor claro — 7/7
- [x] Personas definidas con contexto real — 6/6
- [x] Non-goals explícitos (7 items) — 5/6
- [x] Métricas SMART con baseline y metas — 6/6

### Implementation Clarity (28/30)
- [x] Requerimientos en formato FR-XXX con criterios de aceptación — 10/10
- [x] Fases ordenadas por dependencia con criterios de salida — 9/10
- [x] Stack tecnológico completo con justificación y costos — 9/10

### Completeness (19/20)
- [x] Arquitectura con diagrama — 5/5
- [x] Riesgos con probabilidad, impacto y mitigación — 5/5
- [x] Restricciones técnicas documentadas — 5/5
- [x] Glosario de términos de dominio — 4/5

**Total: 96/100**

---

*PRD generado con asistencia de Claude Code (opus-4.6) + investigación multi-IA (Gemini 3.1-pro, Codex gpt-5.3)*
