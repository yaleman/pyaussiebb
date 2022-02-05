""" base class def """

from http.cookies import Morsel
import logging
from time import time
from typing import Any, Dict, Optional

from .const import API_ENDPOINTS, BASEURL, PHONE_TYPES, NBN_TYPES
from .exceptions import AuthenticationException, RateLimitException, UnrecognisedServiceType

class BaseClass:
    """ Base class for aussiebb API clients """

    API_ENDPOINTS = API_ENDPOINTS
    BASEURL = BASEURL

    def __init__(
        self,
        username: str,
        password: str,
        debug: bool = False,
        services_cache_time: int = 28800,
        logger = None
        ):


        if not (username and password):
            raise AuthenticationException("You need to supply both username and password")

        self.myaussie_cookie: Optional[Morsel] = None
        self.token_expires = -1

        self.services_cache_time = services_cache_time # defaults to 8 hours
        self.services_last_update = -1
        self.services = None
        self.username = username
        self.password = password

        if not logger:
            self.logger = logging.getLogger()
        self.debug = debug


    def get_url(self, function_name: str, data: dict=None):
        """ gets the URL based on the data/function """
        if function_name not in self.API_ENDPOINTS:
            raise ValueError(f"Function name {function_name} not found, cannot find URL")
        if data:
            api_endpoint = self.API_ENDPOINTS[function_name].format(**data)
        else:
            api_endpoint = self.API_ENDPOINTS[function_name]

        return f"{self.BASEURL.get('api')}{api_endpoint}"

    def _has_token_expired(self):
        """ Returns bool of if the token has expired """
        if time() > self.token_expires:
            return True
        return False

    def _handle_login_response(
        self,
        status_code: int,
        jsondata: Dict[str, Any],
        cookies: Dict[str, Morsel],
        ) -> bool:
        """ handles the login response we expire a little early just because, and if we don't get an expiry, we just bail """

        # just reset it in case
        self.token_expires = -1
        self.myaussie_cookie = None
        if status_code == 422:
            raise AuthenticationException(jsondata)
        if status_code == 429:
            raise RateLimitException(jsondata)

        if "expiresIn" not in jsondata:
            return False

        if "myaussie_cookie" not in cookies or str(cookies["myaussie_cookie"]).strip() == "":
            return False

        self.token_expires = time() + jsondata.get('expiresIn', 0) - 50
        self.myaussie_cookie = cookies["myaussie_cookie"]
        self.logger.debug("Login Cookie: %s", self.myaussie_cookie)
        return True

    @classmethod
    def validate_service_type(cls, service: Dict[str, Any]):
        """ Check the service types against known types """
        if "type" not in service:
            raise ValueError("field 'type' not found in service data")
        if service["type"] not in NBN_TYPES + PHONE_TYPES:
            raise UnrecognisedServiceType(f"Service type {service['type']} not recognised - please raise an issue about this - https://github.com/yaleman/aussiebb/issues/new")
