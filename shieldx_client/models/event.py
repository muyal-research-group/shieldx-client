from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone

# ------------------------------
# Uso de Pydantic en modelos
# ------------------------------
# Modelar eventos con Pydantic es clave porque:
# ✅ Valida automáticamente los tipos (como str, datetime, dict).
# ✅ Asigna valores por defecto con seguridad (como fechas UTC).
# ✅ Permite extender el modelo fácilmente y mantener consistencia en toda la API.
# ✅ Mejora la interoperabilidad entre backend y frontend gracias a su conversión automática a JSON.

class EventModel(BaseModel):
    """
    Modelo base que representa un evento generado dentro del sistema ShieldX.

    Este modelo se utiliza para registrar la ejecución de funciones dentro de un microservicio
    y contiene información clave para su trazabilidad y procesamiento.
    """

    service_id: str  # Identificador del servicio de nivel superior (por ejemplo, almacenamiento, analítica)
    microservice_id: str  # ID del microservicio dentro del servicio
    function_id: str  # ID de la función que generó el evento
    event_type: str  # Tipo de evento generado (por ejemplo, EncryptStart, SkmeansDone)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # Fecha y hora del evento; se asigna automáticamente en UTC si no se proporciona

    payload: Optional[Any] = None
    # Información adicional del evento: puede ser dict, string, lista, etc. (flexible para cada tipo de evento)
