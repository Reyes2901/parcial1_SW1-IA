# AGENTS.md — Guía de Convenciones para Agentes de IA

Este archivo define las convenciones, restricciones y patrones que cualquier agente de IA debe seguir al trabajar en este proyecto **FastAPI + Google Gemini** (generador de diagramas BPMN).

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI (Python 3.12+) |
| IA Principal | Google Gemini (`google-generativeai`) |
| Modelos de datos | Pydantic v2 |
| Servidor | Uvicorn (ASGI) |
| Variables de entorno | `python-dotenv` / `.env` |

---

## Estructura del Proyecto

```
wbs-ia-ai/
├── main.py                      # Punto de entrada FastAPI
├── .env                         # Variables de entorno (NO commitear)
├── requirements.txt
├── app/
│   ├── config.py                # Configuración central y cliente LLM
│   ├── routers/
│   │   └── diagram.py           # Endpoints REST
│   ├── services/
│   │   ├── ai_service.py        # Lógica de IA + fallback Mock
│   │   └── prompt_builder.py    # Construcción de prompts
│   └── models/
│       ├── request.py           # Modelos de entrada (Pydantic)
│       └── response.py          # Modelos de salida (Pydantic)
```

---

## Reglas de Código

### 1. Manejo de Errores — Graceful Degradation

**Nunca** lanzar HTTP 500 por fallos de APIs externas. Todo error de la IA externa **debe** caer al Mock:

```python
# ✅ CORRECTO
try:
    raw_json = await self._call_llm(user_message)
    diagram_dict = await self._parse_with_retry(raw_json)
except Exception as e:
    logger.error("Error en el servicio de IA, cayendo a Mock: %s", str(e))
    return self._generate_mock(request.prompt)

# ❌ INCORRECTO — deja que la excepción propague un HTTP 500
raw_json = await self._call_llm(user_message)
```

### 2. Logging

Usar `logging.getLogger(__name__)` en cada módulo. Niveles:
- `logger.info` → flujo normal
- `logger.warning` → degradación o cliente no inicializado
- `logger.error` → fallo capturado que activa el fallback

### 3. Proveedor LLM

El proveedor se controla con `LLM_PROVIDER` en `.env` (`gemini` | `openai` | `anthropic`). Siempre normalizar a minúsculas: `LLM_PROVIDER.lower()`.

### 4. Modelos Pydantic

- Usar Pydantic v2 (`model_config`, `model_validator`, etc.).
- **No** usar `response_schema` en Gemini (conflicto con Pydantic v2); usar `response_mime_type="application/json"`.

### 5. Endpoints

- Los routers viven en `app/routers/`.
- Registrarlos en `main.py` con `app.include_router(...)`.
- Usar `async def` para todos los handlers.

---

## Variables de Entorno Requeridas

```env
LLM_PROVIDER=gemini          # gemini | openai | anthropic
GEMINI_API_KEY=...
MODEL_NAME=gemini-1.5-flash
MAX_TOKENS=8192
TEMPERATURE=0.3
```

---

## Convenciones Git

- `main` → rama estable
- Commits en español o inglés, descriptivos
- No commitear `.env`, `__pycache__/`, `*.pyc`

---

## Instrucciones para el Agente

1. **Leer este archivo primero** antes de modificar cualquier servicio.
2. Mantener la estrategia de **Graceful Degradation**: si la IA externa falla, retornar `_generate_mock(...)`.
3. No romper la estructura de `DiagramResponse`; todos los campos son requeridos por el frontend.
4. Al añadir dependencias, agregarlas a `requirements.txt`.
5. Ejecutar `uvicorn main:app --reload --port 8000` para probar localmente.
