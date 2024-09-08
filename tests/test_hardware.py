""" test the service with hardware"""

import json
import os
from pathlib import Path

from pydantic import SecretStr

from aussiebb.asyncio import AussieBB

from aussiebb.const import USAGE_ENABLED_SERVICE_TYPES

testfile = Path(
    os.path.join("/".join(__file__.split("/")[:-1]), "test_hardware.json")
).read_text(encoding="utf-8")
testjson = json.loads(testfile)


async def test_hardware() -> None:
    """test  parsing the hardware thing"""

    client = AussieBB(
        username="testuser",
        password=SecretStr("testpassword"),
        debug=True,
        services_cache_time=86400,
    )
    _, _, service_data = client.handle_services_response(testjson, [])
    client.services = service_data
    print(client.services)
    assert len(client.services) == 6

    filtered_services = client.filter_services(
        USAGE_ENABLED_SERVICE_TYPES, drop_unknown_types=True
    )
    print(filtered_services)
    assert len(filtered_services) == 5
