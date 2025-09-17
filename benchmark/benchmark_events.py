import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import EventCreateDTO, EventUpdateDTO, EventTypeCreateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_events(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"create": 0, "list": 0, "update": 0, "delete": 0}
    _ =await client.create_event_type(EventTypeCreateDTO(event_type="EventForEvents"))

    for i in range(n):
        # -------- CREATE (único por iteración)
        event = EventCreateDTO(
            service_id=f"s{i}",
            microservice_id=f"m{i}",
            function_id=f"f{i}",
            event_type=f"EventForEvents",
            payload={"test": True}
        )

        cre = await client.create_event(event)
        if cre.is_err:
            errors["create"] += 1
            # print(f"[CREATE] {i} -> {cre.unwrap_err()}")
            continue
        event_id = cre.unwrap().id  # ID válido recién creado
        

        # -------- LIST (una vez por iteración)
        get_name  = await client.get_event_by_id(event_id=event_id)
        if get_name.is_err:
            errors["get"] += 1
            # print(f"[LIST] {i} -> {lst.unwrap_err()}")

        # -------- UPDATE (sobre el ID recién creado)
        event_update = EventUpdateDTO(
            service_id=f"s{i}-updated"
        )

        

        upd = await client.update_event(
            event_id,
            event_update
        )
        if upd.is_err:
            errors["update"] += 1
            # print(f"[UPDATE] {trigger_id} -> {upd.unwrap_err()}")

        current_name = event_id
        # -------- DELETE (el mismo ID, una vez)
        dele = await client.delete_event(current_name)
        if dele.is_err:
            errors["delete"] += 1
            # print(f"[DELETE] {trigger_id} -> {dele.unwrap_err()}")

    print(
        f"Resumen CRUD por iteración (n={n}) -> "
        f"create:{errors['create']} list:{errors['list']} "
        f"update:{errors['update']} delete:{errors['delete']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_events())