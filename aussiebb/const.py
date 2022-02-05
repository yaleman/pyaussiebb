""" constants and utilities """

BASEURL = {
    'api' : 'https://myaussie-api.aussiebroadband.com.au',
    'login' : "https://myaussie-auth.aussiebroadband.com.au/login"
}

DEFAULT_BACKOFF_DELAY = 90

def default_headers():
    """ returns a default set of headers """
    return {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Origin': "https://my.aussiebroadband.com.au",
        'Referer': "https://my.aussiebroadband.com.au/",
        'cache-control': "no-cache",
    }

API_ENDPOINTS = {
    'account_contacts' : '/contacts',
    'account_paymentplans' : '/billing/paymentplans',
    'account_transactions' : '/billing/transactions?group=true',
    'billing_invoices' : '/billing/invoices/{invoice_id}',
    'get_appointment' : '/tickets/{ticketid}/appointment',
    'get_customer_details' : '/customer',
    'test_line_state' : '/tests/{service_id}/linestate',
    'get_services' : '/services',
    'get_service_tests' : '/tests/{service_id}/available',
    'get_test_history' : '/tests/{service_id}',
    'get_usage' : '/broadband/{service_id}/usage',
    'service_boltons' : '/nbn/{service_id}/boltons',
    'service_datablocks' : '/nbn/{service_id}/datablocks',
    'service_outages' : '/nbn/{service_id}/outages',
    'service_plans' : '/planchange/{service_id}',
    'support_tickets' : '/tickets',
    'telephony_usage' : '/telephony/{service_id}/usage',
}


TEST_MOCKDATA = {
    'telephony_usage' : {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]},
    "service_voip" : {
        'service_id': 123456, 'type': 'VOIP', 'name': 'VOIP', 'plan': 'Aussie VOIP Casual ($0)', 'description': 'VOIP: 123 DRURY LN, SUBURBTON', 'voipDetails': {'phoneNumber': '0912345678', 'barInternational': True, 'divertNumber': None, 'supportsNumberDiversion': True}, 'nextBillDate': '2054-01-01T13:00:00Z', 'openDate': '1970-01-01T13:00:00Z', 'usageAnniversary': 16, 'address': None, 'contract': None, 'discounts': []
    },
    "service_nbn_fttc" : {
        "service_id": 12345,
        "type": "NBN",
        "name": "NBN",
        "plan": "NBN 100/40Mbps - Plan Name",
        "description": "NBN: 123 DRURY LN, SUBURBTON QLD - AVC000000000001",
        "nbnDetails": {
            "product": "FTTC",
            "poiName": "Camp Hill",
            "cvcGraph": "https://cvcs.aussiebroadband.com.au/camphilllink2.png"
        },
        "nextBillDate": '2054-01-01T13:00:00Z',
        "openDate": '1970-01-05T13:00:00Z',
        "usageAnniversary": 16,
        "ipAddresses": [
            "2403:1001:b33f:1::/64",
            "2403:7007:face::/48",
            "123.123.123.1"
        ],
        "address": {
            "subaddresstype": None,
            "subaddressnumber": None,
            "streetnumber": "123",
            "streetname": "DRURY",
            "streettype": "LN",
            "locality": "SUBURBTON",
            "postcode": "4001",
            "state": "QLD"
        },
        "contract": None,
        "discounts": []
    }
}


NBN_TYPES = [
    "NBN"
]

PHONE_TYPES = [
    "VOIP",
    "PhoneMobile",
]
