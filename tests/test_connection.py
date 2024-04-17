import pytest
from tokka import Client


@pytest.mark.asyncio(scope="session")
async def test_client_fixture(client: Client) -> None:
    ping_response = await client.motor.admin.command("ping")
    assert ping_response["ok"] != 0.0
