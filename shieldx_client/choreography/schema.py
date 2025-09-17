from __future__ import annotations
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, model_validator
"""Pydantic models for the choreography YAML.

Models:
- ParameterSpec: describes each Rule parameter.
- RuleRef: Rule target and its parameters.
- TriggerSpec: trigger with a name and a Rule; can bind to multiple EventTypes.
- LinkSpec: parent→child trigger chaining.
- ChoreographySpec: YAML root with basic validation.
"""


"""Allowed parameter types for a Rule.

Note:
    If your backend does not support native `json`, map it to `string` in the interpreter.
"""

class RefSpec(BaseModel):
    """
    A parameter value that can either be:
        - a literal `value`, OR
        - an external reference via `ref` or `$ref` (string-validated, existence not required here).
    Optional metadata fields are accepted for DX (type/name/description).
    """
    ref: Optional[str] = None
    ref_dollar: Optional[str] = Field(default=None, alias="$ref")

    value: Optional[Any] = None

    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def _require_ref_or_value(self) -> "RefSpec":
        effective_ref = self.ref or self.ref_dollar
        if effective_ref is None and self.value is None:
            raise ValueError("RefSpec requires either 'ref'/'$ref' or 'value'.")
        if effective_ref is not None and not isinstance(effective_ref, str):
            raise ValueError("'ref'/'$ref' must be a string.")
        return self

ParamValue = Union[RefSpec, Any]  # Each parameter can be a RefSpec or a plain literal


# ----------------
# Parameters (init/call)
# ----------------

class ParametersSpec(BaseModel):
    """
    Split parameters:
        - init: kwargs passed to the class constructor (__init__)
        - call: kwargs passed to the selected method (default: 'run')
    At least one of {init, call} must be present.
    """
    init: Optional[Dict[str, ParamValue]] = None
    call: Optional[Dict[str, ParamValue]] = None

    @model_validator(mode="after")
    def _at_least_one_block(self) -> "ParametersSpec":
        if not (self.init or self.call):
            raise ValueError("Provide at least one of 'parameters.init' or 'parameters.call'.")
        return self

class TargetSpec(BaseModel):
    """
    Identify the invocation target:
        - alias: "artifact_or_class.method"
            (Runner should resolve class + method; method default 'run' if not present in alias)
        - OR a persisted object:
            bucket_id + key (+ method, default 'run')
    """
    alias: Optional[str] = None
    bucket_id: Optional[str] = None
    key: Optional[str] = None
    method: Optional[str] = None

    @model_validator(mode="after")
    def _require_alias_or_bucket_key(self) -> "TargetSpec":
        has_alias = bool(self.alias)
        has_bucket_key = bool(self.bucket_id and self.key)
        if not has_alias and not has_bucket_key:
            raise ValueError("TargetSpec requires 'alias' OR ('bucket_id' and 'key').")
        return self


class RuleSpec(BaseModel):
    """Reference to a Rule: target + parameters.
    Attributes:
        target: Target function/action identifier.
        parameters: Mapping of parameter name to `ParameterSpec`.
    """
    target: TargetSpec
    parameters: ParametersSpec

class TriggerSpec(BaseModel):
    """Trigger definition.

    Attributes:
        name: Trigger name.
        rule: Rule to execute when the trigger fires.
        event_types: Optional list of Event Type names to bind; if empty, `name` is used.
    """
    name: str
    depends_on: Optional[str] = None
    rule: RuleSpec
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
