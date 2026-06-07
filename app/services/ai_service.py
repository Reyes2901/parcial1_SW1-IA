# app/services/ai_service.py
import json
import logging
import os
import uuid
import google.generativeai as genai
from app.config import (
    get_llm_client, 
    MODEL_NAME, 
    MAX_TOKENS, 
    TEMPERATURE, 
    LLM_PROVIDER, 
    OPENAI_API_KEY, 
    ANTHROPIC_API_KEY
)
from app.models.response import DiagramResponse
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_message, build_refine_message

try:
    from app.config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = None
        
        # Forzar minúsculas para evitar fallos por "Gemini" vs "gemini"
        provider = LLM_PROVIDER.lower() if LLM_PROVIDER else ""
        
        if provider == "openai" and OPENAI_API_KEY:
            self.client = get_llm_client()
        elif provider == "anthropic" and ANTHROPIC_API_KEY:
            self.client = get_llm_client()
        elif provider == "gemini":
            active_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if active_key:
                genai.configure(api_key=active_key)
                self.client = genai.GenerativeModel(
                    model_name=MODEL_NAME if MODEL_NAME else "gemini-1.5-flash",
                    system_instruction=SYSTEM_PROMPT
                )
                logger.info("✨ Cliente Gemini inicializado con éxito.")
            else:
                logger.error("❌ ERROR: LLM_PROVIDER es 'gemini' pero no se encontró GEMINI_API_KEY.")
    
    async def generate_diagram(self, request) -> DiagramResponse:
        """Llama al LLM y parsea la respuesta como DiagramResponse."""
        if self.client is None:
            logger.warning("⚠️ El cliente de IA no está inicializado. Usando flujo Mock de respaldo.")
            return self._generate_mock(request.prompt)
        
        try:
            user_message = build_user_message(request)
            raw_json = await self._call_llm(user_message)
            diagram_dict = await self._parse_with_retry(raw_json)
            
            diagram_dict["generatedBy"] = "ai"
            diagram_dict["promptUsed"] = request.prompt
            
            return DiagramResponse(**diagram_dict)
        except Exception as e:
            logger.error("Error en el servicio de IA (Generación), cayendo a Mock: %s", str(e))
            return self._generate_mock(request.prompt)
    
    async def refine_diagram(self, request) -> DiagramResponse:
        """Modifica un diagrama existente con soporte de resiliencia."""
        if self.client is None:
            logger.warning("⚠️ El cliente de IA no está inicializado. Usando flujo Mock de respaldo.")
            return self._generate_mock(request.prompt)
        
        try:
            user_message = build_refine_message(request)
            raw_json = await self._call_llm(user_message)
            diagram_dict = await self._parse_with_retry(raw_json)
            
            diagram_dict["generatedBy"] = "ai-refined"
            diagram_dict["promptUsed"] = request.prompt
            
            return DiagramResponse(**diagram_dict)
        except Exception as e:
            logger.error("Error en el servicio de IA (Refinación), cayendo a Mock: %s", str(e))
            return self._generate_mock(request.prompt)
    
    async def _call_llm(self, user_message: str) -> str:
        """Llamada al LLM según el proveedor configurado."""
        provider = LLM_PROVIDER.lower() if LLM_PROVIDER else ""
        logger.info("Llamando LLM: %s | provider: %s", MODEL_NAME, provider)

        if provider == "openai":
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

        elif provider == "anthropic":
            response = await self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text

        elif provider == "gemini":
            response = await self.client.generate_content_async(
                user_message,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS
                )
            )
            return response.text

        raise ValueError(f"Proveedor no soportado: {LLM_PROVIDER}")

    async def _parse_with_retry(self, raw: str, attempts: int = 2) -> dict:
        """Intenta parsear el JSON. Si falla, pide al LLM que lo corrija."""
        for attempt in range(attempts):
            try:
                cleaned = self._clean_json_string(raw)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning("JSON inválido en intento %d: %s", attempt + 1, e)
                provider = LLM_PROVIDER.lower() if LLM_PROVIDER else ""
                if attempt < attempts - 1 and provider != "gemini":
                    fix_prompt = f"El siguiente JSON tiene un error de sintaxis: {e}\nCorrígelo y devuelve SOLO el JSON válido sin texto adicional:\n\n{raw}"
                    raw = await self._call_llm(fix_prompt)
                else:
                    raise ValueError(f"No se pudo parsear: {e}\n\nRespuesta: {raw[:500]}")
    
    def _clean_json_string(self, raw: str) -> str:
        """Elimina bloques markdown de manera segura sin expresiones regulares."""
        texto = raw.strip()
        if texto.startswith("```"):
            salto_linea = texto.find("\n")
            if salto_linea != -1:
                texto = texto[salto_linea:].strip()
            else:
                texto = texto[3:].strip()
        if texto.endswith("```"):
            texto = texto[:-3].strip()
        return texto
    
    def _generate_mock(self, prompt: str) -> DiagramResponse:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        
        # XML BPMN 2.0 con mapeo posicional completo para renderizado gráfico
        mock_bpmn_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:collaboration id="Collaboration_1">
    <bpmn:participant id="Participant_1" name="Instalación de Medidor Eléctrico" processRef="Process_{timestamp}" />
  </bpmn:collaboration>
  
  <bpmn:process id="Process_{timestamp}" isExecutable="false">
    <bpmn:laneSet id="LaneSet_1">
      <bpmn:lane id="lane-1" name="Atención al Cliente">
        <bpmn:flowNodeRef>node-start</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-verify</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-gate</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-reject</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-end-reject</bpmn:flowNodeRef>
      </bpmn:lane>
      <bpmn:lane id="lane-2" name="Área Técnico / Operaciones">
        <bpmn:flowNodeRef>node-inspect</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-install</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>node-end-ok</bpmn:flowNodeRef>
      </bpmn:lane>
    </bpmn:laneSet>
    
    <bpmn:startEvent id="node-start" name="Cliente Solicita Medidor" />
    <bpmn:userTask id="node-verify" name="Verificar Deuda" />
    <bpmn:exclusiveGateway id="node-gate" name="¿Tiene Deuda?" />
    <bpmn:userTask id="node-reject" name="Rechazar Solicitud" />
    <bpmn:endEvent id="node-end-reject" name="Solicitud Cancelada" />
    
    <bpmn:userTask id="node-inspect" name="Inspeccionar Terreno" />
    <bpmn:userTask id="node-install" name="Instalar con Firma" />
    <bpmn:endEvent id="node-end-ok" name="Medidor Instalado Exitosamente" />
    
    <bpmn:sequenceFlow id="f1" sourceRef="node-start" targetRef="node-verify" />
    <bpmn:sequenceFlow id="f2" sourceRef="node-verify" targetRef="node-gate" />
    <bpmn:sequenceFlow id="f3_yes" name="Si debe" sourceRef="node-gate" targetRef="node-reject" />
    <bpmn:sequenceFlow id="f4" sourceRef="node-reject" targetRef="node-end-reject" />
    <bpmn:sequenceFlow id="f3_no" name="No debe" sourceRef="node-gate" targetRef="node-inspect" />
    <bpmn:sequenceFlow id="f5" sourceRef="node-inspect" targetRef="node-install" />
    <bpmn:sequenceFlow id="f6" sourceRef="node-install" targetRef="node-end-ok" />
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_1">
      <bpmndi:BPMNShape id="Participant_1_di" bpmnElement="Participant_1" isHorizontal="true">
        <dc:Bounds x="120" y="50" width="850" height="340" />
      </bpmndi:BPMNShape>
      
      <bpmndi:BPMNShape id="lane-1_di" bpmnElement="lane-1" isHorizontal="true">
        <dc:Bounds x="150" y="50" width="820" height="170" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="lane-2_di" bpmnElement="lane-2" isHorizontal="true">
        <dc:Bounds x="150" y="220" width="820" height="170" />
      </bpmndi:BPMNShape>
      
      <bpmndi:BPMNShape id="node-start_di" bpmnElement="node-start">
        <dc:Bounds x="190" y="110" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-verify_di" bpmnElement="node-verify">
        <dc:Bounds x="270" y="90" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-gate_di" bpmnElement="node-gate" isMarkerVisible="true">
        <dc:Bounds x="420" y="105" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-reject_di" bpmnElement="node-reject">
        <dc:Bounds x="530" y="60" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-end-reject_di" bpmnElement="node-end-reject">
        <dc:Bounds x="690" y="82" width="36" height="36" />
      </bpmndi:BPMNShape>
      
      <bpmndi:BPMNShape id="node-inspect_di" bpmnElement="node-inspect">
        <dc:Bounds x="530" y="250" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-install_di" bpmnElement="node-install">
        <dc:Bounds x="690" y="250" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="node-end-ok_di" bpmnElement="node-end-ok">
        <dc:Bounds x="850" y="272" width="36" height="36" />
      </bpmndi:BPMNShape>
      
      <bpmndi:BPMNEdge id="f1_di" bpmnElement="f1">
        <di:waypoint x="226" y="128" />
        <di:waypoint x="270" y="128" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f2_di" bpmnElement="f2">
        <di:waypoint x="370" y="130" />
        <di:waypoint x="420" y="130" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f3_yes_di" bpmnElement="f3_yes">
        <di:waypoint x="445" y="105" />
        <di:waypoint x="445" y="100" />
        <di:waypoint x="530" y="100" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f4_di" bpmnElement="f4">
        <di:waypoint x="630" y="100" />
        <di:waypoint x="690" y="100" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f3_no_di" bpmnElement="f3_no">
        <di:waypoint x="445" y="155" />
        <di:waypoint x="445" y="290" />
        <di:waypoint x="530" y="290" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f5_di" bpmnElement="f5">
        <di:waypoint x="630" y="290" />
        <di:waypoint x="690" y="290" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="f6_di" bpmnElement="f6">
        <di:waypoint x="790" y="290" />
        <di:waypoint x="850" y="290" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>"""

        # Inyección de formSchema estructurados requeridos por la validación de publicación del Backend
        return DiagramResponse(
            name=f"Proceso Instalación Medidor - {timestamp}",
            description=f"Flujo completo mock: {prompt[:50]}...",
            bpmnXml=mock_bpmn_xml,
            lanes=[
                {"id": "lane-1", "name": "Atención al Cliente", "departmentId": "DEP-UX", "order": 1, "color": "#E3F2FD"},
                {"id": "lane-2", "name": "Área Técnico / Operaciones", "departmentId": "DEP-OPS", "order": 2, "color": "#FFF3E0"}
            ],
            nodes=[
                {
                    "id": "node-start", 
                    "type": "START", 
                    "label": "Cliente solicita medidor", 
                    "laneId": "lane-1", 
                    "position": {"x": 190, "y": 110}
                },
                {
                    "id": "node-verify", 
                    "type": "TASK", 
                    "label": "Verificar deuda", 
                    "laneId": "lane-1", 
                    "position": {"x": 270, "y": 90},
                    "formSchema": {
                        "title": "Formulario de Verificación",
                        "fields": [{"name": "montoDeuda", "type": "number", "label": "Monto Deuda Pendiente", "required": True}]
                    }
                },
                {
                    "id": "node-gate", 
                    "type": "GATEWAY", 
                    "label": "¿Debe?", 
                    "laneId": "lane-1", 
                    "position": {"x": 420, "y": 105}
                },
                {
                    "id": "node-reject", 
                    "type": "TASK", 
                    "label": "Rechazar solicitud", 
                    "laneId": "lane-1", 
                    "position": {"x": 530, "y": 60},
                    "formSchema": {
                        "title": "Formulario de Rechazo",
                        "fields": [{"name": "motivoRechazo", "type": "string", "label": "Justificación del Rechazo", "required": True}]
                    }
                },
                {
                    "id": "node-end-reject", 
                    "type": "END", 
                    "label": "Fin: Solicitud rechazada", 
                    "laneId": "lane-1", 
                    "position": {"x": 690, "y": 82}
                },
                {
                    "id": "node-inspect", 
                    "type": "TASK", 
                    "label": "Inspeccionar terreno", 
                    "laneId": "lane-2", 
                    "position": {"x": 530, "y": 250},
                    "formSchema": {
                        "title": "Formulario Técnico de Inspección",
                        "fields": [
                            {"name": "esFactible", "type": "boolean", "label": "Factibilidad Técnica", "required": True},
                            {"name": "observaciones", "type": "string", "label": "Detalles del Terreno", "required": False}
                        ]
                    }
                },
                {
                    "id": "node-install", 
                    "type": "TASK", 
                    "label": "Instalar con firma", 
                    "laneId": "lane-2", 
                    "position": {"x": 690, "y": 250},
                    "formSchema": {
                        "title": "Acta de Conformidad",
                        "fields": [
                            {"name": "numMedidor", "type": "string", "label": "Número de Serie del Medidor", "required": True},
                            {"name": "firmaCliente", "type": "string", "label": "Firma Digital o Token", "required": True}
                        ]
                    }
                },
                {
                    "id": "node-end-ok", 
                    "type": "END", 
                    "label": "Fin: Instalado", 
                    "laneId": "lane-2", 
                    "position": {"x": 850, "y": 272}
                }
            ],
            transitions=[
                {"id": "t1", "sourceId": "node-start", "targetId": "node-verify", "condition": None},
                {"id": "t2", "sourceId": "node-verify", "targetId": "node-gate", "condition": None},
                {"id": "t3-yes", "sourceId": "node-gate", "targetId": "node-reject", "condition": "Si debe"},
                {"id": "t4", "sourceId": "node-reject", "targetId": "node-end-reject", "condition": None},
                {"id": "t3-no", "sourceId": "node-gate", "targetId": "node-inspect", "condition": "No debe"},
                {"id": "t5", "sourceId": "node-inspect", "targetId": "node-install", "condition": None},
                {"id": "t6", "sourceId": "node-install", "targetId": "node-end-ok", "condition": None}
            ],
            generatedBy="mock",
            promptUsed=prompt
        )