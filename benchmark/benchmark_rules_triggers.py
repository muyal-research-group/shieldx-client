# 📄 benchmark_rules_triggers.py
import asyncio
import uuid
from shieldx_client import ShieldXClient
from shieldx_core.dtos import RuleCreateDTO, TriggerCreateDTO

BASE_URL = "http://localhost:20000/api/v1"

async def run_benchmark_rules_triggers(n=5000):
    client = ShieldXClient(base_url=BASE_URL)
    errors = {"create": 0, "list": 0, "link": 0, "unlink": 0}

    # ⚡ Preparar un Trigger inicial
    trigger_name = f"TriggerForRules-{uuid.uuid4()}"
    trigger_name = TriggerCreateDTO(name=trigger_name)
    trigger_res = await client.create_trigger(trigger= trigger_name)
    if trigger_res.is_err:
        print(f"No se pudo crear el trigger inicial: {trigger_res.unwrap_err()}")
        return
    trigger_id = trigger_res.unwrap().id

    for i in range(n):
        # -------- CREATE RULE + LINK (único por iteración)
        rule_name = f"RuleBench-{i}-{uuid.uuid4()}"
        rule_dto = RuleCreateDTO(
            target= f"mictlanx.get-{i}",
            parameters={
                "bucket_id": {"type": "string", "description": "ID del bucket"},
                "key": {"type": "string", "description": "Llave"},
                "sink_path": {"type": "string", "description": "Ruta destino"}
                }
        )

        cre = await client.create_and_link_rule(trigger_id=trigger_id, rule_payload=rule_dto)
        if cre.is_err:
            errors["create"] += 1
            continue
        rule_id = cre.unwrap().id  # ID válido recién creado

        # -------- LIST (una vez por iteración)
        lst = await client.list_rules_for_trigger(trigger_id=trigger_id)
        if lst.is_err:
            errors["list"] += 1

        # -------- LINK (vincular explícitamente, si aplica)
        lnk = await client.link_rule_to_trigger(trigger_id=trigger_id, rule_id=rule_id)
        if lnk.is_err:
            errors["link"] += 1

        # -------- UNLINK (el mismo ID, una vez)
        unl = await client.unlink_rule_from_trigger(trigger_id=trigger_id, rule_id=rule_id)
        if unl.is_err:
            errors["unlink"] += 1

    print(
        f"Resumen Rules⇄Triggers (n={n}) -> "
        f"create:{errors['create']} list:{errors['list']} "
        f"link:{errors['link']} unlink:{errors['unlink']}"
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark_rules_triggers())
