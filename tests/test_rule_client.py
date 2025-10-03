from uuid import uuid4
import pytest
from shieldx_client.client import ShieldXClient
from shieldx_core.dtos import (TriggerCreateDTO, MessageWithIDDTO, EventTypeCreateDTO, EventCreateDTO, 
                                RuleCreateDTO, RuleUpdateDTO, TriggerUpdateDTO, EventUpdateDTO)

BASE_URL = "http://localhost:20000/api/v1"

client = ShieldXClient(base_url=BASE_URL)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_rule():
    rule = RuleCreateDTO(
                        target={
                            "alias": "bellmanford_v1test1.run"
                        },
                        parameters={
                            "init":{  
                                "graph":{
                                        "type": "DiGraph",
                                        "name": "graph",
                                        "description": "Grafo dirigido almacenado en MictlanX",
                                        "ref": "mictlanx://graphs_bucket@graph_k1/0/?content_type=application/octet-stream"
                                },
                                "other_init_param": {"value": "A"},
                            },
                            "call":{  
                                "source": {"value": "A"},
                                "target":{
                                    "$ref": "mictlanx://params_bucket@target_label/0/?content_type=text/plain",
                                    "type": "str",
                                    "name": "target",
                                    "description": "Nodo destino",
                                    "value": "Z"
                                },
                            }
                        }
    )
    result = await client.create_rule(rule)
    print(result)
    assert result.is_ok

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_rule_by_id():
    rule = RuleCreateDTO(
                        target={
                            "alias": "bellmanford_v1test1.run"
                        },
                        parameters={
                            "init":{  
                                "graph":{
                                        "type": "DiGraph",
                                        "name": "graph",
                                        "description": "Grafo dirigido almacenado en MictlanX",
                                        "ref": "mictlanx://graphs_bucket@graph_k1/0/?content_type=application/octet-stream"
                                },
                                "other_init_param": {"value": "A"},
                            },
                            "call":{  
                                "source": {"value": "A"},
                                "target":{
                                    "$ref": "mictlanx://params_bucket@target_label/0/?content_type=text/plain",
                                    "type": "str",
                                    "name": "target",
                                    "description": "Nodo destino",
                                    "value": "Z"
                                },
                            }
                        }
    )
    created = await client.create_rule(rule)
    assert created.is_ok
    rule_id = created.unwrap()

    result = await client.get_rule_by_id(rule_id.id)
    assert result.is_ok
    fetched = result.unwrap()
    assert fetched.rule_id == rule_id.id
    assert fetched.target.alias == "bellmanford_v1test1.run"

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_list_rules():
    result = await client.list_rules()
    assert result.is_ok
    rules = result.unwrap()
    assert isinstance(rules, list)
    
#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_update_rule():
    rule = RuleCreateDTO(
                        target={
                            "alias": "bellmanford_v1test1original.run"
                        },
                        parameters={
                            "init":{  
                                "graph":{
                                        "type": "DiGraph",
                                        "name": "graph",
                                        "description": "Grafo dirigido almacenado en MictlanX",
                                        "ref": "mictlanx://graphs_bucket@graph_k1/0/?content_type=application/octet-stream"
                                },
                                "other_init_param": {"value": "A"},
                            },
                            "call":{  
                                "source": {"value": "A"},
                                "target":{
                                    "$ref": "mictlanx://params_bucket@target_label/0/?content_type=text/plain",
                                    "type": "str",
                                    "name": "target",
                                    "description": "Nodo destino",
                                    "value": "Z"
                                },
                            }
                        }
    )
    created = await client.create_rule(rule)
    print(created)
    assert created.is_ok
    rule_id = created.unwrap()
    rule_id = rule_id.id
    updated_rule = RuleCreateDTO(
                        target={
                            "alias": "bellmanford_v1test1Update.run"
                        },
                        parameters={
                            "init":{  
                                "graph":{
                                        "type": "DiGraph",
                                        "name": "graph",
                                        "description": "Grafo dirigido almacenado en MictlanX",
                                        "ref": "mictlanx://graphs_bucket@graph_k1/0/?content_type=application/octet-stream"
                                },
                                "other_init_param": {"value": "A"},
                            },
                            "call":{  
                                "source": {"value": "A"},
                                "target":{
                                    "$ref": "mictlanx://params_bucket@target_label/0/?content_type=text/plain",
                                    "type": "str",
                                    "name": "target",
                                    "description": "Nodo destino",
                                    "value": "Z"
                                },
                            }
                        }
    )
    update_result = await client.update_rule(rule_id, updated_rule)
    assert update_result.is_ok
    msg = update_result.unwrap()
    assert msg.message == "Rule updated"
    
#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_delete_rule():
    rule = RuleCreateDTO(
                        target={
                            "alias": "bellmanford_v1test1Update.run"
                        },
                        parameters={
                            "init":{  
                                "graph":{
                                        "type": "DiGraph",
                                        "name": "graph",
                                        "description": "Grafo dirigido almacenado en MictlanX",
                                        "ref": "mictlanx://graphs_bucket@graph_k1/0/?content_type=application/octet-stream"
                                },
                                "other_init_param": {"value": "A"},
                            },
                            "call":{  
                                "source": {"value": "A"},
                                "target":{
                                    "$ref": "mictlanx://params_bucket@target_label/0/?content_type=text/plain",
                                    "type": "str",
                                    "name": "target",
                                    "description": "Nodo destino",
                                    "value": "Z"
                                },
                            }
                        }
    )
    created = await client.create_rule(rule)
    assert created.is_ok
    rule_id = created.unwrap()

    result = await client.delete_rule(rule_id.id)
    assert result.is_ok
    assert result.unwrap() is True


@pytest.mark.asyncio
async def test_create_trigger():
    trigger = TriggerCreateDTO(
        name=f"test_trigger_create-{uuid4()}",
        depends_on="BellmanFordtest"
    )
    result = await client.create_trigger(trigger)
    print(result)
    assert result.is_ok
