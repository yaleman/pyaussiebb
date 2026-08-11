"""test some things"""

import json

import pytest

import aussiebb.const
from aussiebb.asyncio import AussieBB

# from aussiebb.exceptions import InvalidTestForService
from aussiebb.types import ConfigUser

from .test_utils import configloader, users  # noqa: F401

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture(name="config_users")
def fixture_users() -> list[ConfigUser]:
    """users fixture"""
    config = configloader()
    if config is None:
        return []
    result: list[ConfigUser] = config.users
    return result


@pytest.mark.network
async def test_login_cycle(users: list[AussieBB]) -> None:  # noqa: F811
    """test the login step"""
    for api in users:
        # login = await api.login()
        # assert login
        api.logger.debug("Checking if token has expired...")
        assert not api._has_token_expired()  # pylint: disable=protected-access


@pytest.mark.network
async def test_get_customer_details(users: list[AussieBB]) -> None:  # noqa: F811
    """test get_customer_details"""

    for config_user in users:
        config_user.logger.info("Testing get_details")
        response = await config_user.get_customer_details()
        assert response.get("customer_number", False)


@pytest.mark.network
async def test_get_services(users: list[AussieBB]) -> None:  # noqa: F811
    """test get_services"""

    for config_user in users:
        services = await config_user.get_services()
        config_user.logger.debug("Dumping services for api1")
        print(json.dumps(services, indent=4, default=str))
        assert services


# can't run this because it's throwing errors for some reason
# @pytest.mark.network
# async def test_line_state(users: list[AussieBB]) -> None:
#     """test test_line_state"""
#     for user in users:
#         async with aiohttp.ClientSession() as session:
#             api = AussieBB(
#                 username=user.username,
#                 password=user.password,
#                 debug=True,
#                 session=session,
#             )

#             services = await api.get_services()
#             for service in services:
#                 if service["type"] in aussiebb.const.NBN_TYPES:
#                     service_id = service["service_id"]
#                     print(f"Got service ID: {service_id}")
#                     print(f"Service:\n{service}")
#                     try:
#                         line_state = await api.test_line_state(service_id)
#                         assert line_state.get("id")
#                         break
#                     except InvalidTestForService as error:
#                         print(error)


@pytest.mark.network
async def test_get_usage(users: list[AussieBB]) -> None:  # noqa: F811
    """test get_usage"""
    for api_user in users:
        services = await api_user.get_services()
        service_id = int(services[0]["service_id"])

        usage = await api_user.get_usage(service_id)
        assert usage.get("daysTotal")


@pytest.mark.network
async def test_get_service_tests(users: list[AussieBB]) -> None:  # noqa: F811
    """test the get_service_tests function and its return type"""

    for test_api in users:
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


@pytest.mark.network
async def test_get_referral_code(users: list[AussieBB]) -> None:  # noqa: F811
    """tests the referral code func"""
    for api in users:
        refcode = await api.referral_code
        assert isinstance(refcode, int)


@pytest.mark.network
async def test_get_account_contacts(users: list[AussieBB]) -> None:  # noqa: F811
    """tests the account_contacts function"""
    for api in users:
        contacts = await api.account_contacts()
        print(contacts)
        assert len(contacts) > 0


@pytest.mark.network
async def test_get_voip_devices(users: list[AussieBB]) -> None:  # noqa: F811
    """finds voip services and returns the devices"""
    for api in users:
        services = await api.get_services()
        if services is None:
            print(f"no services for user {api}")
            continue

        for service in services:
            if service["type"] not in aussiebb.const.PHONE_TYPES:
                continue
            print(f"Found a voip service! {service['service_id']}")

            service_devices = await api.get_voip_devices(service_id=int(service["service_id"]))
            print(json.dumps(service_devices, indent=4, default=str))


@pytest.mark.network
async def test_get_voip_service(users: list[AussieBB]) -> None:  # noqa: F811
    """finds voip services and returns the specific info endpoint"""
    for api in users:
        services = await api.get_services()
        if not services:
            print(f"no services for user {api}")
            continue

        for service in services:
            if service["type"] not in aussiebb.const.PHONE_TYPES:
                continue
            print(f"Found a voip service! {service['service_id']}")

            service_devices = await api.get_voip_service(service_id=int(service["service_id"]))
            print(json.dumps(service_devices, indent=4, default=str))
