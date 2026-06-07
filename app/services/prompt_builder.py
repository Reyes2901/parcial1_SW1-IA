# app/services/prompt_builder.py

SYSTEM_PROMPT = """
Eres un arquitecto experto en BPMN 2.0, ingenieria de software y automatización de procesos. 
Tu única tarea es diseñar diagramas de procesos empresariales robustos y devolverlos estrictamente en formato JSON válido que cumpla con el esquema requerido.

REGLAS CRÍTICAS DE CONTROL (ESTRICTAS):

1. OBLIGATORIEDAD DE FORMSCHEMA EN USER TASKS:
Cualquier nodo con tipo 'TASK' representa una interacción humana en el frontend. Para evitar errores de publicación (422 Unprocessable Content), cada 'TASK' DEBE incluir un objeto 'formSchema' coherente con el contexto de la tarea. No se permiten esquemas vacíos ni nulos.
El formato del 'formSchema' debe ser:
{
  "title": "Título del Formulario",
  "fields": [
    {
      "name": "nombreEnCamelCase",
      "type": "string" | "number" | "boolean",
      "label": "Etiqueta visible para el usuario",
      "required": true | false
    }
  ]
}

2. INTEGRIDAD GRÁFICA (BPMN XML DI):
El campo 'bpmnXml' debe contener un string XML válido de BPMN 2.0 completo. Es obligatorio incluir la sección `<bpmndi:BPMNDiagram>` con coordenadas espaciales reales y proporcionales para CADA elemento (Lanes, Nodos, Transitions).
- Los carriles (Lanes) deben ser rectángulos paralelos apilados verticalmente sin solaparse.
- Los nodos deben mapearse con `<dc:Bounds>` dentro del carril que les corresponde (laneId).
- Los flujos deben mapearse con `<bpmndi:BPMNEdge>` utilizando múltiples `<di:waypoint>` para dibujar quiebres limpios y evitar diagonales cruzadas sobre las cajas.

3. CORRESPONDENCIA ABSOLUTA:
Los IDs de los elementos en el XML (procesos, carriles, tareas, compuertas y flujos) deben ser EXACTAMENTE IDÉNTICOS a los IDs definidos en las propiedades raíz del JSON (`lanes`, `nodes`, `transitions`).

FORMATO JSON DE SALIDA REQUERIDO:
Devuelve un objeto JSON plano que contenga estrictamente las siguientes llaves:
{
  "name": "Nombre descriptivo del proceso",
  "description": "Explicación detallada de lo que hace el flujo",
  "bpmnXml": "<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>...",
  "lanes": [
    { "id": "lane-id", "name": "Nombre del Rol/Departamento", "departmentId": "DEP-XXX", "order": 1, "color": "#HEX" }
  ],
  "nodes": [
    {
      "id": "node-id",
      "type": "START" | "TASK" | "GATEWAY" | "END",
      "label": "Texto del nodo",
      "laneId": "lane-id-perteneciente",
      "position": { "x": 123, "y": 456 },
      "formSchema": { ... } // Solo obligatorio si type es 'TASK'
    }
  ],
  "transitions": [
    { "id": "t-id", "sourceId": "node-origen", "targetId": "node-destino", "condition": "Texto si es flujo condicional, o null" }
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
    """
    Construye el mensaje del usuario para la generación de un diagrama nuevo
    basado en un prompt de texto plano.
    """
    return f"""
    Genera un diagrama de proceso completo y profesional basado en el siguiente requerimiento del usuario.
    Recuerda calcular coordenadas espaciales lógicas y adjuntar esquemas de formulario detallados a cada tarea.

    REQUERIMIENTO DEL USUARIO:
    "{request.prompt}"

    Genera una respuesta puramente en formato JSON que cumpla exactamente con las instrucciones del sistema.
    """

def build_refine_message(request) -> str:
    """
    Construye el mensaje para modificar o refinar un diagrama existente,
    pasándole a la IA el estado actual para mantener la consistencia de los IDs.
    """
    # Intentamos formatear el diagrama actual de forma limpia para la lectura de la IA
    current_diagram_json = ""
    if hasattr(request, 'current_diagram') and request.current_diagram:
        try:
            current_diagram_json = json.dumps(request.current_diagram, indent=2, ensure_ascii=False)
        except Exception:
            current_diagram_json = str(request.current_diagram)

    return f"""
    Se te ha solicitado modificar y refinar un diagrama de proceso existente. 
    Debes mantener la estructura base y los IDs existentes en la medida de lo posible, aplicando los cambios solicitados por el usuario.
    Asegúrate de recalcular las posiciones visuales si agregas nuevos nodos y mantén la regla estricta de incluir 'formSchema' en cualquier tarea nueva o modificada.

    DIAGRAMA ACTUAL A MODIFICAR:
    ```json
    {current_diagram_json}
    ```

    INSTRUCCIONES DE MODIFICACIÓN DEL USUARIO:
    "{request.prompt}"

    Devuelve la versión final del diagrama completo modificado siguiendo estrictamente la estructura JSON requerida.
    """