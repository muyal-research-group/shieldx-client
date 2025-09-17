import httpx
import json
import time as T
from pydantic import BaseModel
from typing import Optional, Dict, Any,TypeVar,Type,List
from shieldx_client.log.logger_config import get_logger
from option import Result,Ok,Err
from pathlib import Path
import shieldx_core.dtos as DTOS
from shieldx_client.choreography.interpreter import ChoreographyInterpreter
import asyncio

L =  get_logger(name="shieldx-client")
R = TypeVar(name="R", bound=BaseModel)

"""Async HTTP client for the ShieldX API.

Provides CRUD for:
- Events, Event Types, Rules, Triggers
- Relations: EventType⇄Trigger, Trigger⇄Rule, Trigger⇄Trigger

Public methods return `option.Result[T, Exception]`. Use `is_ok`, `unwrap`,
and `unwrap_err` instead of catching exceptions in normal flows.
"""
class ShieldXClient:
    """Client for interacting with the ShieldX backend.

    Manages shared headers, Pydantic serialization/validation, and basic logging.

    Attributes:
        base_url: Base API URL (without a trailing slash).
        headers: Default headers (JSON and optional Authorization).
    """
    def __init__(self, base_url: str, token: Optional[str] = None):
        """Initialize the client.

        Args:
            base_url: e.g. "http://localhost:20000/api/v1".
            token: Optional Bearer token added as `Authorization: Bearer <token>`.

        Note:
            `base_url` is normalized to not end with a slash.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"


    def interpret(self, choreography_path_or_text: str, *, as_text: bool = False) -> Result[Dict[str, Any], Exception]:
        """Interpret a choreography YAML and index entities (blocking).

        Internally uses `ChoreographyInterpreter`. Prefer `interpret_async` in async code.

        Args:
            choreography_path_or_text: File path to a YAML or the YAML text itself if `as_text=True`.
            as_text: When True, treat the input as raw YAML text.

        Returns:
            Dict with created/found IDs:
            {
                "event_types": {name: id, ...},
                "triggers": {name: id, ...},
                "rules": {target: id, ...},
                "links_count": int
            }

        Raises:
            FileNotFoundError: When a file path is provided and does not exist.
            RuntimeError: If an event loop is already running (use `interpret_async` instead).
            ValueError: If the YAML does not match the schema.
        """
        async def _runner(yaml_text: str) -> Result[Dict[str, Any], Exception]:
            interpreter = ChoreographyInterpreter(self)
            return await interpreter.index_from_text(yaml_text)
        try:
            if as_text:
                yaml_text = choreography_path_or_text
            else:
                p = Path(choreography_path_or_text)
                if not p.exists():
                    raise FileNotFoundError(f"No se encontró el archivo: {p}")
                yaml_text = p.read_text(encoding="utf-8")

            return asyncio.run(_runner(yaml_text))
        except RuntimeError as re:
            # ya hay loop → pedir interpret_async
            return Err(RuntimeError("Ya hay un event loop ejecutándose. Use interpret_async(...)."))
        except Exception as e:
            return Err(e)

    

    async def interpret_async(self, choreography_path_or_text: str, *, as_text: bool = False) -> Result[Dict[str, Any], Exception]:
        """Interpret a choreography YAML and index entities (async).

        Args:
            choreography_path_or_text: File path to the YAML or the YAML text if `as_text=True`.
            as_text: When True, treat the input as raw YAML text.

        Returns:
            Same structure as `interpret`.
        """
        try:
            if as_text:
                yaml_text = choreography_path_or_text
            else:
                p = Path(choreography_path_or_text)
                if not p.exists():
                    raise FileNotFoundError(f"No se encontró el archivo: {p}")
                yaml_text = p.read_text(encoding="utf-8")
            interpreter = ChoreographyInterpreter(self)
            return await interpreter.index_from_text(yaml_text)
        except Exception as e:
            return Err(e)

# --- Events ---
    async def create_event(self, event: DTOS.EventCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Create a new Event.

        Args:
            event: DTO with service_id, microservice_id, function_id, event_type, and payload.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` (contains message and created event `id`).
        """
        try:
            payload = json.loads(event.model_dump_json(by_alias=True))
            result = await self._post("/events", payload, model=DTOS.MessageWithIDDTO, operation="CREATE_EVENT", headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def get_all_events(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventResponseDTO], Exception]:
        """List all Events.

        Args:
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventResponseDTO`.
        """
        try:
            return await self._get("/events", model=DTOS.EventResponseDTO, operation="GET_ALL_EVENTS", headers=headers, is_list=True)
        except Exception as e:
            return Err(e)

    async def get_events_by_service(self, service_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filter Events by `service_id` (query parameter).

        Args:
            service_id: Service identifier.
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventResponseDTO`.
        """
        try:
            result = await self._get(f"/events?service_id={service_id}", model=DTOS.EventResponseDTO, operation="GET_EVENTS_BY_SERVICE", headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_service_path(self, service_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filtra eventos por ID de servicio (como path param)."""
        try:
            result = await self._get(f"/events/service/{service_id}", model=DTOS.EventResponseDTO, operation="GET_EVENTS_BY_SERVICE_PATH", headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_microservice(self, microservice_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filter Events by `microservice_id`.

        Args:
            microservice_id: Microservice identifier.
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventResponseDTO`.
        """
        try:
            result = await self._get(f"/events/microservice/{microservice_id}", model=DTOS.EventResponseDTO, operation="GET_EVENTS_BY_MICROSERVICE", headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_events_by_function(self, function_id: str, headers: Dict[str, str] = {})  -> Result[List[DTOS.EventResponseDTO], Exception]:
        """Filter Events by `function_id`.

        Args:
            function_id: Function identifier.
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventResponseDTO`.
        """
        try:
            result = await self._get(f"/events/function/{function_id}", model=DTOS.EventResponseDTO, operation="GET_EVENTS_BY_FUNCTION", headers=headers, is_list=True)
            return result
        except Exception as e:
            return Err(e)

    async def get_event_by_id(self, event_id: str, headers: Dict[str,str] = {}) ->  Result[DTOS.EventResponseDTO, Exception]:
        """Get an Event by ID.

        Args:
            event_id: Event identifier.
            headers: Optional extra headers.

        Returns:
            Result with `EventResponseDTO`.
        """
        try:
            result = await self._get(f"/events/{event_id}", model=DTOS.EventResponseDTO,operation="GET_EVENT_BY_ID", headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def update_event(self, event_id: str, data: DTOS.EventUpdateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.EventResponseDTO, Exception]:
        """Update an Event.

        Args:
            event_id: Event identifier.
            data: DTO with the fields to update.
            headers: Optional extra headers.

        Returns:
            Result with the updated `EventResponseDTO`.
        """
        try:
            payload = json.loads(data.model_dump_json(by_alias=True, exclude_none=True))
            result = await self._put(f"/events/{event_id}", payload, model=DTOS.EventResponseDTO, operation="UPDATE_EVENT", headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def delete_event(self, event_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Delete an Event by ID.

        Args:
            event_id: Event identifier.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the deletion succeeded.
        """
        try:
            await self._delete(f"/events/{event_id}",operation="DELETE_EVENT", headers= headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

# ---Events Types---

    async def create_event_type(self, event_type: DTOS.EventTypeCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO,Exception]:
        """Create an Event Type.

        Args:
            event_type: DTO with `event_type`.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` (created id).
        """
        try:
            payload = event_type.model_dump()
            result = await self._post(f"/event-types", payload=payload,model=DTOS.MessageWithIDDTO, operation="CREATE_EVENT_TYPE", headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def find_event_type_by_name_dict(self, event_type: str) -> Result[Optional[dict], Exception]:
        """Find an Event Type by name.

        Args:
            event_type: Event Type name.

        Returns:
            Dict `{"id": str, "event_type": str}` if found, otherwise `None`.
        """
        try:
            res = await self.list_event_types()
            if res.is_ok:
                for dto in res.unwrap():
                    if dto.event_type == event_type:
                        return Ok({"id": dto.event_type_id, "event_type": dto.event_type})
                return Ok(None)
        except Exception as e:
            return Err(e)

    async def create_event_type_dict(self, event_type_name: str) -> Result[dict, Exception]:
        """Create an Event Type and return a simple dict.

        Args:
            event_type_name: Event Type name.

        Returns:
            Dict `{"id": str, "event_type": str}`.
        """
        try:
            req = DTOS.EventTypeCreateDTO(event_type=event_type_name)
            res = await self.create_event_type(req)
            if res.is_err:
                return Err(res.unwrap_err())
            msg = res.unwrap()  # MessageWithIDDTO
            return Ok({"id": msg.id, "event_type": event_type_name})
        except Exception as e:
            return Err(e)
        

    async def list_event_types(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.EventTypeResponseDTO],Exception]:
        """List all Event Types.

        Args:
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventTypeResponseDTO`.
        """
        try:
            data = await self._get(path = "/event-types", model=DTOS.EventTypeResponseDTO, operation="LIST_EVENT_TYPES", headers=headers,is_list=True)
            return data
            # return [EventTypeModel(**et) for et in data]
        except Exception as e:
            return Err(e)

    async def get_event_type_by_id(self, event_type_id: str, headers: Dict[str, str] = {}) -> Result[DTOS.EventTypeResponseDTO, Exception]:
        """Get an Event Type by ID.

        Args:
            event_type_id: Event Type identifier.
            headers: Optional extra headers.

        Returns:
            Result with `EventTypeResponseDTO`.
        """
        #data = await self._get(f"/event-types/{event_type_id}", headers)
        #return EventTypeModel(**data)

        try:
            result = await self._get(f"/event-types/{event_type_id}", model=DTOS.EventTypeResponseDTO, operation="GET_EVENT_TYPE_BY_ID", headers=headers)
            return result
        except Exception as e:
            return Err(e)

    async def delete_event_type(self, event_type_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Delete an Event Type by ID.

        Args:
            event_type_id: Event Type identifier.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the deletion succeeded.
        """
        try:
            await self._delete(f"/event-types/{event_type_id}",operation="DELETE_EVENT_TYPE", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
    # --- Relaciones EventType ⇄ Trigger ---

    async def is_trigger_bound_to_event_type_bool(self, event_type_id: str, trigger_id: str) -> Result[bool, Exception]:
        """Check whether a Trigger is bound to an Event Type.

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.

        Returns:
            True if the relation exists; otherwise False.
        """
        try:
            res = await self.list_triggers_for_event_type(event_type_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok(any(link.trigger_id == trigger_id for link in res.unwrap()))
        except Exception as e:
            return Err(e)

    async def bind_event_type_to_trigger_dict(self, event_type_id: str, trigger_id: str)  -> Result[dict, Exception]:
        """Bind a Trigger to an Event Type.

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.

        Returns:
            Dict `{"event_type_id": str, "trigger_id": str}`.
        """
        try:
            res = await self.link_trigger_to_event_type(event_type_id, trigger_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok({"event_type_id": event_type_id, "trigger_id": trigger_id})
        except Exception as e:
            return Err(e)

    async def link_trigger_to_event_type(self, event_type_id: str, trigger_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Create the EventType⇄Trigger relation.

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the link was created.
        """
        try:
            await self._post(f"/event-types/{event_type_id}/triggers/{trigger_id}", payload={}, model=None,operation="LINK_TRIGGER_TO_EVENT_TYPE", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        
    async def list_triggers_for_event_type(self, event_type_id: str, headers: Dict[str, str] = {})-> Result[List[DTOS.EventsTriggersDTO], Exception]:
        """List Triggers bound to an Event Type.

        Args:
            event_type_id: Event Type ID.
            headers: Optional extra headers.

        Returns:
            Result with a list of `EventsTriggersDTO`.
        """
        try:
            return await self._get(f"/event-types/{event_type_id}/triggers",model=DTOS.EventsTriggersDTO,operation="LIST_TRIGGERS_FOR_EVENT_TYPE", headers=headers,is_list=True)
        except Exception as e:
            return Err(e)    

    async def replace_triggers_for_event_type(self, event_type_id: str, trigger_ids: list[str], headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Replace all Triggers bound to an Event Type.

        Args:
            event_type_id: Event Type ID.
            trigger_ids: Trigger IDs to remain linked.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the replacement succeeded.
        """
        try:
            await self._put(f"/event-types/{event_type_id}/triggers", payload=trigger_ids, model=None, operation="REPLACE_TRIGGERS_FOR_EVENT_TYPE", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    async def unlink_trigger_from_event_type(self, event_type_id: str, trigger_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Remove the EventType⇄Trigger relation.

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the unlink succeeded.
        """
        try:
            await self._delete(f"/event-types/{event_type_id}/triggers/{trigger_id}", operation="UNLINK_TRIGGER_FROM_EVENT_TYPE", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)
        
        # --- Relaciones Trigger ⇄ Rule ---


# --- Relaciones Trigger ⇄ Rule ---

    async def is_rule_bound_to_trigger_bool(self, trigger_id: str, rule_id: str) -> Result[bool, Exception]:
        """Check whether a Rule is bound to a Trigger.

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.

        Returns:
            True if the relation exists; otherwise False.
        """
        try:
            res = await self.list_rules_for_trigger(trigger_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok(any(link.rule_id == rule_id for link in res.unwrap()))
        except Exception as e:
            return Err(e)

    async def bind_rule_to_trigger_dict(self, trigger_id: str, rule_id: str) -> dict:
        """Bind a Rule to a Trigger.

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.

        Returns:
            Dict `{"trigger_id": str, "rule_id": str}`.
        """
        try:
            res = await self.link_rule_to_trigger(trigger_id, rule_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok({"trigger_id": trigger_id, "rule_id": rule_id})
        except Exception as e:
            return Err(e)


    async def link_rule_to_trigger(self, trigger_id: str, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Create the Trigger⇄Rule relation.

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the link was created.
        """
        try:
            await self._post(f"/triggers/{trigger_id}/rules/{rule_id}", payload={}, model=None,operation="LINK_RULE_TO_TRIGGER", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    async def list_rules_for_trigger(self, trigger_id: str, headers: Dict[str, str] = {})-> Result[List[DTOS.RulesTriggerDTO], Exception]:
        """List Rules bound to a Trigger.

        Args:
            trigger_id: Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with a list of `RulesTriggerDTO`.
        """
        try:
            return await self._get(f"/triggers/{trigger_id}/rules",model=DTOS.RulesTriggerDTO,operation="LIST_RULES_FOR_TRIGGER", headers=headers,is_list=True)
        except Exception as e:
            return Err(e)    

    async def create_and_link_rule(self, trigger_id: str, rule_payload: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Create a Rule and link it to a Trigger.

        Args:
            trigger_id: Destination Trigger ID.
            rule_payload: Rule creation DTO.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` for the created Rule.
        """
        try:
            payload = json.loads(rule_payload.model_dump_json(by_alias=True))
            result = await self._post(f"/triggers/{trigger_id}/rules", payload, model=DTOS.MessageWithIDDTO,operation="CREATE_RULE_AND_LINK_RULE", headers=headers) 
            return result
        except Exception as e:
            return Err(e)

    async def unlink_rule_from_trigger(self, trigger_id: str, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Remove the Trigger⇄Rule relation.

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the unlink succeeded.
        """
        try:
            await self._delete(f"/triggers/{trigger_id}/rules/{rule_id}",operation="UNLINK_RULE_FROM_TRIGGER",  headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

# --- CRUD Rule (helpers estilo dict) ---

    async def find_rule_by_target_dict(self, target: str) -> Result[Optional[dict], Exception]:
        """Find a Rule by `target`.

        Args:
            target: Target function/action.

        Returns:
            Dict `{"id": str, "target": str}` if found, otherwise `None`.
        """
        try:
            res = await self.list_rules()
            if res.is_err:
                return Err(res.unwrap_err())
            for dto in res.unwrap():
                if dto.target == target:
                    return Ok({"id": dto.rule_id, "target": dto.target})
            return Ok(None)
        except Exception as e:
            return Err(e)

    async def create_rule_dict(self, target: str, parameters: dict) -> Result[dict, Exception]:
        """Create a Rule and return a small dict.

        Args:
            target: Rule target.
            parameters: Parameter map `{name: {type, description, ...}}`.

        Returns:
            Dict `{"id": str, "target": str}`.
        """
        try:
            res = await self.create_rule(DTOS.RuleCreateDTO(target=target, parameters=parameters))
            if res.is_err:
                return Err(res.unwrap_err())
            msg = res.unwrap()
            return Ok({"id": msg.id, "target": target})
        except Exception as e:
            return Err(e)


    async def create_rule(self, rule: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Create a new Rule.

        Args:
            rule: DTO with `target` and `parameters`.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` (created id).
        """
        try:
            payload = json.loads(rule.model_dump_json(by_alias=True))
            response = await self._post("/rules", payload, model=DTOS.MessageWithIDDTO,operation="CREATE_RULE", headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def get_rule_by_id(self, rule_id: str, headers: Dict[str, str] = {})  -> Result[DTOS.RuleResponseDTO, Exception]:
        """Get a Rule by ID.

        Args:
            rule_id: Rule identifier.
            headers: Optional extra headers.

        Returns:
            Result with `RuleResponseDTO`.
        """
        try:
            response = await self._get(f"/rules/{rule_id}", model=DTOS.RuleResponseDTO,operation="GET_RULE_BY_ID", headers=headers)
            return response
        except Exception as e:
            return Err(e)    

    async def update_rule(self, rule_id: str, rule: DTOS.RuleCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Update a Rule.

        Args:
            rule_id: Rule identifier.
            rule: DTO with new `target`/`parameters`.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` (backend message).
        """
        try:
            payload = json.loads(rule.model_dump_json(by_alias=True))
            response = await self._put(f"/rules/{rule_id}", payload, model=DTOS.MessageWithIDDTO, operation="UPDATE_RULE", headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def list_rules(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.RuleResponseDTO],Exception]:
        """List all Rules.

        Args:
            headers: Optional extra headers.

        Returns:
            Result with a list of `RuleResponseDTO`.
        """
        try:
            rules = await self._get("/rules", model=DTOS.RuleResponseDTO, operation="LIST_RULES", headers=headers,is_list=True)
            return rules
        except Exception as e:
            return Err(e)

    async def delete_rule(self, rule_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Delete a Rule by ID.

        Args:
            rule_id: Rule identifier.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the deletion succeeded.
        """
        try:
            await self._delete(f"/rules/{rule_id}", operation="DELETE_RULE", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    # --- CRUD: Trigger (por nombre) ---
        
    async def find_trigger_by_name_dict(self, name: str) -> Result[Optional[dict], Exception]:
        """Find a Trigger by name.

        Args:
            name: Trigger name.

        Returns:
            Dict `{"id": str, "name": str}` if found; `None` on 404.
        """
        try:
            res = await self.get_trigger_by_name(name)
            if res.is_ok:
                dto = res.unwrap()
                return Ok({"id": dto.trigger_id, "name": dto.name})
            # Si fue 404, tu _get ya convertiría en Err; aquí lo tratamos como None si es 404.
            err = res.unwrap_err()
            if isinstance(err, httpx.HTTPStatusError) and err.response.status_code == 404:
                return Ok(None)
            return Err(err)
        except Exception as e:
            return Err(e)

    async def create_trigger_dict(self,payload: dict) -> Result[dict, Exception]:
        """Create a Trigger and return a small dict.

        Args:
            name: Trigger name.

        Returns:
            Dict `{"id": str, "name": str}`.
        """
        try:
            dto = DTOS.TriggerCreateDTO(**payload)
            res = await self.create_trigger(dto)
            if res.is_err:
                return Err(res.unwrap_err())
            msg = res.unwrap()
            return Ok({"id": msg.id, "name": dto.name})
        except Exception as e:
            return Err(e)

    async def create_trigger(self,  trigger: DTOS.TriggerCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Create a new Trigger.

        Args:
            trigger: DTO with name (and optionally nested rule per your backend).
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO` (created id).
        """
        try:
            payload = trigger.model_dump(by_alias=True)
            response = await self._post("/triggers/", payload, model=DTOS.MessageWithIDDTO, operation="CREATE_TRIGGER", headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def get_trigger_by_name(self, name: str, headers: Dict[str, str] = {}) -> Result[DTOS.TriggerResponseDTO, Exception]:
        """Get a Trigger by name.

        Args:
            name: Trigger name.
            headers: Optional extra headers.

        Returns:
            Result with `TriggerResponseDTO`.
        """
        try:
            response = await self._get(f"/triggers/{name}", model=DTOS.TriggerResponseDTO, operation="GET_TRIGGER_BY_NAME", headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def get_all_triggers(self, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggerResponseDTO], Exception]:
        """List all Triggers.

        Args:
            headers: Optional extra headers.

        Returns:
            Result with a list of `TriggerResponseDTO`.
        """
        try:
            response = await self._get("/triggers/", model=DTOS.TriggerResponseDTO, operation="LIST_TRIGGERS", headers=headers, is_list=True)
            return response
        except Exception as e:
            return Err(e)

    async def update_trigger(self, name: str, updated_trigger: DTOS.TriggerCreateDTO, headers: Dict[str, str] = {}) -> Result[DTOS.MessageWithIDDTO, Exception]:
        """Update a Trigger by name.

        Args:
            name: Trigger name (path identifier).
            updated_trigger: DTO with the new fields.
            headers: Optional extra headers.

        Returns:
            Result with `MessageWithIDDTO`.
        """
        try:
            payload = updated_trigger.model_dump(by_alias=True)
            response = await self._put(f"/triggers/{name}", payload, model=DTOS.MessageWithIDDTO, operation="UPDATE_TRIGGER", headers=headers)
            return response
        except Exception as e:
            return Err(e)

    async def delete_trigger(self, name: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Delete a Trigger by name.

        Args:
            name: Trigger name.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the deletion succeeded.
        """
        try:
            await self._delete(f"/triggers/{name}", operation="DELETE_TRIGGER", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    # --- Relaciones Trigger ⇄ Trigger (Encadenamiento) ---

    async def is_trigger_linked_to_trigger_bool(self, parent_id: str, child_id: str) -> Result[bool, Exception]:
        """Check whether a parent Trigger is linked to a child Trigger.

        Args:
            parent_id: Parent Trigger ID.
            child_id: Child Trigger ID.

        Returns:
            True if the relation exists; otherwise False.
        """
        try:
            res = await self.list_trigger_children(parent_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok(any(link.trigger_child_id == child_id for link in res.unwrap()))
        except Exception as e:
            return Err(e)

    async def bind_trigger_to_trigger_dict(self, parent_id: str, child_id: str) -> Result[dict, Exception]:
        """Bind a child Trigger to a parent Trigger.

        Args:
            parent_id: Parent Trigger ID.
            child_id: Child Trigger ID.

        Returns:
            Dict `{"trigger_parent_id": str, "trigger_child_id": str}`.
        """
        try:
            res = await self.link_trigger_child(parent_id, child_id)
            if res.is_err:
                return Err(res.unwrap_err())
            return Ok({"trigger_parent_id": parent_id, "trigger_child_id": child_id})
        except Exception as e:
            return Err(e)


    async def link_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Create the Parent⇄Child Trigger relation.

        Args:
            parent_id: Parent Trigger ID.
            child_id: Child Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the link was created.
        """
        try:
            
            await self._post(f"/triggers/{parent_id}/children/{child_id}", payload={}, model=None, operation="LINK_TRIGGER_CHILD", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)

    async def list_trigger_children(self, parent_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggersTriggersDTO], Exception]:
        """List all children for a parent Trigger.

        Args:
            parent_id: Parent Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with a list of `TriggersTriggersDTO`.
        """
        try:
            response = await self._get(
                f"/triggers/{parent_id}/children",model=DTOS.TriggersTriggersDTO, operation="LIST_TRIGGER_CHILDREN", headers=headers,is_list=True)
            return response
        except Exception as e:
            return Err(e)

    async def list_trigger_parents(self, child_id: str, headers: Dict[str, str] = {}) -> Result[List[DTOS.TriggersTriggersDTO], Exception]:
        """List all parents for a child Trigger.

        Args:
            child_id: Child Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with a list of `TriggersTriggersDTO`.
        """
        try:
            response = await self._get(f"/triggers/{child_id}/parents", model=DTOS.TriggersTriggersDTO, operation="LIST_TRIGGER_PARENTS", headers=headers,is_list=True)
            return response
        except Exception as e:
            return Err(e)

    async def unlink_trigger_child(self, parent_id: str, child_id: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """Remove the Parent⇄Child Trigger relation.

        Args:
            parent_id: Parent Trigger ID.
            child_id: Child Trigger ID.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the unlink succeeded.
        """
        try:
            await self._delete(f"/triggers/{parent_id}/children/{child_id}", operation="UNLINK_TRIGGER_CHILD", headers=headers)
            return Ok(True)
        except Exception as e:
            return Err(e)


    async def _post(self, path: str, payload: Dict[str, Any],model:Type[R], operation: str, headers: Dict[str, str] = {})->Result[R, Exception]:
        """POST helper that validates the JSON response with a Pydantic model.

        Args:
            path: Relative path (joined with `base_url`).
            payload: Request JSON body.
            model: Pydantic model used to parse the response.
            headers: Optional extra headers.

        Returns:
            Result with an instance of `model`.
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.post(url, json=payload)

            
            
            L.info({"event": f"CLIENT.{operation}.RESPONSE", 
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

    async def _get(self, path: str,model:Type[R], operation: str, headers: Dict[str, str] = {},is_list:bool =False)->Result[R| List[R], Exception]:
        """GET helper that validates the JSON response with a Pydantic model.

        Args:
            path: Relative path.
            model: Expected Pydantic model.
            headers: Optional extra headers.
            is_list: When True, parse the response as a list of `model`.

        Returns:
            Result with `model` or `List[model]`.
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.get(url)

            
            L.info({"event": f"CLIENT.{operation}.RESPONSE", 
                    "path": path, 
                    "status": response.status_code, 
                    "time": T.time() - t1
                    })

            response.raise_for_status()
            raw = response.json()
            if is_list:
                parsed = [model.model_validate(item) for item in raw]
                return Ok(parsed)
            return Ok(model.model_validate(raw))
        except Exception as e:
            return Err(e)

    async def _put(self, path: str, payload: Any, model: Type[R], operation: str, headers: Dict[str, str] = {}) -> Result[R , Exception]:
        """PUT helper with Pydantic validation.

        Args:
            path: Relative path.
            payload: Request JSON body.
            model: Expected Pydantic model (when None, returns raw JSON).
            headers: Optional extra headers.

        Returns:
            Result with an instance of `model` (or raw JSON if `model` is None).
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.put(url, json=payload)

            L.info({
                "event": f"CLIENT.{operation}.RESPONSE",
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

    async def _delete(self, path: str, operation: str, headers: Dict[str, str] = {}) -> Result[bool, Exception]:
        """DELETE helper with basic logging.

        Args:
            path: Relative path.
            headers: Optional extra headers.

        Returns:
            Result with `True` if the deletion succeeded.
        """
        try:
            url = f"{self.base_url}{path}"
            full_headers = {**self.headers, **headers}
            t1 = T.time()

            async with httpx.AsyncClient(headers=full_headers) as client:
                response = await client.delete(url)

            L.info({
                "event": f"CLIENT.{operation}.RESPONSE",
                "path": path,
                "status": response.status_code,
                "time": T.time() - t1
            })

            response.raise_for_status()
            return Ok(True)

        except Exception as e:
            return Err(e)