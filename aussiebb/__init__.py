""" A class for interacting with Aussie Broadband APIs """

import inspect

import json
from time import time
import sys

from loguru import logger
import requests

from .const import BASEURL, API_ENDPOINTS, default_headers
from .exceptions import AuthenticationException, RateLimitException, RecursiveDepth
from .utils import get_url

#pylint: disable=too-many-public-methods,too-many-instance-attributes
class AussieBB():
    """ A class for interacting with Aussie Broadband APIs """
    def __init__(self, username: str, password: str, debug: bool=False, **kwargs):
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

        self.debug = debug
        # TODO: set the debug level in loguru when this is set to False

        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")
        self.session = requests.Session()

        self.myaussie_cookie = ""
        self.token_expires = -1

        self.services_cache_time = kwargs.get('services_cache_time', 28800) # defaults to 8 hours
        self.services_last_update = -1
        self.services = None

    def login(self, depth=0):
        """ Logs into the account and caches the cookie.  """
        if depth>2:
            raise RecursiveDepth("Login recursion depth > 2")
        logger.debug("Logging in...")

        url = BASEURL.get('login')

        payload = {
            'username' : self.username,
            'password' : self.password,
            }
        headers = default_headers()

        response = self.session.post(url,
                                     headers=headers,
                                     data=json.dumps(payload),
                                     )
        if response.status_code == 422:
            raise AuthenticationException(response.json())
        if response.status_code == 429:
            raise RateLimitException(response.json())
        response.raise_for_status()

        jsondata = response.json()

        # we expire a little early just because
        self.token_expires = time() + jsondata.get('expiresIn') - 50

        self.myaussie_cookie = response.cookies.get('myaussie_cookie')
        if self.myaussie_cookie:
            logger.debug(f"Login Cookie: {self.myaussie_cookie}")
        return True

    def _has_token_expired(self):
        """ Returns bool of if the token has expired """
        if time() > self.token_expires:
            return True
        return False

    def request_get(self, skip_login_check: bool = False, **kwargs):
        """ Performs a GET request and logs in first if needed.

        Returns the `requests.Response` object."""
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self._has_token_expired():
                logger.debug("token has expired, logging in...")
                self.login()
        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        response = self.session.get(**kwargs)
        response.raise_for_status()
        return response

    def request_get_json(self, skip_login_check: bool = False, **kwargs):
        """ Performs a GET request and logs in first if needed.

        Returns a dict of the JSON response.
        """
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self._has_token_expired():
                logger.debug("token has expired, logging in...")
                self.login()
        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        response = self.session.get(**kwargs)
        response.raise_for_status()
        return response.json()

    def request_post(self, skip_login_check: bool = False, **kwargs):
        """ Performs a POST request and logs in first if needed."""
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self._has_token_expired():
                logger.debug("token has expired, logging in...")
                self.login()
        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        if 'headers' not in kwargs:
            kwargs['headers'] = default_headers()
        response = self.session.post(**kwargs)
        response.raise_for_status()
        return response

    def get_customer_details(self):
        """ Grabs the customer details.

        Returns a dict """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        querystring = {"v":"2"}
        responsedata = self.request_get_json(url=url,
                                    params=querystring,
                                    )
        return responsedata


    def _check_reload_cached_services(self):
        """ If the age of the service data caching is too old, clear it and re-poll.

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


    def get_services(self, page: int = 1, servicetypes: list=None, use_cached: bool=False):
        """ Returns a `list` of `dicts` of services associated with the account.

            If you want a specific kind of service, or services,
            provide a list of matching strings in servicetypes.

            If you want to use cached data, call it with `use_cached=True`
        """
        if use_cached:
            logger.debug("Using cached data for get_services.")
            self._check_reload_cached_services()
        else:
            frame = inspect.currentframe()
            url = get_url(inspect.getframeinfo(frame).function)
            querystring = {'page' : page}

            responsedata = self.request_get_json(url=url, params=querystring)
            # cache the data
            self.services_last_update = time()
            self.services = responsedata.get('data')

        # only filter if we need to
        if servicetypes:
            logger.debug("Filtering services based on provided list: {}", servicetypes)
            filtered_responsedata = []
            for service in self.services:
                if service.get('type') in servicetypes:
                    filtered_responsedata.append(service)
                else:
                    logger.debug("Skipping as type=={} - {}", service.get('type'), service)
            return filtered_responsedata

        return self.services


    def account_transactions(self):
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
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)


    def billing_invoice(self, invoice_id):
        """ Downloads an invoice

            This returns the bare response object, parsing the result is an exercise for the consumer. It's a PDF file.
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'invoice_id' : invoice_id})
        return self.request_get_json(url=url)

    def account_paymentplans(self):
        """ Returns a dict of payment plans for an account """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)


    def get_usage(self, service_id: int):
        """
        Returns a dict of usage for a service.

        If it's a telephony service (`type=PhoneMobile`) it'll pull from the telephony endpoint.

        """

        if not self.services:
            self.get_services(use_cached=True)
        for service in self.services:
            if service_id == service.get('service_id'):
                if service.get('type') in ['PhoneMobile']:
                    return self.telephony_usage(service_id)
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def get_service_tests(self, service_id: int):
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
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def get_test_history(self, service_id: int):
        """ Gets the available tests for a given service ID

        Returns a list of dicts with tests which have been run
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def test_line_state(self, service_id: int):
        """ Tests the line state for a given service ID """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        logger.debug("Testing line state, can take a few seconds...")
        response = self.request_post(url=url)
        return response.json()

    def run_test(self, service_id: int, test_name: str, test_method: str = 'post'):
        """ Run a test, but it checks it's valid first

            There doesn't seem to be a valid way to identify what method you're supposed to use on each test.

            See the README for more analysis

            - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
            - 'status' of 'Completed' means you've got the full response
        """

        test_links = [test for test in self.get_service_tests(service_id) if test.get('link', '').endswith(f'/{test_name}')] #pylint: disable=line-too-long

        if not test_links:
            return False
        if len(test_links) != 1:
            logger.debug(f"Too many tests? {test_links}")

        test_name = test_links[0].get('name')
        logger.debug(f"Running {test_name}")
        if test_method == 'get':
            return self.request_get_json(url=test_links[0].get('link'))
        return self.request_post(url=test_links[0].get('link')).json()

    def service_plans(self, service_id: int):
        """ Pulls the plan data for a given service.

            Keys: `['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']`

        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def service_outages(self, service_id: int):
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
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def service_boltons(self, service_id: int):
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
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def service_datablocks(self, service_id: int):
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
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def telephony_usage(self, service_id: int):
        """ Pulls the telephony usage associated with the service.

            Keys: `['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']`

            Example data:

            ```
            {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
            ```
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def support_tickets(self):
        """ Pulls the support tickets associated with the account, returns a list of dicts.

            Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`

            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)

    def get_appointment(self, ticketid: int):
        """ Pulls the support tickets associated with the account, returns a list of dicts.

            Dict keys: `['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']`
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'ticketid' : ticketid})
        return self.request_get_json(url=url)


    def account_contacts(self):
        """ Pulls the contacts with the account, returns a list of dicts

            Dict keys: `['id', 'first_name', 'last_name', 'email', 'dog', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']`
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)
