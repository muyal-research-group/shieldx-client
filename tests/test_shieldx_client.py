from uuid import uuid4
import pytest
from shieldx_client.client import ShieldXClient
from shieldx_client.models.event import EventModel
from shieldx_client.models.rule import RuleModel
from shieldx_client.models.trigger import TriggerModel
from shieldx_client.models.event_type import EventTypeModel
from shieldx_core.dtos import TriggerDTO, IDResponseDTO



BASE_URL = "http://localhost:20000/api/v1"

client = ShieldXClient(base_url=BASE_URL)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_event_type():
    event_type = await client.create_event_type("TestEventType")
    print(event_type)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_list_event_types():
    event_type = await client.list_event_types()
    assert event_type.is_ok

    # print(event_type)
    # assert event_type.event_type_id

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_event_type_by_id():
    creation_result = await client.create_event_type("TestEventType")
    
    assert creation_result.is_ok
    created_event_type = creation_result.unwrap()

    # ✅ Usa el atributo correcto `id`
    fetch_result = await client.get_event_type_by_id(created_event_type.id)
    assert fetch_result.is_ok
    fetched_event_type = fetch_result.unwrap()

    # Validaciones
    assert fetched_event_type.event_type == "TestEventType"
    assert fetched_event_type.event_type_id == created_event_type.id

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_delete_event_type():
    # Crear un tipo de evento para eliminar
    creation_result = await client.create_event_type("EventToDelete")
    assert creation_result.is_ok
    created_event = creation_result.unwrap()
    event_type_id = created_event.id

    # Eliminar el tipo de evento
    deletion_result = await client.delete_event_type(event_type_id)
    assert deletion_result.is_ok

    # Verificar que ya no existe
    fetch_result = await client.get_event_type_by_id(event_type_id)
    assert fetch_result.is_err  # Debería fallar porque ya fue eliminado

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_Event():
    await client.create_event_type("EventForEvents")
    event = EventModel(
        service_id="s1",
        microservice_id="m1",
        function_id="f1",
        event_type="EventForEvents",
        payload={"test": True}
    )
    created = await client.create_event(event)
    assert created.is_ok
    dto = created.unwrap()
    assert dto.message == "Evento creado exitosamente"
    assert dto.event_id is not None

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_all_Events():
    all_events = await client.get_all_events()
    assert all_events.is_ok

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_events_by_service():
    result = await client.get_events_by_service("s1")
    assert result.is_ok
    assert isinstance(result.unwrap(), list)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_events_by_service_pat():
    result =await client.get_events_by_service_path("s1")
    assert result.is_ok
    assert isinstance(result.unwrap(), list)

@pytest.mark.asyncio
async def test_get_events_by_microservice():
    result =await client.get_events_by_microservice("m1")
    assert result.is_ok
    assert isinstance(result.unwrap(), list)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_events_by_function():
    result =await client.get_events_by_function("f1")
    assert result.is_ok
    assert isinstance(result.unwrap(), list)

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_update_event():
    await client.create_event_type("EventForUpdate")
    # Crear evento inicial
    event = EventModel(
        service_id="s1",
        microservice_id="m1",
        function_id="f1",
        event_type="EventForUpdate",
        payload={"old_key": "old_value"}
    )
    creation_result = await client.create_event(event)
    assert creation_result.is_ok

    # Extraer el ID del evento recién creado
    created = creation_result.unwrap()
    event_id = created.event_id  # <- Aquí NO necesitas uuid4()

    # Paso 3: Actualizar el evento
    update_data = {"payload": {"new_key": "new_value"}}
    update_result = await client.update_event(event_id, update_data)
    assert update_result.is_ok
    updated = update_result.unwrap()
    assert updated.payload == {"new_key": "new_value"}

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_delete_event():
    # Crear evento inicial
    event = EventModel(
        service_id="s1",
        microservice_id="m1",
        function_id="f1",
        event_type="EventForEvents",
        payload={"test": True}
    )
    creation_result = await client.create_event(event)
    assert creation_result.is_ok
    created_event = creation_result.unwrap()


    # Eliminar evento
    delete_result = await client.delete_event(created_event.event_id)
    assert delete_result.is_ok

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_rule():
    rule = RuleModel(
        target="mictlanx.get",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    result = await client.create_rule(rule)
    print(result)
    assert result.is_ok

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_rule_by_id():
    rule = RuleModel(
        target="mictlanx.get",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    created = await client.create_rule(rule)
    assert created.is_ok
    rule_id = created.unwrap()

    result = await client.get_rule_by_id(rule_id.id)
    assert result.is_ok
    fetched = result.unwrap()
    assert fetched.rule_id == rule_id.id
    assert fetched.target == "mictlanx.get"

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
    rule = RuleModel(
        target="original_function",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    created = await client.create_rule(rule)
    print(created)
    assert created.is_ok
    rule_id = created.unwrap()
    rule_id = rule_id.id
    updated_rule = RuleModel(
        target="updated_function",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    update_result = await client.update_rule(rule_id, updated_rule)
    assert update_result.is_ok
    msg = update_result.unwrap()
    assert msg.message == "Rule updated"
    
#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_delete_rule():
    rule = RuleModel(
        target="to_be_deleted",
        parameters={
            "x": {"type": "bool", "description": "to be removed"}
        }
    )
    created = await client.create_rule(rule)
    assert created.is_ok
    rule_id = created.unwrap()

    result = await client.delete_rule(rule_id.id)
    assert result.is_ok
    assert result.unwrap() is True


#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_create_trigger():
    trigger = TriggerModel(
        name="test_trigger_create",
        rule=RuleModel(
            target="mictlanx.get",
            parameters={
                "bucket_id": {"type": "string", "description": "ID del bucket"},
                "key": {"type": "string", "description": "Llave"},
                "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )
    )
    result = await client.create_trigger(trigger)
    print(result)
    assert result.is_ok

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_get_trigger_by_name():
    name = "test_trigger_get"
    trigger = TriggerModel(
        name=name,
        rule=RuleModel(
            target="mictlanx.get",
            parameters={
                "bucket_id": {"type": "string", "description": "ID del bucket"},
                "key": {"type": "string", "description": "Llave"},
                "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )
    )
    created = await client.create_trigger(trigger)
    assert created.is_ok

    result = await client.get_trigger_by_name(name)
    assert result.is_ok
    fetched = result.unwrap()
    assert fetched.name == name
    

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_list_triggers():
    result = await client.get_all_triggers()
    assert result.is_ok


#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_update_trigger():
    name = "test_trigger_update"
    trigger = TriggerModel(
        name=name,
        rule=RuleModel(
            target="original_function",
            parameters={
                "bucket_id": {"type": "string", "description": "ID del bucket"},
                "key": {"type": "string", "description": "Llave"},
                "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )
    )
    created = await client.create_trigger(trigger)
    assert created.is_ok

    updated_trigger = TriggerModel(
        name=name,
        rule=RuleModel(
            target="updated_function",
            parameters={
                "bucket_id": {"type": "string", "description": "ID del bucket"},
                "key": {"type": "string", "description": "Llave"},
                "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )
    )
    update_result = await client.update_trigger(name, updated_trigger)
    assert update_result.is_ok
    updated = update_result.unwrap()
    

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_delete_trigger():
    name = "test_trigger_delete"
    trigger = TriggerModel(
        name=name,
        rule=RuleModel(
            target="to_be_deleted",
            parameters={
                "x": {"type": "bool", "description": "to be removed"}
            }
        )
    )
    created = await client.create_trigger(trigger)
    assert created.is_ok

    result = await client.delete_trigger(name)
    assert result.is_ok
    assert result.unwrap() is True

#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_link_trigger_to_event_type():
    event_type_id = f"event_type_id-{uuid4()}"
    trigger_id = f"trigger_id-{uuid4()}"

    event_type_result = await client.create_event_type(event_type=event_type_id)
    trigger_result = await client.create_trigger(TriggerModel(name=trigger_id))

    assert event_type_result.is_ok
    assert trigger_result.is_ok

    # Parche temporal si hay doble Ok
    event_type_dto = event_type_result.unwrap()
    trigger_dto = trigger_result.unwrap().unwrap()

    assert isinstance(event_type_dto, IDResponseDTO)
    assert isinstance(trigger_dto, TriggerDTO)

    event_type_id = event_type_dto.id
    trigger_id = trigger_dto.trigger_id

    link_result = await client.link_trigger_to_event_type(event_type_id, trigger_id)
    assert link_result.is_ok

        
    children_result = await client.list_triggers_for_event_type(event_type_id)
    assert children_result.is_ok
    children = children_result.unwrap()

    children_result = await client.replace_triggers_for_event_type(event_type_id, [trigger_id])
    assert children_result.is_ok
    # Verificar padres del child
    parents_result = await client.unlink_trigger_from_event_type(event_type_id, trigger_id)
    assert parents_result.is_ok
    parents = parents_result.unwrap()
    
    

@pytest.mark.asyncio
async def test_link_rule_to_trigger():
    rule = RuleModel(
        target="mictlanx.get",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
        }
    )
    trigger_id = f"trigger_id-{uuid4()}"

    rule_result = await client.create_rule(rule)
    trigger_result = await client.create_trigger(TriggerModel(name=trigger_id))

    assert rule_result.is_ok
    assert trigger_result.is_ok

    # Parche temporal si hay doble Ok
    rule_dto = rule_result.unwrap()
    trigger_dto = trigger_result.unwrap().unwrap()

    assert isinstance(rule_dto, IDResponseDTO)
    assert isinstance(trigger_dto, TriggerDTO)

    rule_id = rule_dto.id
    trigger_id = trigger_dto.trigger_id

    link_result = await client.link_rule_to_trigger(trigger_id, rule_id)
    assert link_result.is_ok

        
    list_result = await client.list_rules_for_trigger(trigger_id)
    assert list_result.is_ok
    list_result = list_result.unwrap()

    create_and_link_result = await client.create_and_link_rule(trigger_id, rule)
    assert create_and_link_result.is_ok
    # Verificar padres del child
    unlink_result = await client.unlink_rule_from_trigger(trigger_id, rule_id )
    assert unlink_result.is_ok
    parents = unlink_result.unwrap()
    


#@pytest.mark.skip("")
@pytest.mark.asyncio
async def test_link_and_unlink_triggers():
    parent_name = f"ParentTrigger-{uuid4()}"
    child_name = f"ChildTrigger-{uuid4()}"

    parent_result = await client.create_trigger(TriggerModel(name=parent_name))
    child_result = await client.create_trigger(TriggerModel(name=child_name))

    assert parent_result.is_ok
    assert child_result.is_ok

    # Parche temporal si hay doble Ok
    parent_dto = parent_result.unwrap().unwrap()
    child_dto = child_result.unwrap().unwrap()

    assert isinstance(parent_dto, TriggerDTO)
    assert isinstance(child_dto, TriggerDTO)

    parent_id = parent_dto.trigger_id
    child_id = child_dto.trigger_id

    link_result = await client.link_trigger_child(parent_id, child_id)
    assert link_result.is_ok

        # Verificar hijos del parent
    children_result = await client.list_trigger_children(child_id)
    assert children_result.is_ok
    children = children_result.unwrap()

    # Verificar padres del child
    parents_result = await client.list_trigger_parents(parent_id)
    assert parents_result.is_ok
    parents = parents_result.unwrap()
    
    unlink_result = await client.unlink_trigger_child(parent_id, child_id)
    assert unlink_result.is_ok
