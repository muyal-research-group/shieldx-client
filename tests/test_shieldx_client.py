import pytest
from shieldx_client.client import ShieldXClient
from shieldx_client.models.event import EventModel
from shieldx_client.models.rule import RuleModel


BASE_URL = "http://localhost:20000/api/v1"

client = ShieldXClient(base_url=BASE_URL)

@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_event_type():
    event_type = await client.create_event_type("TestEventType")
    print(event_type)

@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_list_event_types():
    event_type = await client.list_event_types()
    assert event_type.is_ok
    # print(event_type)
    # assert event_type.event_type_id

    

@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_shieldx_client_end_to_end():

    # --- EventType ---
    event_type = await client.create_event_type("TestEventType")
    assert event_type.event_type_id

    event_type_list = await client.list_event_types()
    assert any(et.event_type == "TestEventType" for et in event_type_list)

    event_type_fetched = await client.get_event_type_by_id(event_type.event_type_id)
    assert event_type_fetched.event_type == "TestEventType"

    # --- Trigger ---
    trigger1 = await client.create_trigger("TriggerA")
    trigger2 = await client.create_trigger("TriggerB")
    assert trigger1["name"] == "TriggerA"

    trigger_by_name = await client.get_trigger_by_name("TriggerA")
    assert trigger_by_name["name"] == "TriggerA"

    all_triggers = await client.get_all_triggers()
    assert any(t["name"] == "TriggerA" for t in all_triggers)

    await client.update_trigger("TriggerA", {"name": "TriggerAUpdated"})
    updated = await client.get_trigger_by_name("TriggerAUpdated")
    assert updated["name"] == "TriggerAUpdated"

    # --- Rule ---
    rule_payload = RuleModel(
        target="mictlanx.get",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    rule = await client.create_rule(rule_payload)
    rule_fetched = await client.get_rule_by_id(rule.rule_id)
    assert rule_fetched.target == rule_payload.target

    # --- Link EventType ⇄ Trigger ---
    await client.link_trigger_to_event_type(event_type.event_type_id, trigger1["_id"])
    links = await client.list_triggers_for_event_type(event_type.event_type_id)
    assert any(link["trigger_id"] == trigger1["_id"] for link in links)

    await client.replace_triggers_for_event_type(event_type.event_type_id, [trigger2["_id"]])
    links_replaced = await client.list_triggers_for_event_type(event_type.event_type_id)
    assert all(link["trigger_id"] == trigger2["_id"] for link in links_replaced)

    await client.unlink_trigger_from_event_type(event_type.event_type_id, trigger2["_id"])

    # --- Link Trigger ⇄ Rule ---
    await client.link_rule_to_trigger(trigger1["_id"], rule.rule_id)
    rules_for_trigger = await client.list_rules_for_trigger(trigger1["_id"])
    assert any(r["rule_id"] == rule.rule_id for r in rules_for_trigger)

    new_rule = await client.create_and_link_rule(trigger1["_id"], rule_payload.model_dump(by_alias=True))
    await client.unlink_rule_from_trigger(trigger1["_id"], new_rule.rule_id)

    # --- Link Trigger ⇄ Trigger ---
    await client.link_trigger_child(trigger1["_id"], trigger2["_id"])
    children = await client.list_trigger_children(trigger1["_id"])
    assert any(c["trigger_child_id"] == trigger2["_id"] for c in children)

    parents = await client.list_trigger_parents(trigger2["_id"])
    assert any(p["trigger_parent_id"] == trigger1["_id"] for p in parents)

    await client.unlink_trigger_child(trigger1["_id"], trigger2["_id"])

    # --- Event ---
    await client.create_event_type("EventForEvents")
    event = EventModel(
        service_id="s1",
        microservice_id="m1",
        function_id="f1",
        event_type="EventForEvents",
        payload={"test": True}
    )
    created = await client.create_event(event)
    assert "event_id" in created or created  # si el backend devuelve el id

    all_events = await client.get_all_events()
    assert isinstance(all_events, list)

    await client.get_events_by_service("s1")
    await client.get_events_by_service_path("s1")
    await client.get_events_by_microservice("m1")
    await client.get_events_by_function("f1")


    await client.delete_trigger("TriggerAUpdated")
    await client.delete_trigger("TriggerB")
    await client.delete_event_type(event_type.event_type_id)
    await client.delete_rule(rule.rule_id)
