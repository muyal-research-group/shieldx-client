import httpx
import json
import time as T
from pydantic import BaseModel
from typing import Optional, Dict, Any,TypeVar,Type,List
from shieldx_client.log.logger_config import get_logger
from option import Result,Ok,Err
import shieldx_core.dtos as DTOS


L =  get_logger(name="shieldx-client")
R = TypeVar(name="R", bound=BaseModel)


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



    async def create_event(self, event: DTOS.EventCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """
        Crea un nuevo evento en el sistema ShieldX.
        """
        try:
            payload = json.loads(event.model_dump_json(by_alias=True))
            result = await self._post("/events", payload, model=DTOS.MessageWithIDDTO, headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def get_all_events(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Recupera todos los eventos registrados."""
        try:
            return await self._get("/events", model=DTOS.EventResponseDTO, headers=headers, is_list=True)
        except Exception as e:
            return Err(e)

    async def get_events_by_service(self, service_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filtra eventos por ID de servicio (como query param)."""
        try:
            result = await self._get(f"/events?service_id={service_id}", model=DTOS.EventResponseDTO, headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_service_path(self, service_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filtra eventos por ID de servicio (como path param)."""
        try:
            result = await self._get(f"/events/service/{service_id}", model=DTOS.EventResponseDTO, headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_microservice(self, microservice_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filtra eventos por ID de microservicio."""
        try:
            result = await self._get(f"/events/microservice/{microservice_id}", model=DTOS.EventResponseDTO, headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_function(self, function_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filtra eventos por ID de función."""
        try:
            result = await self._get(f"/events/function/{function_id}", model=DTOS.EventResponseDTO, headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_event_by_id(self, event_id: str, headers: Dict[str,str] = {}) ->  Result[DTOS.EventResponseDTO, Exception]:
        try:
            result = await self._get(f"/events/{event_id}", model=DTOS.EventResponseDTO, headers=headers)
            return Ok(result)
        except Exception as e:
            return Err(e)

    async def update_event(self, event_id: str, data: DTOS.EventUpdateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.EventResponseDTO, Exception]:
        """Actualiza los campos de un evento existente."""
        try:
            result = await self._put(f"/events/{event_id}", data, model=DTOS.EventResponseDTO, headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def delete_event(self, event_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Elimina un evento del sistema."""
        try:
            await self._delete(f"/events/{event_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        
# ---Events Types---

    async def create_event_type(self, event_type: DTOS.EventTypeCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO,Exception]:
        """Crea un nuevo tipo de evento."""
        try:
            payload = event_type.model_dump()
            result = await self._post(f"/event-types", payload=payload,model=DTOS.MessageWithIDDTO, headers=headers)
            return result
        except Exception as e:
            return Err(e)
        

    async def list_event_types(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventTypeResponseDTO],Exception]:
        """Lista todos los tipos de evento."""
        try:
            data = await self._get(path = "/event-types", model=DTOS.EventTypeResponseDTO,headers=headers,is_list=True)
            return data
            # return [EventTypeModel(**et) for et in data]
        except Exception as e:
            return Err(e)
        
        
    async def get_event_type_by_id(self, event_type_id: str, headers: Dict[str, str] = {}) -> Result[DTOS.EventTypeResponseDTO, Exception]:
        """Obtiene un tipo de evento específico por su ID."""
        #data = await self._get(f"/event-types/{event_type_id}", headers)
        #return EventTypeModel(**data)

        try:
            result = await self._get(f"/event-types/{event_type_id}", model=DTOS.EventTypeResponseDTO, headers=headers)
            return Ok(result)
        except Exception as e:
            return Err(e)

    async def delete_event_type(self, event_type_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        try:
            """Elimina un tipo de evento existente."""
            await self._delete(f"/event-types/{event_type_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
    # --- Relaciones EventType ⇄ Trigger ---

    async def link_trigger_to_event_type(self, event_type_id: str, trigger_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Asocia un trigger a un tipo de evento."""
        try:
            await self._post(f"/event-types/{event_type_id}/triggers/{trigger_id}", payload={}, model=None, headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        
    async def list_triggers_for_event_type(self, event_type_id: str, headers: Dict[str, str] = {})-> Result[List[DTOS.EventsTriggersDTO], Exception]:
        """Lista los triggers vinculados a un tipo de evento."""
        try:
            return await self._get(f"/event-types/{event_type_id}/triggers",model=DTOS.EventsTriggersDTO, headers=headers,is_list=True)
        except Exception as e:
            return Err(e)    

    async def replace_triggers_for_event_type(self, event_type_id: str, trigger_ids: list[str], headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Reemplaza completamente los triggers de un tipo de evento."""
        try:
            await self._put(f"/event-types/{event_type_id}/triggers", payload=trigger_ids, model=None, headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)


    async def unlink_trigger_from_event_type(self, event_type_id: str, trigger_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Desvincula un trigger de un tipo de evento."""
        try:
            await self._delete(f"/event-types/{event_type_id}/triggers/{trigger_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        
        # --- Relaciones Trigger ⇄ Rule ---


    async def link_rule_to_trigger(self, trigger_id: str, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Asocia una regla a un trigger."""
        try:
            await self._post(f"/triggers/{trigger_id}/rules/{rule_id}", payload={}, model=None, headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    async def list_rules_for_trigger(self, trigger_id: str, headers: Dict[str, str] = {})-> Result[List[DTOS.RulesTriggerDTO], Exception]:
        """Lista las reglas asociadas a un trigger."""
        try:
            return await self._get(f"/triggers/{trigger_id}/rules",model=DTOS.RulesTriggerDTO, headers=headers,is_list=True)
        except Exception as e:
            return Err(e)    
    

    async def create_and_link_rule(self, trigger_id: str, rule_payload: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Crea y vincula una regla a un trigger."""
        try:
            payload = json.loads(rule_payload.model_dump_json(by_alias=True))
            result = await self._post(f"/triggers/{trigger_id}/rules", payload, model=DTOS.MessageWithIDDTO, headers=headers) 
            return result
        except Exception as e:
            return Err(e)


    async def unlink_rule_from_trigger(self, trigger_id: str, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Desvincula una regla de un trigger."""
        try:
            await self._delete(f"/triggers/{trigger_id}/rules/{rule_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    # --- CRUD: Rule ---

    async def create_rule(self, rule: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Crea una nueva regla."""
        try:
            payload = json.loads(rule.model_dump_json(by_alias=True))
            response = await self._post("/rules", payload, model=DTOS.MessageWithIDDTO, headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def get_rule_by_id(self, rule_id: str, headers: Dict[str, str] = {})  -> Result[DTOS.RuleResponseDTO, Exception]:
        """Obtiene una regla por su ID."""
        try:
            response = await self._get(f"/rules/{rule_id}", model=DTOS.RuleResponseDTO, headers=headers)
            return Ok(response)
        except Exception as e:
            return Err(e)    

    async def update_rule(self, rule_id: str, rule: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Actualiza los atributos de una regla existente."""
        try:
            payload = json.loads(rule.model_dump_json(by_alias=True))
            response = await self._put(f"/rules/{rule_id}", payload, model=DTOS.MessageWithIDDTO, headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def list_rules(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.RuleResponseDTO],Exception]:
        """Lista todas las reglas existentes."""
        try:
            rules = await self._get("/rules", model=DTOS.RuleResponseDTO,headers=headers,is_list=True)
            return rules
        except Exception as e:
            return Err(e)

    async def delete_rule(self, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Elimina una regla por ID."""
        try:
            await self._delete(f"/rules/{rule_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        

    # --- CRUD: Trigger (por nombre) ---

    async def create_trigger(self,  trigger: DTOS.TriggerCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Crea un nuevo trigger."""
        try:
            payload = trigger.model_dump(by_alias=True)
            response = await self._post("/triggers/", payload, model=DTOS.MessageWithIDDTO, headers=headers)
            return Ok(response)
        except Exception as e:
            return Err(e)

    async def get_trigger_by_name(self, name: str, headers: Dict[str, str] = {}) -> Result[DTOS.TriggerResponseDTO, Exception]:
        """Obtiene un trigger por su nombre."""
        try:
            response = await self._get(f"/triggers/{name}", model=DTOS.TriggerResponseDTO, headers=headers)
            return Ok(response)
        except Exception as e:
            return Err(e)

    async def get_all_triggers(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggerResponseDTO], Exception]:
        """Lista todos los triggers registrados."""
        try:
            response = await self._get("/triggers/", model=DTOS.TriggerResponseDTO, headers=headers, is_list=True)
            return Ok(response)
        except Exception as e:
            return Err(e)

    async def update_trigger(self, name: str, updated_trigger: DTOS.TriggerCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Actualiza un trigger existente."""
        try:
            payload = updated_trigger.model_dump(by_alias=True)
            response = await self._put(f"/triggers/{name}", payload, model=DTOS.MessageWithIDDTO, headers=headers)
            return Ok(response)
        except Exception as e:
            return Err(e)

    async def delete_trigger(self, name: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Elimina un trigger existente."""
        try:
            await self._delete(f"/triggers/{name}", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)


    # --- Relaciones Trigger ⇄ Trigger (Encadenamiento) ---

    async def link_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Asocia un trigger hijo a un trigger padre."""
        try:
            
            await self._post(f"/triggers/{parent_id}/children/{child_id}", payload={}, model=None, headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)


    async def list_trigger_children(self, parent_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggersTriggersDTO], Exception]:
        """Lista los triggers hijos de un trigger padre."""
        try:
            response = await self._get(
                f"/triggers/{parent_id}/children",model=DTOS.TriggersTriggersDTO, headers=headers,is_list=True)
            return response
        except Exception as e:
            return Err(e)
        

    async def list_trigger_parents(self, child_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggersTriggersDTO], Exception]:
        """Lista los triggers padres de un trigger hijo."""
        try:
            response = await self._get(f"/triggers/{child_id}/parents",model=DTOS.TriggersTriggersDTO,headers=headers,is_list=True)
            return response
        except Exception as e:
            return Err(e)


    async def unlink_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Elimina la relación padre-hijo entre triggers."""
        try:
            await self._delete(f"/triggers/{parent_id}/children/{child_id}", headers)
            return Ok(True)
        except Exception as e:
            return Err(e)


    async def list_trigger_parents(
        self,
        child_id: str,
        headers: Dict[str, str] = {}
    ) -> Result[List[DTOS.TriggersTriggersDTO], Exception]:
        """Lista los triggers padres de un trigger hijo."""
        try:
            response = await self._get(
                f"/triggers/{child_id}/parents",
                model=List[DTOS.TriggersTriggersDTO],
                headers=headers,
                is_list=True
            )
            return Ok(response)
        except Exception as e:
            return Err(e)


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
        
    async def _post(self, path: str, payload: Dict[str, Any],model:Type[R], headers: Dict[str, str] = {})->Result[R, Exception]:
        """
        Método interno para enviar solicitudes POST.
        Combina cabeceras, mide el tiempo y maneja errores.
        Devuelve JSON si hay contenido, o {} en caso de 204.
        """
        try:
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
            # if response.status_code == 204 or not response.content:
                # return Ok({})
            return Ok(model.model_validate(response.json()))
        except Exception as e:
            return Err(e)


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

    async def _get(self, path: str,model:Type[R], headers: Dict[str, str] = {},is_list:bool =False)->Result[R| List[R], Exception]:
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
        raw = response.json()
        if is_list:
            parsed = [model.model_validate(item) for item in raw]
            return Ok(parsed)
        return model.model_validate(raw)

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
        
    async def _put(self, path: str, payload: Any, model: Type[R], headers: Dict[str, str] = {}) -> Result[R , Exception]:
        """
        Método interno para PUT (actualizaciones).
        Si `model` es proporcionado, parsea la respuesta al modelo.
        Si no hay contenido o status 204, retorna `Ok(True)`.
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.put(url, json=payload)

            L.info({
                "event": "CLIENT.PUT.RESPONSE",
                "path": path,
                "status": response.status_code,
                "time": T.time() - t1
            })

            response.raise_for_status()

            #if response.status_code == 204 or not response.content:
                #return Ok(True)

            json_data = response.json()
            return Ok(model.model_validate(json_data) if model else json_data)

        except Exception as e:
            return Err(e)

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




    async def _delete(self, path: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """
        Método interno para DELETE.
        Retorna `Ok(True)` si se elimina exitosamente.
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.delete(url)

            L.info({
                "event": "CLIENT.DELETE.RESPONSE",
                "path": path,
                "status": response.status_code,
                "time": T.time() - t1
            })

            response.raise_for_status()
            return Ok(True)

        except Exception as e:
            return Err(e)
