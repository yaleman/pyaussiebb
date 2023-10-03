""" A class for interacting with Aussie Broadband APIs """

# import json
import sys
from time import time
from typing import Any, Dict, List, Optional, cast
from pydantic import SecretStr

import requests
import requests.sessions

from .baseclass import BaseClass
from .const import BASEURL, default_headers, PHONE_TYPES
from .exceptions import RecursiveDepth
from .types import (
    FetchService,
    MFAMethod,
    ServiceTest,
    AccountContact,
    AccountTransaction,
    AussieBBOutage,
    OrderResponse,
    OrderDetailResponse,
    OrderDetailResponseModel,
    VOIPDevice,
    VOIPDetails,
)


class AussieBB(BaseClass):
    """A class for interacting with Aussie Broadband APIs"""

    def __init__(
        self,
        username: str,
        password: SecretStr,
        debug: bool = False,
        services_cache_time: int = 28800,
        session: Optional[requests.sessions.Session] = None,
    ):
        """Setup function

        ```
        @param username: str - username for Aussie Broadband account
        @param password: str - password for Aussie Broadband account
        @param debug: bool - debug mode
        @param services_cache_time: int
            - seconds between caching get_services()
            - defaults to 8 hours
        @param session : requests.session - session object
        ```
        """
        super().__init__(username, password, debug, services_cache_time)
        if session is None:
            self.session = requests.Session()
        else:
            self.session = session

    def login(self, depth: int = 0) -> bool:
        """Logs into the account and caches the cookie."""
        if depth > 2:
            raise RecursiveDepth("Login recursion depth > 2")
        self.logger.debug("Logging in...")

        url = BASEURL["login"]

        payload = {
            "username": self.username,
            "password": self.password.get_secret_value(),
        }
        headers: Dict[str, Any] = dict(default_headers())

        response = self.session.post(
            url,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
        jsondata = response.json()

        return self._handle_login_response(
            response.status_code, jsondata, response.cookies
        )

    def do_login_check(self, skip_login_check: bool) -> None:
        """checks if we're skipping the login check and logs in if necessary"""
        if not skip_login_check:
            self.logger.debug("skip_login_check false")
            if self._has_token_expired():
                self.logger.debug("token has expired, logging in...")
                self.login()

    def request_get(  # type: ignore
        self,
        url: str,
        skip_login_check: bool = False,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """Performs a GET request and logs in first if needed.

        Returns the `requests.Response` object."""
        self.do_login_check(skip_login_check)
        if cookies is None:
            cookies = {"myaussie_cookie": self.myaussie_cookie}

        response = self.session.get(url=url, cookies=cookies, params=params)
        response.raise_for_status()
        return response

    def request_get_list(
        self,
        url: str,
        skip_login_check: bool = False,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Performs a GET request and logs in first if needed.

        Returns a list from the response.
        """
        self.do_login_check(skip_login_check)
        response = self.session.get(url=url, cookies=cookies, params=params)
        response.raise_for_status()
        result: List[Any] = response.json()
        return result

    def request_get_json(
        self,
        url: str,
        skip_login_check: bool = False,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Performs a GET request and logs in first if needed.

        Returns a dict of the JSON response.
        """
        self.do_login_check(skip_login_check)
        response = self.session.get(url=url, cookies=cookies, params=params)
        response.raise_for_status()
        result: Dict[str, Any] = response.json()
        return result

    def request_post(
        self, url: str, skip_login_check: bool = False, **kwargs: Dict[str, Any]
    ) -> requests.Response:
        """Performs a POST request and logs in first if needed."""
        self.do_login_check(skip_login_check)
        if "cookies" not in kwargs:
            kwargs["cookies"] = {"myaussie_cookie": self.myaussie_cookie}

        if "headers" in kwargs:
            headers: Dict[str, Any] = kwargs["headers"]
        else:
            headers = dict(default_headers())

        response = self.session.post(
            url=url,
            headers=headers,
            **kwargs,  # type: ignore
        )
        response.raise_for_status()
        return response

    def get_customer_details(self) -> Dict[str, Any]:
        """Grabs the customer details.

        Returns a dict"""
        url = self.get_url("get_customer_details")
        querystring = {"v": "2"}
        responsedata = self.request_get_json(
            url=url,
            params=querystring,
        )
        return responsedata

    @property
    def referral_code(self) -> int:
        """returns the referral code, which is just the customer number"""
        response = self.get_customer_details()
        if "customer_number" not in response:
            raise ValueError("Couldn't get customer_number from customer_details call.")
        return int(response["customer_number"])

    def _check_reload_cached_services(self) -> bool:
        """If the age of the service data caching is too old, clear it and re-poll.

        Returns bool - if it reloaded the cache.
        """
        if not self.services:
            self.get_services(use_cached=False)
            return True

        cache_expiry = self.services_last_update + self.services_cache_time
        if time() >= cache_expiry:
            self.get_services(use_cached=False)
            return True
        return False

    def get_services(
        self,
        page: int = 1,
        use_cached: bool = False,
        servicetypes: Optional[List[str]] = None,
        drop_types: Optional[List[str]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """Returns a `list` of `dicts` of services associated with the account.

        If you want a specific kind of service, or services,
        provide a list of matching strings in servicetypes.

        If you want to use cached data, call it with `use_cached=True`
        """
        if use_cached:
            self.logger.debug("Using cached data for get_services.")
            self._check_reload_cached_services()
        else:
            url = self.get_url("get_services")
            services_list: List[Dict[str, Any]] = []
            while True:
                params = {"page": page}
                responsedata = self.request_get_json(url=url, params=params)
                next_url, page, services_list = self.handle_services_response(
                    responsedata, services_list
                )
                if next_url is None:
                    break
                url = next_url
            self.services = services_list
            self.services_last_update = int(time())

        self.services = self.filter_services(
            service_types=servicetypes,
            drop_types=drop_types,
        )

        return self.services

    def account_transactions(self) -> Dict[str, AccountTransaction]:
        """Pulls the data for transactions on your account.

        Returns a dict where the key is the month and year of the transaction.

        Keys: `['id', 'type', 'time', 'description', 'amountCents', 'runningBalanceCents']`

        Example output:

        ``` json
        "August 2021": [
          {
                "id": 12345,
                "type": "receipt",
                "time": "2021-08-06",
                "description": "Payment #12345",
                "amountCents": -8400,
                "runningBalanceCents": 0
            }
        ],
        ```
        """
        url = self.get_url("account_transactions")
        responsedata = self.request_get_json(url=url)

        result: Dict[str, AccountTransaction] = responsedata
        return result

    def billing_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Downloads an invoice

        This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        url = self.get_url("billing_invoice", {"invoice_id": invoice_id})
        result = self.request_get_json(url=url)

        return result

    def account_paymentplans(self) -> Dict[str, Any]:
        """Returns a dict of payment plans for an account"""
        url = self.get_url("account_paymentplans")
        return self.request_get_json(url=url)

    def get_usage(self, service_id: int, use_cached: bool = True) -> Dict[str, Any]:
        """
        Returns a dict of usage for a service.

        If it's a telephony service (`type=PhoneMobile`) it'll pull from the telephony endpoint.

        """
        if self.services is None:
            self.get_services(use_cached=use_cached)

        if self.services is not None:
            for service in self.services:
                if service_id == service["service_id"]:
                    # throw an error if we're trying to parse something we can't
                    self.validate_service_type(service)
                    if service["type"] in PHONE_TYPES:
                        return self.telephony_usage(service_id)
            url = self.get_url("get_usage", {"service_id": service_id})
            result = self.request_get_json(url=url)
            return result
        return {}

    def get_service_tests(self, service_id: int) -> List[ServiceTest]:
        """Gets the available tests for a given service ID
        Returns list of dicts

        Example data:

        ```
        [{
            'name' : str(),
            'description' : str',
            'link' : str(a url to the test)
        },]
        ```

        This has a habit of throwing 400 errors if you query a VOIP service...
        """
        url = self.get_url("get_service_tests", {"service_id": service_id})
        results: List[ServiceTest] = [
            ServiceTest.model_validate(test) for test in self.request_get_list(url=url)
        ]
        return results

    def get_test_history(self, service_id: int) -> Dict[str, Any]:
        """Gets the available tests for a given service ID

        Returns a list of dicts with tests which have been run
        """
        url = self.get_url("get_test_history", {"service_id": service_id})
        return self.request_get_json(url=url)

    def test_line_state(self, service_id: int) -> Dict[str, Any]:
        """Tests the line state for a given service ID"""
        tests = self.get_service_tests(service_id)
        url = self.get_url("test_line_state", {"service_id": service_id})

        self.is_valid_test(url, tests)

        self.logger.debug("Testing line state, can take a few seconds...")
        response = self.request_post(url=url)
        result: Dict[str, Any] = response.json()
        return result

    def run_test(
        self, service_id: int, test_name: str, test_method: str = "post"
    ) -> Optional[Dict[str, Any]]:
        """Run a test, but it checks it's valid first

        There doesn't seem to be a valid way to identify what method you're supposed to use on each test.

        See the README for more analysis

        - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
        - 'status' of 'Completed' means you've got the full response
        """

        test_links = [
            test
            for test in self.get_service_tests(service_id)
            if test.link.endswith(f"/{test_name}")
        ]

        if not test_links:
            return None
        if len(test_links) != 1:
            self.logger.debug("Too many tests? %s", test_links)

        test_name = test_links[0].name
        self.logger.debug("Running %s", test_name)
        if test_method == "get":
            return self.request_get_json(url=test_links[0].link)
        result: Dict[str, Any] = self.request_post(url=test_links[0].link).json()
        return result

    def service_plans(self, service_id: int) -> Dict[str, Any]:
        """
        Pulls the plan data for a given service. You MUST MFA-verify first.

        Keys: `['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']`

        """
        url = self.get_url("service_plans", {"service_id": service_id})
        return self.request_get_json(url=url)

    def service_outages(self, service_id: int) -> Dict[str, Any]:
        """Pulls outages associated with a service.

        Keys: `['networkEvents', 'aussieOutages', 'currentNbnOutages', 'scheduledNbnOutages', 'resolvedScheduledNbnOutages', 'resolvedNbnOutages']`

        ```
        """
        url = self.get_url("service_outages", {"service_id": service_id})
        data = self.request_get_json(url=url)
        result = AussieBBOutage.model_validate(data)
        return result.model_dump()

    def service_boltons(self, service_id: int) -> Dict[str, Any]:
        """Pulls addons associated with the service.

        Keys: `['id', 'name', 'description', 'costCents', 'additionalNote', 'active']`

        Example data:

        ```
        [{
            "id": 4,
            "name": "Small Change Big Change Donation",
            "description": "Charitable donation to the Small Change Big Change program, part of the Telco Together Foundation, which helps build resilient young Australians",
            "costCents": 100,
            "additionalNote": null,
            "active": false
        }]
        ```
        """
        url = self.get_url("service_boltons", {"service_id": service_id})
        return self.request_get_json(url=url)

    def service_datablocks(self, service_id: int) -> Dict[str, Any]:
        """Pulls datablocks associated with the service.

        Keys: `['current', 'available']`

        Example data:

        ```
        {
            "current": [],
            "available": []
        }
        ```
        """
        url = self.get_url("service_datablocks", {"service_id": service_id})
        return self.request_get_json(url=url)

    def telephony_usage(self, service_id: int) -> Dict[str, Any]:
        """Pulls the telephony usage associated with the service.

        Keys: `['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']`

        Example data:

        ```
        {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},
        "international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},
        "internet":{"kbytes":0,"cost":0},
        "voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},
        "daysTotal":31,"daysRemaining":2,"historical":[]}
        ```
        """
        url = self.get_url("telephony_usage", {"service_id": service_id})
        return self.request_get_json(url=url)

    def support_tickets(self) -> Dict[str, Any]:
        """Pulls the support tickets associated with the account, returns a list of dicts.

        Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`

        """
        url = self.get_url("support_tickets")
        return self.request_get_json(url=url)

    def get_appointment(self, ticketid: int) -> Dict[str, Any]:
        """Pulls the support tickets associated with the account, returns a list of dicts.

        Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`
        """
        url = self.get_url("get_appointment", {"ticketid": ticketid})
        return self.request_get_json(url=url)

    def account_contacts(self) -> List[AccountContact]:
        """Pulls the contacts with the account, returns a list of dicts

        Dict keys: `['id', 'first_name', 'last_name', 'email', 'dob', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']`
        """
        url = self.get_url("account_contacts")
        response = self.request_get_json(url=url)
        return [AccountContact.model_validate(contact) for contact in response]

    # TODO: type get_orders
    def get_orders(self) -> Dict[str, Any]:
        """pulls the outstanding orders for an account"""
        url = self.get_url("get_orders")
        responsedata = self.request_get_json(url=url)

        result = OrderResponse(**responsedata)
        return result.model_dump()

    def get_order(self, order_id: int) -> OrderDetailResponse:
        """gets a specific order"""
        url = self.get_url("get_order", {"order_id": order_id})
        responsedata = self.request_get_json(url=url)
        result = cast(
            OrderDetailResponse,
            OrderDetailResponseModel.model_validate(responsedata).model_dump(),
        )
        return result

    def get_voip_devices(self, service_id: int) -> List[VOIPDevice]:
        """gets the devices associatd with a VOIP service"""
        url = self.get_url("voip_devices", {"service_id": service_id})
        service_list: List[VOIPDevice] = []
        for service in self.request_get_json(url=url):
            service_list.append(VOIPDevice.model_validate(service))
        return service_list

    def get_voip_service(self, service_id: int) -> VOIPDetails:
        """gets the details of a VOIP service"""
        url = self.get_url("voip_service", {"service_id": service_id})
        return VOIPDetails.model_validate(self.request_get_json(url=url))

    def get_fetch_service(self, service_id: int) -> FetchService:
        """gets the details of a Fetch service"""
        url = self.get_url("fetch_service", {"service_id": service_id})
        return FetchService.model_validate(self.request_get_json(url=url))

    async def mfa_send(self, method: MFAMethod) -> None:
        """sends an MFA code to the user"""
        url = self.get_url("mfa_send")
        print(method.model_dump(), file=sys.stderr)
        self.request_post(url=url, data=method.model_dump())

    async def mfa_verify(self, token: str) -> None:
        """got the token from send_mfa? send it back to validate it"""
        url = self.get_url("mfa_verify")
        self.request_post(url=url, data={"token": token})
