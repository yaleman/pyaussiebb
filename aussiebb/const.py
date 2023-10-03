""" constants and utilities """

import sys

if sys.version_info.major == 3 and sys.version_info.minor < 12:
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


BASEURL = {
    "api": "https://myaussie-api.aussiebroadband.com.au",
    "login": "https://myaussie-auth.aussiebroadband.com.au/login",
}

DEFAULT_BACKOFF_DELAY = 90

DefaultHeaders = TypedDict(
    "DefaultHeaders",
    {
        "Accept": str,
        "Cache-Control": str,
        "Content-Type": str,
        "Origin": str,
        "Referer": str,
        "x-two-factor-auth-capable-client": str,
    },
)


def default_headers() -> DefaultHeaders:
    """returns a default set of headers"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://my.aussiebroadband.com.au",
        "Referer": "https://my.aussiebroadband.com.au/",
        "Cache-Control": "no-cache",
        "x-two-factor-auth-capable-client": "true",
    }


API_ENDPOINTS = {
    "account_contacts": "/contacts",
    "account_paymentplans": "/billing/paymentplans",
    "account_transactions": "/billing/transactions?group=true",
    "billing_invoice": "/billing/invoices/{invoice_id}",
    "billing_receipt": "/billing/receipts/{receipt_id}",
    "fetch_service": "/fetch/{service_id}",
    "get_appointment": "/tickets/{ticketid}/appointment",
    "get_customer_details": "/customer",
    "get_order": "/orders/nbn/{order_id}",
    "get_orders": "/orders?v=2",
    "get_service_tests": "/tests/{service_id}/available",
    "get_services": "/services",
    "get_test_history": "/tests/{service_id}",
    "get_usage": "/broadband/{service_id}/usage",
    "service_boltons": "/nbn/{service_id}/boltons",
    "service_datablocks": "/nbn/{service_id}/datablocks",
    "service_outages": "/nbn/{service_id}/outages",
    "service_plans": "/planchange/{service_id}",
    "support_tickets": "/tickets",
    "telephony_usage": "/telephony/{service_id}/usage",
    "test_line_state": "/tests/{service_id}/linestate",
    "voip_devices": "/voip/{service_id}/devices",
    "voip_service": "/voip/{service_id}",
    "mfa_send": "/2fa/send",
    "mfa_verify": "/2fa/verify",
}


TEST_MOCKDATA = {
    "telephony_usage": {
        "national": {"calls": 0, "cost": 0},
        "mobile": {"calls": 0, "cost": 0},
        "international": {"calls": 0, "cost": 0},
        "sms": {"calls": 0, "cost": 0},
        "internet": {"kbytes": 0, "cost": 0},
        "voicemail": {"calls": 0, "cost": 0},
        "other": {"calls": 0, "cost": 0},
        "daysTotal": 31,
        "daysRemaining": 2,
        "historical": [],
    },
    "service_voip": {
        "service_id": 123456,
        "type": "VOIP",
        "name": "VOIP",
        "plan": "Aussie VOIP Casual ($0)",
        "description": "VOIP: 123 DRURY LN, SUBURBTON",
        "voipDetails": {
            "phoneNumber": "0912345678",
            "barInternational": True,
            "divertNumber": None,
            "supportsNumberDiversion": True,
        },
        "nextBillDate": "2054-01-01T13:00:00Z",
        "openDate": "1970-01-01T13:00:00Z",
        "usageAnniversary": 16,
        "address": None,
        "contract": None,
        "discounts": [],
    },
    "service_nbn_fttc": {
        "service_id": 12345,
        "type": "NBN",
        "name": "NBN",
        "plan": "NBN 100/40Mbps - Plan Name",
        "description": "NBN: 123 DRURY LN, SUBURBTON QLD - AVC000000000001",
        "nbnDetails": {
            "product": "FTTC",
            "poiName": "Camp Hill",
            "cvcGraph": "https://cvcs.aussiebroadband.com.au/camphilllink2.png",
        },
        "nextBillDate": "2054-01-01T13:00:00Z",
        "openDate": "1970-01-05T13:00:00Z",
        "usageAnniversary": 16,
        "ipAddresses": [
            "2403:1001:b33f:1::/64",
            "2403:7007:face::/48",
            "123.123.123.1",
        ],
        "address": {
            "subaddresstype": None,
            "subaddressnumber": None,
            "streetnumber": "123",
            "streetname": "DRURY",
            "streettype": "LN",
            "locality": "SUBURBTON",
            "postcode": "4001",
            "state": "QLD",
        },
        "contract": None,
        "discounts": [],
    },
}

FETCH_TYPES = [
    "FETCHTV",
]

NBN_TYPES = [
    "NBN",
    "Opticomm",
]

PHONE_TYPES = [
    "VOIP",
    "PhoneMobile",
]

# you should be able to get usage for these types
USAGE_ENABLED_SERVICE_TYPES = NBN_TYPES + PHONE_TYPES

HARDWARE_TYPES = ["Hardware"]
