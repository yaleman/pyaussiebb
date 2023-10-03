""" base class def """

from http.cookies import SimpleCookie, Morsel
import logging
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import SecretStr

from requests.cookies import RequestsCookieJar

from .const import (
    API_ENDPOINTS,
    BASEURL,
    HARDWARE_TYPES,
    PHONE_TYPES,
    NBN_TYPES,
    FETCH_TYPES,
    USAGE_ENABLED_SERVICE_TYPES,
)
from .types import GetServicesResponse, ServiceTest
from .exceptions import (
    AuthenticationException,
    InvalidTestForService,
    RateLimitException,
    UnrecognisedServiceType,
)


class BaseClass:
    """Base class for aussiebb API clients"""

    API_ENDPOINTS = API_ENDPOINTS
    BASEURL = BASEURL

    def __init__(
        self,
        username: str,
        password: SecretStr,
        debug: bool = False,
        services_cache_time: int = 28800,
        logger: logging.Logger = logging.getLogger(),
    ):
        if not (username and password):
            raise AuthenticationException(
                "You need to supply both username and password"
            )

        self.myaussie_cookie: Optional[Union[Morsel[Any], SimpleCookie[Any]]] = None
        self.token_expires = -1

        self.services_cache_time = services_cache_time  # defaults to 8 hours
        self.services_last_update = -1
        self.services: List[Dict[str, Any]] = []
        self.username = username
        self.password = password
        self.logger = logger
        self.debug = debug

    def __str__(self) -> str:
        """string repr of account - returns username"""
        return self.username

    def get_url(self, function_name: str, data: Optional[Dict[str, Any]] = None) -> str:
        """gets the URL based on the data/function"""
        if function_name not in self.API_ENDPOINTS:
            raise ValueError(
                f"Function name {function_name} not found, cannot find URL"
            )
        if data:
            api_endpoint = self.API_ENDPOINTS[function_name].format(**data)
        else:
            api_endpoint = self.API_ENDPOINTS[function_name]

        return f"{self.BASEURL.get('api')}{api_endpoint}"

    def _has_token_expired(self) -> bool:
        """Returns bool of if the token has expired"""
        if time() > self.token_expires:
            return True
        return False

    def _handle_login_response(
        self,
        status_code: int,
        jsondata: Dict[str, Any],
        cookies: Union[RequestsCookieJar, SimpleCookie[Any]],
    ) -> bool:
        """Handles the login response.

        We expire the session a little early just to be safe, and if we don't get an expiry, we just bail.
        """

        # just reset it in case
        self.token_expires = -1
        self.myaussie_cookie = None
        if status_code == 422:
            raise AuthenticationException(jsondata)
        if status_code == 429:
            raise RateLimitException(jsondata)

        # expected response from the API looks like
        # data: { "expiresIn" : 500 }
        # cookies:  { "myaussie_cookie" : "somerandomcookiethings" }

        if "expiresIn" not in jsondata:
            return False

        if (
            "myaussie_cookie" not in cookies
            or str(cookies["myaussie_cookie"]).strip() == ""
        ):
            return False

        self.token_expires = time() + jsondata.get("expiresIn", 0) - 50
        self.myaussie_cookie = cookies["myaussie_cookie"]
        self.logger.debug("Login Cookie: %s", self.myaussie_cookie)
        return True

    @classmethod
    def validate_service_type(cls, service: Dict[str, Any]) -> None:
        """Check the service types against known types"""
        if "type" not in service:
            raise ValueError("Field 'type' not found in service data")
        if service["type"] not in USAGE_ENABLED_SERVICE_TYPES + HARDWARE_TYPES:
            raise UnrecognisedServiceType(
                f"Service type {service['type']=} {service['name']=} -  not recognised - please raise an issue about this - https://github.com/yaleman/aussiebb/issues/new"
            )

    def filter_services(
        self,
        service_types: Optional[List[str]] = None,
        drop_types: Optional[List[str]] = None,
        drop_unknown_types: bool = False,
    ) -> List[Dict[str, Any]]:
        """filter services"""

        if drop_types is None:
            drop_types = []

        self.logger.debug(
            f"Filtering services {self.services=} {service_types=} {drop_types=}"
        )
        filtered_responsedata: List[Dict[str, Any]] = []
        if self.services is not None:
            for service in self.services:
                if "type" not in service:
                    raise ValueError(f"No type field in service info: {service}")
                if service["type"] in drop_types:
                    continue
                if service_types is None or service["type"] in service_types:
                    filtered_responsedata.append(service)
                else:
                    self.logger.debug(
                        "Skipping as type==%s - %s", service["type"], service
                    )
            # skip things we don't know about
            if drop_unknown_types:
                filtered_responsedata = [
                    service
                    for service in filtered_responsedata
                    if service["type"] in FETCH_TYPES + NBN_TYPES + PHONE_TYPES
                ]
            return filtered_responsedata
        return []

    @classmethod
    def is_valid_test(cls, test_url: str, service_tests: List[ServiceTest]) -> bool:
        """pass it the service test url and the list of service tests and it'll give you a bool or raise an InvalidTestForService exception if not"""

        test_is_valid = False
        for test in service_tests:
            if test.link == test_url:
                test_is_valid = True

        if not test_is_valid:
            raise InvalidTestForService(
                "You can't check line state, test not available!"
            )
        return test_is_valid

    @classmethod
    def handle_services_response(
        cls,
        responsedata: Dict[str, Any],
        services_list: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], int, List[Dict[str, Any]]]:
        """handle the response, parse the JSON and update the services list"""
        servicedata = GetServicesResponse.model_validate(responsedata)

        for service in servicedata.data:
            services_list.append(service)

        return (
            servicedata.links.next,  # url
            servicedata.meta["current_page"],  # page
            services_list,
        )
