""" test some things """

import os

from loguru import logger
import pytest

from aussiebb import AussieBB

try:
    from config import username, password
except ImportError:
    username = os.environ.get('username')
    password = os.environ.get('password')

testapi = AussieBB(username=username, password=password)

def test_login_cycle(testapi=testapi):
    logger.info("Testing login")
    assert testapi.login()

    logger.debug("Checking if token has expired...")
    assert testapi.has_token_expired() == False

def test_customer_details(testapi=testapi):
    logger.info("Testing get_details")
    response = testapi.get_customer_details()
    assert response.get('customer_number', False)

def test_get_services(testapi=testapi):
    logger.debug(testapi.get_services())

def test_line_state(testapi=testapi):
    assert testapi.test_line_state(testapi.get_services()[0].get('service_id')).get('id')

if __name__ == '__main__':
    test_get_services()