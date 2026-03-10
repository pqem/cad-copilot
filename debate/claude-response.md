# CAD Copilot -- Posicion del Backend Architect (Claude Code / Opus 4.6)

Mi perspectiva es la de quien disenya servicios, APIs y flujos de datos entre componentes distribuidos. Coincido con Gemini en varios puntos fundamentales pero discrepo en la arquitectura de comunicacion y en el enfoque de aprendizaje. Mi propuesta es construir un **sistema de dos nodos con contrato fuerte**, donde cada pieza tiene responsabilidades claras y el acoplamiento se minimiza a traves de un protocolo bien definido.

---

## 1. CONEXION CON AUTOCAD: MCP Server en Windows + Agent Bridge via WebSocket

**Posicion: MCP Server en Windows, pero con transporte WebSocket persistente, no HTTP request-response.**

Gemini propone MCP y estoy de acuerdo en el concepto, pero hay que ser mas precisos sobre la arquitectura de red. El problema real tiene tres capas:

1. **Claude Code en Linux** necesita invocar operaciones en AutoCAD.
2. **AutoCAD en Windows** solo expone COM Automation (pyautocad) o .NET API.
3. **La red local** conecta ambas maquinas.

La solucion concreta:

- **Nodo Windows**: Un proceso Python que actua como MCP Server y se conecta a AutoCAD via COM (`win32com.client` / `pyautocad`). Este proceso expone tools MCP: `draw_entities`, `modify_entity`, `query_selection`, `import_dxf`, `export_dxf`, `run_lisp`.
- **Transporte**: WebSocket bidireccional entre Linux y Windows. No HTTP puro. Razon: necesitamos que Windows pueda **notificar a Linux** cuando el usuario selecciona algo en AutoCAD, cambia de vista, o hace una modificacion manual. Sin WebSocket, perdemos la bidireccionalidad real.
- **Fallback para BricsCAD en Linux**: BricsCAD tiene version nativa Linux con API LISP compatible. Si en el futuro migras a BricsCAD, el mismo MCP Server corre directamente en la NUC sin necesidad de Windows. Esto hace que la arquitectura sea resistente al cambio de CAD.

**Riesgos:**
- COM Automation de AutoCAD es fragil: se cuelga si AutoCAD muestra un dialogo modal. Solucion: health check periodico y reconexion automatica con estado.
- Latencia de red local: despreciable (~1ms LAN), no es un problema real.

**Descarto plugin .NET nativo** porque: (a) requiere compilar contra una version especifica de AutoCAD, (b) el debugging es doloroso, (c) ata el sistema a AutoCAD exclusivamente. Un bridge externo es mas mantenible y portable.

**Descarto AutoLISP puro** como interfaz principal porque: no tiene mecanismo de callback robusto, no maneja estado complejo, y el manejo de errores es primitivo. Pero si lo uso como **capa de ejecucion** dentro del MCP Server (el server manda `SendStringToExecute` con comandos LISP).

---

## 2. GENERACION: ezdxf como motor principal, COM como canal de entrega

**Posicion: Generacion 100% con ezdxf en Linux. AutoCAD es solo visor y editor.**

El flujo que propongo es fundamentalmente distinto al de "controlar AutoCAD remotamente para dibujar":

```
Usuario (lenguaje natural)
    |
    v
Claude Code (interpreta, genera JSON semantico)
    |
    v
Motor de Dibujo Python (ezdxf) en Linux
    |
    v
Archivo DXF temporal
    |
    v
MCP Server envia a AutoCAD: DXFIN / INSERT
    |
    v
Usuario ve resultado en AutoCAD, ajusta manualmente
    |
    v
MCP Server detecta cambios, notifica a Claude Code
```

**Por que no COM en vivo para dibujar:**

1. **Performance**: Dibujar 500 entidades via COM toma 5-10 segundos con overhead de IPC por cada entidad. Un DXF con ezdxf se genera en <100ms para un plano completo de vivienda.
2. **Atomicidad**: Si algo falla a mitad de un dibujo via COM, quedas con medio plano. Un DXF es atomico: o se importa completo o no.
3. **Testabilidad**: Puedo testear toda la generacion de geometria sin tener AutoCAD abierto. CI/CD posible.
4. **Reproducibilidad**: Cada DXF generado es un snapshot que se puede versionar en git.

**COM en vivo SI se usa para:**
- Modificaciones puntuales: "mover esta pared 30cm", "cambiar el layer de la seleccion".
- Queries: "que hay seleccionado?", "dame las cotas del local cocina".
- Sincronizacion: detectar que el usuario modifico algo y reflejar eso en el modelo semantico.

**Riesgos:**
- El DXFIN puede romper estilos de cota o tipos de linea si no se manejan las tablas de estilo correctamente. Solucion: el DXF generado hereda las tablas de estilo de un template DXF base que se extrae una vez del plano actual del usuario.
- Perdida de ediciones manuales: cada regeneracion no debe pisar lo que el usuario ya ajusto. Solucion: trabajar en layers/bloques separados, nunca sobrescribir layers del usuario.

---

## 3. FORMATO INTERMEDIO: JSON Schema estricto con vocabulario arquitectonico

**Posicion: JSON con Pydantic models, vocabulario de dominio arquitectonico, sin DSL nuevo.**

Coincido con Gemini en que JSON semantico es el camino, pero soy mas opinionado sobre la estructura. No inventar un DSL nuevo: el costo de mantener un parser propio no se justifica. JSON + Pydantic da validacion, documentacion automatica, y los LLMs ya son excelentes generando JSON estructurado.

**Schema propuesto (simplificado):**

```json
{
  "$schema": "cad-copilot/v1",
  "operation": "create_floor_plan",
  "target_layer_prefix": "PLANTA_BAJA",
  "elements": [
    {
      "type": "wall",
      "id": "w1",
      "start": [0.0, 0.0],
      "end": [4.0, 0.0],
      "thickness": 0.30,
      "material": "ladrillo_comun",
      "classification": "exterior_portante",
      "openings": [
        {
          "type": "window",
          "position_along_wall": 1.5,
          "width": 1.50,
          "height": 1.10,
          "sill_height": 0.90,
          "block_name": "V1"
        }
      ]
    },
    {
      "type": "space",
      "id": "s1",
      "name": "Dormitorio 1",
      "function": "dormitorio",
      "bounded_by": ["w1", "w2", "w3", "w4"],
      "min_area_m2": 9.0,
      "min_side_m": 2.50,
      "requires_ventilation": true,
      "ventilation_ratio": 0.125
    }
  ],
  "annotations": {
    "north_angle": 45.0,
    "scale": "1:50"
  }
}
```

**Claves de disenyo del schema:**

1. **`classification`** en muros: permite que el motor de dibujo asigne automaticamente layer, grosor de pluma y tipo de linea segun normas IRAM.
2. **`space` como entidad de primer nivel**: los locales no se infieren de la geometria, se declaran explicitamente. Esto permite validar normas (superficie minima, ventilacion) antes de dibujar.
3. **`openings` anidados en walls**: la abertura pertenece semanticamente al muro. El motor resuelve como cortar el muro y colocar el bloque.
4. **IDs explicitos**: permiten que operaciones posteriores referencien elementos ("mover w1 30cm al norte").

**Riesgos:**
- El LLM puede generar coordenadas geometricamente imposibles (muros que no cierran). Solucion: validacion topologica post-generacion con Shapely antes de enviar a ezdxf.
- Esquema demasiado rigido para casos edge. Solucion: campo `raw_geometry` opcional que permite inyectar entidades DXF arbitrarias para casos no cubiertos por el vocabulario.

**Descarto DSL propio** porque: (a) ningun LLM esta entrenado en tu DSL, (b) requiere parser custom, (c) JSON tiene tooling universal.
**Descarto codigo Python directo** porque: (a) es un vector de inyeccion de codigo, (b) no es validable sin ejecutarlo, (c) no separa intencion de implementacion.

---

## 4. APRENDIZAJE DE PLANOS: Analisis estructural de DXF + Template System + RAG liviano

**Posicion: No embeddings vectoriales. Analisis deterministico de DXF existentes + sistema de templates + contexto inyectado en prompt.**

Gemini propone RAG con base vectorial (LanceDB). Discrepo parcialmente: para este caso de uso, los embeddings vectoriales son overkill y agregan complejidad sin beneficio proporcional. El "estilo" de un arquitecto en planos 2D es mucho mas estructurado que texto libre.

**Lo que realmente necesitas aprender de los planos existentes:**

1. **Convencion de layers**: nombres, colores, tipos de linea, grosores. Esto es una tabla, no un vector.
2. **Bloques recurrentes**: sanitarios, aberturas, muebles, simbolos. Son archivos DXF/DWG reutilizables.
3. **Estilos de cota y texto**: fuentes, alturas, tolerancias. Parametros discretos.
4. **Patrones compositivos**: como distribuye locales, proporciones tipicas, circulaciones. Esto SI es mas complejo.

**Implementacion concreta en 3 capas:**

### Capa 1: Extractor de Convenciones (deterministico)
Script Python que analiza N planos DXF del usuario y genera un archivo `user_conventions.json`:

```python
# Pseudocodigo
for dxf_file in user_plans:
    doc = ezdxf.readfile(dxf_file)
    for layer in doc.layers:
        register_layer_convention(layer.dxf.name, layer.color, layer.linetype)
    for block in doc.blocks:
        if not block.name.startswith('*'):  # skip anonymous
            register_block(block.name, extract_geometry_bounds(block))
    for dimstyle in doc.dimstyles:
        register_dimstyle(dimstyle.dxf.name, extract_dimstyle_params(dimstyle))
```

Resultado: un JSON con todas las convenciones del usuario. Sin embeddings, sin vectores, sin base de datos extra.

### Capa 2: Biblioteca de Bloques (filesystem)
Exportar todos los bloques del usuario a archivos DXF individuales en `~/.cad-copilot/blocks/`. El motor de dibujo los referencia por nombre cuando genera un plano.

### Capa 3: Templates de Plano (parametricos)
Para los patrones compositivos, creo templates Jinja2 de JSON que representan tipologias:

- `vivienda_unifamiliar_municipal.json.j2` -- template para legajo municipal
- `ampliacion_municipal.json.j2` -- existente + ampliacion
- `plano_ejecutivo_estructura.json.j2`

El LLM no inventa desde cero: selecciona un template, lo parametriza, y ajusta.

**Cuando SI usar RAG:**
Si en el futuro tenes 200+ planos y queres buscar "como resolvi la cocina en el proyecto de calle Mitre", ahi si tiene sentido un indice de busqueda. Pero para eso basta un indice full-text sobre metadatos extraidos (Tantivy/SQLite FTS), no hace falta embedding vectorial.

**Riesgos:**
- Planos viejos con convenciones inconsistentes contaminan el sistema. Solucion: el extractor genera un reporte de inconsistencias y el usuario elige cual es el estandar canonico.
- Templates rigidos limitan la creatividad. Solucion: los templates son punto de partida, el LLM puede modificar cualquier parametro.

---

## 5. STACK Y UX: CLI (Claude Code) + Panel Web liviano para preview

**Posicion: Claude Code como interfaz principal + app web minima (Vite + Canvas 2D) para preview interactivo. No Next.js.**

Coincido con Gemini en que CLI-first es correcto, pero un SVG estatico es insuficiente para un arquitecto. Necesitas poder hacer zoom, pan, y hacer click en elementos para referenciarlos en el proximo comando.

**Arquitectura de la UI:**

```
Claude Code (terminal)
    |
    | genera DXF + metadata JSON
    |
    v
Preview Server (Python, uvicorn, <200 lineas)
    |
    | WebSocket: push de actualizaciones
    |
    v
Browser Tab (Vite SPA, Canvas 2D)
    |
    | Renderiza DXF simplificado
    | Click en elemento -> ID vuelve a Claude Code via stdin/pipe
```

**Por que NO Next.js:**
- SSR es innecesario: no hay SEO, no hay usuarios externos.
- React hydration en un Celeron J4005 con 7GB RAM es un desperdicio.
- Un canvas 2D con vanilla JS o Preact pesa <50KB y renderiza 10,000 entidades sin problema.

**Por que NO solo CLI:**
- Un arquitecto necesita VER lo que esta generando. "Dibujame la planta" sin ver el resultado es volar a ciegas.
- El preview permite iteracion rapida: "esa pared corremela" senalando visualmente.

**Por que NO extension de AutoCAD como UI principal:**
- El LLM no corre en Windows.
- La logica del copilot vive en Linux.
- AutoCAD es el destino final, no la interfaz de interaccion con la IA.

**El flujo de trabajo real del arquitecto seria:**

1. Abre terminal con Claude Code.
2. Abre browser con preview (localhost:3456).
3. Describe lo que quiere en lenguaje natural.
4. Ve el preview, ajusta con mas instrucciones.
5. Cuando esta conforme: "mandalo a AutoCAD".
6. En AutoCAD hace ajustes finos manuales.
7. Vuelve a Claude Code para el proximo paso.

**Riesgos:**
- Mantener dos visualizaciones sincronizadas (preview + AutoCAD) puede confundir. Solucion: el preview es borrador, AutoCAD es el plano real. Workflow unidireccional hasta la validacion.
- El preview no reemplaza la precision de AutoCAD. Solucion: mostrar cotas y medidas en el preview, pero siempre marcar "BORRADOR - Verificar en AutoCAD".

---

## 6. NORMAS Y CALCULOS: Motor de reglas Python deterministico + Base de datos de normas versionada

**Posicion: 100% de acuerdo con Gemini. El LLM NUNCA calcula. Python calcula. Pero voy mas lejos en la implementacion.**

Los calculos normativos son la parte mas critica del sistema porque tienen responsabilidad profesional. Un error de FOS puede significar que el municipio rechace el legajo o, peor, un problema legal para el arquitecto.

**Arquitectura del Motor de Normas:**

```
normas/
  neuquen/
    codigo_urbano.py       # FOS, FOT, retiros, alturas por zona
    codigo_edificacion.py  # superficies minimas, ventilacion, iluminacion
  iram/
    iram_11603.py          # clasificacion bioambiental, K admisible
    iram_11605.py          # condensacion
    iram_11625.py          # verificacion riesgo condensacion
  schemas/
    zona_r1.json           # parametros zona R1 Neuquen
    zona_r2.json
    zona_c1.json
  tests/
    test_fos_fot.py        # tests con casos reales conocidos
    test_iluminacion.py
    test_superficies.py
```

**Funciones clave del motor:**

```python
# Superficie e indicadores urbanisticos
def calcular_superficies(spaces: list[Space]) -> SuperficieReport:
    """Calcula cubierta, semicubierta, total, usando Shapely."""

def verificar_fos_fot(
    terreno: Polygon,
    superficies: SuperficieReport,
    zona: ZonaUrbana
) -> Verificacion:
    """Compara contra limites de zona. Retorna cumple/no cumple."""

# Iluminacion y ventilacion natural
def verificar_iluminacion_natural(
    space: Space,
    openings: list[Opening]
) -> VerificacionIluminacion:
    """Relacion vidrio/piso >= ratio segun destino del local."""

def verificar_ventilacion_natural(
    space: Space,
    openings: list[Opening]
) -> VerificacionVentilacion:
    """Superficie de ventilacion >= 50% de iluminacion (tipico)."""

# Retiros
def verificar_retiros(
    building_footprint: Polygon,
    lot: Polygon,
    zona: ZonaUrbana
) -> VerificacionRetiros:
    """Frente, fondo, laterales segun zona."""
```

**Principios del motor:**

1. **Determinismo absoluto**: misma entrada, misma salida, siempre. Sin LLM en el loop.
2. **Trazabilidad**: cada verificacion cita la norma especifica (ej: "Codigo Urbano Neuquen, Art. 42, Zona R1").
3. **Versionado**: las normas cambian. Cada archivo tiene fecha de vigencia. El sistema advierte si una norma esta desactualizada.
4. **Tests con casos reales**: usar planos ya aprobados por el municipio como test cases. Si el motor dice "no cumple" para un plano que ya fue aprobado, hay un bug en el motor.

**El LLM participa solo en:**
- Interpretar que quiere calcular el usuario ("verificame las superficies").
- Formatear el resultado en lenguaje natural.
- Sugerir correcciones si algo no cumple ("el dormitorio 2 tiene 8.5m2, necesita 9m2 minimo, sugiero extender la pared w3 50cm al norte").

**Riesgos:**
- Codificar normas incorrectamente. Solucion: tests exhaustivos con casos reales + revision manual del arquitecto (Pablo) antes de confiar en el motor.
- Normas municipales de Neuquen no estan digitalizadas en formato parseable. Solucion: carga manual inicial, luego mantenimiento incremental. No es escalable a todo el pais, pero no necesita serlo.

---

## Resumen: Arquitectura Completa Propuesta

```
+--------------------------------------------------+
|              LINUX (NUC)                          |
|                                                   |
|  Claude Code (orquestador principal)              |
|       |                                           |
|       v                                           |
|  JSON Semantico (Pydantic validated)              |
|       |                                           |
|       +---> Motor de Normas Python                |
|       |         (calcula, valida, verifica)        |
|       |                                           |
|       +---> Motor de Dibujo Python (ezdxf)        |
|       |         (genera DXF desde JSON)           |
|       |                                           |
|       +---> Preview Server (uvicorn + WebSocket)  |
|                 |                                  |
|                 v                                  |
|             Browser (Canvas 2D preview)            |
|                                                   |
+--------------------------------------------------+
           |  WebSocket persistente (LAN)
           v
+--------------------------------------------------+
|              WINDOWS                              |
|                                                   |
|  MCP Server (Python)                              |
|       |                                           |
|       +---> AutoCAD via COM / pyautocad           |
|       |         (importa DXF, modifica, consulta) |
|       |                                           |
|       +---> File watcher                          |
|                 (detecta cambios del usuario)      |
|                                                   |
+--------------------------------------------------+
```

**Diferencias clave con la propuesta de Gemini:**

| Aspecto | Gemini | Mi propuesta |
|---------|--------|-------------|
| Transporte MCP | Implicito (HTTP?) | WebSocket bidireccional explicito |
| Preview | SVG estatico | Canvas 2D interactivo (zoom, pan, click) |
| Aprendizaje | RAG + LanceDB | Analisis deterministico + templates + FTS |
| Web framework | Ninguno (solo SVG) | Vite minimal (sin Next.js) |
| Motor de normas | Archivo JSON de limites | Modulos Python con logica + tests + trazabilidad |
| Bloques del usuario | En base vectorial | Filesystem (DXF individuales) |

**Orden de implementacion sugerido (iterativo):**

1. **Semana 1-2**: Extractor de convenciones + motor ezdxf basico (muros + aberturas).
2. **Semana 3-4**: MCP Server en Windows + conexion COM con AutoCAD.
3. **Semana 5-6**: Preview web con Canvas 2D + JSON schema completo.
4. **Semana 7-8**: Motor de normas (FOS/FOT + superficies + ventilacion).
5. **Semana 9-10**: Templates de planos + flujo completo end-to-end.
6. **Iteracion continua**: Agregar tipologias, normas IRAM, bloques, refinamiento.

**Tecnologias concretas:**

| Componente | Tecnologia | Justificacion |
|-----------|-----------|---------------|
| Orquestador | Claude Code + MCP | Nativo, ya instalado, soporta tools |
| Generacion DXF | Python 3.12 + ezdxf | Liviano, sin dependencias pesadas, funciona en Linux |
| Validacion JSON | Pydantic v2 | Rapido, tipado, genera JSON Schema |
| Geometria | Shapely | Estandar para operaciones 2D, calculo de areas |
| Preview backend | uvicorn + websockets | Minimo, async, eficiente |
| Preview frontend | Vite + Canvas 2D API | <50KB, sin framework pesado |
| MCP Server (Win) | Python + pyautocad + mcp lib | Bridge COM <-> MCP |
| Tests | pytest | Estandar Python, facil de mantener |
| Normas | Python puro + JSON de parametros | Deterministico, testeable, versionable |
