from __future__ import annotations
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
"""Pydantic models for the choreography YAML.

Models:
- ParameterSpec: describes each Rule parameter.
- RuleRef: Rule target and its parameters.
- TriggerSpec: trigger with a name and a Rule; can bind to multiple EventTypes.
- LinkSpec: parent→child trigger chaining.
- ChoreographySpec: YAML root with basic validation.
"""

ParamType = Literal["string", "int", "float", "bool", "json"]  # 'json' lo mapeamos si quieres permitirlo

"""Allowed parameter types for a Rule.

Note:
    If your backend does not support native `json`, map it to `string` in the interpreter.
"""

class ParameterSpec(BaseModel):
    """Rule parameter specification.

    Attributes:
        type: Parameter type (see `ParamType`).
        description: Optional description.
        required: Whether the parameter is required (default: True).
        default: Optional default value.
    """
    type: ParamType
    description: Optional[str] = None
    required: bool = True
    default: Optional[object] = None

class RuleRef(BaseModel):
    """Reference to a Rule: target + parameters.

    Attributes:
        target: Target function/action identifier.
        parameters: Mapping of parameter name to `ParameterSpec`.
    """
    target: str
    parameters: Dict[str, ParameterSpec] = Field(default_factory=dict)

class TriggerSpec(BaseModel):
    """Trigger definition.

    Attributes:
        name: Trigger name.
        rule: Rule to execute when the trigger fires.
        event_types: Optional list of Event Type names to bind; if empty, `name` is used.
    """
    name: str
    rule: RuleRef
    # M:N con EventTypes (si no lo pones, se usa name como event_type)
    event_types: List[str] = Field(default_factory=list)

class LinkSpec(BaseModel):
    """Trigger-to-trigger chaining.

    Attributes:
        from_trigger: Source trigger name (YAML alias: `from`).
        to_trigger: Destination trigger name (YAML alias: `to`).
        order: Optional execution order.
        condition: Optional condition expression.
    """
    from_trigger: str = Field(alias="from")
    to_trigger: str = Field(alias="to")
    order: Optional[int] = None
    condition: Optional[str] = None

class ChoreographySpec(BaseModel):
    """Choreography root schema.

    Attributes:
        policy_id: Optional policy identifier.
        version: Optional choreography version.
        triggers: List of triggers (required; must not be empty).
        links: Optional trigger chaining definitions.
    """
    policy_id: Optional[str] = None
    version: Optional[str] = None
    triggers: List[TriggerSpec]
    links: List[LinkSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _non_empty_triggers(self) -> "ChoreographySpec":
        if not self.triggers:
            raise ValueError("La coreografía debe contener al menos un trigger.")
        return self
