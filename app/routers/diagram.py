# app/routers/diagram.py
from fastapi import APIRouter, HTTPException
from app.models.request import DiagramRequest, RefineDiagramRequest
from app.models.response import DiagramResponse, ErrorResponse
from app.services.ai_service import AIService
import logging

router = APIRouter(prefix="/ai", tags=["diagram"])
logger = logging.getLogger(__name__)

# Instancia única del servicio
ai_service = AIService()

@router.post(
    "/generate-diagram",
    response_model=DiagramResponse,
    summary="Genera un diagrama desde un prompt de texto"
)
async def generate(request: DiagramRequest):
    """
    Recibe un prompt en lenguaje natural y devuelve un diagrama
    completo con lanes, nodes y transitions compatible con el
    diagramador Angular y el motor Spring Boot.
    """
    try:
        logger.info("Generando diagrama para prompt: %s", request.prompt[:80])
        result = await ai_service.generate_diagram(request)
        logger.info("Diagrama generado: %d nodos, %d transiciones",
                    len(result.nodes), len(result.transitions))
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Error generando diagrama: %s", e)
        raise HTTPException(status_code=500, detail=f"Error del servicio IA: {str(e)}")


@router.post(
    "/refine-diagram",
    response_model=DiagramResponse,
    summary="Modifica un diagrama existente con instrucciones adicionales"
)
async def refine(request: RefineDiagramRequest):
    """
    Recibe el diagrama actual y una instrucción de modificación.
    Devuelve el diagrama actualizado.
    """
    try:
        return await ai_service.refine_diagram(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refinando diagrama: {str(e)}")


@router.post(
    "/validate-diagram",
    summary="Valida la estructura lógica de un diagrama"
)
async def validate(diagram: dict):
    """
    Valida que el diagrama tenga la estructura correcta.
    """
    errors = []
    nodes = diagram.get("nodes", [])
    transitions = diagram.get("transitions", [])
    node_ids = {n["id"] for n in nodes}

    starts = [n for n in nodes if n.get("type") == "START"]
    ends = [n for n in nodes if n.get("type") == "END"]

    if len(starts) != 1:
        errors.append(f"Debe haber exactamente 1 nodo START (encontrados: {len(starts)})")
    if len(ends) < 1:
        errors.append("Debe haber al menos 1 nodo END")

    for t in transitions:
        if t.get("sourceId") not in node_ids:
            errors.append(f"Transición {t.get('id')}: sourceId '{t.get('sourceId')}' no existe")
        if t.get("targetId") not in node_ids:
            errors.append(f"Transición {t.get('id')}: targetId '{t.get('targetId')}' no existe")

    for n in nodes:
        if n.get("type") == "ACTIVITY" and not n.get("formSchema"):
            errors.append(f"Nodo ACTIVITY '{n.get('label')}' no tiene formSchema")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "nodeCount": len(nodes),
        "transitionCount": len(transitions)
    }


@router.get("/health", summary="Health check del servicio IA")
async def health():
    return {"status": "ok", "service": "wbs-ia-ai", "version": "1.0"}