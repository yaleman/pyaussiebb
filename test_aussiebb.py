#!/usr/bin/env python3
""" test some things """

import os
import pytest
import requests.exceptions
from loguru import logger

from aussiebb import AussieBB

try:
    from config import username, password
    from config import username2, password2
except ImportError:
    username = os.environ.get('username')
    password = os.environ.get('password')
    username2 = os.environ.get('username2')
    password2 = os.environ.get('password2')

TESTAPI = AussieBB(username=username, password=password)
TESTAPI2 = AussieBB(username=username2, password=password2)
def test_login_cycle(api=TESTAPI):
    """ test the login step """
    logger.info("Testing login")
    assert api.login()

    logger.debug("Checking if token has expired...")
    assert not api.has_token_expired()

def test_customer_details(api=TESTAPI):
    """ test get_customer_details """
    logger.info("Testing get_details")
    response = api.get_customer_details()
    assert response.get('customer_number', False)

def test_get_services(api=TESTAPI, api2=TESTAPI2):
    """ test get_services """
    logger.debug(api.get_services())
    assert api.get_services()

    # api2 has a VOIP service
    VOIPservice = [service for service in api2.get_services() if service.get('type') == 'VOIP']
    assert VOIPservice
#        with pytest.raises(requests.exceptions.HTTPError) as e_info:
#            logger.debug('Getting services tests for a VOIP Service...?')
#            logger.debug(api2.get_service_tests(VOIPservice[-1].get('service_id')))

def test_line_state(api=TESTAPI):
    """ test test_line_state """
    serviceid = api.get_services()[0].get('service_id')
    assert api.test_line_state(serviceid).get('id')

def test_get_usage(api=TESTAPI):
    """ test get_usage """
    serviceid = api.get_services()[0].get('service_id')
    assert api.get_usage(serviceid).get('daysTotal')

def test_get_service_plans():
    for un, pw in [ [username, password], [username2, password2]]:
        api = AussieBB(un, pw)
        services = [ service for service in api.get_services() if service.get('type') == 'NBN' ]
        if services:
            plans = api.get_service_plans(services[0].get('service_id'))
            assert plans
            for key in ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']:
                assert key in plans.keys()

if __name__ == '__main__':
    for un, pw in [ [username, password], [username2, password2]]:
        api = AussieBB(un, pw)

        services = [ service for service in api.get_services() if service.get('type') == 'NBN' ]
        for service in services:
            plans = api.get_service_plans(service.get('service_id'))

            for plan in plans.get('available'):
                if plan.get('download') >= 900:
                    logger.info(plan.get('name'))
                    logger.info("OVER 900!")
