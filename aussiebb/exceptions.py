""" exceptions for the AussieBB module """

class InvalidTestForService(BaseException):
    """ user specified an invalid test """

class AuthenticationException(BaseException):
    """ authentication error for AussieBB """

class RateLimitException(BaseException):
    """ rate limit error for AussieBB """

class RecursiveDepth(BaseException):
    """ you've gone too far down the rabbit hole """
