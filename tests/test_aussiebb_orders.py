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


@pytest.mark.network
def test_get_orders() -> None:
    """test the login step"""

    config = configloader()
    user = AussieBB(config.users[0].username, config.users[0].password)

    orders = user.get_orders()
    print(json.dumps(orders, indent=4, default=str, ensure_ascii=False))
    for order in orders["data"]:
        assert "id" in order
        print(f"Dumping order detail for {order['id']}")
        order_detail = user.get_order(order["id"])
        print(json.dumps(order_detail, indent=4, default=str, ensure_ascii=False))
        assert "id" in order_detail
