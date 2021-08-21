""" aiohttp support for AussieBB """


import asyncio
import json
from time import time

import sys
try:
    import aiohttp
except ImportError as error_message:
    print("Failed to import aiohttp, bailing: {error_message}", file=sys.stderr)
    sys.exit(1)

from ..const import BASEURL, default_headers, DEFAULT_BACKOFF_DELAY
from ..exceptions import AuthenticationException, RateLimitException, RecursiveDepth

class AussieBB(): #pylint: disable=too-many-public-methods
    """ aiohttp class for interacting with Aussie Broadband APIs """
    def __init__(self, username: str, password: str, session: aiohttp.client.ClientSession=None, debug: bool=False ):
        """ class for interacting with Aussie Broadband APIs """
        self.username = username
        self.password = password
        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")

        self.session = session

        self.myaussie_cookie = ""
        self.token_expires = -1
        self.debug = debug

    async def login(self, depth=0):
        """ does the login bit """
        if depth>2:
            raise RecursiveDepth("Login recursion depth > 2")
        print("logging in...")

        url = BASEURL.get('login')
        if self.session is None:
            self.session = aiohttp.ClientSession()

        if not self.has_token_expired():
            return True

        payload = {
            'username' : self.username,
            'password' : self.password,
            }
        headers = default_headers()

        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                await self.handle_response_fail(response)
                jsondata = await response.json()
            except RateLimitException:
                return await self.login(depth+1)
            if self.debug:
                print(f"Login response status: {response.status}", file=sys.stderr)
        if self.debug:
            print(f"Dumping login response: {json.dumps(jsondata)}", file=sys.stderr)
        self.token_expires = time() + jsondata.get('expiresIn') - 50
        self.myaussie_cookie = response.cookies.get('myaussie_cookie')
        if self.myaussie_cookie:
            if self.debug:
                print(f"Login Cookie: {self.myaussie_cookie}", file=sys.stderr)
        return True

    async def handle_response_fail(self, response, wait_on_rate_limit: bool=True):
        """ handles response status codes """
        ratelimit_remaining = int(response.headers.get('x-ratelimit-remaining', -1))
        if self.debug:
            print(f"Rate limit header: {response.headers.get('x-ratelimit-remaining', -1)}", file=sys.stderr)
        if ratelimit_remaining < 5 and wait_on_rate_limit:
            print("Rate limit below 5, sleeping for 1 second.", file=sys.stderr)
            asyncio.sleep(1)

        if response.status == 422:
            raise AuthenticationException(await response.json())
        if response.status == 429:
            jsondata = await response.json()
            if self.debug:
                print(f"Dumping headers: {response.headers}", file=sys.stderr)
                print(f"Dumping response: {jsondata}", file=sys.stderr)
            delay = DEFAULT_BACKOFF_DELAY
            if 'Please try again in ' in jsondata.get('errors'):
                delay = jsondata.get('errors').split()[-2]
                if int(delay) > 0 and int(delay) > 1000:
                    if self.debug:
                        print(f"Found delay: {delay}", file=sys.stderr)
                    delay = int(delay)
                elif self.debug:
                    print(f"Couldn't parse delay, using default: {delay}", file=sys.stderr)
            else:
                delay = DEFAULT_BACKOFF_DELAY
                if self.debug:
                    print(f"Couldn't parse delay, using default: {delay}", file=sys.stderr)
            if wait_on_rate_limit:
                print(f"Rate limit on Aussie API calls raised, sleeping for {delay} seconds.", file=sys.stderr)
                await asyncio.sleep(delay)
            raise RateLimitException(jsondata)
        response.raise_for_status()

    def has_token_expired(self):
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
            if self.debug:
                print("skip_login_check false", file=sys.stderr)
            if self.has_token_expired():
                if self.debug:
                    print("token has expired, logging in...", file=sys.stderr)
                self.login()

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
            if self.has_token_expired():
                if self.debug:
                    print("token has expired, logging in...", file=sys.stderr)
                self.login()

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
            if self.has_token_expired():
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
                jsondata = await self.request_post_json(url, depth=depth+1, **kwargs)
        return jsondata

    async def get_customer_details(self) -> dict:
        """ grabs the customer details, returns a dict """
        url = f"{BASEURL.get('api')}/customer"
        querystring = {"v":"2"}
        return await self.request_get_json(url=url,
                                    params=querystring,
                                    )

    async def get_services(self, page: int = 1):
        """ returns a list of dicts of services associated with the account """

        url = f"{BASEURL.get('api')}/services?page={page}"

        responsedata = await self.request_get_json(url=url)

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
        url = f"{BASEURL.get('api')}/billing/transactions?group=true"
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def billing_invoice(self, invoice_id):
        """ downloads an invoice

            this returns the response object
        """
        url = f"{BASEURL.get('api')}/billing/invoices/{invoice_id}"
        responsedata = await self.request_get(url=url)
        return responsedata

    async def account_paymentplans(self):
        """ returns a json blob of payment plans for an account """
        url = f"{BASEURL.get('api')}/billing/paymentplans"
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_usage(self, serviceid: int):
        """ returns a json blob of usage for a service """
        url = f"{BASEURL.get('api')}/broadband/{serviceid}/usage"
        responsedata = await self.request_get_json(url=url)
        return responsedata

    async def get_service_tests(self, serviceid: int):
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
            print(f"Getting service tests for {serviceid}", file=sys.stderr)
        url = f"{BASEURL.get('api')}/tests/{serviceid}/available"
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def get_test_history(self, serviceid: int):
        """ gets the available tests for a given service ID

        returns a list of dicts with tests which have been run
        """
        url = f"{BASEURL.get('api')}/tests/{serviceid}"
        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def test_line_state(self, serviceid: int):
        """ tests the line state for a given service ID """

        url = f"{BASEURL.get('api')}/tests/{serviceid}/linestate"
        if self.debug:
            print("Testing line state, can take a few seconds...")
        response = await self.request_post_json(url=url)
        if self.debug:
            print(f"Response: {response}", file=sys.stderr)
        return response

    async def run_test(self, serviceid: int, test_name: str, test_method: str = 'post'):
        """ run a test, but it checks it's valid first
            There doesn't seem to be a valid way to identify what method you're supposed to use on each test.
            See the README for more analysis

            - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
            - 'status' of 'Completed' means you've got the full response
        """

        service_tests = await self.get_service_tests(serviceid)
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

    async def service_plans(self, serviceid: int):
        """ pulls the JSON for the plan data
            keys: ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']
            """
        url = f"{BASEURL.get('api')}/planchange/{serviceid}"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_outages(self, serviceid: int):
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

        url = f"{BASEURL.get('api')}/nbn/{serviceid}/outages"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_boltons(self, serviceid: int):
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

        url = f"{BASEURL.get('api')}/nbn/{serviceid}/boltons"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def service_datablocks(self, serviceid: int):
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

        url = f"{BASEURL.get('api')}/nbn/{serviceid}/datablocks"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def support_tickets(self):
        """ pulls the support tickets associated with the account, returns a list of dicts
            dict keys: ['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']

            """

        url = f"{BASEURL.get('api')}/tickets"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata

    async def account_contacts(self):
        """ pulls the contacts with the account, returns a list of dicts
            dict keys: ['id', 'first_name', 'last_name', 'email', 'dog', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']
            """
        url = f"{BASEURL.get('api')}/contacts"

        responsedata = await self.request_get_json(url=url)
        if self.debug:
            print(responsedata, file=sys.stderr)
        return responsedata
