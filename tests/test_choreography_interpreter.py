import pytest
from pathlib import Path
from shieldx_client import ShieldXClient


@pytest.mark.asyncio
async def test_interpret_choreography_real_yaml():
    """
    Prueba el intérprete usando un YAML real desde el disco.
    """
    # Ruta al YAML real
    yaml_path = Path(__file__).parent.parent / "triggers.yml"
    assert yaml_path.exists(), f"No se encontró el archivo {yaml_path}"

    client = ShieldXClient(base_url="http://localhost:20000/api/v1")

    result = await client.interpret_async(str(yaml_path))

    # Verificaciones básicas
    assert "event_types" in result
    assert "triggers" in result
    assert "rules" in result
    assert isinstance(result["links_count"], int)
