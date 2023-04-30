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

from typing import List

import pytest
from test_utils import configloader

from aussiebb import AussieBB
import aussiebb.const
from aussiebb.exceptions import InvalidTestForService
from aussiebb.types import GetServicesResponse


@pytest.mark.network
@pytest.fixture(name="users", scope="session")
def userfactory() -> List[AussieBB]:
    """API factory"""
    return [
        AussieBB(username=user.username, password=user.password)
        for user in configloader().users
    ]


@pytest.mark.network
def test_login_cycle(users: List[AussieBB]) -> None:
    """test the login step"""

    test_api = users[0]
    test_api.logger.info("Testing login")
    assert test_api.login()

    test_api.logger.debug("Checking if token has expired...")
    assert not test_api._has_token_expired()  # pylint: disable=protected-access


@pytest.mark.network
def test_customer_details(users: List[AussieBB]) -> None:
    """test get_customer_details"""
    for test_api in users:
        test_api.logger.info("Testing get_details")
        response = test_api.get_customer_details()
        assert response.get("customer_number", False)
        print(json.dumps(response, indent=4, default=str))


@pytest.mark.network
def test_get_services(users: List[AussieBB]) -> None:
    """test get_services"""

    for test_api in users:
        test_api.logger.debug(test_api.get_services())
        services = test_api.get_services()
        assert services
        for service in services:
            test_api.validate_service_type(service)


@pytest.mark.network
def test_line_state(users: List[AussieBB]) -> None:
    """test test_line_state"""
    for test_api in users:
        services = test_api.get_services()
        if services is None:
            pytest.skip("No services returned")
        for service in services:
            if service["type"] in aussiebb.const.NBN_TYPES:
                print(service)

                try:
                    result = test_api.test_line_state(int(service["service_id"]))
                    print(result)
                    assert result.get("id")
                    break
                except InvalidTestForService as error_message:
                    print(error_message)


@pytest.mark.network
def test_get_usage(users: List[AussieBB]) -> None:
    """test get_usage"""
    for test_api in users:
        services = test_api.get_services()

        if services is None:
            pytest.skip("No services returned")

        service_id = int(services[0].get("service_id", "-1"))
        assert test_api.get_usage(service_id).get("daysTotal")


@pytest.mark.network
def test_get_service_tests(users: List[AussieBB]) -> None:
    """tests... getting the tests for services."""
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


@pytest.mark.network
def test_get_services_raw(users: List[AussieBB]) -> None:
    """allows one to dump the full result of a get_services call"""
    for user in users:
        url = user.get_url("get_services", {"page": 1})
        response = GetServicesResponse.parse_obj(user.request_get_json(url=url))
        print(json.dumps(response.links, indent=4, default=str))
        print(json.dumps(response.data, indent=4, default=str))

        while hasattr(response, "links") and (response.links.next is not None):
            print("Theres's another page!")
            url = response.links.next
            response = GetServicesResponse.parse_obj(user.request_get_json(url=url))
            print(json.dumps(response.links, indent=4, default=str))


@pytest.mark.network
def test_get_referral_code(users: List[AussieBB]) -> None:
    """tests the referral code func"""
    for user in users:
        assert isinstance(user.referral_code, int)


@pytest.mark.network
def test_account_contacts(users: List[AussieBB]) -> None:
    """tests the referral code func"""
    for user in users:
        contacts = user.account_contacts()
        print(contacts)
        assert len(contacts) > 0


@pytest.mark.network
def test_get_voip_devices(users: List[AussieBB]) -> None:
    """finds voip services and returns the devices"""
    for user in users:
        services = user.get_services()
        if services is None:
            print(f"no services for user {user}")
            continue

        for service in services:
            if service["type"] not in aussiebb.const.PHONE_TYPES:
                continue
            print(f"Found a voip service! {service['service_id']}")

            service_devices = user.get_voip_devices(
                service_id=int(service["service_id"])
            )
            print(json.dumps(service_devices, indent=4, default=str))


@pytest.mark.network
def test_get_voip_service(users: List[AussieBB]) -> None:
    """finds voip services and returns the specific info endpoint"""
    for user in users:
        services = user.get_services()
        if services is None:
            print(f"no services for user {user}")
            continue

        for service in services:
            if service["type"] not in aussiebb.const.PHONE_TYPES:
                continue
            print(f"Found a voip service! {service['service_id']}")

            service_devices = user.get_voip_service(
                service_id=int(service["service_id"])
            )
            print(json.dumps(service_devices, indent=4, default=str))
