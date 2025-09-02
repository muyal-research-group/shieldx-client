import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import RuleCreateDTO, RuleUpdateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_rule(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"create": 0, "list": 0, "update": 0, "delete": 0}

    for i in range(n):
        # -------- CREATE (único por iteración)
        rule = RuleCreateDTO(
        target= f"mictlanx.get-{i}",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )

        cre = await client.create_rule(rule=rule)
        if cre.is_err:
            errors["create"] += 1
            # print(f"[CREATE] {i} -> {cre.unwrap_err()}")
            continue
        rule_id = cre.unwrap().id 

        # -------- LIST (una vez por iteración)
        get_name  = await client.get_rule_by_id(rule_id=rule_id)
        if get_name.is_err:
            errors["list"] += 1
            # print(f"[LIST] {i} -> {lst.unwrap_err()}")

        # -------- UPDATE (sobre el ID recién creado)
        updated_rule = RuleUpdateDTO(
        target="updated_function",
        parameters={
            "bucket_id": {"type": "string", "description": "ID del bucket"},
            "key": {"type": "string", "description": "Llave"},
            "sink_path": {"type": "string", "description": "Ruta destino"}
            }
        )
        current_id = rule_id

        upd = await client.update_rule(
            current_id,
            updated_rule
        )
        if upd.is_err:
            errors["update"] += 1
            # print(f"[UPDATE] {trigger_id} -> {upd.unwrap_err()}")

        # -------- DELETE (el mismo ID, una vez)
        dele = await client.delete_rule(current_id)
        if dele.is_err:
            errors["delete"] += 1
            # print(f"[DELETE] {trigger_id} -> {dele.unwrap_err()}")

    print(
        f"Resumen CRUD por iteración (n={n}) -> "
        f"create:{errors['create']} list:{errors['list']} "
        f"update:{errors['update']} delete:{errors['delete']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_rule())