""" class for interacting with Aussie Broadband APIs """

import inspect

import json
from time import time
import sys

from loguru import logger
import requests

from .const import BASEURL, API_ENDPOINTS, default_headers
from .exceptions import AuthenticationException, RateLimitException
from .utils import get_url

#pylint: disable=too-many-public-methods
class AussieBB():
    """ class for interacting with Aussie Broadband APIs """
    def __init__(self, username: str, password: str, debug: bool=False):
        """ class for interacting with Aussie Broadband APIs """
        self.username = username
        self.password = password

        self.debug = debug
        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")
        self.session = requests.Session()

        self.myaussie_cookie = ""
        self.token_expires = -1

    def login(self):
        """ does the login bit """
        logger.debug("logging in...")
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
        self.token_expires = time() + jsondata.get('expiresIn') - 50
        self.myaussie_cookie = response.cookies.get('myaussie_cookie')
        if self.myaussie_cookie:
            logger.debug(f"Login Cookie: {self.myaussie_cookie}")
        return True

    def has_token_expired(self):
        """ returns bool if the token has expired """
        if time() > self.token_expires:
            return True
        return False

    def request_get(self, skip_login_check: bool = False, **kwargs):
        """ does a GET request and logs in first if need be"""
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self.has_token_expired():
                logger.debug("token has expired, logging in...")
                self.login()
        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        response = self.session.get(**kwargs)
        response.raise_for_status()
        return response

    def request_get_json(self, skip_login_check: bool = False, **kwargs):
        """ does a GET request and logs in first if need be, returns the JSON dict """
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self.has_token_expired():
                logger.debug("token has expired, logging in...")
                self.login()
        if 'cookies' not in kwargs:
            kwargs['cookies'] = {'myaussie_cookie' : self.myaussie_cookie}
        response = self.session.get(**kwargs)
        response.raise_for_status()
        return response.json()

    def request_post(self, skip_login_check: bool = False, **kwargs):
        """ does a POST request and logs in first if need be"""
        if not skip_login_check:
            logger.debug("skip_login_check false")
            if self.has_token_expired():
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
        """ grabs the customer details """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        querystring = {"v":"2"}
        responsedata = self.request_get_json(url=url,
                                    params=querystring,
                                    )
        return responsedata

    def get_services(self, page: int = 1, servicetypes: list=None):
        """ returns a list of dicts of services associated with the account

            if you want a specific kind of service, or services,
            provide a list of matching strings in servicetypes
        """

        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        querystring = {'page' : page}
        responsedata = self.request_get_json(url=url, params=querystring)

        # only filter if we need to
        if servicetypes and responsedata:
            logger.debug("Filtering services based on provided list: {}", servicetypes)
            filtered_responsedata = []
            for service in responsedata.get('data'):
                if service.get('type') in servicetypes:
                    filtered_responsedata.append(service)
                else:
                    logger.debug("Skipping as type=={} - {}", service.get('type'), service)
            # return the filtered responses to the source data
            responsedata['data'] = filtered_responsedata

        if responsedata.get('last_page') != responsedata.get('current_page'):
            logger.debug("You've got a lot of services - please contact the package maintainer to test the multi-page functionality!") #pylint: disable=line-too-long
        return responsedata.get('data')


    def account_transactions(self):
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
        return self.request_get_json(url=url)


    def billing_invoice(self, invoice_id):
        """ downloads an invoice

            this returns the bare response object, parsing the result is an exercise for the consumer
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'invoice_id' : invoice_id})
        return self.request_get_json(url=url)

    def account_paymentplans(self):
        """ returns a json blob of payment plans for an account """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)

    def get_usage(self, service_id: int):
        """ returns a json blob of usage for a service """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def get_service_tests(self, service_id: int):
        """ gets the available tests for a given service ID
        returns list of dicts
        [{
            'name' : str(),
            'description' : str',
            'link' : str(a url to the test)
        },]

        this is known to throw 400 errors if you query a VOIP service...
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def get_test_history(self, service_id: int):
        """ gets the available tests for a given service ID

        returns a list of dicts with tests which have been run
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def test_line_state(self, service_id: int):
        """ tests the line state for a given service ID """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        logger.debug("Testing line state, can take a few seconds...")
        response = self.request_post(url=url)
        return response.json()

    def run_test(self, service_id: int, test_name: str, test_method: str = 'post'):
        """ run a test, but it checks it's valid first
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
        """ pulls the JSON for the plan data
            keys: ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def service_outages(self, service_id: int):
        """ pulls the JSON for outages
            keys: ['networkEvents', 'aussieOutages', 'currentNbnOutages', 'scheduledNbnOutages', 'resolvedScheduledNbnOutages', 'resolvedNbnOutages']
        """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def service_boltons(self, service_id: int):
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
        return self.request_get_json(url=url)

    def service_datablocks(self, service_id: int):
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
        return self.request_get_json(url=url)

    def telephony_usage(self, service_id: int):
        """ pulls the JSON for telephony usage associated with the service
            keys: ['national', 'mobile', 'international', 'sms', 'internet', 'voicemail', 'other', 'daysTotal', 'daysRemaining', 'historical']

            example data
            ```
            {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
            ```
            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'service_id' : service_id})
        return self.request_get_json(url=url)

    def support_tickets(self):
        """ pulls the support tickets associated with the account, returns a list of dicts
            dict keys: ['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']

            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)

    def get_appointment(self, ticketid):
        """ pulls the support tickets associated with the account, returns a list of dicts
            dict keys: ['ref', 'create', 'updated', 'service_id', 'type', 'subject', 'status', 'closed', 'awaiting_customer_reply', 'expected_response_minutes']

            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function, {'ticketid' : ticketid})
        return self.request_get_json(url=url)


    def account_contacts(self):
        """ pulls the contacts with the account, returns a list of dicts
            dict keys: ['id', 'first_name', 'last_name', 'email', 'dog', 'home_phone', 'work_phone', 'mobile_phone', 'work_mobile', 'primary_contact']

            """
        frame = inspect.currentframe()
        url = get_url(inspect.getframeinfo(frame).function)
        return self.request_get_json(url=url)
