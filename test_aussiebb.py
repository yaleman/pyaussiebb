#!/usr/bin/env python
""" test some things """

import os

import pytest

from aussiebb import AussieBB
import aussiebb.const

try:
    from config import USERNAME, PASSWORD
    from config import USERNAME2, PASSWORD2
except ImportError:
    USERNAME = os.environ.get('username', "")
    PASSWORD = os.environ.get('password', "")
    USERNAME2 = os.environ.get('username2', "")
    PASSWORD2 = os.environ.get('password2', "")

@pytest.fixture(name="test_api", scope="session")
def test_api_one():
    """ API factory """
    return AussieBB(username=USERNAME, password=PASSWORD)

@pytest.fixture(name="api2", scope="session")
def test_api_two():
    """ API factory """
    return AussieBB(username=USERNAME2, password=PASSWORD2)

TESTAPI = AussieBB(username=USERNAME, password=PASSWORD)
TESTAPI2 = AussieBB(username=USERNAME2, password=PASSWORD2)

def test_login_cycle(test_api):
    """ test the login step """
    test_api.logger.info("Testing login")
    assert test_api.login()

    test_api.logger.debug("Checking if token has expired...")
    assert not test_api._has_token_expired() #pylint: disable=protected-access

def test_customer_details(test_api):
    """ test get_customer_details """
    test_api.logger.info("Testing get_details")
    response = test_api.get_customer_details()
    assert response.get('customer_number', False)

def test_get_services(test_api, api2):
    """ test get_services """
    test_api.logger.debug(test_api.get_services())
    assert test_api.get_services()

    # api2 has a VOIP service
    voip_service = [service for service in api2.get_services() if service.get('type') == 'VOIP']
    assert voip_service

def test_line_state(test_api):
    """ test test_line_state """
    service_id = test_api.get_services()[0].get('service_id')
    assert test_api.test_line_state(service_id).get('id')

def test_get_usage(test_api):
    """ test get_usage """
    service_id = test_api.get_services()[0].get('service_id')
    assert test_api.get_usage(service_id).get('daysTotal')

def test_get_service_plans():
    """ tests the plan pulling for services """
    for test_username, test_password in [ [USERNAME, PASSWORD], [USERNAME2, PASSWORD2]]:
        test_api = AussieBB(test_username, test_password)
        test_services = [ service for service in test_api.get_services() if service.get('type') == 'NBN' ]
        if test_services:
            test_plans = test_api.service_plans(test_services[0].get('service_id'))
            assert test_plans
            for key in ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']:
                assert key in test_plans.keys()

def test_get_service_tests(test_api):
    """ blah """
    services = test_api.get_services()
    if services is None:
        pytest.skip("No services returned")
    test_service = None
    for service in services:
        if service["type"] in aussiebb.const.NBN_TYPES:
            test_service = service
            break

    if test_service is None:
        pytest.skip("Didn't find any NBN services")

    service_tests = test_api.get_service_tests(test_service["service_id"])
    print(service_tests)
    assert isinstance(service_tests, list)


def test_dump_services():
    """ dumps a list of services """
    for user_name, password_value in [ [USERNAME, PASSWORD], [USERNAME2, PASSWORD2]]:
        api = AussieBB(user_name, password_value)

        if api.get_services() is None:
            return

        services = [ service for service in api.get_services() if service.get('type') == 'NBN' ]
        for service in services:
            plans = api.service_plans(service.get('service_id'))

            for plan in plans.get('available'):
                if plan.get('download') >= 900:
                    api.logger.info(plan.get('name'))
                    api.logger.info("OVER 900!")

if __name__ == '__main__':
    test_dump_services()
