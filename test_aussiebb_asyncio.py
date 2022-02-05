#!/usr/bin/env python3
""" test some things """

import aiohttp
import pytest


from aussiebb.asyncio import AussieBB
import aussiebb.const
from test_aussiebb import configloader

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

CONFIG = configloader()
if len(CONFIG.users) == 0:
    pytest.exit("You need some users in config.json")

async def test_login_cycle(users=CONFIG.users):
    """ test the login step """
    for user in users:
        async with aiohttp.ClientSession() as session:
            api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            login = await api.login()
            assert login

            api.logger.debug("Checking if token has expired...")
            assert not api._has_token_expired() #pylint: disable=protected-access


async def test_get_customer_details(users=CONFIG.users):
    """ test get_customer_details """

    for user in users:
        async with aiohttp.ClientSession() as session:
            api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            api.logger.info("Testing get_details")
            response = await api.get_customer_details()
            assert response.get('customer_number', False)

async def test_get_services(users=CONFIG.users):
    """ test get_services """

    for user in users:
        async with aiohttp.ClientSession() as session:
            api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            services = await api.get_services()
            api.logger.debug("Dumping services for api1")
            api.logger.debug(services)
            assert services

async def test_line_state(users=CONFIG.users):
    """ test test_line_state """
    for user in users:
        async with aiohttp.ClientSession() as session:
            api = AussieBB(username=user.username, password=user.password, debug=True, session=session)

            services = await api.get_services()
            service_id = services[0].get('service_id')

            print(f"Got service ID: {service_id}")
            line_state = await api.test_line_state(service_id)
            assert line_state.get('id')


async def test_get_usage(users=CONFIG.users):
    """ test get_usage """
    for user in users:
        async with aiohttp.ClientSession() as session:
            api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            services = await api.get_services()
            service_id = services[0].get('service_id')

            usage = await api.get_usage(service_id)
            assert usage.get('daysTotal')


async def test_get_service_tests(users=CONFIG.users):
    """ test the get_service_tests function and its return type """

    for user in users:
        async with aiohttp.ClientSession() as session:
            test_api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            services = await test_api.get_services()
            if services is None:
                pytest.skip("No services returned")
            test_service = None
            for service in services:
                if service["type"] in aussiebb.const.NBN_TYPES:
                    test_service = service
                    break

            if test_service is None:
                pytest.skip("Didn't find any NBN services")

            service_tests = await test_api.get_service_tests(test_service["service_id"])
            print(service_tests)
            assert isinstance(service_tests, list)


async def test_get_service_plans(users=CONFIG.users):
    """ tests the plan pulling for services """

    for user in users:
        async with aiohttp.ClientSession() as session:
            test_api = AussieBB(username=user.username, password=user.password, debug=True, session=session)
            result = await test_api.get_services()

            test_services = [ service for service in result if service.get('type') == 'NBN' ]

            if test_services:
                test_plans = await test_api.service_plans(test_services[0].get('service_id'))
                assert test_plans
                for key in ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']:
                    assert key in test_plans.keys()
