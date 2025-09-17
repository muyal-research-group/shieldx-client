import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import EventTypeCreateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_event_type(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"create": 0, "list": 0, "update": 0, "delete": 0}

    for i in range(n):
        # -------- CREATE (único por iteración)
        name = f"EventTypeBench-{i}-{uuid.uuid4()}"
        event_type = EventTypeCreateDTO(
            event_type= name
        )

        cre = await client.create_event_type(event_type)
        if cre.is_err:
            errors["create"] += 1
            # print(f"[CREATE] {i} -> {cre.unwrap_err()}")
            continue

        event_type_id = cre.unwrap().id  # ID válido recién creado

        # -------- LIST (una vez por iteración)
        get_name  = await client.get_event_type_by_id(event_type_id=event_type_id)
        if get_name.is_err:
            errors["get"] += 1
            # print(f"[LIST] {i} -> {lst.unwrap_err()}")

        current_id = event_type_id
        # -------- DELETE (el mismo ID, una vez)
        dele = await client.delete_event_type(event_type_id=current_id)
        if dele.is_err:
            errors["delete"] += 1
            # print(f"[DELETE] {trigger_id} -> {dele.unwrap_err()}")

    print(
        f"Resumen CRUD por iteración (n={n}) -> "
        f"create:{errors['create']} list:{errors['list']} "
        f"delete:{errors['delete']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_event_type())