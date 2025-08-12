from __future__ import annotations
from typing import Any, Dict, List, Optional
import yaml
from pydantic import ValidationError
from option import Result, Ok, Err
from shieldx_client.choreography.schema import ChoreographySpec, TriggerSpec

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

            for trig in spec.triggers:
                # 1) EventTypes
                et_names = trig.event_types or [trig.name]
                et_ids: List[str] = []

                for et_name in et_names:
                    et_res = await self._get_or_create_event_type(et_name)
                    if et_res.is_err:
                        return Err(et_res.unwrap_err())
                    et_id = et_res.unwrap()
                    event_type_ids[et_name] = et_id
                    et_ids.append(et_id)

                # 2) Rule
                rule_res = await self._get_or_create_rule(trig)
                if rule_res.is_err:
                    return Err(rule_res.unwrap_err())
                rule_id = rule_res.unwrap()
                rule_ids[trig.rule.target] = rule_id

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
                for et_id in et_ids:
                    bind_et = await self._bind_event_trigger(event_type_id=et_id, trigger_id=trig_id)
                    if bind_et.is_err:
                        return Err(bind_et.unwrap_err())

            # 6) Links opcionales (Triggers ⇄ Triggers)
            for link in (spec.links or []):
                src = trigger_ids.get(link.from_trigger)
                dst = trigger_ids.get(link.to_trigger)
                if src and dst:
                    bind_tt = await self._bind_triggers_triggers(
                        src_trigger_id=src, dst_trigger_id=dst,
                        order=link.order, condition=link.condition
                    )
                    if bind_tt.is_err:
                        return Err(bind_tt.unwrap_err())

            return Ok({
                "event_types": event_type_ids,
                "triggers": trigger_ids,
                "rules": rule_ids,
                "links_count": len(spec.links or []),
            })
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

            created_res = await self.client.create_trigger_dict(trig.name)
            if created_res.is_err:
                return Err(created_res.unwrap_err())
            created = created_res.unwrap()
            return Ok(created["id"])
        except Exception as e:
            return Err(e)
            
    async def _get_or_create_rule(self, trig: TriggerSpec) -> Result[str, Exception]:
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
            target = trig.rule.target

            found_res = await self.client.find_rule_by_target_dict(target)
            if found_res.is_err:
                return Err(found_res.unwrap_err())
            found = found_res.unwrap()
            if found:
                return Ok(found["id"])

            allowed_types = {"string", "int", "float", "bool"}
            params: Dict[str, Dict[str, Any]] = {}
            for pname, pspec in (trig.rule.parameters or {}).items():
                if pspec.type not in allowed_types:
                    return Err(ValueError(f"Invalid parameter type '{pname}': '{pspec.type}'"))
                params[pname] = {"type": pspec.type, "description": pspec.description or ""}

            created_res = await self.client.create_rule_dict(target, params)
            if created_res.is_err:
                return Err(created_res.unwrap_err())
            created = created_res.unwrap()
            return Ok(created["id"])
        except Exception as e:
            return Err(e)

    async def _bind_rules_trigger(self, *, trigger_id: str, rule_id: str,
                                    priority: int = 0, condition: Optional[str] = None) -> Result[bool, Exception]:
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

    async def _bind_event_trigger(self, *, event_type_id: str, trigger_id: str,
                                    priority: int = 0, condition: Optional[str] = None) -> Result[bool, Exception]:
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
        
    async def _bind_triggers_triggers(self, *, src_trigger_id: str, dst_trigger_id: str,
                                        order: Optional[int], condition: Optional[str]) -> Result[bool, Exception]:
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