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
import os
from pathlib import Path
from typing import List

import pytest

from aussiebb import AussieBB
import aussiebb.const
from aussiebb.types import GetServicesResponse, AussieBBConfigFile


def configloader():
    """ loads config """
    for filename in [ os.path.expanduser("~/.config/aussiebb.json"), "aussiebb.json" ]:
        filepath = Path(filename).resolve()
        if filepath.exists():
            try:
                return AussieBBConfigFile.parse_file(filepath)
            except json.JSONDecodeError as json_error:
                pytest.exit(f"Failed to parse config file: {json_error}")

CONFIG = configloader()
if len(CONFIG.users) == 0:
    pytest.exit("You need some users in config.json")

@pytest.fixture(name="users", scope="session")
def userfactory():
    """ API factory """
    return [ AussieBB(username=user.username, password=user.password) for user in CONFIG.users ]

def test_login_cycle(users):
    """ test the login step """

    test_api = users[0]
    test_api.logger.info("Testing login")
    assert test_api.login()

    test_api.logger.debug("Checking if token has expired...")
    assert not test_api._has_token_expired() #pylint: disable=protected-access

def test_customer_details(users):
    """ test get_customer_details """
    for test_api in users:
        test_api.logger.info("Testing get_details")
        response = test_api.get_customer_details()
        assert response.get('customer_number', False)

def test_get_services(users: List[AussieBB]):
    """ test get_services """

    for test_api in users:
        test_api.logger.debug(test_api.get_services())
        services = test_api.get_services()
        assert services
        for service in services:
            test_api.validate_service_type(service)

def test_line_state(users):
    """ test test_line_state """
    for test_api in users:
        services = test_api.get_services()
        for service in services:
            if service['type'] in aussiebb.const.NBN_TYPES:
                assert test_api.test_line_state(service["service_id"]).get('id')
                return

def test_get_usage(users):
    """ test get_usage """
    for test_api in users:
        service_id = test_api.get_services()[0].get('service_id')
        assert test_api.get_usage(service_id).get('daysTotal')

def test_get_service_plans(users):
    """ tests the plan pulling for services """
    for test_api in users:
        test_services = [ service for service in test_api.get_services() if service.get('type') in aussiebb.const.NBN_TYPES ]
        if test_services:
            test_plans = test_api.service_plans(test_services[0].get('service_id'))
            assert test_plans
            for key in ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']:
                assert key in test_plans.keys()

def test_get_service_tests(users):
    """ tests... getting the tests for services. """
    for user in users:
        services = user.get_services()
        if services is None:
            pytest.skip("No services returned")
        test_service = None
        for service in services:
            if service["type"] in aussiebb.const.NBN_TYPES:
                test_service = service
                break

        if test_service is None:
            pytest.skip("Didn't find any NBN services")

        service_tests = user.get_service_tests(test_service["service_id"])
        print(service_tests)
        assert isinstance(service_tests, list)


def test_get_services_raw(users: List[AussieBB]):
    """ allows one to dump the full result of a get_services call """
    for user in users:
        url = user.get_url("get_services", { "page" : 1 })
        response : GetServicesResponse = user.request_get_json(url=url)
        print(json.dumps(response, indent=4))

        while "links" in response and "next" in response["links"] and response["links"]["next"]:
            print("Theres's another page!")
            url = response["links"]["next"]
            response = user.request_get_json(url=url)
            print(json.dumps(response, indent=4))
