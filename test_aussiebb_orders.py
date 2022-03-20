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
from aussiebb.types import AussieBBConfigFile

from test_utils import configloader

config: AussieBBConfigFile = configloader()


if len(config.users) == 0:
    sys.exit("You need some users in config.json")


@pytest.fixture(name="users", scope="session")
def userfactory_sync(config_object : AussieBBConfigFile = config) -> List[AussieBB]:
    """ API factory """
    return [ AussieBB(username=user.username, password=user.password) for user in config_object.users ]

def test_get_orders(users: List[AussieBB], indent: int=4) -> None:
    """ test the login step """

    user: AussieBB = users[1]
    orders = user.get_orders()
    print(json.dumps(orders, indent=indent, default=str, ensure_ascii=False))
    for order in orders["data"]:
        assert "id" in order
        print(f"Dumping order detail for {order['id']}")
        order_detail = user.get_order(order["id"])
        print(json.dumps(order_detail, indent=indent, default=str, ensure_ascii=False))
        assert "id" in order_detail

if __name__ == "__main__":
    test_get_orders([ AussieBB(username=user.username, password=user.password) for user in config.users ], indent=0)
