# benchmark/benchmark_triggers_triggers.py
import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import TriggerCreateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_triggers_triggers(n: int = 5000) -> None:
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"link": 0, "list_children": 0, "list_parents": 0, "unlink": 0}

    # --- Prepara recursos estáticos: 1 padre y 2 posibles hijos (para poder “mover” el vínculo si quieres) ---
    parent_res = await client.create_trigger(TriggerCreateDTO(name=f"TT-Parent-{uuid.uuid4()}"))
    if parent_res.is_err:
        raise RuntimeError(f"No se pudo crear trigger padre: {parent_res.unwrap_err()}")
    parent_id = parent_res.unwrap().id

    childA_res = await client.create_trigger(TriggerCreateDTO(name=f"TT-ChildA-{uuid.uuid4()}"))
    if childA_res.is_err:
        raise RuntimeError(f"No se pudo crear trigger hijo A: {childA_res.unwrap_err()}")
    childA_id = childA_res.unwrap().id

    childB_res = await client.create_trigger(TriggerCreateDTO(name=f"TT-ChildB-{uuid.uuid4()}"))
    if childB_res.is_err:
        raise RuntimeError(f"No se pudo crear trigger hijo B: {childB_res.unwrap_err()}")
    childB_id = childB_res.unwrap().id

    for i in range(n):
        # --- CLEAN (idempotente): inicia sin vínculos (ignora errores) ---
        _ = await client.unlink_trigger_child(parent_id=parent_id, child_id=childA_id)
        _ = await client.unlink_trigger_child(parent_id=parent_id, child_id=childB_id)

        # --- CREATE (link padre->hijoA) ---
        link_res = await client.link_trigger_child(parent_id=parent_id, child_id=childA_id)
        if link_res.is_err:
            errors["link"] += 1
            # print(f"[LINK] iter {i} -> {link_res.unwrap_err()}")
            continue  # sin vínculo no tiene sentido seguir la iteración

        # --- READ (lista hijos del padre) ---
        list_children_res = await client.list_trigger_children(parent_id=parent_id)
        if list_children_res.is_err:
            errors["list_children"] += 1
            # print(f"[LIST_CHILDREN] iter {i} -> {list_children_res.unwrap_err()}")

        # --- READ (lista padres del hijo) ---
        list_parents_res = await client.list_trigger_parents(child_id=childA_id)
        if list_parents_res.is_err:
            errors["list_parents"] += 1
            # print(f"[LIST_PARENTS] iter {i} -> {list_parents_res.unwrap_err()}")

        # --- DELETE (unlink padre->hijoA) ---
        unlink_res = await client.unlink_trigger_child(parent_id=parent_id, child_id=childA_id)
        if unlink_res.is_err:
            errors["unlink"] += 1
            # print(f"[UNLINK] iter {i} -> {unlink_res.unwrap_err()}")

    print(
        f"Resumen Trigger⇄Trigger (n={n}) -> "
        f"link:{errors['link']} list_children:{errors['list_children']} "
        f"list_parents:{errors['list_parents']} unlink:{errors['unlink']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_triggers_triggers())
