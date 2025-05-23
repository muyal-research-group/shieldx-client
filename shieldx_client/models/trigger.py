from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson import ObjectId

class TriggerModel(BaseModel):
    """
    Modelo que representa un Trigger en el sistema ShieldX.

    En el cliente, este modelo permite construir y validar los datos antes de enviarlos al backend.
    También se encarga de convertir identificadores BSON (ObjectId) a cadenas de texto compatibles
    con JSON para asegurar la correcta serialización en las solicitudes HTTP.

    Atributos:
    - trigger_id: Identificador único del trigger (convertido desde ObjectId si es necesario).
    - name: Nombre asignado al trigger.
    """
    trigger_id: Optional[str] = Field(default=None, alias="_id")
    name: str

    @field_validator("trigger_id", mode="before")
    def convert_object_id(cls, v):
        """
        Convierte un ObjectId a string para que pueda ser serializado correctamente en JSON.
        Esto es necesario cuando los datos provienen directamente de MongoDB.
        """
        if isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = {
        "populate_by_name": True,  # Permite usar tanto "trigger_id" como "_id" en la carga de datos.
        "json_encoders": {ObjectId: str}  # Asegura que los ObjectId se serialicen como cadenas.
    }

class TriggerId(BaseModel):
    """
    Modelo simple para encapsular el ID de un trigger.

    Este modelo se utiliza cuando el cliente recibe o envía únicamente el identificador de un trigger.
    Utilizar un modelo dedicado mejora la claridad en las interfaces y documentación.
    """
    trigger_id: str
