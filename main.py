"""
main.py
-------
Punto de entrada de la aplicación.

Modos de uso:
    1. Modo interactivo (CLI): python main.py
    2. Modo demo (ejemplos automáticos): python main.py --demo
    3. Pregunta única: python main.py --pregunta "Top 5 productos más vendidos"

Flujo de la aplicación:
    1. Inicializar la base de datos (crear tabla + cargar CSV).
    2. Crear el agente de análisis.
    3. Recibir preguntas del usuario.
    4. Pasar las preguntas al agente y mostrar respuestas.
    5. Repetir hasta que el usuario escriba 'salir'.
"""

import argparse
import sys
from pathlib import Path

# Asegura que el directorio del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).parent))

from database import initialize_database
from agent import run_agent


# ─────────────────────────────────────────────────────────
# BANNER Y EJEMPLOS
# ─────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          🤖 AGENTE DE ANÁLISIS DE VENTAS                    ║
║          Powered by LangChain + Claude + SQLite             ║
╠══════════════════════════════════════════════════════════════╣
║  Escribe tu pregunta en lenguaje natural.                   ║
║  Ejemplos:                                                  ║
║    • "Top 5 productos más vendidos en Medellín"             ║
║    • "Vendedor con más ventas en Bogotá"                    ║
║    • "Muéstrame un gráfico de ventas por sede"              ║
║    • "Guarda las ventas por vendedor en un archivo CSV"     ║
║    • "Total de ingresos por producto"                       ║
║  Escribe 'salir' para terminar.                             ║
╚══════════════════════════════════════════════════════════════╝
"""

DEMO_PREGUNTAS = [
    "¿Cuál es el top 5 de productos más vendidos en Medellín?",
    "¿Quién fue el vendedor con más ventas en Bogotá?",
    "Muéstrame un gráfico de barras de las ventas totales por sede",
    "Guarda las ventas por vendedor en un archivo CSV",
    "¿Cuál es el total de ingresos generados por cada producto? Muéstralo en una tabla y en un gráfico",
]


# ─────────────────────────────────────────────────────────
# FUNCIONES PRINCIPALES
# ─────────────────────────────────────────────────────────

def interactive_mode(provider: str = "anthropic"):
    """
    Modo interactivo: el usuario escribe preguntas y el agente responde.
    
    Diseño:
        - Ciclo infinito hasta que el usuario escribe 'salir'.
        - Manejo de errores para no romper la sesión ante fallos.
        - Historial de preguntas en memoria durante la sesión.
    """
    print(BANNER)
    print(f"🔧 Usando proveedor: {provider.upper()}\n")

    historial = []

    while True:
        try:
            pregunta = input("👤 Tu pregunta: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ¡Hasta luego!")
            break

        if not pregunta:
            continue

        if pregunta.lower() in ("salir", "exit", "quit", "q"):
            print("👋 ¡Hasta luego!")
            break

        print(f"\n🤖 Procesando: '{pregunta}'")
        print("─" * 60)

        try:
            respuesta = run_agent(pregunta, provider=provider)
            historial.append({"pregunta": pregunta, "respuesta": respuesta})
            print(f"\n✅ Respuesta:\n{respuesta}")
        except Exception as e:
            print(f"\n❌ Error al procesar la pregunta: {e}")
            print("Por favor, intenta reformular tu pregunta.")

        print("\n" + "═" * 60 + "\n")


def demo_mode(provider: str = "anthropic"):
    """
    Modo demo: ejecuta un conjunto de preguntas de ejemplo automáticamente.
    Útil para mostrar las capacidades del agente sin interacción manual.
    """
    print("\n🎬 MODO DEMO - Ejecutando preguntas de ejemplo...\n")
    print("═" * 60)

    for i, pregunta in enumerate(DEMO_PREGUNTAS, 1):
        print(f"\n[{i}/{len(DEMO_PREGUNTAS)}] 👤 Pregunta: {pregunta}")
        print("─" * 60)

        try:
            respuesta = run_agent(pregunta, provider=provider)
            print(f"\n✅ Respuesta:\n{respuesta}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

        print("\n" + "═" * 60)

    print("\n🎬 Demo completado. Los archivos generados están en la carpeta 'outputs/'")


def single_query_mode(pregunta: str, provider: str = "anthropic"):
    """
    Modo de pregunta única: responde una sola pregunta y termina.
    Útil para scripting o integración con otras aplicaciones.
    """
    print(f"\n🤖 Procesando: '{pregunta}'")
    print("─" * 60)
    respuesta = run_agent(pregunta, provider=provider)
    print(f"\n✅ Respuesta:\n{respuesta}")
    return respuesta


# ─────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────

def main():
    """
    Función principal que parsea argumentos y ejecuta el modo correspondiente.
    """
    parser = argparse.ArgumentParser(
        description="Agente de análisis de ventas con IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                          # Modo interactivo
  python main.py --demo                   # Modo demo con preguntas de ejemplo
  python main.py --pregunta "Top 5 productos en Medellín"
  python main.py --provider openai        # Usar GPT-4o en vez de Claude
        """
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Ejecutar modo demo con preguntas de ejemplo"
    )
    parser.add_argument(
        "--pregunta",
        type=str,
        default=None,
        help="Ejecutar una sola pregunta y terminar"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai"],
        help="Proveedor del LLM: 'anthropic' (Claude) o 'openai' (GPT-4)"
    )

    args = parser.parse_args()

    # ── Paso 1: Inicializar la base de datos ─────────
    print("🔄 Inicializando base de datos...")
    initialize_database()

    # ── Paso 2: Ejecutar el modo solicitado ──────────
    if args.demo:
        demo_mode(provider=args.provider)
    elif args.pregunta:
        single_query_mode(pregunta=args.pregunta, provider=args.provider)
    else:
        interactive_mode(provider=args.provider)


if __name__ == "__main__":
    main()
