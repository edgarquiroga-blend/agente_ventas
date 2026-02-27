# 🤖 Agente de Análisis de Ventas con Agentic AI

Sistema de análisis de ventas en lenguaje natural que combina **LangChain**, **Claude/GPT-4**, **SQLite** y conectores al estilo **MCP** para interpretar preguntas, generar SQL, visualizar datos y exportar archivos.

---

## 📁 Estructura del proyecto

```
sales_agent/
│
├── main.py              # 🚀 Punto de entrada. CLI interactivo y modo demo.
├── agent.py             # 🧠 Definición del agente ReAct con LangChain.
├── sql_connector.py     # 🔌 Herramientas MCP: SQL, gráficos, CSV, Excel.
├── database.py          # 🗄️  Conexión SQLite, inicialización y ejecución SQL.
├── visualizer.py        # 📊 Generación de gráficos con Matplotlib.
├── file_exporter.py     # 💾 Exportación a CSV y Excel con openpyxl.
│
├── ventas.csv           # 📋 Datos de ejemplo (30 registros de ventas).
├── ventas.db            # 🗄️  Base de datos SQLite (se genera automáticamente).
├── requirements.txt     # 📦 Dependencias del proyecto.
├── .env.example         # 🔑 Plantilla para configurar API keys.
│
└── outputs/             # 📤 Archivos generados (gráficos PNG, CSV, Excel).
```

---

## 🧩 Arquitectura del sistema

```
[Usuario en lenguaje natural]
          │
          ▼
    ┌───────────┐
    │  main.py  │  ← CLI / interfaz de usuario
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │  agent.py │  ← Agente ReAct (LangChain)
    │           │    Ciclo: Thought → Action → Observation
    └─────┬─────┘
          │
    ┌─────┴────────────────────────────────┐
    ▼             ▼              ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ejecutar_ │ │generar_  │ │guardar_  │ │guardar_  │
│sql       │ │grafico   │ │csv       │ │excel     │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │             │             │             │
     ▼             ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│database  │ │visualizer│ │file_exp..│ │file_exp..│
│.py       │ │.py       │ │export_.. │ │export_.. │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### ¿Qué es el patrón MCP?

**MCP (Model-Connector Protocol)** es un protocolo que estandariza cómo los agentes de IA se comunican con sistemas externos. En este proyecto, las herramientas (`@tool`) en `sql_connector.py` implementan el mismo patrón de interfaz:

- **Nombre**: identificador de la herramienta.
- **Descripción**: texto en lenguaje natural que el LLM lee para decidir cuándo usarla.
- **Esquema de entrada**: parámetros tipados que el LLM debe proveer.

Esto es compatible con servidores MCP reales como [sqlite-mcp-server](https://github.com/modelcontextprotocol/servers).

---

## ⚙️ Instalación y configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd sales_agent
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API key
```bash
cp .env.example .env
# Editar .env y agregar tu API key de Anthropic o OpenAI
```

```env
ANTHROPIC_API_KEY=sk-ant-api03-...   # Para usar Claude
OPENAI_API_KEY=sk-...                # Para usar GPT-4 (alternativa)
```

---

## 🚀 Uso

### Modo interactivo (por defecto)
```bash
python main.py
```
Abre un chat en la terminal donde puedes escribir preguntas en lenguaje natural.

### Modo demo (preguntas de ejemplo automáticas)
```bash
python main.py --demo
```

### Pregunta única
```bash
python main.py --pregunta "Top 5 productos más vendidos en Medellín"
```

### Usar OpenAI en vez de Claude
```bash
python main.py --provider openai
```

---

## 💬 Ejemplos de preguntas y flujo interno

### Ejemplo 1: Consulta con tabla
**Usuario:** `"Top 5 productos más vendidos en Medellín"`

**Flujo interno:**
```
Thought: El usuario quiere ver los 5 productos con más unidades vendidas en Medellín.
         Necesito ejecutar una consulta SQL.
Action: ejecutar_sql
Action Input: SELECT producto, SUM(cantidad) AS total_vendido 
              FROM ventas 
              WHERE sede='Medellín' 
              GROUP BY producto 
              ORDER BY total_vendido DESC 
              LIMIT 5;
Observation: {"status": "ok", "filas": 5, "datos": [...]}
Final Answer: Los 5 productos más vendidos en Medellín son: ...
```

---

### Ejemplo 2: Consulta con gráfico
**Usuario:** `"Muéstrame un gráfico de ventas por sede"`

**Flujo interno:**
```
Thought: El usuario quiere visualizar datos → usar generar_grafico.
Action: generar_grafico
Action Input: {"consulta_sql": "SELECT sede, SUM(cantidad*precio) AS total FROM ventas GROUP BY sede",
               "tipo_grafico": "barras",
               "titulo": "Ventas Totales por Sede"}
Observation: ✅ Gráfico generado en outputs/grafico_Ventas_Totales_por_Sede_...png
Final Answer: Aquí tienes el gráfico de ventas por sede: ...
```

---

### Ejemplo 3: Exportar a CSV
**Usuario:** `"Guarda las ventas por vendedor en un archivo CSV"`

**Flujo interno:**
```
Thought: El usuario quiere exportar datos → usar guardar_csv.
Action: guardar_csv
Action Input: {"consulta_sql": "SELECT vendedor, SUM(cantidad*precio) AS total FROM ventas GROUP BY vendedor ORDER BY total DESC",
               "nombre_archivo": "ventas_por_vendedor"}
Observation: ✅ Archivo CSV guardado en: outputs/ventas_por_vendedor_...csv
Final Answer: Los datos fueron guardados en ventas_por_vendedor.csv
```

---

## 📖 Explicación de cada módulo

### `database.py` — Capa de datos
- **`initialize_database()`**: Crea la tabla `ventas` y carga el CSV si está vacía.
- **`execute_query(sql)`**: Ejecuta SQL y retorna `pd.DataFrame`. Solo permite SELECT.
- **`get_schema()`**: Retorna descripción textual del esquema para incluir en el prompt del LLM.

### `sql_connector.py` — Herramientas MCP
Define 4 herramientas con el decorador `@tool` de LangChain:
- **`ejecutar_sql`**: Ejecuta SQL y retorna JSON.
- **`generar_grafico`**: Ejecuta SQL + crea gráfico PNG.
- **`guardar_csv`**: Ejecuta SQL + exporta CSV.
- **`guardar_excel`**: Ejecuta SQL + exporta Excel con formato.

### `agent.py` — Agente ReAct
- Configura el LLM (Claude o GPT-4) con `temperature=0` para consistencia.
- Construye el prompt con el esquema de la BD para que el LLM genere SQL correcto.
- Usa `create_react_agent` de LangChain para el ciclo Thought→Action→Observation.
- `AgentExecutor` orquesta el ciclo con límite de 5 iteraciones.

### `visualizer.py` — Gráficos
- Detecta automáticamente las columnas X (texto) e Y (número).
- Soporta: `barras`, `lineas`, `torta`, `dispersion`.
- Guarda PNG en `outputs/` con nombre basado en el título + timestamp.

### `file_exporter.py` — Exportación
- **CSV**: UTF-8 con BOM para compatibilidad con Excel en Windows.
- **Excel**: Con encabezados formateados (negrita + fondo azul) y columnas auto-dimensionadas.

---

## 🗄️ Base de datos de ejemplo

La tabla `ventas` contiene 30 registros con:

| Campo     | Tipo    | Descripción                              |
|-----------|---------|------------------------------------------|
| id        | INTEGER | Identificador único                      |
| vendedor  | TEXT    | Nombre del vendedor (6 vendedores)       |
| sede      | TEXT    | Ciudad: Bogotá, Medellín, Cali           |
| producto  | TEXT    | Laptop, Mouse, Teclado, Monitor, Auriculares |
| cantidad  | INTEGER | Unidades vendidas                        |
| precio    | REAL    | Precio unitario en pesos colombianos     |
| fecha     | TEXT    | Fecha en formato YYYY-MM-DD              |

---

## 🔧 Extensibilidad

### Agregar un nuevo tipo de gráfico
En `visualizer.py`, agregar un nuevo bloque `elif` en `create_chart()`.

### Agregar una nueva herramienta
En `sql_connector.py`, crear una nueva función con `@tool` y agregarla a la lista `TOOLS`.

### Conectar a PostgreSQL/MySQL
En `database.py`, reemplazar `sqlite3.connect()` con el conector apropiado (ej. `psycopg2`, `pymysql`). La interfaz `execute_query()` permanece igual.

### Usar un servidor MCP real
Reemplazar las funciones `@tool` en `sql_connector.py` por llamadas al cliente MCP oficial de Anthropic, manteniendo la misma interfaz de entrada/salida.

---

## 🛠️ Tecnologías utilizadas

| Tecnología          | Rol                                    |
|---------------------|----------------------------------------|
| **LangChain**       | Framework de agentes (ReAct pattern)   |
| **Claude / GPT-4**  | LLM para NL→SQL y razonamiento         |
| **SQLite**          | Base de datos (sin servidor externo)   |
| **Pandas**          | Manipulación de resultados SQL         |
| **Matplotlib**      | Generación de gráficos PNG             |
| **openpyxl**        | Exportación a Excel con formato        |
| **MCP pattern**     | Protocolo de conectores estándar       |

---

## ⚠️ Limitaciones y consideraciones

1. **Seguridad SQL**: Solo se permiten consultas `SELECT` para proteger los datos.
2. **LLM no determinista**: Aunque `temperature=0`, el LLM puede generar SQL diferente.
3. **Base de datos de ejemplo**: Los datos son ficticios para demostración.
4. **API key requerida**: Necesitas una cuenta en Anthropic u OpenAI.
