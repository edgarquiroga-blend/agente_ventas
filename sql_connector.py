"""
sql_connector.py
----------------
Conector SQL que actúa como una herramienta (tool) para el agente LangChain.

¿Qué es un conector MCP?
   MCP (Model-Connector Protocol) es un protocolo que estandariza cómo los
   agentes de IA se comunican con sistemas externos (bases de datos, APIs, etc.).
   En este proyecto simulamos un conector MCP sobre SQLite, siguiendo el mismo
   patrón de interfaz que usaría un conector MCP real (ej. el servidor MCP de SQLite
   de Anthropic: https://github.com/modelcontextprotocol/servers).

   La idea es que el agente llame a esta herramienta pasando SQL como texto,
   y recibe los resultados como JSON/DataFrame, igual que lo haría con MCP real.

Arquitectura:
   [Usuario] → [Agente LangChain] → [Tool: ejecutar_sql] → [SQLite DB]
                                   → [Tool: generar_grafico] → [PNG/HTML]
                                   → [Tool: guardar_archivo] → [CSV/Excel]
"""

import json
from langchain.tools import tool
from database import execute_query
from visualizer import create_chart
from file_exporter import export_to_csv, export_to_excel


# ─────────────────────────────────────────────
# HERRAMIENTA 1: Ejecutar consulta SQL
# ─────────────────────────────────────────────
@tool
def ejecutar_sql(consulta_sql: str) -> str:
    """
    Ejecuta una consulta SQL sobre la base de datos de ventas y retorna
    los resultados en formato JSON.

    Úsala cuando necesites obtener datos de la base de datos.
    La base de datos tiene una tabla llamada 'ventas' con columnas:
    id, vendedor, sede, producto, cantidad, precio, fecha.

    Parámetros:
        consulta_sql: La consulta SQL SELECT a ejecutar.

    Retorna:
        JSON con los resultados o mensaje de error.
    """
    try:
        df = execute_query(consulta_sql)
        if df.empty:
            return json.dumps({"status": "ok", "mensaje": "No se encontraron resultados.", "datos": []})
        
        result = {
            "status": "ok",
            "filas": len(df),
            "columnas": list(df.columns),
            "datos": df.to_dict(orient="records")
        }
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"status": "error", "mensaje": str(e)})


# ─────────────────────────────────────────────
# HERRAMIENTA 2: Generar gráfico
# ─────────────────────────────────────────────
@tool
def generar_grafico(consulta_sql: str, tipo_grafico: str, titulo: str) -> str:
    """
    Ejecuta una consulta SQL y genera un gráfico con los resultados.

    Úsala cuando el usuario quiera ver los datos de forma visual
    (gráfico de barras, líneas, torta, etc.).

    Parámetros:
        consulta_sql:  Consulta SQL que retorna los datos a graficar.
        tipo_grafico:  Tipo de gráfico: 'barras', 'lineas', 'torta', 'dispersion'.
        titulo:        Título descriptivo para el gráfico.

    Retorna:
        Mensaje indicando que el gráfico fue generado y guardado.
    """
    try:
        df = execute_query(consulta_sql)
        if df.empty:
            return "No hay datos para graficar."
        
        path = create_chart(df, tipo_grafico, titulo)
        return f"✅ Gráfico generado y guardado en: {path}"
    except Exception as e:
        return f"❌ Error al generar gráfico: {str(e)}"


# ─────────────────────────────────────────────
# HERRAMIENTA 3: Exportar a CSV
# ─────────────────────────────────────────────
@tool
def guardar_csv(consulta_sql: str, nombre_archivo: str) -> str:
    """
    Ejecuta una consulta SQL y guarda los resultados en un archivo CSV.

    Úsala cuando el usuario quiera exportar datos a un archivo CSV.

    Parámetros:
        consulta_sql:    Consulta SQL que retorna los datos a exportar.
        nombre_archivo:  Nombre del archivo (sin extensión, ej: 'ventas_bogota').

    Retorna:
        Mensaje indicando la ruta del archivo generado.
    """
    try:
        df = execute_query(consulta_sql)
        if df.empty:
            return "No hay datos para exportar."
        
        path = export_to_csv(df, nombre_archivo)
        return f"✅ Archivo CSV guardado en: {path}"
    except Exception as e:
        return f"❌ Error al exportar CSV: {str(e)}"


# ─────────────────────────────────────────────
# HERRAMIENTA 4: Exportar a Excel
# ─────────────────────────────────────────────
@tool
def guardar_excel(consulta_sql: str, nombre_archivo: str) -> str:
    """
    Ejecuta una consulta SQL y guarda los resultados en un archivo Excel (.xlsx).

    Úsala cuando el usuario quiera exportar datos a Excel.

    Parámetros:
        consulta_sql:    Consulta SQL que retorna los datos a exportar.
        nombre_archivo:  Nombre del archivo (sin extensión, ej: 'reporte_ventas').

    Retorna:
        Mensaje indicando la ruta del archivo generado.
    """
    try:
        df = execute_query(consulta_sql)
        if df.empty:
            return "No hay datos para exportar."
        
        path = export_to_excel(df, nombre_archivo)
        return f"✅ Archivo Excel guardado en: {path}"
    except Exception as e:
        return f"❌ Error al exportar Excel: {str(e)}"


# Lista de todas las herramientas disponibles para el agente
TOOLS = [ejecutar_sql, generar_grafico, guardar_csv, guardar_excel]
