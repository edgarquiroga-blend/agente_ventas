"""
database.py
-----------
Módulo responsable de:
1. Crear la base de datos SQLite en memoria (o en archivo).
2. Cargar los datos desde el CSV de ejemplo.
3. Exponer funciones para ejecutar consultas SQL de forma segura.

¿Por qué SQLite?
   - No requiere servidor externo.
   - Ideal para prototipado rápido.
   - Compatible con el conector MCP sqlite que se usa en el agente.
"""

import sqlite3
import pandas as pd
from pathlib import Path


DB_PATH = Path(__file__).parent / "ventas.db"
CSV_PATH = Path(__file__).parent / "ventas.csv"


def get_connection() -> sqlite3.Connection:
    """
    Retorna una conexión a la base de datos SQLite.
    Si el archivo no existe, lo crea automáticamente.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder columnas por nombre
    return conn


def initialize_database():
    """
    Inicializa la base de datos:
    - Crea la tabla 'ventas' si no existe.
    - Carga los datos desde el CSV si la tabla está vacía.

    Estructura de la tabla:
        id        INTEGER  - Identificador único
        vendedor  TEXT     - Nombre del vendedor
        sede      TEXT     - Ciudad de la sede (Bogotá, Medellín, Cali, etc.)
        producto  TEXT     - Nombre del producto
        cantidad  INTEGER  - Unidades vendidas
        precio    REAL     - Precio unitario en pesos colombianos
        fecha     TEXT     - Fecha de la venta (formato YYYY-MM-DD)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Crear tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id       INTEGER PRIMARY KEY,
            vendedor TEXT    NOT NULL,
            sede     TEXT    NOT NULL,
            producto TEXT    NOT NULL,
            cantidad INTEGER NOT NULL,
            precio   REAL    NOT NULL,
            fecha    TEXT    NOT NULL
        )
    """)

    # Cargar datos desde CSV si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM ventas")
    count = cursor.fetchone()[0]

    if count == 0 and CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        df.to_sql("ventas", conn, if_exists="append", index=False)
        print(f"✅ Base de datos inicializada con {len(df)} registros desde '{CSV_PATH.name}'")
    else:
        print(f"✅ Base de datos lista ({count} registros existentes)")

    conn.commit()
    conn.close()


def execute_query(sql: str) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL SELECT y retorna los resultados como DataFrame.

    Parámetros:
        sql: Consulta SQL (solo SELECT por seguridad).

    Retorna:
        DataFrame con los resultados.

    Lanza:
        ValueError si la consulta no es un SELECT.
        Exception si hay error en la ejecución.
    """
    # Seguridad básica: solo permitir consultas de lectura
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT"):
        raise ValueError("Solo se permiten consultas SELECT para proteger los datos.")

    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def get_schema() -> str:
    """
    Retorna el esquema de la tabla 'ventas' como texto.
    Esto se incluye en el prompt del LLM para que entienda la estructura.
    """
    return """
    Tabla: ventas
    Columnas:
      - id       INTEGER  : Identificador único del registro
      - vendedor TEXT     : Nombre completo del vendedor
      - sede     TEXT     : Ciudad de la sede (Bogotá, Medellín, Cali)
      - producto TEXT     : Nombre del producto (Laptop, Mouse, Teclado, Monitor, Auriculares)
      - cantidad INTEGER  : Número de unidades vendidas en esa transacción
      - precio   REAL     : Precio unitario en pesos colombianos
      - fecha    TEXT     : Fecha de la venta en formato 'YYYY-MM-DD'
    
    Nota: El total de una venta se calcula como cantidad * precio
    """
