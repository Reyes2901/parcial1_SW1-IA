# app/models/request.py
from pydantic import BaseModel
from typing import Optional, List

class DiagramRequest(BaseModel):
    prompt: str                        # "Necesito un flujo para instalar medidores..."
    language: str = "es"               # idioma del diagrama
    existing_lanes: Optional[List[str]] = None  # lanes ya definidos por el admin
    max_nodes: int = 15                # límite de nodos en el diagrama generado
    include_forms: bool = True         # si debe generar formSchema por actividad

class RefineDiagramRequest(BaseModel):
    prompt: str                        # "Agrega un paso de inspección antes de la instalación"
    current_diagram: dict              # el diagrama actual para modificarlo
    language: str = "es"