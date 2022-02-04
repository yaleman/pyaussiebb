""" types """

from typing import TypedDict

class AccountTransaction(TypedDict):
    """ Transaction data typing, returns from account_transactions """
    id: int
    type: str
    time: str
    description: str
    amountCents: int
    runningBalanceCents: int

class ServiceTest(TypedDict):
    """ A service test object """
    name: str
    description: str
    link: str
