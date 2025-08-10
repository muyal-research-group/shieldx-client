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

    assert result.is_ok, f"interpret_async() falló: {result.unwrap_err()}"
    # Verificaciones básicas
    data = result.unwrap()
    assert "event_types" in data
    assert "triggers" in data
    assert "rules" in data
    assert isinstance(data["links_count"], int)