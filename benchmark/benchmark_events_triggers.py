import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import EventTypeCreateDTO, TriggerCreateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_event_triggers(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"link": 0, "list": 0, "replace": 0, "unlink": 0}

    # ---- Prepara recursos estáticos para el benchmark ----
    # EventType único y dos triggers fijos para mover la relación
    et_res = await client.create_event_type(EventTypeCreateDTO(event_type=f"ET-Bench-{uuid.uuid4()}"))
    if et_res.is_err:
        raise RuntimeError(f"No se pudo crear EventType inicial: {et_res.unwrap_err()}")
    event_type_id = et_res.unwrap().id

    tA_res = await client.create_trigger(TriggerCreateDTO(name=f"TrigA-{uuid.uuid4()}"))
    if tA_res.is_err:
        raise RuntimeError(f"No se pudo crear Trigger A: {tA_res.unwrap_err()}")
    triggerA_id = tA_res.unwrap().id

    tB_res = await client.create_trigger(TriggerCreateDTO(name=f"TrigB-{uuid.uuid4()}"))
    if tB_res.is_err:
        raise RuntimeError(f"No se pudo crear Trigger B: {tB_res.unwrap_err()}")
    triggerB_id = tB_res.unwrap().id

    for i in range(n):
        # --- CLEAN (idempotente): asegúrate de empezar sin vínculos ---
        _ = await client.unlink_trigger_from_event_type(event_type_id=event_type_id, trigger_id=triggerA_id)
        _ = await client.unlink_trigger_from_event_type(event_type_id=event_type_id, trigger_id=triggerB_id)

        # --- CREATE (link) ---
        link_res = await client.link_trigger_to_event_type(event_type_id=event_type_id, trigger_id=triggerA_id)
        if link_res.is_err:
            errors["link"] += 1
            # print(f"[LINK] iter {i} -> {link_res.unwrap_err()}")
            continue  # sin link, no seguimos con el ciclo

        # --- READ (list) ---
        list_res = await client.list_triggers_for_event_type(event_type_id=event_type_id)
        if list_res.is_err:
            errors["list"] += 1
            # print(f"[LIST] iter {i} -> {list_res.unwrap_err()}")

        # --- UPDATE (replace) ---
        # IMPORTANTE: replace espera una lista de IDs
        replace_res = await client.replace_triggers_for_event_type(
            event_type_id=event_type_id,
            trigger_ids=[triggerB_id]            # <--- lista, no string suelto
        )
        if replace_res.is_err:
            errors["replace"] += 1
            # print(f"[REPLACE] iter {i} -> {replace_res.unwrap_err()}")

        # --- DELETE (unlink) ---
        unlink_res = await client.unlink_trigger_from_event_type(event_type_id=event_type_id, trigger_id=triggerB_id)
        if unlink_res.is_err:
            errors["unlink"] += 1
            # print(f"[UNLINK] iter {i} -> {unlink_res.unwrap_err()}")

    print(
        f"Resumen n={n} -> "
        f"link:{errors['link']} list:{errors['list']} replace:{errors['replace']} unlink:{errors['unlink']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_event_triggers())