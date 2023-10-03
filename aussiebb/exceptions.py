""" exceptions for the AussieBB module """


class InvalidTestForService(BaseException):
    """user specified an invalid test"""


class AuthenticationException(BaseException):
    """authentication error for AussieBB"""


class DeprecatedCall(BaseException):
    """Can't use this anymore"""


class RateLimitException(BaseException):
    """rate limit error for AussieBB"""


class RecursiveDepth(BaseException):
    """you've gone too far down the rabbit hole"""


class UnrecognisedServiceType(BaseException):
    """You've got a service type we haven't seen before"""


class NoMoreData(BaseException):
    """There's no more data to pull"""
