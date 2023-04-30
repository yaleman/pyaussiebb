""" tests some fetch-service-related things """

import json
import pytest
from aussiebb import types


@pytest.mark.network
def test_fetch_service_parser() -> None:
    """tests parsing an example service"""

    fetch_service = json.loads(
        """
     {
      "service_id": 332780,
      "type": "FETCHTV",
      "name": "Fetch Tv",
      "plan": "Fetch Starter Pack",
      "description": "UN 1, 28 XXXXXXXX ST, XXXXXXXX QLD",
      "nextBillDate": "2022-04-16T14:00:00Z",
      "openDate": "2018-12-19T13:00:00Z",
      "usageAnniversary": 17,
      "address": {
        "subaddresstype": "UN",
        "subaddressnumber": "1",
        "streetnumber": "28",
        "streetname": "XXXXXXXX",
        "streettype": "ST",
        "locality": "XXXXXXXX",
        "postcode": "4020",
        "state": "QLD"
      },
      "contract": null,
      "discounts": []
    }"""
    )

    test_parse = types.FetchService.parse_obj(fetch_service)
    assert test_parse.service_id


@pytest.mark.network
def test_fetch_service_details() -> None:
    """tests details"""
    fetch_service = json.loads(
        """{
    "id": 332780,
    "maxOutstandingCents": 10000,
    "currentAvailableSpendCents": 0,
    "transactions": [],
    "subscriptions": {
        "": [
        {
            "name": "Fetch Lite",
            "description": "",
            "costCents": 0,
            "startDate": "2018-12-10T10:52:27Z",
            "endDate": null
        }
        ],
        "Premium Channels": [
        {
            "name": "Knowledge",
            "description": "Knowledge brings you compelling factual storytelling, news and adventure from around the world, plus inspirational ideas for your home.",
            "costCents": 600,
            "startDate": "2020-02-17T07:43:10Z",
            "endDate": null
        },
        {
            "name": "Vibe",
            "description": "Feel the buzz with great sports, music, comedy, reality and more. Vibe is the place for the latest games, shows, songs, looks and laughs.",
            "costCents": 600,
            "startDate": "2020-02-17T07:43:32Z",
            "endDate": null
        }
        ]
    }
    }"""
    )

    assert types.FetchDetails.parse_obj(fetch_service)
