"""types"""

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class AccountTransaction(TypedDict):
    """Transaction data typing, returns from account_transactions"""

    id: int
    type: str
    time: str
    description: str
    amountCents: int
    runningBalanceCents: int


class ServiceTest(BaseModel):
    """A service test object"""

    name: str
    description: str
    link: str


class APIResponseLinks(BaseModel):
    """the links field from an API response"""

    first: str
    last: str
    prev: str | None = None
    next: str | None = None


APIResponseMeta = TypedDict(
    "APIResponseMeta",
    {
        "current_page": int,
        "from": int | None,
        "last_page": int,
        "path": str,
        "per_page": int,
        "to": int | None,
        "total": int,
    },
)


class GetServicesResponse(BaseModel):
    """the format for a response from the get_services call"""

    data: list[dict[str, Any]]
    links: APIResponseLinks
    meta: APIResponseMeta

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConfigUser(BaseModel):
    """just a username and password field"""

    username: str
    password: SecretStr


class AussieBBConfigFile(BaseModel):
    """config file definition"""

    users: list[ConfigUser]
    username: str | None = None
    password: SecretStr | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Example extended data for an Aussie Outage
# {
#     "networkEvents": [
#         {
#         "reference": 66522,
#         "title": "Network Maintenance",
#         "summary": "Dear Customer,\r\n\r\nPlease be aware of upcoming
# maintenance on the Aussie Broadband network. Your services may experience
# an outage during the following window:\r\n\r\nSTART DATE: Monday 14th February
# 2022 03:00 Hrs AEST\r\n\r\nEND DATE: Monday 14th February 2022 04:00 Hrs AEST\r\n
# \r\nBREAK/DURATION: 1 Hour\r\n\r\nNBN/Opticomm Services Affected:\r\n
# \r\nCaboolture (Link 2) \r\nNambour (Link 3) \r\n
# Bundaberg (Link 2) \r\nPetrie (Link 2) \r\n
# Cairns (Link 2) \r\nAcacia Ridge Depot (Link 3) \r\n
# Woolloongabba TC2 \r\nSouthport (Link 2) \r\n
# Toowoomba \r\n
# Cairns \r\nEight Mile \r\nNerang (Link 2) \r\n
# Acacia Ridge Depot (Link 2) \r\nCamp Hill (Link 3) \r\n
# Slacks Creek (Link 3) \r\nSlacks Creek (Link 2) \r\n
# Toowoomba (Link 2) \r\nNambour (Link 2) \r\n
# Camp Hill (Link 2) \r\nRockhampton (Link 2) \r\n
# Woolloongabba (Link 2) \r\nMackay (Link 2) \r\n
# Goodna (Link 2) \r\nBundamba (Link 2) \r\nAspley (Link 2) \r\nIpswich (Link 2) \r\n
# Nerang (Link 3) \r\nTownsville (Link 3) \r\nOpticomm QLD\r\n\r\n\r\n\r\n\r\n\r\n
# This work is scheduled maintenance impacting Carrier Grade NAT (CG-NAT) customers,
# and we apologise for any inconvenience this may cause. If you have any concerns,
# please contact our Technical Support team on 1300 880 905.\r\n\r\nCheers\r\n
# Aussie Broadband Limited\r\n                        ",
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
#             "summary": "Dear Customer,\r\n\r\nPlease be aware of upcoming maintenance on the Aussie Broadband network. Your services may experience an outage during the following window:\r\n\r\n
# START DATE: Monday 14th February 2022 03:00 Hrs AEST\r\n\r\n
# END DATE: Monday 14th February 2022 04:00 Hrs AEST\r\n\r\n
# BREAK/DURATION: 1 Hour\r\n\r\nNBN/Opticomm Services Affected:\r\n
# \r\nCaboolture (Link 2) \r\nNambour (Link 3) \r\nBundaberg (Link 2) \r\nPetrie (Link 2) \r\n
# Cairns (Link 2) \r\nAcacia Ridge Depot (Link 3) \r\nWoolloongabba TC2 \r\nSouthport (Link 2) \r\nToowoomba \r\nCairns \r\nEight Mile \r\nNerang (Link 2) \r\nAcacia Ridge Depot (Link 2) \r\n
# Camp Hill (Link 3) \r\n
# Slacks Creek (Link 3) \r\nSlacks Creek (Link 2) \r\nToowoomba (Link 2) \r\nNambour (Link 2) \r\nCamp Hill (Link 2) \r\nRockhampton (Link 2) \r\nWoolloongabba (Link 2) \r\n
# Mackay (Link 2) \r\nGoodna (Link 2) \r\nBundamba (Link 2) \r\nAspley (Link 2) \r\nIpswich (Link 2) \r\n
# Nerang (Link 3) \r\nTownsville (Link 3) \r\nOpticomm QLD\r\n\r\n\r\n\r\n\r\n\r\n
# This work is scheduled maintenance impacting Carrier Grade NAT (CG-NAT) customers,
# and we apologise for any inconvenience this may cause. If you have any concerns, please contact our Technical Support team on 1300 880 905.\r\n\r\n
# Cheers\r\n
# Aussie Broadband Limited\r\n                        ",
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
    """outage def"""

    reference: int
    title: str
    summary: str
    start_time: datetime
    end_time: datetime
    restored_at: datetime | None = None
    last_updated: datetime | None = None


class ScheduledOutageRecord:
    """scheduled outage record"""

    start_date: datetime
    end_date: datetime
    duration: float


class AussieBBOutage(BaseModel):
    """outage class"""

    networkEvents: list[OutageRecord]
    aussieOutages: list[OutageRecord]
    currentNbnOutages: list[Any]  # TODO: define currentNbnOutages
    scheduledNbnOutages: list[ScheduledOutageRecord]
    resolvedScheduledNbnOutages: list[ScheduledOutageRecord]
    resolvedNbnOutages: list[Any]  # TODO: define resolvedNbnOutages

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OrderData(TypedDict):
    """order element for OrderResponse get_orders"""

    id: int
    status: str
    type: str
    description: str


class OrderDetailResponseModel(BaseModel):
    """order Response for get_order(int)"""

    id: int
    status: str
    plan: str
    address: str
    appointment: str
    appointment_reschedule_code: int = Field(..., alias="appointmentRescheduleCode")
    statuses: list[str]


OrderDetailResponse = TypedDict(
    "OrderDetailResponse",
    {
        "id": int,
        "status": str,
        "plan": str,
        "address": str,
        "appointment": str,
        "appointment_reschedule_code": int,
        "statuses": list[str],
    },
)


class OrderResponse(BaseModel):
    """response from get_orders"""

    data: list[OrderData]
    links: APIResponseLinks
    meta: APIResponseMeta

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VOIPDevice(BaseModel):
    """an individual service device"""

    username: str
    password: SecretStr
    registered: bool  # is it online?


class AccountContact(BaseModel):
    """account contact data"""

    contact_id: int = Field(..., alias="id")
    first_name: str
    last_name: str
    email: list[str]
    dob: str
    home_phone: str | None = None
    work_phone: str | None = None
    mobile_phone: str | None = None
    work_mobile: str | None = None
    primary_contact: bool
    username: str | None = None
    preferred_name: str | None = None
    middle_name: str | None = None


class Address(BaseModel):
    """Address for services"""

    subaddresstype: str | None = None
    subaddressnumber: str | None = None
    streetnumber: str
    streetname: str
    locality: str
    postcode: str
    state: str


class BaseService(BaseModel):
    """base service definition"""

    service_id: int
    type: str
    name: str
    plan: str
    description: str
    next_bill_date: datetime = Field(..., alias="nextBillDate")
    open_date: datetime = Field(..., alias="openDate")
    usage_anniversary: datetime = Field(..., alias="usageAnniversary")

    address: Address
    contract: str | None = None
    discounts: list[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FetchSubscription(BaseModel):
    """Fetch Subscription item"""

    name: str
    description: str
    cost_cents: int = Field(..., alias="costCents")
    start_date: datetime | None = Field(..., alias="startDate")
    end_date: datetime | None = Field(..., alias="endDate")


class FetchSubscriptiondict(BaseModel):
    """this is just getting silly"""

    # subscriptions: list[FetchSubscription] = Field(..., alias="")
    premium_channels: list[FetchSubscription] = Field(..., alias="Premium Channels")


class FetchService(BaseService):
    """Fetch TV Service, comes from get_services()"""


class FetchDetails(BaseModel):
    """data from  /fetchtv/{serviceid}"""

    service_id: int = Field(..., alias="id")
    max_outstanding_cents: int = Field(..., alias="maxOutstandingCents")
    current_available_spend_cents: int = Field(..., alias="currentAvailableSpendCents")
    transactions: list[str]
    subscriptions: FetchSubscriptiondict


class VOIPDetails(BaseModel):
    """individual VOIP service"""

    phone_number: str = Field(..., alias="phoneNumber")
    bar_international: bool = Field(..., alias="barInternational")
    divert_number: str | None = Field(..., alias="divertNumber")
    supports_number_diversion: bool = Field(..., alias="supportsNumberDiversion")


class VOIPService(BaseService):
    """VOIP Service details TV Service"""

    voip_details: VOIPDetails = Field(..., alias="voipDetails")


class NBNDetails(BaseModel):
    """sub-details of an NBN service"""

    product: str
    poi_name: str = Field(..., alias="poiName")
    cvc_graph: str = Field(..., alias="cvcGraph")


class NBNService(BaseService):
    """NBN Service"""

    nbn_details: NBNDetails = Field(..., alias="nbnDetails")

    ip_addresses: list[str] = Field(..., alias="ipAddresses")


class MFAMethod(BaseModel):
    """simple model for sending MFA Method"""

    method: str

    @field_validator("method")
    @classmethod
    def check_method(cls, value: str) -> str:
        """validates that the MFA method is either sms or email"""
        if value not in ["sms", "email"]:
            raise ValueError("must be sms or email")
        return value
