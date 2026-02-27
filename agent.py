import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from database import get_schema
from sql_connector import TOOLS

load_dotenv()

def get_system_prompt() -> str:
    schema = get_schema()
    return f"""Eres un agente experto en analisis de ventas. Responde preguntas sobre datos de ventas usando las herramientas disponibles.

ESQUEMA DE LA BASE DE DATOS:
{schema}

REGLAS:
1. SIEMPRE usa ejecutar_sql para obtener datos.
2. Si el usuario quiere ver datos usa ejecutar_sql.
3. Si quiere grafico o visualizar usa generar_grafico.
4. Si quiere guardar en CSV usa guardar_csv.
5. Si quiere guardar en Excel usa guardar_excel.
6. SQL valido para SQLite. Usa comillas simples para strings.
7. Total de ventas = cantidad * precio
8. Responde siempre en espanol."""

def create_agent(provider: str = "groq", model: str = None):
    if provider == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(model=model or "llama-3.3-70b-versatile", temperature=0, max_tokens=2048, groq_api_key=os.environ.get("GROQ_API_KEY"))
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model or "claude-opus-4-5", temperature=0, max_tokens=2048, anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"))
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model or "gpt-4o", temperature=0, max_tokens=2048, openai_api_key=os.environ.get("OPENAI_API_KEY"))
    else:
        raise ValueError(f"Proveedor '{provider}' no soportado.")
    return create_react_agent(model=llm, tools=TOOLS, prompt=get_system_prompt())

def run_agent(pregunta: str, provider: str = "groq") -> str:
    agent = create_agent(provider=provider)
    result = agent.invoke({"messages": [{"role": "user", "content": pregunta}]})
    messages = result.get("messages", [])
    if messages:
        return messages[-1].content
    return "No se pudo obtener una respuesta."
