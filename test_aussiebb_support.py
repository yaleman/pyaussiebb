#!/usr/bin/env python3
""" test some things """

import os
# import pytest
# import requests.exceptions
from loguru import logger

from aussiebb import AussieBB

try:
    from config import USERNAME, PASSWORD

except ImportError:
    USERNAME = os.environ.get('username')
    PASSWORD = os.environ.get('password')


TESTAPI = AussieBB(username=USERNAME, password=PASSWORD)

def test_support_tickets(api_object=TESTAPI):
    """ test the support tickets thing """
    logger.info("Testing login")
    assert api_object.login()

    tickets = api_object.support_tickets()

    for ticket in tickets:
        logger.info(ticket)

def test_get_appointment(api_object=TESTAPI):
    """ test the support tickets thing """
    logger.info("Testing login")
    assert api_object.login()

    data = api_object.get_appointment(123)

    logger.info(data)
