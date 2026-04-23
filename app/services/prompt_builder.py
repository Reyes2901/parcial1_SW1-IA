# app/services/prompt_builder.py
import json

SYSTEM_PROMPT = """
Eres un experto en modelado de procesos de negocio (BPM).
Tu tarea es convertir descripciones en lenguaje natural en diagramas
de actividades UML estructurados como JSON.

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con JSON válido. Sin texto adicional, sin markdown,
   sin bloques ```json. Solo el objeto JSON puro.
2. Sigue EXACTAMENTE el schema definido más abajo.
3. Cada nodo debe tener un id único en formato: "node-{nombre-kebab-case}"
4. Cada lane debe tener un id único en formato: "lane-{nombre-kebab-case}"
5. Cada transición debe tener un id único en formato: "t{numero}"
6. El diagrama SIEMPRE debe tener exactamente 1 nodo START y al menos 1 nodo END.
7. Las condiciones en transiciones usan sintaxis SpEL de Java:
   - "tieneDeuda == true"  |  "monto > 1000"  |  "resultado == 'APROBADO'"
8. Los IDs en transiciones deben referenciar IDs de nodos existentes.
9. Asigna posiciones {x, y} lógicas: el flujo va de arriba hacia abajo,
   x=80 para lane 1, x=340 para lane 2, x=600 para lane 3.
   Incrementar y en 120 por cada nivel del flujo.
10. Para nodos ACTIVITY, genera siempre un formSchema con campos relevantes.

TIPOS DE NODO VÁLIDOS:
- START: inicio del proceso (sin formSchema)
- END: fin del proceso (sin formSchema)
- ACTIVITY: tarea humana (requiere formSchema con al menos 1 campo)
- DECISION: punto de decisión con múltiples salidas condicionales (sin formSchema)
- FORK: inicio de flujo paralelo (sin formSchema)
- JOIN: fin de flujo paralelo — espera todas las ramas (sin formSchema)

TIPOS DE CAMPO EN formSchema:
TEXT, NUMBER, BOOLEAN, DATE, SELECT, MULTISELECT, IMAGE, SIGNATURE, GEOLOCATION

COLORES SUGERIDOS PARA LANES:
- Atención al cliente: "#E1F5EE"
- Área técnica / inspección: "#EEEDFE"
- Instalación / campo: "#FAECE7"
- Administración / aprobación: "#E6F1FB"
- Cualquier otro: "#F1EFE8"

SCHEMA JSON ESPERADO:
{
  "name": "string — nombre descriptivo del proceso",
  "description": "string — descripción breve del proceso",
  "lanes": [
    { "id": "lane-xxx", "name": "string", "departmentId": "string",
      "order": 1, "color": "#HEXCOLOR" }
  ],
  "nodes": [
    { "id": "node-xxx", "type": "START|END|ACTIVITY|DECISION|FORK|JOIN",
      "label": "string", "laneId": "lane-xxx",
      "assigneeRole": "string (solo en ACTIVITY)",
      "estimatedDurationHours": 4,
      "position": {"x": 80, "y": 60},
      "formSchema": {
        "title": "string",
        "fields": [
          { "name": "camelCase", "type": "TEXT", "label": "string",
            "required": true }
        ]
      }
    }
  ],
  "transitions": [
    { "id": "t1", "sourceId": "node-xxx", "targetId": "node-yyy",
      "condition": null, "label": "" }
  ]
}
"""


def build_system_prompt(language: str = "es") -> str:
    """Devuelve el system prompt según el idioma"""
    if language == "es":
        return SYSTEM_PROMPT
    else:
        return SYSTEM_PROMPT  # Por ahora solo español


def build_user_message(request) -> str:
    """Construye el mensaje del usuario con contexto adicional."""
    msg = f"Genera un diagrama de proceso para: {request.prompt}"

    if hasattr(request, 'existing_lanes') and request.existing_lanes:
        lanes_str = ", ".join(request.existing_lanes)
        msg += f"\n\nLanes disponibles (úsalos si aplican): {lanes_str}"

    msg += f"\n\nIdioma del diagrama: {request.language}"
    
    if hasattr(request, 'max_nodes'):
        msg += f"\nMáximo de nodos: {request.max_nodes}"

    if hasattr(request, 'include_forms') and not request.include_forms:
        msg += "\nNO generar formSchema en los nodos."

    return msg


def build_refine_message(request) -> str:
    """Para refinar un diagrama existente."""
    current = json.dumps(request.current_diagram, ensure_ascii=False, indent=2)
    return f"""Modifica el siguiente diagrama según esta instrucción:
"{request.prompt}"

DIAGRAMA ACTUAL:
{current}

Devuelve el diagrama completo modificado en el mismo formato JSON."""