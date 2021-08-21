""" constants and utilities """

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
