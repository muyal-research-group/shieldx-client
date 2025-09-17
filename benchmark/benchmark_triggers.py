import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import TriggerCreateDTO, TriggerUpdateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_triggers(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"create": 0, "list": 0, "update": 0, "delete": 0}

    for i in range(n):
        # -------- CREATE (único por iteración)
        name = f"TriggerBench-{i}-{uuid.uuid4()}"  # evita 409 por duplicado
        cre = await client.create_trigger(TriggerCreateDTO(name=name))
        if cre.is_err:
            errors["create"] += 1
            # print(f"[CREATE] {i} -> {cre.unwrap_err()}")
            continue
        current_name = name
        

        # -------- LIST (una vez por iteración)
        get_name  = await client.get_trigger_by_name(name=name)
        if get_name.is_err:
            errors["list"] += 1
            # print(f"[LIST] {i} -> {lst.unwrap_err()}")

        # -------- UPDATE (sobre el ID recién creado)
        new_name = f"{current_name}-updated"

        upd = await client.update_trigger(
            current_name,
            TriggerUpdateDTO(name=new_name)
        )
        if upd.is_err:
            errors["update"] += 1
            # print(f"[UPDATE] {trigger_id} -> {upd.unwrap_err()}")

        current_name = new_name
        # -------- DELETE (el mismo ID, una vez)
        dele = await client.delete_trigger(current_name)
        if dele.is_err:
            errors["delete"] += 1
            # print(f"[DELETE] {trigger_id} -> {dele.unwrap_err()}")

    print(
        f"Resumen CRUD por iteración (n={n}) -> "
        f"create:{errors['create']} list:{errors['list']} "
        f"update:{errors['update']} delete:{errors['delete']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_triggers())