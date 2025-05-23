from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId

# ------------------------------
# Modelos con Pydantic
# ------------------------------
# Es importante modelar los datos con Pydantic porque:
# ✅ Permite la validación automática de tipos (por ejemplo, fechas, strings, enteros).
# ✅ Facilita la serialización y deserialización (como convertir ObjectId o datetime a string/ISO).
# ✅ Asegura que los datos que entran a nuestra API o salen hacia un cliente tengan una estructura consistente.
# ✅ Proporciona alias y configuraciones que permiten compatibilidad con bases de datos como MongoDB.

class EventTypeModel(BaseModel):
    """
    Modelo principal que representa un tipo de evento.
    Incluye su ID (opcional), nombre y fecha de creación automática.
    """
    event_type_id: Optional[str] = Field(default=None, alias="_id")  # Se usa alias para mapear el campo Mongo _id
    event_type: str  # Nombre del tipo de evento
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Fecha de creación por defecto

    @field_validator("event_type_id", mode="before")
    def convert_object_id(cls, v):
        """
        Convierte el ObjectId de MongoDB en string antes de la validación,
        para que Pydantic pueda procesarlo correctamente.
        """
        if isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = {
        "populate_by_name": True,  # Permite acceder por el nombre real del atributo, no solo el alias
        "json_encoders": {ObjectId: str}  # Asegura que los ObjectId se conviertan correctamente al serializar
    }

class EventTypeId(BaseModel):
    """
    Modelo que encapsula únicamente el ID del tipo de evento.
    Es útil como respuesta simple o clave de referencia en otras entidades.
    """
    event_type_id: str
