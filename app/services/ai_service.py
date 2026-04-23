# app/services/ai_service.py
import json
import re
import logging
from app.config import get_llm_client, MODEL_NAME, MAX_TOKENS, TEMPERATURE, LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.models.response import DiagramResponse
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_message, build_refine_message

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = None
        if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
            self.client = get_llm_client()
        elif LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            self.client = get_llm_client()
    
    async def generate_diagram(self, request) -> DiagramResponse:
        """Llama al LLM y parsea la respuesta como DiagramResponse."""
        
        # Si no hay cliente, usar mock
        if self.client is None:
            return self._generate_mock(request.prompt)
        
        user_message = build_user_message(request)
        raw_json = await self._call_llm(user_message)
        diagram_dict = await self._parse_with_retry(raw_json)
        
        diagram_dict["generatedBy"] = "ai"
        diagram_dict["promptUsed"] = request.prompt
        
        return DiagramResponse(**diagram_dict)
    
    async def refine_diagram(self, request) -> DiagramResponse:
        """Modifica un diagrama existente."""
        if self.client is None:
            return self._generate_mock(request.prompt)
        
        user_message = build_refine_message(request)
        raw_json = await self._call_llm(user_message)
        diagram_dict = await self._parse_with_retry(raw_json)
        
        diagram_dict["generatedBy"] = "ai-refined"
        diagram_dict["promptUsed"] = request.prompt
        
        return DiagramResponse(**diagram_dict)
    
    async def _call_llm(self, user_message: str) -> str:
        """Llamada al LLM según el proveedor configurado."""
        logger.info("Llamando LLM: %s | provider: %s", MODEL_NAME, LLM_PROVIDER)

        if LLM_PROVIDER == "openai":
            response = await self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content

        elif LLM_PROVIDER == "anthropic":
            response = await self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text

        raise ValueError(f"Proveedor no soportado: {LLM_PROVIDER}")
    
    async def _parse_with_retry(self, raw: str, attempts: int = 2) -> dict:
        """Intenta parsear el JSON. Si falla, pide al LLM que lo corrija."""
        for attempt in range(attempts):
            try:
                cleaned = self._clean_json_string(raw)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning("JSON inválido en intento %d: %s", attempt + 1, e)
                if attempt < attempts - 1 and self.client:
                    fix_prompt = f"""El siguiente JSON tiene un error de sintaxis: {e}
Corrígelo y devuelve SOLO el JSON válido sin texto adicional:

{raw}"""
                    raw = await self._call_llm(fix_prompt)
                else:
                    raise ValueError(f"No se pudo parsear: {e}\n\nRespuesta: {raw[:500]}")
    
    def _clean_json_string(self, raw: str) -> str:
        """Elimina bloques markdown y espacios."""
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return cleaned.strip()
    
    def _generate_mock(self, prompt: str) -> DiagramResponse:
        """Mock para desarrollo sin API key"""
        import uuid
        from app.models.response import Lane, Node, Transition, Position
        
        lane_id = f"lane-{uuid.uuid4().hex[:6]}"
        start_id = f"node-start-{uuid.uuid4().hex[:6]}"
        activity_id = f"node-activity-{uuid.uuid4().hex[:6]}"
        end_id = f"node-end-{uuid.uuid4().hex[:6]}"
        
        return DiagramResponse(
            name="Proceso generado por IA (Mock)",
            description=f"Diagrama generado desde: {prompt[:50]}...",
            lanes=[Lane(id=lane_id, name="Departamento Principal", departmentId="dept-1", order=1, color="#4CAF50")],
            nodes=[
                Node(id=start_id, type="START", label="Inicio", laneId=lane_id, position=Position(x=100, y=50)),
                Node(id=activity_id, type="ACTIVITY", label="Procesar solicitud", laneId=lane_id, assigneeRole="FUNCIONARIO", estimatedDurationHours=2, position=Position(x=100, y=150)),
                Node(id=end_id, type="END", label="Fin", laneId=lane_id, position=Position(x=100, y=250))
            ],
            transitions=[
                Transition(id=f"trans-{uuid.uuid4().hex[:6]}", sourceId=start_id, targetId=activity_id, label="Iniciar"),
                Transition(id=f"trans-{uuid.uuid4().hex[:6]}", sourceId=activity_id, targetId=end_id, label="Completar")
            ],
            generatedBy="ai-mock",
            promptUsed=prompt
        )