# app/routers/diagram.py
from fastapi import APIRouter, HTTPException
from app.models.request import DiagramRequest
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

@router.post("/generate")
async def generate_diagram(request: DiagramRequest):
    """Genera un diagrama de workflow a partir de un prompt en lenguaje natural"""
    try:
        # 👇 Pasar el request completo, no prompt y language por separado
        return await ai_service.generate_diagram(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refine")
async def refine_diagram(request: dict):
    """Refina un diagrama existente"""
    try:
        return await ai_service.refine_diagram(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-diagram-generator"}