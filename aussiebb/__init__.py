""" class for interacting with Aussie Broadband APIs """

import json
from time import time

from loguru import logger
import requests

BASEURL = {
    'api' : 'https://myaussie-api.aussiebroadband.com.au',
    'login' : "https://myaussie-auth.aussiebroadband.com.au/login"
}

def default_headers():
    """ returns a default set of headers """
    return {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Origin': "https://my.aussiebroadband.com.au",
        'Referer': "https://my.aussiebroadband.com.au/",
        'cache-control': "no-cache",
    }

class AussieBB():
    """ class for interacting with Aussie Broadband APIs """
    def __init__(self, username, password):
        """ class for interacting with Aussie Broadband APIs """
        self.username = username
        self.password = password

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


    def request_get(self, skip_login_check=False, **kwargs):
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

    def request_post(self, skip_login_check=False, **kwargs):
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

    def get_services(self, page=1):
        """ returns a list of dicts of services associated with the account """

        url = f"{BASEURL.get('api')}/services?page={page}"

        response = self.request_get(url=url)

        responsedata = response.json()
        if responsedata.get('last_page') != responsedata.get('current_page'):
            logger.debug("You've got a lot of services - please contact the package maintainer to test the multi-page functionality!") #pylint: disable=line-too-long
        return responsedata.get('data')

    def test_line_state(self, serviceid):
        """ tests the line state for a given service ID """

        url = f"{BASEURL.get('api')}/tests/{serviceid}/linestate"
        logger.debug("Testing line state, can take a few seconds...")
        response = self.request_post(url=url)
        logger.debug(f"Response: {response}")
        logger.debug(f"Response body: {response.text}")
        logger.debug(f"Response headers: {response.headers}")
        return response.json()
