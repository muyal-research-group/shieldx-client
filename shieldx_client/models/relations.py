from pydantic import BaseModel
from typing import ClassVar

# ------------------------------------------------------------------------
# Uso de modelos Pydantic para relaciones (Many-to-Many) en ShieldX
# ------------------------------------------------------------------------
# Estas clases representan relaciones entre entidades como:
# - Tipos de eventos y triggers
# - Triggers entre sí (padre-hijo)
# - Triggers y reglas
#
# Pydantic permite:
# ✅ Validación automática de los identificadores como cadenas.
# ✅ Ejemplos útiles en la documentación OpenAPI para cada relación.
# ✅ Uso sencillo en endpoints POST para vinculación de entidades.

class EventsTriggersModel(BaseModel):
    """
    Relación entre un tipo de evento y un trigger.
    
    Esta relación permite que un tipo de evento dispare uno o más triggers asociados.
    """
    event_type_id: str  # ID del tipo de evento
    trigger_id: str     # ID del trigger asociado

    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "event_type_id": "661f8d933e3a2eac62cce7ad",
                "trigger_id": "66200e847a824ad0dbb622e1"
            }
        }
    }

class TriggersTriggersModel(BaseModel):
    """
    Relación jerárquica entre triggers (encadenamiento).
    
    Permite que un trigger padre dispare automáticamente un trigger hijo.
    """
    trigger_parent_id: str  # ID del trigger padre
    trigger_child_id: str   # ID del trigger hijo

    model_config: ClassVar[dict] = {
        "json_schema_extra": {
            "example": {
                "trigger_parent_id": "661f9124aa3deebd71eaaa99",
                "trigger_child_id": "661f913faa3deebd71eaaabc"
            }
        }
    }

class RulesTriggerModel(BaseModel):
    """
    Relación entre un trigger y una regla.

    Permite que al activarse un trigger, se evalúe una regla para decidir qué función ejecutar.
    """
    trigger_id: str  # ID del trigger
    rule_id: str     # ID de la regla asociada

    model_config: ClassVar[dict] = {
        "json_schema_extra": {
            "example": {
                "trigger_id": "662018c50c9fba58a4fc1689",
                "rule_id": "662019dd2d132a9aa4fbe27b"
            }
        }
    }
