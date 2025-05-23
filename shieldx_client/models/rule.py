from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Optional
from bson import ObjectId

# ------------------------------------------------------------------------------
# ¿Por qué modelar con Pydantic?
# ------------------------------------------------------------------------------
# ✅ Garantiza que los datos sean válidos antes de procesarlos (ej. tipos, estructuras).
# ✅ Permite transformar automáticamente valores (ej. ObjectId → str).
# ✅ Permite agregar validaciones lógicas y reglas personalizadas (ej. modelo RuleModel).
# ✅ Facilita la documentación automática en OpenAPI (FastAPI) mediante json_schema_extra.

class ParameterDetailModel(BaseModel):
    """
    Modelo que describe un parámetro individual usado en una regla.

    Cada parámetro tiene:
    - type: Tipo de dato esperado (string, int, etc.)
    - description: Explicación del propósito del parámetro
    """
    type_: str = Field(..., alias="type")  # Alias para que en el JSON se acepte "type"
    description: str

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {"type": "string", "description": "ID del bucket origen"}
            ]
        }
    }

class RuleModel(BaseModel):
    """
    Modelo principal para representar una regla en el sistema ShieldX.

    Las reglas definen qué función ejecutar (target) y qué parámetros requiere.
    También se validan automáticamente según el tipo de función.
    """
    rule_id: Optional[str] = Field(default=None, alias="_id")  # ID opcional para MongoDB
    target: str  # Nombre completo de la función objetivo
    parameters: Dict[str, ParameterDetailModel]  # Parámetros que la función requiere

    @field_validator("rule_id", mode="before")
    def convert_object_id(cls, v):
        """Convierte ObjectId a str antes de asignarlo (útil al leer desde MongoDB)."""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @model_validator(mode="after")
    def validate_required_parameters(self) -> "RuleModel":
        """
        Valida que:
        - Cada target tenga los parámetros obligatorios esperados.
        - Cada parámetro tenga un tipo permitido.
        """
        required_by_target = {
            "s_security.cipher_ops.encrypt_data": [
                "source_bucket_id", "source_key", "sink_bucket_id", "sink_key", "security_level"
            ],
            "s_ml.ml_clustering.skmean": ["source_bucket_id", "source_key", "k"],
            "mictlanx.put": ["bucket_id", "key", "source_path", "replication_factor", "num_chunks"],
            "mictlanx.get": ["bucket_id", "key", "sink_path"]
        }

        # Verifica si el target requiere parámetros obligatorios
        expected = required_by_target.get(self.target)
        if expected:
            missing = [param for param in expected if param not in self.parameters]
            if missing:
                raise ValueError(f"El target '{self.target}' requiere los siguientes parámetros: {missing}")

        # Verifica que los tipos definidos sean válidos
        valid_types = {"string", "int", "float", "bool"}
        for key, param in self.parameters.items():
            if param.type_ not in valid_types:
                raise ValueError(f"Parámetro '{key}' tiene un tipo no válido: '{param.type_}'")

        return self

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class RuleId(BaseModel):
    """
    Modelo ligero que representa solo el ID de una regla, útil en respuestas o vínculos.
    """
    rule_id: str
