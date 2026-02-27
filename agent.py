"""
agent.py
--------
Módulo principal del agente de análisis de ventas.

¿Qué es un agente de IA?
    Un agente es un sistema que usa un LLM (Large Language Model) para:
    1. Entender la intención del usuario en lenguaje natural.
    2. Decidir qué herramientas usar (SQL, gráficos, archivos).
    3. Ejecutar las herramientas y observar los resultados.
    4. Iterar hasta tener una respuesta final para el usuario.

Framework usado: LangChain con ReAct (Reasoning + Acting)
    - LangChain: Framework popular para construir aplicaciones con LLMs.
    - ReAct: Patrón de agente que alterna entre razonar y actuar.
    - El agente sigue el ciclo: Thought → Action → Observation → Thought...

Arquitectura del agente:
    ┌────────────────────────────────────────────────────┐
    │                   AGENTE ReAct                     │
    │                                                    │
    │  [Prompt con esquema DB] ──► [LLM: Claude/GPT]    │
    │                                    │               │
    │              ┌─────────────────────┘               │
    │              ▼                                     │
    │         Decide herramienta                         │
    │              │                                     │
    │    ┌─────────┴──────────┐                          │
    │    ▼         ▼          ▼         ▼                │
    │ ejecutar  generar   guardar   guardar               │
    │   sql     grafico    csv      excel                │
    │    │         │          │         │                │
    │    └─────────┴──────────┴─────────┘               │
    │              │                                     │
    │         [Resultado] → LLM → Respuesta final        │
    └────────────────────────────────────────────────────┘

Conector MCP:
    Las herramientas (tools) implementan el patrón MCP:
    - Interfaz estandarizada: nombre, descripción, esquema de entrada.
    - El LLM selecciona y llama herramientas usando su descripción.
    - Compatible con servidores MCP reales (ej. sqlite-mcp-server).
"""

import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from database import get_schema
from sql_connector import TOOLS


# ─────────────────────────────────────────────────────────
# PROMPT DEL SISTEMA
# ─────────────────────────────────────────────────────────
# El prompt es CRUCIAL: le dice al LLM:
#   1. Quién es y qué puede hacer.
#   2. El esquema de la base de datos (para generar SQL correcto).
#   3. Las reglas de comportamiento.
#   4. El formato de respuesta esperado (ReAct).
# ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente experto en análisis de ventas. Tu trabajo es responder 
preguntas sobre datos de ventas usando las herramientas disponibles.

ESQUEMA DE LA BASE DE DATOS:
{schema}

HERRAMIENTAS DISPONIBLES:
{{tools}}

REGLAS IMPORTANTES:
1. SIEMPRE usa la herramienta 'ejecutar_sql' para obtener datos antes de responder.
2. Detecta la INTENCIÓN del usuario de forma flexible:
   - Si quiere ver datos → usa 'ejecutar_sql' y presenta los resultados en tabla.
   - Si quiere visualizar, graficar, ver en gráfico, de forma visual → usa 'generar_grafico'.
   - Si quiere guardar, exportar, descargar en CSV → usa 'guardar_csv'.
   - Si quiere guardar, exportar en Excel → usa 'guardar_excel'.
   - A veces querrá VARIAS cosas a la vez (tabla + gráfico, por ejemplo).
3. Genera SQL válido para SQLite. Usa comillas simples para strings.
4. El total de ventas se calcula como: cantidad * precio
5. Para el nombre del archivo CSV/Excel, usa nombres descriptivos en español sin espacios
   (ej: 'ventas_por_vendedor', 'top_productos_medellin').
6. Para el tipo de gráfico, usa: 'barras', 'lineas', 'torta' o 'dispersion'.

FORMATO DE RESPUESTA (ReAct):
Debes seguir este formato EXACTAMENTE:

Question: la pregunta del usuario
Thought: piensa qué necesitas hacer
Action: nombre_de_la_herramienta
Action Input: el input para la herramienta
Observation: resultado de la herramienta
... (repite Thought/Action/Observation si necesitas)
Thought: ya tengo la respuesta final
Final Answer: respuesta clara y amigable para el usuario

Nombres de herramientas disponibles: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}"""


def create_agent(provider: str = "anthropic", model: str = None):
    """
    Crea y retorna el agente de análisis de ventas.

    Parámetros:
        provider: Proveedor del LLM: 'anthropic' o 'openai'.
        model:    Nombre del modelo. Si es None, usa el modelo por defecto.

    Retorna:
        AgentExecutor: El agente listo para recibir preguntas.

    Configuración del LLM:
        - temperature=0: Respuestas deterministas (ideal para SQL y análisis).
        - max_tokens=2048: Suficiente para respuestas detalladas.
    """
    # ── Seleccionar LLM ───────────────────────────────
    if provider == "anthropic":
        llm = ChatAnthropic(
            model=model or "claude-opus-4-5",
            temperature=0,
            max_tokens=2048,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
    elif provider == "openai":
        llm = ChatOpenAI(
            model=model or "gpt-4o",
            temperature=0,
            max_tokens=2048,
            openai_api_key=os.environ.get("OPENAI_API_KEY")
        )
    else:
        raise ValueError(f"Proveedor '{provider}' no soportado. Usa 'anthropic' o 'openai'.")

    # ── Construir el prompt con el esquema de DB ──────
    # Insertamos el esquema de la BD en el prompt del sistema
    # para que el LLM sepa exactamente qué columnas existen.
    schema = get_schema()
    prompt_text = SYSTEM_PROMPT.format(schema=schema)

    prompt = PromptTemplate.from_template(prompt_text)

    # ── Crear el agente ReAct ─────────────────────────
    # create_react_agent construye el ciclo:
    #   LLM → decide herramienta → ejecuta → observa → LLM → ...
    agent = create_react_agent(
        llm=llm,
        tools=TOOLS,
        prompt=prompt
    )

    # ── AgentExecutor: orquesta el ciclo del agente ───
    # verbose=True → muestra el razonamiento interno (útil para debug)
    # max_iterations=5 → evita bucles infinitos
    # handle_parsing_errors → maneja errores de formato del LLM
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

    return executor


def run_agent(pregunta: str, provider: str = "anthropic") -> str:
    """
    Función de alto nivel: recibe una pregunta y retorna la respuesta del agente.

    Parámetros:
        pregunta: Pregunta en lenguaje natural sobre las ventas.
        provider: Proveedor del LLM ('anthropic' o 'openai').

    Retorna:
        Respuesta final del agente como texto.
    """
    agent = create_agent(provider=provider)
    result = agent.invoke({"input": pregunta})
    return result.get("output", "No se pudo obtener una respuesta.")
