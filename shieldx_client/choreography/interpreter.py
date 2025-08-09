from __future__ import annotations
from typing import Any, Dict, List, Optional
import yaml
from pydantic import ValidationError

from .schema import ChoreographySpec, TriggerSpec

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
    async def index_from_text(self, choreography_yaml: str) -> Dict[str, Any]:
        """Parse YAML and apply the choreography.

        Args:
            choreography_yaml: YAML string.

        Returns:
            Dict with name→ID mappings and the `links_count`.
        """
        spec = self._parse_spec(choreography_yaml)
        return await self._index_entities(spec)

    # -------- Internos --------
    def _parse_spec(self, choreography_yaml: str) -> ChoreographySpec:
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
            return ChoreographySpec.model_validate(raw)
        except ValidationError as ve:
            raise ValueError(f"Coreografía inválida: {ve}") from ve

    async def _index_entities(self, spec: ChoreographySpec) -> Dict[str, Any]:
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
        event_type_ids: Dict[str, str] = {}
        trigger_ids: Dict[str, str] = {}
        rule_ids: Dict[str, str] = {}

        for trig in spec.triggers:
            # 1) EventTypes (si no vienen, usa el nombre del trigger)
            et_names = trig.event_types or [trig.name]
            et_ids: List[str] = []
            for et_name in et_names:
                et_id = await self._get_or_create_event_type(et_name)
                event_type_ids[et_name] = et_id
                et_ids.append(et_id)

            # 2) Rule
            rule_id = await self._get_or_create_rule(trig)
            rule_ids[trig.rule.target] = rule_id

            # 3) Trigger
            trig_id = await self._get_or_create_trigger(trig)
            trigger_ids[trig.name] = trig_id

            # 4) Vincular Trigger ⇄ Rule
            await self._bind_rules_trigger(trigger_id=trig_id, rule_id=rule_id)

            # 5) Vincular EventType ⇄ Trigger
            for et_id in et_ids:
                await self._bind_event_trigger(event_type_id=et_id, trigger_id=trig_id)

        # 6) Links opcionales (Triggers ⇄ Triggers)
        for link in spec.links:
            src = trigger_ids.get(link.from_trigger)
            dst = trigger_ids.get(link.to_trigger)
            if src and dst:
                await self._bind_triggers_triggers(
                    src_trigger_id=src, dst_trigger_id=dst,
                    order=link.order, condition=link.condition
                )

        return {
            "event_types": event_type_ids,
            "triggers": trigger_ids,
            "rules": rule_ids,
            "links_count": len(spec.links),
        }

    # -------- Helpers (usando SOLO campos definidos) --------
    async def _get_or_create_event_type(self, event_type_name: str) -> str:
        """Get or create an Event Type and return its ID.

        Args:
            event_type_name: Event Type name.

        Returns:
            Event Type ID.
        """
        found = await self.client.find_event_type_by_name_dict(event_type_name)
        if found:
            return found["id"]
        created = await self.client.create_event_type_dict(event_type_name)
        return created["id"]

    async def _get_or_create_trigger(self, trig: TriggerSpec) -> str:
        """Get or create a Trigger and return its ID.

        Args:
            trig: `TriggerSpec` with name (and its rule).

        Returns:
            Trigger ID.
        """
        found = await self.client.find_trigger_by_name_dict(trig.name)
        if found:
            return found["id"]
        created = await self.client.create_trigger_dict(trig.name)
        return created["id"]

    async def _get_or_create_rule(self, trig: TriggerSpec) -> str:
        """Get or create a Rule and return its ID.

        Validates that parameter types are allowed.

        Args:
            trig: `TriggerSpec` that contains `rule` and its `parameters`.

        Returns:
            Rule ID.

        Raises:
            ValueError: If any parameter has a disallowed `type`.
        """
        target = trig.rule.target
        found = await self.client.find_rule_by_target_dict(target)
        if found:
            return found["id"]

        # Mapeo limpio: solo 'type' y 'description' (compatibles con tu RuleModel.ParameterDetailModel)
        params: Dict[str, Dict[str, Any]] = {}
        for pname, pspec in trig.rule.parameters.items():
            # Validar tipo permitido por tu servidor
            if pspec.type not in {"string", "int", "float", "bool"}:
                # Si quieres permitir 'json' en tu YAML, aquí lo podrías mapear a 'string' o lanzar error:
                # pspec.type = "string"
                raise ValueError(f"Tipo no válido para parámetro '{pname}': '{pspec.type}'")
            params[pname] = {
                "type": pspec.type,
                "description": pspec.description or "",
            }

        created = await self.client.create_rule_dict(target, params)
        return created["id"]

    async def _bind_rules_trigger(self, *, trigger_id: str, rule_id: str,
                                    priority: int = 0, condition: Optional[str] = None) -> None:
        """Ensure the Trigger⇄Rule relation (idempotent).

        Args:
            trigger_id: Trigger ID.
            rule_id: Rule ID.
            priority: Reserved (not used).
            condition: Reserved (not used).
        """
        bound = await self.client.is_rule_bound_to_trigger_bool(trigger_id, rule_id)
        if not bound:
            await self.client.bind_rule_to_trigger_dict(trigger_id, rule_id)

    async def _bind_event_trigger(self, *, event_type_id: str, trigger_id: str,
                                    priority: int = 0, condition: Optional[str] = None) -> None:
        """Ensure the EventType⇄Trigger relation (idempotent).

        Args:
            event_type_id: Event Type ID.
            trigger_id: Trigger ID.
            priority: Reserved (not used).
            condition: Reserved (not used).
        """
        bound = await self.client.is_trigger_bound_to_event_type_bool(event_type_id, trigger_id)
        if not bound:
            await self.client.bind_event_type_to_trigger_dict(event_type_id, trigger_id)

    async def _bind_triggers_triggers(self, *, src_trigger_id: str, dst_trigger_id: str,
                                        order: Optional[int], condition: Optional[str]) -> None:
        """Ensure the Parent⇄Child Trigger relation (idempotent).

        Args:
            src_trigger_id: Source Trigger ID (parent).
            dst_trigger_id: Destination Trigger ID (child).
            order: Optional execution order.
            condition: Optional chaining condition.
        """
        bound = await self.client.is_trigger_linked_to_trigger_bool(src_trigger_id, dst_trigger_id)
        if not bound:
            await self.client.bind_trigger_to_trigger_dict(src_trigger_id, dst_trigger_id)
