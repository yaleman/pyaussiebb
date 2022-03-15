""" types """

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, SecretStr, Field

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


class APIResponseLinks(BaseModel):
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

class GetServicesResponse(BaseModel):
    """ the format for a response from the get_services call """
    data: List[Dict[str, Any]]
    links: APIResponseLinks
    meta: APIResponseMeta

    class Config:
        """ metadata """
        arbitrary_types_allowed = True

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

# Example extended data for an Aussie Outage
# {
#     "networkEvents": [
#         {
#         "reference": 66522,
#         "title": "Network Maintenance",
#         "summary": "Dear Customer,\r\n\r\nPlease be aware of upcoming maintenance on the Aussie Broadband network. Your services may experience an outage during the following window:\r\n\r\nSTART DATE: Monday 14th February 2022 03:00 Hrs AEST\r\n\r\nEND DATE: Monday 14th February 2022 04:00 Hrs AEST\r\n\r\nBREAK/DURATION: 1 Hour\r\n\r\nNBN/Opticomm Services Affected:\r\n\r\nCaboolture (Link 2) \r\nNambour (Link 3) \r\nBundaberg (Link 2) \r\nPetrie (Link 2) \r\nCairns (Link 2) \r\nAcacia Ridge Depot (Link 3) \r\nWoolloongabba TC2 \r\nSouthport (Link 2) \r\nToowoomba \r\nCairns \r\nEight Mile \r\nNerang (Link 2) \r\nAcacia Ridge Depot (Link 2) \r\nCamp Hill (Link 3) \r\nSlacks Creek (Link 3) \r\nSlacks Creek (Link 2) \r\nToowoomba (Link 2) \r\nNambour (Link 2) \r\nCamp Hill (Link 2) \r\nRockhampton (Link 2) \r\nWoolloongabba (Link 2) \r\nMackay (Link 2) \r\nGoodna (Link 2) \r\nBundamba (Link 2) \r\nAspley (Link 2) \r\nIpswich (Link 2) \r\nNerang (Link 3) \r\nTownsville (Link 3) \r\nOpticomm QLD\r\n\r\n\r\n\r\n\r\n\r\nThis work is scheduled maintenance impacting Carrier Grade NAT (CG-NAT) customers, and we apologise for any inconvenience this may cause. If you have any concerns, please contact our Technical Support team on 1300 880 905.\r\n\r\nCheers\r\nAussie Broadband Limited\r\n                        ",
#         "start_time": "2022-02-13T17:00:00Z",
#         "end_time": "2022-02-13T18:00:00Z",
#         "restored_at": null,
#         "last_updated": null
#         }
#     ],
#     "aussieOutages": {
#         "future": [
#             {
#             "reference": 66522,
#             "title": "Network Maintenance",
#             "summary": "Dear Customer,\r\n\r\nPlease be aware of upcoming maintenance on the Aussie Broadband network. Your services may experience an outage during the following window:\r\n\r\nSTART DATE: Monday 14th February 2022 03:00 Hrs AEST\r\n\r\nEND DATE: Monday 14th February 2022 04:00 Hrs AEST\r\n\r\nBREAK/DURATION: 1 Hour\r\n\r\nNBN/Opticomm Services Affected:\r\n\r\nCaboolture (Link 2) \r\nNambour (Link 3) \r\nBundaberg (Link 2) \r\nPetrie (Link 2) \r\nCairns (Link 2) \r\nAcacia Ridge Depot (Link 3) \r\nWoolloongabba TC2 \r\nSouthport (Link 2) \r\nToowoomba \r\nCairns \r\nEight Mile \r\nNerang (Link 2) \r\nAcacia Ridge Depot (Link 2) \r\nCamp Hill (Link 3) \r\nSlacks Creek (Link 3) \r\nSlacks Creek (Link 2) \r\nToowoomba (Link 2) \r\nNambour (Link 2) \r\nCamp Hill (Link 2) \r\nRockhampton (Link 2) \r\nWoolloongabba (Link 2) \r\nMackay (Link 2) \r\nGoodna (Link 2) \r\nBundamba (Link 2) \r\nAspley (Link 2) \r\nIpswich (Link 2) \r\nNerang (Link 3) \r\nTownsville (Link 3) \r\nOpticomm QLD\r\n\r\n\r\n\r\n\r\n\r\nThis work is scheduled maintenance impacting Carrier Grade NAT (CG-NAT) customers, and we apologise for any inconvenience this may cause. If you have any concerns, please contact our Technical Support team on 1300 880 905.\r\n\r\nCheers\r\nAussie Broadband Limited\r\n                        ",
#             "start_time": "2022-02-13T17:00:00Z",
#             "end_time": "2022-02-13T18:00:00Z",
#             "restored_at": null,
#             "last_updated": null
#             }
#     ]
#     },
#     "currentNbnOutages": [],
#     "scheduledNbnOutages": [],
#     "resolvedScheduledNbnOutages": [
#         {
#             "start_date": "2021-08-17T14:00:00Z",
#             "end_date": "2021-08-17T20:00:00Z",
#             "duration": "6.0"
#         }
#     ],
#     "resolvedNbnOutages": []
# }
class OutageRecord(BaseModel):
    """ outage def """
    reference: int
    title: str
    summary: str
    start_time: datetime
    end_time: datetime
    restored_at: Optional[datetime]
    last_updated: Optional[datetime]

class ScheduledOutageRecord:
    """ scheduled outage record """
    start_date: datetime
    end_date: datetime
    duration: float

class AussieBBOutage(BaseModel):
    """ outage class """
    networkEvents: List[OutageRecord]
    aussieOutages: Dict[str, List[OutageRecord]]
    currentNbnOutages: List[Any] # TODO: define currentNbnOutages
    scheduledNbnOutages: List[ScheduledOutageRecord] # TODO: define scheduledNbnOutages
    resolvedScheduledNbnOutages: List[ScheduledOutageRecord] # TODO: define resolvedScheduledNbnOutages
    resolvedNbnOutages: List[Any] # TODO: define resolvedNbnOutages

    class Config:
        """ config """
        arbitrary_types_allowed=True



class OrderData(TypedDict):
    """ order element for OrderResponse get_orders """
    id: int
    status: str
    type: str
    description: str

class OrderDetailResponseModel(BaseModel):
    """ order Response for get_order(int) """
    id: int
    status: str
    plan: str
    address: str
    appointment: str
    appointment_reschedule_code: int = Field(..., alias="appointmentRescheduleCode")
    statuses: List[str]

OrderDetailResponse = TypedDict("OrderDetailResponse", {
    "id" : int,
    "status" : str,
    "plan": str,
    "address": str,
    "appointment": str,
    "appointment_reschedule_code": int,
    "statuses": List[str]
})

class OrderResponse(BaseModel):
    """ response from get_orders """
    data: List[OrderData]
    links: APIResponseLinks
    meta: APIResponseMeta

    class Config:
        """ config """
        arbitrary_types_allowed=True

class VOIPDevice(BaseModel):
    """ an individual service device """
    username: str
    password: str
    registered: bool # is it online?

class VOIPService(BaseModel):
    """ individual VOIP service """
    phoneNumber: str
    barInternational: bool
    divertNumber: Optional[str]
    supportsNumberDiversion: bool
