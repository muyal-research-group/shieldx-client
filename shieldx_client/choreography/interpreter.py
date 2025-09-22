from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import yaml
from pydantic import ValidationError
from option import Result, Ok, Err
from shieldx_client.choreography.schema import ChoreographySpec, TriggerSpec, TargetSpec, ParametersSpec, RefSpec


"""YAML choreography interpreter for ShieldX.

Parses a choreography (see `schema.py`), creates/finds EventTypes, Rules, and Triggers,
and ensures EventType⇄Trigger, Trigger⇄Rule, and optional Trigger⇄Trigger relations.
"""

class ChoreographyInterpreter:
    """Apply a choreography spec to the ShieldX backend.

    Relies on a `ShieldXClient` that exposes high-level helpers (dict/bool).
    """

    def __init__(self, client):
        """Create the interpreter.

        Args:
            client: A `ShieldXClient` (or compatible) used to call the API.
        """
        self.client = client  # ShieldXClient con wrappers *_dict / *_bool

    # -------- API pública --------
    async def index_from_text(self, choreography_yaml: str) -> Result[Dict[str, Any], Exception]:
        """Parse YAML and apply the choreography.

        Args:
            choreography_yaml: YAML string.

        Returns:
            Result[Dict[str, Any], Exception] con los mapeos name→id y `links_count`.
        """
        try:
            spec_res = self._parse_spec(choreography_yaml)
            if spec_res.is_err:
                return Err(spec_res.unwrap_err())
            return await self._index_entities(spec_res.unwrap())
        except Exception as e:
            return Err(e)

    # -------- Internos --------
    def _parse_spec(self, choreography_yaml: str) -> Result[ChoreographySpec, Exception]:
        """Validate YAML against the Pydantic schema.

        Args:
            choreography_yaml: YAML string.

        Returns:
            `ChoreographySpec` instance.

        Raises:
            ValueError: If the YAML does not match the schema.
        """
        try:
            raw = yaml.safe_load(choreography_yaml) or {}
            spec =  ChoreographySpec.model_validate(raw)
            return Ok(spec)
        except ValidationError as ve:
            return Err(ValueError(f"Invalid choreography: {ve}"))
        except Exception as e:
            return Err(e)

    async def _index_entities(self, spec: ChoreographySpec) -> Result[Dict[str, Any], Exception]:
        """Create/find entities and wire up relations from the spec.

        Order:
            1) EventTypes (explicit ones or inferred from trigger names)
            2) Rule (per trigger)
            3) Trigger
            4) Link Trigger⇄Rule
            5) Link EventType⇄Trigger
            6) (Optional) Link Trigger⇄Trigger

        Args:
            spec: Validated choreography spec.

        Returns:
            Summary dict with {name: id} and `links_count`.
        """
        try:
            event_type_ids: Dict[str, str] = {}
            trigger_ids: Dict[str, str] = {}
            rule_ids: Dict[str, str] = {}

            # 1–5: por cada trigger
            for trig in spec.triggers:
                # 1) EventTypes
                et_names = trig.event_types or [trig.name]
                et_ids_for_this_trigger: List[str] = []
                for et_name in et_names:
                    et_res = await self._get_or_create_event_type(et_name)
                    if et_res.is_err:
                        return Err(et_res.unwrap_err())
                    et_id = et_res.unwrap()
                    event_type_ids[et_name] = et_id
                    et_ids_for_this_trigger.append(et_id)

                # 2) Rule (firma derivada del target + method)
                signature_dict, signature_str = self._signature_from_target(trig.rule.target)
                params_schema = self._encode_parameters(trig.rule.parameters)

                rule_res = await self._get_or_create_rule(signature_dict, params_schema)
                if rule_res.is_err:
                    return Err(rule_res.unwrap_err())
                rule_id = rule_res.unwrap()
                rule_ids[signature_str] = rule_id

                # 3) Trigger
                trig_res = await self._get_or_create_trigger(trig)
                if trig_res.is_err:
                    return Err(trig_res.unwrap_err())
                trig_id = trig_res.unwrap()
                trigger_ids[trig.name] = trig_id

                # 4) Vincular Trigger ⇄ Rule
                bind_rt = await self._bind_rules_trigger(trigger_id=trig_id, rule_id=rule_id)
                if bind_rt.is_err:
                    return Err(bind_rt.unwrap_err())

                # 5) Vincular EventType ⇄ Trigger
                for et_id in et_ids_for_this_trigger:
                    bind_et = await self._bind_event_trigger(event_type_id=et_id, trigger_id=trig_id)
                    if bind_et.is_err:
                        return Err(bind_et.unwrap_err())

            # 6a) Encadenamiento por depends_on (preferido)
            for trig in spec.triggers:
                if trig.depends_on:
                    parent = trigger_ids.get(trig.depends_on)
                    child = trigger_ids.get(trig.name)
                    if parent and child:
                        link_res = await self._bind_triggers_triggers(
                            src_trigger_id=parent,
                            dst_trigger_id=child,
                            order=None,
                            condition=None,
                        )
                        if link_res.is_err:
                            return Err(link_res.unwrap_err())

            # 6b) Links opcionales (legado)
            for link in (spec.links or []):
                src = trigger_ids.get(link.from_trigger)
                dst = trigger_ids.get(link.to_trigger)
                if src and dst:
                    bind_tt = await self._bind_triggers_triggers(
                        src_trigger_id=src,
                        dst_trigger_id=dst,
                        order=link.order,
                        condition=link.condition,
                    )
                    if bind_tt.is_err:
                        return Err(bind_tt.unwrap_err())

            # Summary
            total_links = len([t for t in spec.triggers if t.depends_on]) + len(spec.links or [])
            return Ok(
                {
                    "event_types": event_type_ids,
                    "triggers": trigger_ids,
                    "rules": rule_ids,
                    "links_count": total_links,
                }
            )
        except Exception as e:
            return Err(e)

    # -------- Helpers (usando SOLO campos definidos) --------
    async def _get_or_create_event_type(self, event_type_name: str) -> Result[str, Exception]:
        """Get or create an Event Type and return its ID.

        Args:
            event_type_name: Event Type name.

        Returns:
            Event Type ID.
        """
        try:
            found_res = await self.client.find_event_type_by_name_dict(event_type_name)
            if found_res.is_err:
                return Err(found_res.unwrap_err())
            found = found_res.unwrap()
            if found:
                return Ok(found["id"])

            created_res = await self.client.create_event_type_dict(event_type_name)
            if created_res.is_err:
                return Err(created_res.unwrap_err())
            created = created_res.unwrap()
            return Ok(created["id"])
        except Exception as e:
            return Err(e)

    async def _get_or_create_trigger(self, trig: TriggerSpec) -> Result[str, Exception]:
        """Get or create a Trigger and return its ID.

        Args:
            trig: `TriggerSpec` with name (and its rule).

        Returns:
            Trigger ID.
        """
        try:
            found_res = await self.client.find_trigger_by_name_dict(trig.name)
            if found_res.is_err:
                return Err(found_res.unwrap_err())
            found = found_res.unwrap()
            if found:
                return Ok(found["id"])
            
            payload = {
            "name": trig.name,
            "depends_on": trig.depends_on,
            }

            created_res = await self.client.create_trigger_dict(payload)
            if created_res.is_err:
                return Err(created_res.unwrap_err())
            created = created_res.unwrap()
            return Ok(created["id"])
        except Exception as e:
            return Err(e)
            
    async def _get_or_create_rule(self, signature_dict: Dict[str, Any], params_schema: Dict[str, Dict[str, Any]]) -> Result[str, Exception]:
        """Get or create a Rule and return its ID.

        Validates that parameter types are allowed.

        Args:
            trig: `TriggerSpec` that contains `rule` and its `parameters`.

        Returns:
            Rule ID.

        Raises:
            ValueError: If any parameter has a disallowed `type`.
        """
        try:
            # Buscar por firma (alias o bucket/key/method). Reutilizamos el método existente.
            found_res = await self.client.find_rule_by_target_dict(signature_dict)
            if found_res.is_err:
                return Err(found_res.unwrap_err())
            found = found_res.unwrap()
            if found:
                return Ok(found["id"])
            # Crear con firma + parámetros (el servidor puede ignorar/aceptar este esquema según su modelo).
            created_res = await self.client.create_rule_dict(signature_dict, params_schema)
            if created_res.is_err:
                return Err(created_res.unwrap_err())
            created = created_res.unwrap()
            return Ok(created["id"])
        except Exception as e:
            return Err(e)



    async def _bind_rules_trigger(
        self,
        *,
        trigger_id: str,
        rule_id: str,
        priority: int = 0,
        condition: Optional[str] = None,
    ) -> Result[bool, Exception]:
        """Ensure the Trigger⇄Rule relation (idempotent).

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.
            priority: Reserved (not used).
            condition: Reserved (not used).
        """
        try:
            bound_res = await self.client.is_rule_bound_to_trigger_bool(trigger_id, rule_id)
            if bound_res.is_err:
                return Err(bound_res.unwrap_err())
            bound = bound_res.unwrap()

            if not bound:
                link_res = await self.client.bind_rule_to_trigger_dict(trigger_id, rule_id)
                if link_res.is_err:
                    return Err(link_res.unwrap_err())
            return Ok(True)
        except Exception as e:
            return Err(e)

    async def _bind_event_trigger(
        self,
        *,
        event_type_id: str,
        trigger_id: str,
        priority: int = 0,
        condition: Optional[str] = None,
    ) -> Result[bool, Exception]:
        """Ensure the EventType⇄Trigger relation (idempotent).

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.
            priority: Reserved (not used).
            condition: Reserved (not used).
        """
        try:
            bound_res = await self.client.is_trigger_bound_to_event_type_bool(event_type_id, trigger_id)
            if bound_res.is_err:
                return Err(bound_res.unwrap_err())
            bound = bound_res.unwrap()

            if not bound:
                link_res = await self.client.bind_event_type_to_trigger_dict(event_type_id, trigger_id)
                if link_res.is_err:
                    return Err(link_res.unwrap_err())
            return Ok(True)
        except Exception as e:
            return Err(e)
        

    async def _bind_triggers_triggers(
        self, *, src_trigger_id: str, dst_trigger_id: str, order: Optional[int], condition: Optional[str]
    ) -> Result[bool, Exception]:
        """Ensure the Parent⇄Child Trigger relation (idempotent).

        Args:
            src_trigger_id: Source Trigger ID (parent).
            dst_trigger_id: Destination Trigger ID (child).
            order: Optional execution order.
            condition: Optional chaining condition.
        """
        try:
            bound_res = await self.client.is_trigger_linked_to_trigger_bool(src_trigger_id, dst_trigger_id)
            if bound_res.is_err:
                return Err(bound_res.unwrap_err())
            bound = bound_res.unwrap()

            if not bound:
                link_res = await self.client.bind_trigger_to_trigger_dict(src_trigger_id, dst_trigger_id)
                if link_res.is_err:
                    return Err(link_res.unwrap_err())
            return Ok(True)
        except Exception as e:
            return Err(e)

    def _signature_from_target(self, tgt: TargetSpec) -> Tuple[Dict[str, Any], str]:
        
        if tgt.alias:
            # Si el alias ya incluye un punto, extraemos el método de ahí
            if "." in tgt.alias:
                alias, method = tgt.alias.rsplit(".", 1)
                sig = {"kind": "alias", "alias": f"{alias}.{method}", "method": method}
                s = f"alias:{alias}.{method}#{method}"
            else:
                # Si NO hay método explícito, no lo agregamos
                sig = {"kind": "alias", "alias": tgt.alias}
                s = f"alias:{tgt.alias}"
            return sig, s

        if tgt.bucket_id and tgt.key:
            sig = {"kind": "persisted", "bucket_id": tgt.bucket_id, "key": tgt.key}
            if tgt.method:
                sig["method"] = tgt.method
            s = f"persisted:{tgt.bucket_id}:{tgt.key}" + (f"#{tgt.method}" if tgt.method else "")
            return sig, s
        
        raise ValueError("Target inválido: falta alias o bucket/key")
    
    
    def _encode_parameters(self, params: ParametersSpec) -> Dict[str, Dict[str, Any]]:
        """Serializa ParametersSpec a un dict puro, ignorando bloques vacíos."""
        out: Dict[str, Dict[str, Any]] = {}

        if params.init:
            init_block = self._encode_param_block(params.init)
            if init_block:  # solo agregar si no está vacío
                out["init"] = init_block

        if params.call:
            call_block = self._encode_param_block(params.call)
            if call_block:  # solo agregar si no está vacío
                out["call"] = call_block

        return out

    def _encode_param_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa cada valor del bloque (literal o RefSpec) a dicts JSON-friendly."""
        encoded: Dict[str, Any] = {}
        for name, value in block.items():
            encoded[name] = self._encode_param_value(value)
        return encoded

    def _encode_param_value(self, value: Any) -> Any:
        """Convierte RefSpec → dict {'ref'/'$ref'...'value'...}, y deja literales tal cual.

        Nota: la issue solo exige validar que ref/$ref sean strings; no se resuelve existencia.
        """
        # Caso 1: RefSpec → serializar a dict limpio
        if isinstance(value, RefSpec):
            return value.model_dump(exclude_none=True, by_alias=True)

        # Caso 2: dict → limpiar None y devolver tal cual
        if isinstance(value, dict):
            return {k: v for k, v in value.items() if v is not None}

        # Caso 3: literal → envolver en {"value": ...}
        return {"value": value}
