Como experto en arquitectura de software y sistemas CAD, y considerando las limitaciones de hardware (Celeron J4005) y el contexto profesional en Argentina (CPTN Neuquén / IRAM), mi posición es que debemos construir un sistema **desacoplado y asincrónico**. No podemos sobrecargar la NUC con procesos pesados de CAD ni confiar ciegamente en la aritmética del LLM.

Aquí mi argumentación técnica sobre los 6 ejes:

### 1. Conexión con AutoCAD: MCP Server (Model Context Protocol)
*   **Posición:** **MCP Server** corriendo en la máquina Windows (donde está AutoCAD) actuando como puente para Claude Code (en Linux).
*   **Argumento:** Claude Code soporta MCP nativamente. El servidor MCP en Windows expondría "herramientas" (tools) que AutoCAD entiende. La comunicación sería: `Claude Code (Linux) <-> Red Local <-> MCP Server (Windows/Python) <-> pyautocad/COM <-> AutoCAD`.
*   **Riesgos:** Latencia de red local y configuración de permisos COM en Windows.
*   **Solución:** Un servidor MCP escrito en Python (usando la librería `mcp`) que traduzca intenciones del LLM en comandos `SendStringToExecute` de AutoCAD o llamadas a la API .NET.

### 2. Generación: Híbrido (ezdxf Offline + Inyectores AutoLISP)
*   **Posición:** **Offline DXF con `ezdxf`** para la creación masiva y **AutoLISP** para modificaciones en vivo.
*   **Argumento:** Tu Celeron J4005 sufrirá si intentas mantener una conexión COM bidireccional constante para dibujar miles de entidades. Es mejor que el LLM genere un archivo DXF temporal usando `ezdxf` (muy liviano, corre perfecto en Linux) y luego dar la orden a AutoCAD de insertar ese archivo como bloque o "explodearlo".
*   **Riesgos:** Pérdida de interactividad si solo es offline.
*   **Solución:** Usar `ezdxf` para generar la geometría compleja (plantas, cortes) y comandos de AutoLISP directos para "mover", "borrar" o "cambiar layer" de objetos específicos.

### 3. Formato Intermedio: JSON Estructurado (Semantic Architectural Layer)
*   **Posición:** **JSON con Schema estricto** que represente entidades arquitectónicas, no solo geométricas.
*   **Argumento:** El LLM no debe decir "dibuja una línea de 0,0 a 0,4". Debe decir `{"type": "wall", "start": [0,0], "length": 4.0, "thickness": 0.15, "function": "exterior"}`. Esto permite que el "motor de dibujo" aplique las normas IRAM (layers, espesores de pluma) automáticamente.
*   **Riesgos:** Las "alucinaciones" del LLM en coordenadas decimales.
*   **Solución:** Validar el JSON con **Pydantic** antes de enviarlo al motor de dibujo. Si el JSON no valida, el error vuelve al LLM para corrección.

### 4. Aprendizaje de Planos: RAG sobre Metadatos de DXF
*   **Posición:** **Retrieval-Augmented Generation (RAG)** basado en la estructura de capas y bloques de tus planos existentes.
*   **Argumento:** No necesitas entrenar un modelo. Necesitas un script que analice tus últimos 50 planos municipales, extraiga el estándar de capas (ej: `01-MUROS-EXISTENTES`), nombres de bloques y estilos de cota, y guarde eso en una base de datos vectorial (como LanceDB, que es muy liviana).
*   **Riesgos:** Planos viejos con estándares "sucios" que confundan al modelo.
*   **Solución:** Crear un "Template de Contexto" que se inyecte en el prompt de Claude, listando tus bloques y capas preferidas según el tipo de plano (Municipal vs. Ejecutivo).

### 5. Stack y UX: CLI-First (Claude Code) con Previsualizador SVG
*   **Posición:** Mantener **Claude Code (CLI)** como interfaz principal, pero con un **visualizador SVG liviano**.
*   **Argumento:** No gastes recursos en una App Next.js pesada. Claude Code es extremadamente eficiente. Para el feedback visual (fundamental para un arquitecto), el MCP server debe generar un preview en SVG que puedas abrir en el navegador de Linux para validar antes de "enviar" a AutoCAD en Windows.
*   **Riesgos:** La fricción de cambiar entre la terminal y AutoCAD.
*   **Solución:** Usar la capacidad de Claude Code para ejecutar comandos de shell y abrir el visualizador de imágenes/browser automáticamente al generar una propuesta.

### 6. Normas y Cálculos: Motor de Reglas Determinístico (Python)
*   **Posición:** **Nunca dejar que el LLM calcule el FOS/FOT o iluminación.** El LLM extrae los datos, Python calcula.
*   **Argumento:** Los LLMs son pésimos en aritmética precisa. El flujo debe ser: 1. LLM identifica polígonos de locales. 2. Librería `Shapely` (Python) calcula superficies reales. 3. Un archivo `normas_neuquen.json` provee los límites. 4. El sistema devuelve la planilla de superficies calculada.
*   **Riesgos:** Que el LLM interprete mal las zonas del código urbano.
*   **Solución:** Crear una "Calculadora de Normas" como una herramienta (tool) del MCP server. El LLM solo pasa los parámetros (ej: "Zona R1, Terreno 300m2"), y Python devuelve el veredicto técnico basado en las tablas IRAM y el código local.

**Conclusión:** Tu ventaja competitiva no es que el LLM "dibuje", sino que "coordine" tu estándar profesional. Mi propuesta es un **Orquestador en Linux (Claude Code)** que mande **instrucciones JSON** a un **Agente de Ejecución en Windows**, usando **Python** como validador de geometría y normas.
