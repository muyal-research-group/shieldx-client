import httpx
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import TypeAdapter
import json
import time as T
from typing import Optional, Dict, Any, List
from shieldx_client.log.logger_config import get_logger
from shieldx_client.models.event_type import EventTypeId, EventTypeModel
from shieldx_client.models.event import EventModel
from shieldx_client.models.trigger import TriggerId
from shieldx_client.models.rule import RuleId, RuleModel
from shieldx_client.models.relations import (
    EventsTriggersModel,
    TriggersTriggersModel,
    RulesTriggerModel,
)


L =  get_logger("shieldx-client")


class ShieldXClient:
    """
    Client for interacting with the ShieldX API, specifically for managing event types (`event-types`).

    This client supports asynchronous operations for creating and deleting event types using httpx.
    It also allows injecting additional custom headers (e.g., for tracing or extended authentication).
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize a new instance of the ShieldXClient.

        :param base_url: Base URL of the ShieldX API server (e.g., http://localhost:8000).
        :param token: Optional Bearer token for authentication. If provided, it will be included in request headers.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
#
    #async def create_event_type(self, event_type: str, headers: Dict[str, str] = {}) -> EventTypeId:
    #    """
    #    Create a new event type in the ShieldX system.
#
    #    :param event_type: The name or label of the event type to be created.
    #    :param headers: Optional dictionary of additional headers to include in the request.
    #    :return: The ID of the newly created event type.
    #    :raises httpx.HTTPStatusError: If the API returns an HTTP error response.
    #    """
    #    payload = {"event_type": event_type}
    #    __headers = {**self.headers, **headers}
#
    #    async with httpx.AsyncClient(headers=__headers) as client:
    #        response = await client.post(f"{self.base_url}/event-types", json=payload)
    #        response.raise_for_status()
    #        response_json = await response.json()
    #        return response_json.get("event_type_id", "")
#
    #async def delete_event_type(self, event_type_id: str, headers: Dict[str, str] = {}) -> EventTypeId:
    #    """
    #    Delete an existing event type by its ID.
#
    #    :param event_type_id: The ID of the event type to be deleted.
    #    :param headers: Optional dictionary of additional headers to include in the request.
    #    :return: The ID of the deleted event type (as returned by the API).
    #    :raises httpx.HTTPStatusError: If the API returns an HTTP error response.
    #    """
    #    __headers = {**self.headers, **headers}
    #    async with httpx.AsyncClient(headers=__headers) as client:
    #        response = await client.delete(f"{self.base_url}/event-types/{event_type_id}")
    #        response.raise_for_status()
    #        response_json = await response.json()
    #        return response_json.get("event_type_id", "")
    #    
# --- Events ---


    async def create_event(self, event: EventModel, headers: Dict[str, str] = {}) -> dict:
        """
        Crea un nuevo evento en el sistema ShieldX.
        Serializa correctamente los campos datetime usando model_dump_json.
        """
        payload = json.loads(event.model_dump_json(by_alias=True))  # <-- convierte datetime automáticamente
        return await self._post("/events", payload, headers)

    async def get_all_events(self, headers: Dict[str, str] = {}) -> list[dict]:
        """Recupera todos los eventos registrados."""
        return await self._get("/events", headers)

    async def get_events_by_service(self, service_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Filtra eventos por ID de servicio (como query param)."""
        return await self._get(f"/events?service_id={service_id}", headers)

    async def get_events_by_service_path(self, service_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Filtra eventos por ID de servicio (como path param)."""
        return await self._get(f"/events/service/{service_id}", headers)

    async def get_events_by_microservice(self, microservice_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Filtra eventos por ID de microservicio."""
        return await self._get(f"/events/microservice/{microservice_id}", headers)

    async def get_events_by_function(self, function_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Filtra eventos por ID de función."""
        return await self._get(f"/events/function/{function_id}", headers)

    async def update_event(self, event_id: str, data: dict, headers: Dict[str, str] = {}) -> dict:
        """Actualiza los campos de un evento existente."""
        return await self._put(f"/events/{event_id}", data, headers)

    async def delete_event(self, event_id: str, headers: Dict[str, str] = {}) -> dict:
        """Elimina un evento del sistema."""
        return await self._delete(f"/events/{event_id}", headers)

    # --- EventType CRUD completo ---

    async def create_event_type(self, event_type: str, headers: Dict[str, str] = {}) -> EventTypeId:
        """Crea un nuevo tipo de evento."""
        payload = {"event_type": event_type}
        result = await self._post("/event-types", payload, headers)
        if isinstance(result, str):
            return EventTypeId(event_type_id=result)
        return EventTypeId(event_type_id=result.get("event_type_id", ""))

    async def list_event_types(self, headers: Dict[str, str] = {}) -> list[EventTypeModel]:
        """Lista todos los tipos de evento."""
        data = await self._get("/event-types", headers)
        return [EventTypeModel(**et) for et in data]

    async def get_event_type_by_id(self, event_type_id: str, headers: Dict[str, str] = {}) -> EventTypeModel:
        """Obtiene un tipo de evento específico por su ID."""
        data = await self._get(f"/event-types/{event_type_id}", headers)
        return EventTypeModel(**data)

    async def delete_event_type(self, event_type_id: str, headers: Dict[str, str] = {}) -> bool:
        """Elimina un tipo de evento existente."""
        await self._delete(f"/event-types/{event_type_id}", headers)
        return True

    # --- Relaciones EventType ⇄ Trigger ---

    async def link_trigger_to_event_type(self, event_type_id: str, trigger_id: str):
        """Asocia un trigger a un tipo de evento."""
        return await self._post(f"/event-types/{event_type_id}/triggers/{trigger_id}", payload={})

    async def list_triggers_for_event_type(self, event_type_id: str) -> list[Dict[str, str]]:
        """Lista los triggers vinculados a un tipo de evento."""
        return await self._get(f"/event-types/{event_type_id}/triggers")

    async def replace_triggers_for_event_type(self, event_type_id: str, trigger_ids: list[str]):
        """Reemplaza completamente los triggers de un tipo de evento."""
        return await self._put(f"/event-types/{event_type_id}/triggers", payload=trigger_ids)

    async def unlink_trigger_from_event_type(self, event_type_id: str, trigger_id: str):
        """Desvincula un trigger de un tipo de evento."""
        return await self._delete(f"/event-types/{event_type_id}/triggers/{trigger_id}")

    # --- Relaciones Trigger ⇄ Rule ---

    async def link_rule_to_trigger(self, trigger_id: str, rule_id: str):
        """Asocia una regla a un trigger."""
        return await self._post(f"/triggers/{trigger_id}/rules/{rule_id}", payload={})

    async def list_rules_for_trigger(self, trigger_id: str) -> list[dict]:
        """Lista las reglas asociadas a un trigger."""
        return await self._get(f"/triggers/{trigger_id}/rules")

    async def create_and_link_rule(self, trigger_id: str, rule_payload: dict) -> RuleId:
        """Crea y vincula una regla a un trigger."""
        result = await self._post(f"/triggers/{trigger_id}/rules", payload=rule_payload)
        if isinstance(result, str):
            return RuleId(rule_id=result)
        return RuleId(rule_id=result.get("rule_id", result))

    async def unlink_rule_from_trigger(self, trigger_id: str, rule_id: str):
        """Desvincula una regla de un trigger."""
        return await self._delete(f"/triggers/{trigger_id}/rules/{rule_id}")

    # --- CRUD: Rule ---

    async def create_rule(self, rule: RuleModel, headers: Dict[str, str] = {}) -> RuleId:
        """Crea una nueva regla."""
        result = await self._post("/rules", rule.model_dump(by_alias=True), headers)
        if isinstance(result, str):
            return RuleId(rule_id=result)
        return RuleId(rule_id=result.get("rule_id", result))

    async def get_rule_by_id(self, rule_id: str, headers: Dict[str, str] = {}) -> RuleModel:
        """Obtiene una regla por su ID."""
        result = await self._get(f"/rules/{rule_id}", headers)
        return RuleModel(**result)

    async def update_rule(self, rule_id: str, payload: dict, headers: Dict[str, str] = {}) -> dict:
        """Actualiza los atributos de una regla existente."""
        return await self._put(f"/rules/{rule_id}", payload, headers)

    async def list_rules(self, headers: Dict[str, str] = {}) -> list[RuleModel]:
        """Lista todas las reglas existentes."""
        rules = await self._get("/rules", headers)
        return [RuleModel(**r) for r in rules]

    async def delete_rule(self, rule_id: str, headers: Dict[str, str] = {}) -> bool:
        """Elimina una regla por ID."""
        await self._delete(f"/rules/{rule_id}", headers)
        return True

    # --- CRUD: Trigger (por nombre) ---

    async def create_trigger(self, name: str, headers: Dict[str, str] = {}) -> dict:
        """Crea un nuevo trigger."""
        payload = {"name": name}
        return await self._post("/triggers/", payload, headers)

    async def get_trigger_by_name(self, name: str, headers: Dict[str, str] = {}) -> dict:
        """Obtiene un trigger por su nombre."""
        return await self._get(f"/triggers/{name}", headers)

    async def get_all_triggers(self, headers: Dict[str, str] = {}) -> list[dict]:
        """Lista todos los triggers registrados."""
        return await self._get("/triggers/", headers)

    async def update_trigger(self, name: str, updated_data: dict, headers: Dict[str, str] = {}) -> dict:
        """Actualiza un trigger existente."""
        return await self._put(f"/triggers/{name}", updated_data, headers)

    async def delete_trigger(self, name: str, headers: Dict[str, str] = {}) -> bool:
        """Elimina un trigger existente."""
        await self._delete(f"/triggers/{name}", headers)
        return True

    # --- Relaciones Trigger ⇄ Trigger (Encadenamiento) ---

    async def link_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> bool:
        """Asocia un trigger hijo a un trigger padre."""
        return await self._post(f"/triggers/{parent_id}/children/{child_id}", payload={}, headers=headers)

    async def list_trigger_children(self, parent_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Lista los triggers hijos de un trigger padre."""
        return await self._get(f"/triggers/{parent_id}/children", headers)

    async def list_trigger_parents(self, child_id: str, headers: Dict[str, str] = {}) -> list[dict]:
        """Lista los triggers padres de un trigger hijo."""
        return await self._get(f"/triggers/{child_id}/parents", headers)

    async def unlink_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> bool:
        """Elimina la relación padre-hijo entre triggers."""
        return await self._delete(f"/triggers/{parent_id}/children/{child_id}", headers)

    # --- Métodos internos genéricos con logging detallado ---

    #async def _post(self, path: str, payload: Dict[str, Any], headers: Dict[str, str] = {}):
#
    #    url = f"{self.base_url}{path}"
    #    full_headers = {**self.headers, **headers}
    #    start = time.time()
#
    #    async with httpx.AsyncClient(headers=full_headers) as client:
    #        response = await client.post(url, json=payload)
    #        elapsed = time.time() - start
    #        logger.info(f"POST {path} - {response.status_code} - {elapsed:.3f}s")
    #        response.raise_for_status()
#
    #        if response.status_code == 204 or not response.content:
    #            return {}
    #        return response.json()
        
    async def _post(self, path: str, payload: Dict[str, Any], headers: Dict[str, str] = {}):
        """
        Método interno para enviar solicitudes POST.
        Combina cabeceras, mide el tiempo y maneja errores.
        Devuelve JSON si hay contenido, o {} en caso de 204.
        """
        url = f"{self.base_url}{path}"
        full_headers = {**self.headers, **headers}
        t1 = T.time()

        

        async with httpx.AsyncClient(headers=full_headers) as client:
            response = await client.post(url, json=payload)

        
        L.info({"event": "CLIENT.POST.RESPONSE", 
                "path": path, 
                "status": response.status_code, 
                "time": T.time() - t1
                })

        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()


    #async def _get(self, path: str, headers: Dict[str, str] = {}):
    #    """
    #    Método interno para solicitudes GET.
    #    Devuelve JSON de la respuesta. Mide tiempo y registra logs.
    #    """
    #    url = f"{self.base_url}{path}"
    #    full_headers = {**self.headers, **headers}
    #    start = time.time()
#
    #    async with httpx.AsyncClient(headers=full_headers) as client:
    #        response = await client.get(url)
    #        elapsed = time.time() - start
    #        logger.info(f"GET {path} - {response.status_code} - {elapsed:.3f}s")
    #        response.raise_for_status()
    #        return response.json()

    async def _get(self, path: str, headers: Dict[str, str] = {}):
        """
        Método interno para solicitudes GET.
        Devuelve JSON de la respuesta. Mide tiempo y registra logs.
        """
        url = f"{self.base_url}{path}"
        full_headers = {**self.headers, **headers}
        t1 = T.time()

        

        async with httpx.AsyncClient(headers=full_headers) as client:
            response = await client.get(url)

        
        L.info({"event": "CLIENT.GET.RESPONSE", 
                "path": path, 
                "status": response.status_code, 
                "time": T.time() - t1
                })

        response.raise_for_status()
        return response.json()

    #async def _put(self, path: str, payload: Any, headers: Dict[str, str] = {}):
    #    """
    #    Método interno para PUT (actualizaciones).
    #    Devuelve True si no hay cuerpo (204), JSON en caso contrario.
    #    """
    #    url = f"{self.base_url}{path}"
    #    full_headers = {**self.headers, **headers}
    #    start = time.time()
#
    #    async with httpx.AsyncClient(headers=full_headers) as client:
    #        response = await client.put(url, json=payload)
    #        elapsed = time.time() - start
    #        logger.info(f"PUT {path} - {response.status_code} - {elapsed:.3f}s")
    #        response.raise_for_status()
#
    #        if response.status_code == 204 or not response.content:
    #            return True
    #        return response.json()
        
    async def _put(self, path: str, payload: Any, headers: Dict[str, str] = {}):
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.put(url, json=payload)

            
            L.info({"event": "CLIENT.PUT.RESPONSE", 
                    "path": path, 
                    "status": response.status_code, 
                    "time": T.time() - t1
                    })

            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return True
            return response.json()

    #async def _delete(self, path: str, headers: Dict[str, str] = {}):
    #    """
    #    Método interno para DELETE.
    #    Devuelve True si no hay cuerpo, o JSON si lo hay.
    #    """
    #    url = f"{self.base_url}{path}"
    #    full_headers = {**self.headers, **headers}
    #    start = time.time()
#
    #    async with httpx.AsyncClient(headers=full_headers) as client:
    #        response = await client.delete(url)
    #        elapsed = time.time() - start
    #        logger.info(f"DELETE {path} - {response.status_code} - {elapsed:.3f}s")
    #        response.raise_for_status()
#
    #        if response.status_code == 204 or not response.content:
    #            return True
    #        return response.json()
    #    
    #        # --- Métodos internos genéricos con logging detallado ---




    async def _delete(self, path: str, headers: Dict[str, str] = {}):
        """
        Método interno para DELETE.
        Devuelve True si no hay cuerpo, o JSON si lo hay.
        """
        url = f"{self.base_url}{path}"
        full_headers = {**self.headers, **headers}
        t1 = T.time()

        async with httpx.AsyncClient(headers=full_headers) as client:
            response = await client.delete(url)

        
        L.info({"event": "CLIENT.DELETE.RESPONSE", 
                "path": path, 
                "status": response.status_code, 
                "time": T.time() - t1
                })

        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return True
        return response.json()
