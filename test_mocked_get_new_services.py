""" uses mocked calls to test what happens when an unknown service type appears """

from copy import deepcopy
import json

import pytest
import requests_testing

from aussiebb import AussieBB
import aussiebb

from aussiebb.const import TEST_MOCKDATA, BASEURL

@requests_testing.activate
def test_handling_invalid_service():
    """ test  API endpoint, with mocking """

    invalid_service = deepcopy(TEST_MOCKDATA["service_voip"])
    invalid_service["service_id"] = 666
    invalid_service["type"] = "thisistotallybroken"

    testdata_invalid = {
        "data" : [
            TEST_MOCKDATA["service_voip"],
            invalid_service,
            TEST_MOCKDATA["service_nbn_fttc"],
        ]
    }


    # mock the login
    requests_testing.add(
        request = {
            'url': BASEURL["login"],
            "method" : "POST",
        },
        response = {
            'body': json.dumps({ "expiresIn" : 500 }),
            },
            calls_limit=3,
        )


    testapi = AussieBB(username="test", password="test")
    requests_testing.add(
        request = {
            'url': f"{BASEURL['api']}/services?page=1",
            "method" : "GET",
        },
        response = {
            'body': json.dumps(testdata_invalid),
            },
        calls_limit=1,
        )
    testapi.get_services()

    print(testapi.services)
    for service in testapi.services:
        print(f"testing type: {service['type']} id: {service['service_id']}")
        if service["type"] in aussiebb.const.PHONE_TYPES:
            requests_testing.add(
                request = {
                    'url': testapi.get_url("telephony_usage", {'service_id' : service["service_id"]}),
                    "method" : "GET",
                },
                response = {
                    'body': json.dumps(testdata_invalid),
                    },
                calls_limit=1,
                )
            testapi.get_usage(service["service_id"])
        elif service["type"] in aussiebb.const.NBN_TYPES:
            requests_testing.add(
                request = {
                    'url': testapi.get_url("get_usage", {'service_id' : service["service_id"]}),
                    "method" : "GET",
                },
                response = {
                    'body': json.dumps(testdata_invalid),
                    },
                calls_limit=1,
                )
            testapi.get_usage(service["service_id"])
        else:
            with pytest.raises(aussiebb.exceptions.UnrecognisedServiceType):
                testapi.get_usage(service["service_id"])
