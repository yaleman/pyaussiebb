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
    'telephony_usage' : {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
}
