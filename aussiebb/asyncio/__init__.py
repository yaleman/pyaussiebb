""" aiohttp support for AussieBB """


import asyncio

import inspect
import json
from time import time

import sys
try:
    import aiohttp
except ImportError as error_message:
    print(f"Failed to import aiohttp, bailing: {error_message}", file=sys.stderr)
    sys.exit(1)

from ..const import BASEURL, default_headers, DEFAULT_BACKOFF_DELAY
from ..exceptions import AuthenticationException, RateLimitException, RecursiveDepth
from ..utils import get_url


class AussieBB(): #pylint: disable=too-many-public-methods
    """ aiohttp class for interacting with Aussie Broadband APIs """
    def __init__(self, username: str, password: str, session: aiohttp.client.ClientSession=None, debug: bool=False, **kwargs):
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
        self.username = username
        self.password = password
        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")

        if not session:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

        self.myaussie_cookie = ""
        self.token_expires = -1
        self.debug = debug

        self.services_cache_time = kwargs.get('services_cache_time', 28800) # defaults to 8 hours
        self.services_last_update = -1
        self.services = None


    def _debug_print(self, message: str):
        """ Prints a debug message to stderr if the class is in debug mode. """
        if self.debug:
            print(message, file=sys.stderr)

    async def _check_reload_cached_services(self):
        """ If the age of the service data caching is too old, clear it and re-poll """
        cache_expiry = self.services_last_update + self.services_cache_time
        if time() > cache_expiry:
            await self.get_services(use_cached=False)
        return True

    async def login(self, depth=0):
        """ Logs into the account and caches the cookie.  """
        if depth>2:
            raise RecursiveDepth("Login recursion depth > 2")
        self._debug_print("Logging in...")

        url = BASEURL.get('login')

        if not self._has_token_expired():
            return True

        payload = {
            'username' : self.username,
            'password' : self.password,
            }
        headers = default_headers()

        async with self.session.post(url=url, headers=headers, json=payload) as response:
            try:
                await self.handle_response_fail(response)
                jsondata = await response.json()
            except RateLimitException:
                return await self.login(depth+1)
            self._debug_print(f"Login response status: {response.status}")
        self._debug_print(f"Dumping login response: {json.dumps(jsondata)}")

        # we expire a little early just because
        self.token_expires = time() + jsondata.get('expiresIn') - 50
        self.myaussie_cookie = response.cookies.get('myaussie_cookie')
        if self.myaussie_cookie:
            self._debug_print(f"Login Cookie: {self.myaussie_cookie}")
        return True

    async def handle_response_fail(self, response, wait_on_rate_limit: bool=True):
        """ handles response status codes """
        ratelimit_remaining = int(response.headers.get('x-ratelimit-remaining', -1))
        self._debug_print(f"Rate limit header: {response.headers.get('x-ratelimit-remaining', -1)}")
        if ratelimit_remaining < 5 and wait_on_rate_limit:
            print("Rate limit below 5, sleeping for 1 second.", file=sys.stderr)
            await asyncio.sleep(1)

        if response.status == 422:
            raise AuthenticationException(await response.json())
        if response.status == 429:
            jsondata = await response.json()
            self._debug_print(f"Dumping headers: {response.headers}")
            self._debug_print(f"Dumping response: {jsondata}")
            delay = DEFAULT_BACKOFF_DELAY
            if 'Please try again in ' in str(jsondata.get('errors')):
                fallback_value = [f"default {DEFAULT_BACKOFF_DELAY} seconds"]
                delay = jsondata.get('errors', {}).get('username', fallback_value)[0].split()[-2]
                # give it some extra time to cool off
                delay = int(delay)+5

                if 0 < delay < 1000:
                    self._debug_print(f"Found delay: {delay}")
                    delay = int(delay)
                else:
                    self._debug_print(f"Couldn't parse delay, using default: {delay}")
            else:
                delay = DEFAULT_BACKOFF_DELAY
                if self.debug:
                    print(f"Couldn't parse delay, using default: {delay}", file=sys.stderr)
            if wait_on_rate_limit:
                print(f"Rate limit on Aussie API calls raised, sleeping for {delay} seconds.", file=sys.stderr)
                await asyncio.sleep(delay)
            raise RateLimitException(jsondata)
        response.raise_for_status()

    def _has_token_expired(self):
        """ returns bool if the token has expired """
        if time() > self.token_expires:
            return True
        return False

    async def request_get(self, skip_login_check: bool = False, **kwargs) -> dict:
        """ does a GET request and logs in first if need be, returns the body bytes """
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        if not skip_login_check:
            if self._has_token_expired():
                if self.debug:
                    print("token has expired, logging in...", file=sys.stderr)
                await self.login()

        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        async with self.session.get(**kwargs) as response:
            try:
                await self.handle_response_fail(response)
                await response.read()
            except RateLimitException:
                response = await self.request_get_json(skip_login_check, **kwargs)
            return response

    async def request_get_json(self, skip_login_check: bool = False, **kwargs) -> dict:
        """ does a GET request and logs in first if need be, returns a dict of json """
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        if not skip_login_check:
            if self.debug:
                print("skip_login_check false", file=sys.stderr)
            if self._has_token_expired():
                if self.debug:
                    print("token has expired, logging in...", file=sys.stderr)
                await self.login()

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
        """ does a POST request and logs in first if need be"""
        depth = kwargs.get('depth', 0)
        if depth > 2:
            raise RecursiveDepth(f"depth: {depth}")

        if self.session is None:
            self.session = aiohttp.ClientSession()

        if not kwargs.get('skip_login_check', False):
            if self.debug:
                print("skip_login_check false", file=sys.stderr)
            if self._has_token_expired():
                if self.debug:
                    print("token has expired, logging in...", file=sys.stderr)
                await self.login()

        #if 'cookies' not in kwargs:
        #    kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
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
        """ grabs the customer details, returns a dict """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        params = {"v":"2"}
        return await self.request_get_json(url=url,
                                    params=params,
                                    )

    async def get_services(self, page: int=1, servicetypes: list=None, use_cached: bool=False):
        """ Returns a `list` of `dicts` of services associated with the account.

            If you want a specific kind of service, or services,
            provide a list of matching strings in servicetypes.

            If you want to use cached data, call it with `use_cached=True`
        """
        if use_cached:
            self._check_reload_cached_services()
            responsedata = self.services
        else:
            frame = inspect.currentframe()
            url = get_url(inspect.getframeinfo(frame).function)
            params = {'page' : page}

            responsedata = await self.request_get_json(url=url, params=params)
            # cache the data
            self.services_last_update = time()
            self.services = responsedata.get('data')

        # only filter if we need to
        if servicetypes:
            if self.debug:
                print(f"Filtering services based on provided list: {servicetypes}", file=sys.stderr)
            filtered_responsedata = []
            for service in responsedata.get('data'):
                if service.get('type') in servicetypes:
                    filtered_responsedata.append(service)
                else:
                    if self.debug:
                        print(f"Skipping as type=={service.get('type')} - {service}", file=sys.stderr)
            # return the filtered responses to the source data
            responsedata['data'] = filtered_responsedata

        if responsedata.get('last_page') != responsedata.get('current_page'):
            if self.debug:
                print("You've got a lot of services - please contact the package maintainer to test the multi-page functionality!", file=sys.stderr) #pylint: disable=line-too-long
        return responsedata.get('data')

    async def account_transactions(self):
        """ pulls the json for transactions on your account
            keys: ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']
            returns a dict where the key is the Month and year of the transaction, eg:
            ```
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
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def billing_invoice(self, invoice_id):
        """ downloads an invoice

            this returns the response object
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'invoice_id', invoice_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def account_paymentplans(self):
        """ returns a json blob of payment plans for an account """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_usage(self, service_id: int):
        """
        Returns a dict of usage for a service.

        If it's a telephony service (`type=PhoneMobile`) it'll pull from the telephony endpoint.

        """
        services = await self.get_services(use_cached=True)
        for service in services:
            if service_id == service.get('service_id'):
                if service.get('type') in ['PhoneMobile']:
                    return await self.telephony_usage(service_id)

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_service_tests(self, service_id: int):
        """ gets the available tests for a given service ID
        returns list of dicts
        [{
            'name' : str(),
            'description' : str',
            'link' : str(a url to the test)
        },]

        this is known to throw 400 errors if you query a VOIP service...
        """
        if self.debug:
            print(f"Getting service tests for {service_id}", file=sys.stderr)
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_test_history(self, service_id: int):
        """ gets the available tests for a given service ID

        returns a list of dicts with tests which have been run
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def test_line_state(self, service_id: int):
        """ tests the line state for a given service ID """

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})

        if self.debug:
            print("Testing line state, can take a few seconds...")
        response = await self.request_post_json(url=url)
        if self.debug:
            print(f"Response: {response}", file=sys.stderr)
        return response

    async def run_test(self, service_id: int, test_name: str, test_method: str = 'post'):
        """ run a test, but it checks it's valid first
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

        test_name = test_links[0].get('name')
        if self.debug:
            print(f"Running {test_name}", file=sys.stderr)
        if test_method == 'get':
            result = await self.request_get_json(url=test_links[0].get('link'))
        else:
            result = await self.request_post_json(url=test_links[0].get('link'))
        return result

    async def service_plans(self, service_id: int):
        """ pulls the JSON for the plan data
            keys: ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']
            """

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_outages(self, service_id: int):
        """ pulls the JSON for outages
            keys: ['networkEvents', 'aussieOutages', 'currentNbnOutages', 'scheduledNbnOutages', 'resolvedScheduledNbnOutages', 'resolvedNbnOutages']

            example data
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

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_boltons(self, service_id: int):
        """ pulls the JSON for addons associated with the service
            keys: ['id', 'name', 'description', 'costCents', 'additionalNote', 'active']

            example data
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

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_datablocks(self, service_id: int):
        """ pulls the JSON for datablocks associated with the service
            keys: ['current', 'available']

            example data
            ```
            {
                "current": [],
                "available": []
            }
            ```
            """

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def telephony_usage(self, service_id: int):
        """ pulls the JSON for telephony usage associated with the service
            keys: ['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']

            example data
            ```
            {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
            ```
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def support_tickets(self):
        """ pulls the support tickets associated with the account, returns a list of dicts
            dict keys: ['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']

            """

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def account_contacts(self):
        """ pulls the contacts with the account, returns a list of dicts
            dict keys: ['id', 'first_name', 'last_name', 'email', 'dog', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata
