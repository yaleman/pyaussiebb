""" types """

from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, SecretStr

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


class APIResponseLinks(TypedDict):
    """ the links field from an API response"""
    first: str
    last: str
    prev: Optional[str]
    next: Optional[str]

APIResponseMeta = TypedDict("APIResponseMeta",
{
    "current_page": int,
    "from": int,
    "last_page": int,
    "path": str,
    "per_page": int,
    "to": int,
    "total": int
})

class GetServicesResponse(TypedDict):
    """ the format for a response from the get_services call """
    data: List[Dict[str, Any]]
    links: APIResponseLinks
    meta: APIResponseMeta

class ConfigUser(BaseModel):
    """ just a username and password field """
    username: str
    password: str


class AussieBBConfigFile(BaseModel):
    """ config file definition """
    users: List[ConfigUser]
    username : Optional[str]
    password : Optional[SecretStr]

    class Config:
        """ metadata """
        arbitrary_types_allowed = True
