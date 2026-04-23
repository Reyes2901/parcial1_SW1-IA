# app/models/response.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class FieldOption(BaseModel):
    value: str
    label: str

class FormField(BaseModel):
    name: str
    type: str          # TEXT | NUMBER | BOOLEAN | IMAGE | SIGNATURE | GEOLOCATION
    label: str
    required: bool = False
    options: Optional[List[FieldOption]] = None
    placeholder: Optional[str] = None
    helpText: Optional[str] = None

class FormSchema(BaseModel):
    title: Optional[str] = None
    fields: List[FormField] = []

class Position(BaseModel):
    x: float
    y: float

class Lane(BaseModel):
    id: str
    name: str
    departmentId: str
    order: int
    color: Optional[str] = "#E1F5EE"

class Node(BaseModel):
    id: str
    type: str          # START | END | ACTIVITY | DECISION | FORK | JOIN
    label: str
    laneId: str
    assigneeRole: Optional[str] = None
    estimatedDurationHours: Optional[int] = None
    formSchema: Optional[FormSchema] = None
    position: Optional[Position] = None

class Transition(BaseModel):
    id: str
    sourceId: str
    targetId: str
    condition: Optional[str] = None
    label: Optional[str] = ""

class DiagramResponse(BaseModel):
    name: str                    # nombre sugerido para la política
    description: str             # descripción del proceso generado
    lanes: List[Lane]
    nodes: List[Node]
    transitions: List[Transition]
    generatedBy: str = "ai"
    promptUsed: str              # el prompt original para trazabilidad

class ErrorResponse(BaseModel):
    error: str
    detail: str