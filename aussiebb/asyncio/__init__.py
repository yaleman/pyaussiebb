""" aiohttp support for AussieBB """


import asyncio

import json
from time import time
import sys
from typing import Any, Dict, List, Optional

from pydantic import SecretStr

try:
    import aiohttp
    from aiohttp.client import ClientResponse
except ImportError as error_message:
    print(f"Failed to import aiohttp, bailing: {error_message}", file=sys.stderr)
    sys.exit(1)

from ..baseclass import BaseClass
from ..const import BASEURL, default_headers, DEFAULT_BACKOFF_DELAY, PHONE_TYPES
from ..exceptions import (
    AuthenticationException,
    RateLimitException,
    RecursiveDepth,
)

from ..types import (
    MFAMethod,
    ServiceTest,
    AccountContact,
    AccountTransaction,
    FetchService,
    OrderDetailResponseModel,
    VOIPDevice,
    VOIPDetails,
)


class AussieBB(BaseClass):
    """aiohttp class for interacting with Aussie Broadband APIs"""

    def __init__(
        self,
        username: str,
        password: SecretStr,
        session: Optional[aiohttp.client.ClientSession] = None,
        debug: bool = False,
        services_cache_time: int = 28800,
    ):
        """Setup function

        ```
        @param username: str - username for Aussie Broadband account
        @param password: str - password for Aussie Broadband account
        @param debug: bool - debug mode
        @param services_cache_time: int
            - seconds between caching get_services()
            - defaults to 8 hours
        ```
        """
        super().__init__(username, password, debug, services_cache_time)

        if not session:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

    async def login(self, depth: int = 0) -> bool:
        """Logs into the account and caches the cookie."""
        if depth > 2:
            raise RecursiveDepth("Login recursion depth > 2")
        self.logger.debug("Logging in...")

        url = BASEURL["login"]

        if not self._has_token_expired():
            return True

        payload = {
            "username": self.username,
            "password": self.password.get_secret_value(),
        }
        headers = default_headers()

        async with self.session.post(
            url=url,
            headers=headers,
            json=payload,
        ) as response:
            try:
                await self.handle_response_fail(response)
                jsondata = await response.json()
            except RateLimitException:
                return await self.login(depth + 1)
            self.logger.debug("Login response status: %s", response.status)
        self.logger.debug("Dumping login response: %s", json.dumps(jsondata))

        return self._handle_login_response(response.status, jsondata, response.cookies)

    async def handle_response_fail(
        self,
        response: ClientResponse,
        wait_on_rate_limit: bool = True,
    ) -> None:
        """Handles response status codes. Tries to gracefully handle the rate limiting.

        ```
        @param response - aiohttp.Response - the full response object
        @param wait_on_rate_limit - bool - if hitting a rate limit, async wait on the time limit
        ```
        """
        ratelimit_remaining = int(response.headers.get("X-RateLimit-Remaining", -1))
        self.logger.debug(
            "Rate limit header: %s", response.headers.get("X-RateLimit-Remaining", -1)
        )
        if ratelimit_remaining < 5 and wait_on_rate_limit:
            self.logger.info("Rate limit below 5, sleeping for 1 second.")
            await asyncio.sleep(1)

        if response.status == 422:
            raise AuthenticationException(await response.json())
        if response.status == 429:
            jsondata = await response.json()
            self.logger.debug("Dumping headers: %s", response.headers)
            self.logger.debug("Dumping response: %s", json.dumps(jsondata, default=str))
            delay = DEFAULT_BACKOFF_DELAY
            if "Please try again in " in str(jsondata.get("errors")):
                fallback_value = [f"default {DEFAULT_BACKOFF_DELAY} seconds"]
                delay = (
                    jsondata.get("errors", {})
                    .get("username", fallback_value)[0]
                    .split()[-2]
                )
                # give it some extra time to cool off
                delay = int(delay) + 5

                if 0 < delay < 1000:
                    self.logger.debug("Found required rate limit delay: %s", delay)
                    delay = int(delay)
                else:
                    self.logger.debug(
                        "Couldn't parse rate limit delay, using default: %s", delay
                    )
            else:
                delay = DEFAULT_BACKOFF_DELAY
                self.logger.debug("Couldn't parse delay, using default: %s", delay)
            if wait_on_rate_limit:
                self.logger.debug(
                    "Rate limit on Aussie API calls raised, sleeping for %s seconds.",
                    delay,
                )
                await asyncio.sleep(delay)
            raise RateLimitException(jsondata)
        if response.status == 500:
            self.logger.error("AussieBB API returned 500, dumping headers.")
            self.logger.error(response.headers)
            self.logger.error("body: %s", await response.content.read())
        response.raise_for_status()

    async def do_login_check(self, skip_login_check: bool) -> None:
        """checks if we're skipping the login check and logs in if necessary"""
        if not skip_login_check:
            self.logger.debug("skip_login_check false")
            if self._has_token_expired():
                self.logger.debug("token has expired, logging in...")
                await self.login()

    async def request_get(
        self,
        url: str,
        skip_login_check: bool = False,
        depth: int = 0,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> ClientResponse:
        """Performs a GET request and logs in first if needed."""
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        await self.do_login_check(skip_login_check)

        if cookies is None:
            cookies = {"myaussie_cookie": self.myaussie_cookie}

        # telling it where we're coming from
        headers = {
            "referer": "https://my.aussiebroadband.com.au/",
            "x-two-factor-auth-capable-client": "false",  # this might need to be a thing...
        }
        response: ClientResponse = await self.session.get(
            url=url, cookies=cookies, params=params, headers=headers
        )
        try:
            await self.handle_response_fail(response)
            await response.read()
        except RateLimitException:
            response = await self.request_get(
                url=url,
                skip_login_check=skip_login_check,
                depth=depth,
                cookies=cookies,
                params=params,
            )
        return response

    async def request_get_list(
        self,
        url: str,
        skip_login_check: bool = False,
        depth: int = 0,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Performs a GET request and logs in first if needed.

        Returns a list from the JSON response.
        """
        response = await self.request_get(url, skip_login_check, depth, cookies, params)
        result: List[Any] = await response.json()
        return result

    async def request_get_json(
        self,
        url: str,
        skip_login_check: bool = False,
        depth: int = 0,
        cookies: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Performs a GET request and logs in first if needed.

        Returns a dict of the JSON response.
        """
        response = await self.request_get(url, skip_login_check, depth, cookies, params)
        result: Dict[str, Any] = await response.json()
        return result

    async def request_post_json(
        self,
        url: str,
        depth: int = 0,
        skip_login_check: bool = False,
        **kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Performs a POST request and logs in first if needed.

        Returns a dict of the response data.
        """
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        await self.do_login_check(skip_login_check)

        cookies = kwargs.get("cookies", {"myaussie_cookie": self.myaussie_cookie})
        headers = kwargs.get("headers", default_headers())
        async with self.session.post(
            url=url, cookies=cookies, headers=headers, json=kwargs.get("data")
        ) as response:
            try:
                await self.handle_response_fail(response)
                jsondata: Dict[str, Any] = await response.json()
            except RateLimitException:
                jsondata = await self.request_post_json(
                    url=url,
                    depth=depth + 1,
                    skip_login_check=skip_login_check,
                    **kwargs,
                )
        return jsondata

    async def get_customer_details(self) -> Dict[str, Any]:
        """Grabs the customer details.

        Returns a dict"""

        url = self.get_url("get_customer_details")
        result: Dict[str, Any] = await self.request_get_json(
            url=url,
            params={"v": "2"},
        )
        return result

    @property
    async def referral_code(self) -> int:
        """returns the referral code, which is just the customer number"""
        response = await self.get_customer_details()
        if "customer_number" not in response:
            raise ValueError("Couldn't get customer_number from customer_details call.")
        return int(response["customer_number"])

    async def _check_reload_cached_services(self) -> bool:
        """If the age of the service data caching is too old, clear it and re-poll.

        Returns bool - if it reloaded the cache.
        """
        if not self.services:
            await self.get_services(use_cached=False)
            return True
        cache_expiry = self.services_last_update + self.services_cache_time
        if time() >= cache_expiry:
            await self.get_services(use_cached=False)
            return True
        return False

    async def get_services(
        self,
        page: int = 1,
        use_cached: bool = False,
        servicetypes: Optional[List[str]] = None,
        drop_types: Optional[List[str]] = None,
        drop_unknown_types: bool = False,
    ) -> List[Dict[str, Any]]:
        """Returns a `list` of `dicts` of services associated with the account.

        If you want a specific kind of service, or services,
        provide a list of matching strings in servicetypes.

        If you want to use cached data, call it with `use_cached=True`

        If you want to drop service types, then pass a list of strings to drop_types, or if you want to drop things we don't recognize, pass `drop_unknown_types=True`
        """
        if use_cached:
            self.logger.debug("Using cached data for get_services.")
            await self._check_reload_cached_services()
        else:
            url = self.get_url("get_services")
            services_list: List[Dict[str, Any]] = []
            while True:
                params = {"page": page}
                responsedata = await self.request_get_json(url=url, params=params)

                next_url, page, services_list = self.handle_services_response(
                    responsedata, services_list
                )
                if next_url is None:
                    break
                url = next_url

            self.services = services_list
            self.services_last_update = int(time())

        # TODO: validate the expected fields in the service (type, name, plan, description, service_id at a minimum)

        self.services = self.filter_services(
            service_types=servicetypes,
            drop_types=drop_types,
            drop_unknown_types=drop_unknown_types,
        )

        return self.services

    async def account_transactions(self) -> Dict[str, AccountTransaction]:
        """Pulls the data for transactions on your account.

        Returns a dict where the key is the month and year of the transaction.

        Keys: `['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']`

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
        responsedata: Dict[str, AccountTransaction] = await self.request_get_json(
            url=url
        )
        return responsedata

    async def billing_receipt(self, receipt_id: int) -> ClientResponse:
        """Downloads a receipt

        This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        return await self.billing_download("receipt", receipt_id)

    async def billing_invoice(self, invoice_id: int) -> ClientResponse:
        """Downloads an invoice

        This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        return await self.billing_download("invoice", invoice_id)

    async def billing_download(
        self, download_type: str, item_id: int
    ) -> ClientResponse:
        """Downloads a billing file

        This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        url = f"{self.BASEURL.get('api')}/billing/{download_type}s/{item_id}"

        responsedata = await self.request_get(url=url)
        return responsedata

    async def account_paymentplans(self) -> Dict[str, Any]:
        """Returns a dict of payment plans for an account"""
        url = self.get_url("account_paymentplans")
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_usage(
        self, service_id: int, use_cached: bool = True
    ) -> Dict[str, Any]:
        """
        Returns a dict of usage for a service.

        If it's a telephony service (`type in aussiebb.const.PHONE_TYPES`) it'll pull from the telephony endpoint.

        """
        services = await self.get_services(use_cached=use_cached)
        for service in services:
            if service_id == service["service_id"]:
                # throw an error if we're trying to parse something we can't
                self.validate_service_type(service)
                if service["type"] in PHONE_TYPES:
                    return await self.telephony_usage(service_id)
        url = self.get_url("get_usage", {"service_id": service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_service_tests(self, service_id: int) -> List[ServiceTest]:
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
        if self.debug:
            print(f"Getting service tests for {service_id}", file=sys.stderr)

        url = self.get_url("get_service_tests", {"service_id": service_id})
        responsedata: List[Any] = await self.request_get_list(url=url)
        return [ServiceTest.model_validate(test) for test in responsedata]

    async def get_test_history(self, service_id: int) -> Dict[str, Any]:
        """Gets the available tests for a given service ID

        Returns a list of dicts with tests which have been run
        """

        url = self.get_url("get_test_history", {"service_id": service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def test_line_state(self, service_id: int) -> Dict[str, Any]:
        """Tests the line state for a given service ID"""
        tests = await self.get_service_tests(service_id)
        url = self.get_url("test_line_state", {"service_id": service_id})

        self.is_valid_test(url, tests)

        # if self.debug:
        # print("Testing line state, can take a few seconds...")
        response = await self.request_post_json(url=url)
        # if self.debug:
        # print(f"Response: {response}", file=sys.stderr)
        return response

    async def run_test(
        self, service_id: int, test_name: str, test_method: str = "post"
    ) -> Optional[Dict[str, Any]]:
        """Run a test, but it checks it's valid first

        There doesn't seem to be a valid way to identify what method you're supposed to use on each test.

        See the README for more analysis

        - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
        - 'status' of 'Completed' means you've got the full response
        """

        service_tests = await self.get_service_tests(service_id)
        test_links = [
            test for test in service_tests if test.link.endswith(f"/{test_name}")
        ]

        if not test_links:
            return None
        if len(test_links) != 1:
            if self.debug:
                print(f"Too many tests? {test_links}", file=sys.stderr)

        test_name = test_links[0].name
        if self.debug:
            print(f"Running {test_name}", file=sys.stderr)
        if test_method == "get":
            result = await self.request_get_json(url=test_links[0].link)
        else:
            result = await self.request_post_json(url=test_links[0].link)
        return result

    async def service_plans(self, service_id: int) -> Dict[str, Any]:
        """
        Pulls the plan data for a given service. You MUST MFA-verify first.

        Keys: `['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']`

        """

        url = self.get_url("service_plans", {"service_id": service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_outages(self, service_id: int) -> Dict[str, Any]:
        """Pulls outages associated with a service.

        Keys: `['networkEvents', 'aussieOutages', 'currentNbnOutages', 'scheduledNbnOutages', 'resolvedScheduledNbnOutages', 'resolvedNbnOutages']`

        Example data:
        ```
        {
            "networkEvents": [],
            "aussieOutages": [],
            "currentNbnOutages": [],
            "scheduledNbnOutages": [],
            "resolvedScheduledNbnOutages": [
                {
                    "start_date": "2021-08-17T14:00:00Z",
                    "end_date": "2021-08-17T20:00:00Z",
                    "duration": "6.0"
                }
            ],
            "resolvedNbnOutages": []
        }
        ```
        """
        url = self.get_url("service_outages", {"service_id": service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_boltons(self, service_id: int) -> Dict[str, Any]:
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
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_datablocks(self, service_id: int) -> Dict[str, Any]:
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
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def telephony_usage(self, service_id: int) -> Dict[str, Any]:
        """Pulls the telephony usage associated with the service.

        Keys: `['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']`

        Example data:

        ```
        {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},
        "international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},
        "internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},
        "other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
        ```
        """
        url = self.get_url("telephony_usage", {"service_id": service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def support_tickets(self) -> Dict[str, Any]:
        """Pulls the support tickets associated with the account, returns a list of dicts.

        Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`

        """
        url = self.get_url("support_tickets")
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_appointment(self, ticketid: int) -> Dict[str, Any]:
        """Pulls the support tickets associated with the account, returns a list of dicts.

        Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`
        """
        url = self.get_url("get_appointment", {"ticketid": ticketid})
        return await self.request_get_json(url=url)

    async def account_contacts(self) -> List[AccountContact]:
        """Pulls the contacts with the account, returns a list of dicts

        Dict keys: `['id', 'first_name', 'last_name', 'email', 'dob', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']`
        """
        url = self.get_url("account_contacts")
        response = await self.request_get_json(url=url)
        return [AccountContact.model_validate(contact) for contact in response]

    async def get_orders(self) -> Dict[str, Any]:
        """pulls the outstanding orders for an account"""
        url = self.get_url("get_orders")
        responsedata = await self.request_get_json(url=url)
        result = OrderDetailResponseModel(**responsedata)
        return result.dict()

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """gets a specific order"""
        url = self.get_url("get_order", {"order_id": order_id})
        responsedata = await self.request_get_json(url=url)
        result = OrderDetailResponseModel(**responsedata)
        return result.dict()

    async def get_voip_devices(self, service_id: int) -> List[VOIPDevice]:
        """gets the devices associatd with a VOIP service"""
        url = self.get_url("voip_devices", {"service_id": service_id})
        service_list: List[VOIPDevice] = []
        data = await self.request_get_json(url=url)
        for service in data:
            service_list.append(VOIPDevice.model_validate(service))
        return service_list

    async def get_voip_service(self, service_id: int) -> VOIPDetails:
        """gets the details of a VOIP service"""
        url = self.get_url("voip_service", {"service_id": service_id})
        data = await self.request_get_json(url=url)
        return VOIPDetails.model_validate(data)

    async def get_fetch_service(self, service_id: int) -> FetchService:
        """gets the details of a Fetch service"""
        url = self.get_url("fetch_service", {"service_id": service_id})
        data = await self.request_get_json(url=url)
        return FetchService.model_validate(data)

    async def mfa_send(self, method: MFAMethod) -> None:
        """sends an MFA code to the user"""
        url = self.get_url("mfa_send")
        print(method.dict())
        await self.request_post_json(url=url, data=method.dict())

    async def mfa_verify(self, token: str) -> None:
        """got the token from send_mfa? send it back to validate it"""
        url = self.get_url("mfa_verify")
        await self.request_post_json(url=url, data={"token": token})
