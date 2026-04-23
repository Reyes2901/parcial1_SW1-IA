# app/config.py
from dotenv import load_dotenv
import os

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
SPRING_BOOT_URL = os.getenv("SPRING_BOOT_URL", "http://localhost:8080")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://localhost:8080").split(",")


def get_llm_client():
    """Devuelve el cliente LLM según la configuración"""
    if LLM_PROVIDER == "openai":
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=OPENAI_API_KEY)
    elif LLM_PROVIDER == "anthropic":
        import anthropic
        return anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    else:
        raise ValueError(f"Proveedor no soportado: {LLM_PROVIDER}")


def get_model_config():
    """Devuelve la configuración del modelo"""
    return {
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE
    }