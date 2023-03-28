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
from typing import List
import sys

import pytest

from aussiebb import AussieBB
from aussiebb.types import AussieBBConfigFile, AussieBBOutage

from test_utils import configloader

config: AussieBBConfigFile = configloader()


if len(config.users) == 0:
    sys.exit("You need some users in config.json")


@pytest.fixture(name="users", scope="session")
def userfactory_sync(config_object : AussieBBConfigFile=config) -> List[AussieBB]:
    """ API factory """
    return [ AussieBB(username=user.username, password=user.password) for user in config_object.users ]

def test_login_cycle(users: List[AussieBB], indent: int=4) -> None:
    """ test the login step """

    user: AussieBB = users[0]

    services = user.get_services()
    if services is None:
        pytest.skip("No services found")
    for service in services:
        outages = user.service_outages(service["service_id"])
        print(json.dumps(outages, indent=indent, default=str, ensure_ascii=False))
        AussieBBOutage.parse_obj(outages)


if __name__ == "__main__":
    test_login_cycle([ AussieBB(username=user.username, password=user.password) for user in config.users ], indent=0)
