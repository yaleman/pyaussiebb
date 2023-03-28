"""
Using this

You really need a file called "aussiebb.json" in either the local dir or ~/.config/.

It needs at least one user in the "users" field. eg:

{
    "users" : [
        { "username" : "mickeymouse.123", "password" : "hunter2" }
    ]
}
"""

import json

import pytest
from test_utils import configloader

from aussiebb import AussieBB
from aussiebb.types import AussieBBOutage

@pytest.mark.network
def test_login_cycle() -> None:
    """ test the login step """

    user: AussieBB = [ AussieBB(username=user.username, password=user.password) for user in configloader().users ][0]

    services = user.get_services()
    if services is None:
        pytest.skip("No services found")
    for service in services:
        outages = user.service_outages(service["service_id"])
        print(json.dumps(outages, indent=4, default=str, ensure_ascii=False))
        AussieBBOutage.parse_obj(outages)
