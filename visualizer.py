"""
visualizer.py
-------------
Módulo de visualización de datos usando Matplotlib.

Responsabilidades:
    - Recibir un DataFrame de pandas con los resultados de una consulta SQL.
    - Detectar automáticamente qué columnas usar para X e Y.
    - Generar el tipo de gráfico solicitado.
    - Guardar el gráfico como imagen PNG en la carpeta 'outputs/'.

¿Por qué Matplotlib?
    - No requiere conexión a internet ni servidor externo.
    - Genera imágenes estáticas fáciles de compartir.
    - Alternativas: Plotly (interactivo), Altair (declarativo).
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from datetime import datetime


OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)  # Crear carpeta si no existe


def _detect_columns(df: pd.DataFrame):
    """
    Detecta automáticamente cuál columna usar como:
    - x_col: categoría o etiqueta (columna de texto)
    - y_col: valor numérico a graficar
    
    Estrategia:
        1. La primera columna de texto es el eje X (categoría).
        2. La primera columna numérica es el eje Y (valor).
    """
    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    x_col = text_cols[0] if text_cols else df.columns[0]
    y_col = num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]

    return x_col, y_col


def create_chart(df: pd.DataFrame, tipo: str, titulo: str) -> str:
    """
    Genera un gráfico a partir de un DataFrame y lo guarda en PNG.

    Parámetros:
        df:     DataFrame con los datos (resultado de una consulta SQL).
        tipo:   Tipo de gráfico: 'barras', 'lineas', 'torta', 'dispersion'.
        titulo: Título del gráfico.

    Retorna:
        Ruta del archivo PNG generado.
    """
    x_col, y_col = _detect_columns(df)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')

    tipo_lower = tipo.lower().strip()

    # ── Gráfico de Barras ─────────────────────────────
    if tipo_lower in ("barras", "barra", "bar", "bars"):
        colors = plt.cm.Blues_r([i / len(df) * 0.7 + 0.3 for i in range(len(df))])
        bars = ax.bar(df[x_col].astype(str), df[y_col], color=colors, edgecolor='white', linewidth=0.5)
        
        # Etiquetas sobre cada barra
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                    f'{h:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xlabel(x_col.replace("_", " ").title(), fontsize=11)
        ax.set_ylabel(y_col.replace("_", " ").title(), fontsize=11)
        ax.tick_params(axis='x', rotation=30)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # ── Gráfico de Líneas ─────────────────────────────
    elif tipo_lower in ("lineas", "linea", "line", "lines"):
        ax.plot(df[x_col].astype(str), df[y_col], marker='o', linewidth=2.5,
                color='#2196F3', markersize=8, markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(range(len(df)), df[y_col], alpha=0.1, color='#2196F3')
        ax.set_xlabel(x_col.replace("_", " ").title(), fontsize=11)
        ax.set_ylabel(y_col.replace("_", " ").title(), fontsize=11)
        ax.tick_params(axis='x', rotation=30)

    # ── Gráfico de Torta ──────────────────────────────
    elif tipo_lower in ("torta", "pie", "pastel", "dona"):
        wedges, texts, autotexts = ax.pie(
            df[y_col], labels=df[x_col].astype(str),
            autopct='%1.1f%%', startangle=90,
            colors=plt.cm.Set3.colors[:len(df)]
        )
        for text in autotexts:
            text.set_fontsize(9)

    # ── Gráfico de Dispersión ─────────────────────────
    elif tipo_lower in ("dispersion", "scatter", "puntos"):
        ax.scatter(df[x_col].astype(str), df[y_col], s=100, color='#4CAF50', alpha=0.7, edgecolors='white')
        ax.set_xlabel(x_col.replace("_", " ").title(), fontsize=11)
        ax.set_ylabel(y_col.replace("_", " ").title(), fontsize=11)
        ax.tick_params(axis='x', rotation=30)

    else:
        # Por defecto: barras horizontales
        ax.barh(df[x_col].astype(str), df[y_col], color='#42A5F5')
        ax.set_xlabel(y_col.replace("_", " ").title(), fontsize=11)

    # Estilo general del gráfico
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20, color='#1a1a2e')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    plt.tight_layout()

    # Guardar con nombre único basado en timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_titulo = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in titulo)[:40]
    filename = OUTPUT_DIR / f"grafico_{safe_titulo}_{timestamp}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return str(filename)
