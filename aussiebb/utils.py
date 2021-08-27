""" shared utility functions """

from .const import API_ENDPOINTS, BASEURL

def get_url(function: str, data: dict=None):
    """ gets the URL based on the data/function """
    if data:
        api_endpoint = API_ENDPOINTS.get(function).format(**data)
    else:
        api_endpoint = API_ENDPOINTS.get(function)

    return f"{BASEURL.get('api')}{api_endpoint}"
