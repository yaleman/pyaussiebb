""" aiohttp support for AussieBB """


import asyncio

import json
from time import time
import sys
from typing import Any, Dict, List, Optional
from unittest import skip

try:
    import aiohttp
    from aiohttp.client import ClientResponse
except ImportError as error_message:
    print(f"Failed to import aiohttp, bailing: {error_message}", file=sys.stderr)
    sys.exit(1)

from ..baseclass import BaseClass
from ..const import BASEURL, default_headers, DEFAULT_BACKOFF_DELAY, PHONE_TYPES
from ..exceptions import AuthenticationException, RateLimitException, RecursiveDepth

from ..types import ServiceTest, AccountTransaction

class AussieBB(BaseClass): #pylint: disable=too-many-public-methods
    """ aiohttp class for interacting with Aussie Broadband APIs """
    #pylint: disable=too-many-arguments
    def __init__(
        self,
        username: str,
        password: str,
        session: Optional[aiohttp.client.ClientSession] = None,
        debug: bool=False,
        services_cache_time: int = 28800):
        """ Setup function

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

    async def login(self, depth: int=0) -> bool:
        """ Logs into the account and caches the cookie.  """
        if depth>2:
            raise RecursiveDepth("Login recursion depth > 2")
        self.logger.debug("Logging in...")

        url = BASEURL["login"]

        if not self._has_token_expired():
            return True

        payload = {
            'username' : self.username,
            'password' : self.password,
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
                return await self.login(depth+1)
            self.logger.debug("Login response status: %s", response.status)
        self.logger.debug("Dumping login response: %s", json.dumps(jsondata))

        return self._handle_login_response(response.status, jsondata, response.cookies)

    async def handle_response_fail(self, response, wait_on_rate_limit: bool=True):
        """ Handles response status codes. Tries to gracefully handle the rate limiting.

        ```
        @param response - aiohttp.Response - the full response object
        @param wait_on_rate_limit - bool - if hitting a rate limit, async wait on the time limit
        ```
        """
        ratelimit_remaining = int(response.headers.get('x-ratelimit-remaining', -1))
        self.logger.debug("Rate limit header: %s", response.headers.get('x-ratelimit-remaining', -1))
        if ratelimit_remaining < 5 and wait_on_rate_limit:
            print("Rate limit below 5, sleeping for 1 second.", file=sys.stderr)
            await asyncio.sleep(1)

        if response.status == 422:
            raise AuthenticationException(await response.json())
        if response.status == 429:
            jsondata = await response.json()
            self.logger.debug("Dumping headers: %s", response.headers)
            self.logger.debug("Dumping response: %s", json.dumps(jsondata, default=str))
            delay = DEFAULT_BACKOFF_DELAY
            if 'Please try again in ' in str(jsondata.get('errors')):
                fallback_value = [f"default {DEFAULT_BACKOFF_DELAY} seconds"]
                delay = jsondata.get('errors', {}).get('username', fallback_value)[0].split()[-2]
                # give it some extra time to cool off
                delay = int(delay)+5

                if 0 < delay < 1000:
                    self.logger.debug("Found required rate limit delay: %s", delay)
                    delay = int(delay)
                else:
                    self.logger.debug("Couldn't parse rate limit delay, using default: %s", delay)
            else:
                delay = DEFAULT_BACKOFF_DELAY
                self.logger.debug("Couldn't parse delay, using default: %s", delay)
            if wait_on_rate_limit:
                self.logger.debug("Rate limit on Aussie API calls raised, sleeping for %s seconds.", delay)
                await asyncio.sleep(delay)
            raise RateLimitException(jsondata)
        response.raise_for_status()

    async def do_login_check(self, skip_login_check: bool) -> None:
        """ checks if we're skipping the login check and logs in if necessary """
        if not skip_login_check:
            self.logger.debug("skip_login_check false")
            if self._has_token_expired():
                self.logger.debug("token has expired, logging in...")
                await self.login()

    async def request_get(self, skip_login_check: bool = False, **kwargs) -> ClientResponse:
        """ Performs a GET request and logs in first if needed. """
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        await self.do_login_check(skip_login_check)

        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        async with self.session.get(**kwargs) as response:
            try:
                await self.handle_response_fail(response)
                await response.read()
            except RateLimitException:
                response = await self.request_get(skip_login_check, **kwargs)
            return response

    async def request_get_json(self, skip_login_check: bool = False, **kwargs):
        """ Performs a GET request and logs in first if needed.

        Returns a dict of the JSON response.
        """
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        await self.do_login_check(skip_login_check)

        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        async with self.session.get(**kwargs) as response:
            try:
                await self.handle_response_fail(response)
                jsondata = await response.json()
            except RateLimitException:
                jsondata = await self.request_get_json(skip_login_check, **kwargs)
        return jsondata

    async def request_post_json(self, url, **kwargs):
        """ Performs a POST request and logs in first if needed.

        Returns a dict of the response data.
        """
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        await self.do_login_check(kwargs.get("skip_login_check", False))

        cookies = kwargs.get('cookies', {'myaussie_cookie' : self.myaussie_cookie})
        headers = kwargs.get('headers', default_headers())
        async with self.session.post(url=url, cookies=cookies, headers=headers) as response:
            try:
                await self.handle_response_fail(response)
                jsondata = await response.json()
            except RateLimitException:
                jsondata = await self.request_post_json(url=url, depth=depth+1, **kwargs)
        return jsondata

    async def get_customer_details(self) -> dict:
        """ Grabs the customer details.

        Returns a dict """

        url = self.get_url("get_customer_details")
        params = {"v":"2"}
        return await self.request_get_json(url=url,
                                    params=params,
                                    )

    async def _check_reload_cached_services(self):
        """ If the age of the service data caching is too old, clear it and re-poll.

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
        page: int=1,
        servicetypes: Optional[List[str]]=None,
        use_cached: bool=False,
        ):
        """ Returns a `list` of `dicts` of services associated with the account.

            If you want a specific kind of service, or services,
            provide a list of matching strings in servicetypes.

            If you want to use cached data, call it with `use_cached=True`
        """
        if use_cached:
            self.logger.debug("Using cached data for get_services.")
            await self._check_reload_cached_services()
        else:
            url = self.get_url("get_services")
            params = {'page' : page}

            responsedata = await self.request_get_json(url=url, params=params)
            # cache the data
            self.services_last_update = int(time())
            self.services = responsedata.get('data')

        # checking that service types are valid
        if self.services is not None:
            for service in self.services:
                self.validate_service_type(service)

        # only filter if we need to
        if servicetypes is not None:
            self.logger.debug("Filtering services based on provided list: %s", servicetypes)
            filtered_responsedata: List[Any]= []
            if self.services is not None:
                for service in self.services:
                    if service.get('type') in servicetypes:
                        filtered_responsedata.append(service)
                    else:
                        self.logger.debug("Skipping as type==%s - %s", service.get('type'), service)
            return filtered_responsedata

        return self.services

    async def account_transactions(self) -> Dict[str, AccountTransaction]:
        """ Pulls the data for transactions on your account.

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
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def billing_invoice(self, invoice_id):
        """ Downloads an invoice

            This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        url = self.get_url("billing_invoice", {'invoice_id', invoice_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def account_paymentplans(self):
        """ Returns a dict of payment plans for an account """
        url = self.get_url("account_paymentplans")
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_usage(self, service_id: int):
        """
        Returns a dict of usage for a service.

        If it's a telephony service (`type in ["PhoneMobile","VOIP"]`) it'll pull from the telephony endpoint.

        """
        services = await self.get_services(use_cached=True)
        for service in services:
            if service_id == service.get('service_id'):
                if service.get('type') in PHONE_TYPES:
                    return await self.telephony_usage(service_id)

        url = self.get_url("get_usage", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_service_tests(self, service_id: int) -> List[ServiceTest]:
        """ Gets the available tests for a given service ID
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

        url = self.get_url("get_service_tests", {'service_id' : service_id})
        responsedata: List[ServiceTest] = await self.request_get_json(url=url)
        return responsedata

    async def get_test_history(self, service_id: int):
        """ Gets the available tests for a given service ID

        Returns a list of dicts with tests which have been run
        """

        url = self.get_url("get_test_history", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def test_line_state(self, service_id: int):
        """ Tests the line state for a given service ID """
        url = self.get_url("test_line_state", {'service_id' : service_id})

        if self.debug:
            print("Testing line state, can take a few seconds...")
        response = await self.request_post_json(url=url)
        if self.debug:
            print(f"Response: {response}", file=sys.stderr)
        return response

    async def run_test(self, service_id: int, test_name: str, test_method: str = 'post'):
        """ Run a test, but it checks it's valid first

            There doesn't seem to be a valid way to identify what method you're supposed to use on each test.

            See the README for more analysis

            - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
            - 'status' of 'Completed' means you've got the full response
        """

        service_tests = await self.get_service_tests(service_id)
        test_links = [test for test in service_tests if test.get('link', '').endswith(f'/{test_name}')] #pylint: disable=line-too-long

        if not test_links:
            return False
        if len(test_links) != 1:
            if self.debug:
                print(f"Too many tests? {test_links}", file=sys.stderr)

        test_name = test_links[0]["name"]
        if self.debug:
            print(f"Running {test_name}", file=sys.stderr)
        if test_method == 'get':
            result = await self.request_get_json(url=test_links[0].get('link'))
        else:
            result = await self.request_post_json(url=test_links[0].get('link'))
        return result

    async def service_plans(self, service_id: int):
        """ Pulls the plan data for a given service.

            Keys: `['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']`

        """

        url = self.get_url("service_plans", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_outages(self, service_id: int):
        """ Pulls outages associated with a service.

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
        url = self.get_url("service_outages", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_boltons(self, service_id: int):
        """ Pulls addons associated with the service.

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
        url = self.get_url("service_boltons", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_datablocks(self, service_id: int):
        """ Pulls datablocks associated with the service.

            Keys: `['current', 'available']`

            Example data:

            ```
            {
                "current": [],
                "available": []
            }
            ```
        """
        url = self.get_url("service_datablocks", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def telephony_usage(self, service_id: int):
        """ Pulls the telephony usage associated with the service.

            Keys: `['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']`

            Example data:

            ```
            {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
            ```
            """
        url = self.get_url("telephony_usage", {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def support_tickets(self):
        """ Pulls the support tickets associated with the account, returns a list of dicts.

            Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`

            """
        url = self.get_url("support_tickets")
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def get_appointment(self, ticketid: int):
        """ Pulls the support tickets associated with the account, returns a list of dicts.

            Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`
            """
        url = self.get_url("get_appointment", {'ticketid' : ticketid})
        return await self.request_get_json(url=url)

    async def account_contacts(self):
        """ Pulls the contacts with the account, returns a list of dicts

            Dict keys: `['id', 'first_name', 'last_name', 'email', 'dog', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']`
            """
        url = self.get_url("account_contacts")
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata
