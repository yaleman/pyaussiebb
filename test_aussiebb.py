#!/usr/bin/env python3
""" test some things """

import os

from loguru import logger

from aussiebb import AussieBB

try:
    from config import username, password
except ImportError:
    username = os.environ.get('username')
    password = os.environ.get('password')

TESTAPI = AussieBB(username=username, password=password)

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

def test_get_services(api=TESTAPI):
    """ test get_services """
    logger.debug(api.get_services())

def test_line_state(api=TESTAPI):
    """ test test_line_state """
    serviceid = api.get_services()[0].get('service_id')
    assert api.test_line_state(serviceid).get('id')

def test_get_usage(api=TESTAPI):
    """ test get_usage """
    serviceid = api.get_services()[0].get('service_id')
    assert api.get_usage(serviceid).get('daysTotal')

if __name__ == '__main__':
    test_get_usage()
