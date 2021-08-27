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
    'test_line_state' : '/tests/{serviceid}/linestate',
    'get_services' : '/services',
    'get_service_tests' : '/tests/{serviceid}/available',
    'get_test_history' : '/tests/{serviceid}',
    'get_usage' : '/broadband/{serviceid}/usage',
    'service_boltons' : '/nbn/{serviceid}/boltons',
    'service_datablocks' : '/nbn/{serviceid}/datablocks',
    'service_outages' : '/nbn/{serviceid}/outages',
    'service_plans' : '/planchange/{serviceid}',
    'support_tickets' : '/tickets',
    'telephony_usage' : '/telephony/{serviceid}/usage',
}


TEST_MOCKDATA = {
    'telephony_usage' : {"national":{"calls":0,"cost":0},"mobile":{"calls":0,"cost":0},"international":{"calls":0,"cost":0},"sms":{"calls":0,"cost":0},"internet":{"kbytes":0,"cost":0},"voicemail":{"calls":0,"cost":0},"other":{"calls":0,"cost":0},"daysTotal":31,"daysRemaining":2,"historical":[]}
}
