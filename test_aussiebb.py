#!/usr/bin/env python3
""" test some things """

import os
# import pytest
# import requests.exceptions
from loguru import logger

from aussiebb import AussieBB

try:
    from config import USERNAME, PASSWORD
    from config import USERNAME2, PASSWORD2
except ImportError:
    USERNAME = os.environ.get('username')
    PASSWORD = os.environ.get('password')
    USERNAME2 = os.environ.get('username2')
    PASSWORD2 = os.environ.get('password2')

TESTAPI = AussieBB(username=USERNAME, password=PASSWORD)
TESTAPI2 = AussieBB(username=USERNAME2, password=PASSWORD2)
def test_login_cycle(api_object=TESTAPI):
    """ test the login step """
    logger.info("Testing login")
    assert api_object.login()

    logger.debug("Checking if token has expired...")
    assert not api_object.has_token_expired()

def test_customer_details(test_api=TESTAPI):
    """ test get_customer_details """
    logger.info("Testing get_details")
    response = test_api.get_customer_details()
    assert response.get('customer_number', False)

def test_get_services(test_api=TESTAPI, api2=TESTAPI2):
    """ test get_services """
    logger.debug(test_api.get_services())
    assert test_api.get_services()

    # api2 has a VOIP service
    voip_service = [service for service in api2.get_services() if service.get('type') == 'VOIP']
    assert voip_service
#        with pytest.raises(requests.exceptions.HTTPError) as e_info:
#            logger.debug('Getting services tests for a VOIP Service...?')
#            logger.debug(api2.get_service_tests(VOIPservice[-1].get('service_id')))

def test_line_state(test_api=TESTAPI):
    """ test test_line_state """
    service_id = test_api.get_services()[0].get('service_id')
    assert test_api.test_line_state(service_id).get('id')

def test_get_usage(test_api=TESTAPI):
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

if __name__ == '__main__':
    for un, pw in [ [USERNAME, PASSWORD], [USERNAME2, PASSWORD2]]:
        api = AussieBB(un, pw)

        services = [ service for service in api.get_services() if service.get('type') == 'NBN' ]
        for service in services:
            plans = api.service_plans(service.get('service_id'))

            for plan in plans.get('available'):
                if plan.get('download') >= 900:
                    logger.info(plan.get('name'))
                    logger.info("OVER 900!")
