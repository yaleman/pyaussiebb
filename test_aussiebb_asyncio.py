#!/usr/bin/env python3
""" test some things """

import os
import sys
import pytest
from loguru import logger
from aussiebb.asyncio import AussieBB

try:
    import aiohttp #pylint: disable=unused-import
except ImportError as error_message:
    print(f"Failed to import aiohttp: {error_message}")
    sys.exit(1)

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

try:
    from config import USERNAME, PASSWORD
    from config import USERNAME2, PASSWORD2
except ImportError:
    USERNAME = os.environ.get('username')
    PASSWORD = os.environ.get('password')
    USERNAME2 = os.environ.get('username2')
    PASSWORD2 = os.environ.get('password2')


async def test_login_cycle():
    """ test the login step """

    logger.info("Testing login")

    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)
        login = await api.login()
        assert login

        logger.debug("Checking if token has expired...")
        assert not api._has_token_expired() #pylint: disable=protected-access


async def test_get_customer_details():
    """ test get_customer_details """

    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)
        logger.info("Testing get_details")
        response = await api.get_customer_details()
        assert response.get('customer_number', False)

async def test_get_services():
    """ test get_services """

    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)

        api2 = AussieBB(username=USERNAME2, password=PASSWORD2, debug=True, session=session)

        services = await api.get_services()
        logger.debug("Dumping services for api1")
        logger.debug(services)
        assert services

        # api2 has a VOIP service
        services2 = await api2.get_services()
        logger.debug("Dumping VOIP services for api2")
        voip_service = [service for service in services2 if service.get('type') == 'VOIP']
        assert voip_service

async def test_line_state():
    """ test test_line_state """
    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)

        services = await api.get_services()
        service_id = services[0].get('service_id')

        print(f"Got service ID: {service_id}")
        line_state = await api.test_line_state(service_id)
        assert line_state.get('id')


async def test_get_usage():
    """ test get_usage """

    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)
        services = await api.get_services()
        service_id = services[0].get('service_id')

        usage = await api.get_usage(service_id)
        assert usage.get('daysTotal')


async def test_get_service_plans():
    """ tests the plan pulling for services """

    async with aiohttp.ClientSession() as session:
        api = AussieBB(username=USERNAME, password=PASSWORD, debug=True, session=session)
        api2 = AussieBB(username=USERNAME2, password=PASSWORD2, debug=True, session=session)

        for test_api in [api, api2]:

            result = await test_api.get_services()

            test_services = [ service for service in result if service.get('type') == 'NBN' ]

            if test_services:
                test_plans = await test_api.service_plans(test_services[0].get('service_id'))
                assert test_plans
                for key in ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']:
                    assert key in test_plans.keys()
