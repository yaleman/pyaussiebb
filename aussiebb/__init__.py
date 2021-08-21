""" class for interacting with Aussie Broadband APIs """

import json
from time import time

from loguru import logger
import requests

from .const import BASEURL, default_headers
from .exceptions import AuthenticationException, RateLimitException

class AussieBB():
    """ class for interacting with Aussie Broadband APIs """
    def __init__(self, username: str, password: str):
        """ class for interacting with Aussie Broadband APIs """
        self.username = username
        self.password = password
        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")

        self.session = requests.Session()

        self.token_expires = -1
        self.login()

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
        url = f"{BASEURL.get('api')}/customer"
        querystring = {"v":"2"}
        response = self.request_get(url=url,
                                    params=querystring,
                                    )
        return response.json()

    def get_services(self, page: int = 1):
        """ returns a list of dicts of services associated with the account """

        url = f"{BASEURL.get('api')}/services?page={page}"

        response = self.request_get(url=url)

        responsedata = response.json()
        if responsedata.get('last_page') != responsedata.get('current_page'):
            logger.debug("You've got a lot of services - please contact the package maintainer to test the multi-page functionality!") #pylint: disable=line-too-long
        return responsedata.get('data')

    def get_usage(self, serviceid: int):
        """ returns a json blob of usage for a service """
        url = f"{BASEURL.get('api')}/broadband/{serviceid}/usage"
        response = self.request_get(url=url)
        responsedata = response.json()
        logger.debug(responsedata)
        return responsedata

    def get_service_tests(self, serviceid: int):
        """ gets the available tests for a given service ID
        returns list of dicts
        [{
            'name' : str(),
            'description' : str',
            'link' : str(a url to the test)
        },]

        this is known to throw 400 errors if you query a VOIP service...
        """
        logger.debug(f"Getting service tests for {serviceid}")
        url = f"{BASEURL.get('api')}/tests/{serviceid}/available"
        response = self.request_get(url=url)
        responsedata = response.json()
        logger.debug(responsedata)
        return responsedata

    def get_test_history(self, serviceid: int):
        """ gets the available tests for a given service ID

        returns a list of dicts with tests which have been run
        """
        url = f"{BASEURL.get('api')}/tests/{serviceid}"
        response = self.request_get(url=url)
        responsedata = response.json()
        logger.debug(responsedata)
        return responsedata

    def test_line_state(self, serviceid: int):
        """ tests the line state for a given service ID """

        url = f"{BASEURL.get('api')}/tests/{serviceid}/linestate"
        logger.debug("Testing line state, can take a few seconds...")
        response = self.request_post(url=url)
        logger.debug(f"Response: {response}")
        logger.debug(f"Response body: {response.text}")
        logger.debug(f"Response headers: {response.headers}")
        return response.json()

    def run_test(self, serviceid: int, test_name: str, test_method: str = 'post'):
        """ run a test, but it checks it's valid first
            There doesn't seem to be a valid way to identify what method you're supposed to use on each test.
            See the README for more analysis

            - 'status' of 'InProgress' use 'AussieBB.get_test_history()' and look for the 'id'
            - 'status' of 'Completed' means you've got the full response
        """

        test_links = [test for test in self.get_service_tests(serviceid) if test.get('link', '').endswith(f'/{test_name}')] #pylint: disable=line-too-long

        if not test_links:
            return False
        if len(test_links) != 1:
            logger.debug(f"Too many tests? {test_links}")

        test_name = test_links[0].get('name')
        logger.debug(f"Running {test_name}")
        if test_method == 'get':
            return self.request_get(url=test_links[0].get('link')).json()
        return self.request_post(url=test_links[0].get('link')).json()

    def get_service_plans(self, serviceid: int):
        """ pulls the JSON for the plan data
            keys: ['current', 'pending', 'available', 'filters', 'typicalEveningSpeeds']
            """
        url = f"{BASEURL.get('api')}/planchange/{serviceid}"

        response = self.request_get(url=url)

        return response.json()
