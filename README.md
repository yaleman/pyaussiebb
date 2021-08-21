# pyAussieBB

[![Build Status](https://droneio.yaleman.org/api/badges/yaleman/aussiebb/status.svg)](https://droneio.yaleman.org/yaleman/aussiebb)

This is a very simple module for interacting with the Aussie Broadband APIs.

I wrote this so I can pull a line test periodically and show the NBN how garbage they are.

# Usage

```
pip install --user pyaussiebb
python
>>> from aussiebb import AussieBB
>>> account = AussieBB(username, password)
>>> account.get_services()
[{allyourservicedetails}]
```

For more, check out the module.



# AsyncIO version

You can replace `from aussiebb import AussieBB` with `from aussiebb.asyncio import AussieBB` and you'll get an `aiohttp`-powered version. The only difference in this case is that you have to explicitly call `login()` for reasons.


# AsyncIO version

You can replace `from aussiebb import AussieBB` with `from aussiebb.asyncio import AussieBB` and you'll get an `aiohttp`-powered version. The only difference in this case is that you have to explicitly call `login()` for reasons.

If you hit the rate limit it'll raise a `RateLimit` exception. I haven't put that functionality into the blocking version yet, since ... that tends not to hit it. 🤣

# Example service tests I've seen

All the "endpoints" should be tacked onto `aussiebb.BASEURL['api']`.

**Warning: `/nbn/{service_id}/connection` seems to have both a GET and POST method endpoint - tests on other endpoints may be similar.**

These can be run by using `AussieBB.run_test()` with the string after the last forward-slash as the "test" - ie, `connection` or `linestate`.

## HFC 

These are entirely untested so far.

| Endpoint | Method | Name | Description |
| --- | --- | --- | --- |
| `/nbn/{service_id}/connection` | Probably GET | Check Connection | Check to see if your service is currently connected |
| `/nbn/{service_id}/connection` | Probably POST | Kick Connection | Kick your current session and force your device to reauthenticate |
| `/tests/{service_id}/loopback` | Probably POST | Loopback Test | This will test the connectivity between the point NBN’s network transitions to ours and to the closest point to your property. Usually either the Network Termination Device or Node. |
| `/tests/{service_id}/ntdstatus` | Probably POST | NTD Status | An NTD Status will show you the operational state of the Network Termination Device (NTD). The test will also show if the NTD is detecting the wired connection from your router. |

## FTTC

| Endpoint | Method | Name | Description |
| --- | --- | --- | --- |
| `/nbn/{service_id}/connection` | GET |Check Connection | Check to see if your service is currently connected |
| `/nbn/{service_id}/connection`  | Probably POST |Kick Connection | Kick your current session and force your device to reauthenticate |
| `/tests/{service_id}/dpuportreset` | Probably POST |DPU Port Reset | Reset the Port on the DPU (Distribution Point Unit) along with clearing any errors that maybe causing issues with connectivity.  |
| `/tests/{service_id}/dpuportstatus` | POST |DPU Port Status | A DPU (Distribution Point Unit) port status will show if the NCD (Network Connection Device) is providing power to the DPU. It will also state if the NCD (Network Connection Device) is in sync. |
| `/tests/{service_id}/dpustatus` | POST |DPU Status | This will provide if the DPU (Distribution Point Unit) is currently being powered. |
| `/tests/{service_id}/loopback` | POST |Loopback Test | This will test the connectivity between the point NBN’s network transitions to ours and to the closest point to your property. Usually either the Network Termination Device or Node. |
| `/tests/{service_id}/ncdportreset` | Probably POST |NCD Port Reset | Reset the gateway port on your NCD (Network Connection Device). |
| `/tests/{service_id}/ncdreset` | Probably POST |NCD Reset | This will remotely restart your Network Termination Device. |

## FTTN

| Endpoint | Method | Name | Description |
|  --- | --- | --- | --- |
| `/nbn/{service_id}/connection` | GET | Check Connection | Check to see if your service is currently connected |
| `/nbn/{service_id}/connection` | Probably POST | Kick Connection | Kick your current session and force your device to reauthenticate |
| `/tests/{service_id}/linestate` | POST | Line State | A line state test will determine if you have “sync” (connection) to the node. If the service is in sync this test will also return your maximum and current attainable transfer rate. |
| `/tests/{service_id}/loopback` | POST | Loopback Test | This will test the connectivity between the point NBN’s network transitions to ours and to the closest point to your property. Usually either the Network Termination Device or Node. |
| `/tests/{service_id}/portreset` | Probably POST | Port Reset | This will reset the connection from the Node and also clear errors that may be causing issues with gaining sync. |
| `/tests/{service_id}/stabilityprofile` | Probably POST | Stability Profile | This will apply changes to your FTTN service including allowing increased noise to occur before making the connection unstable. This will cause your speeds to degrade as a result, but in turn making the service more stable. For NBN to investigate a fault this profile needs to be applied and a minimum of 5 dropouts recorded over a 24hr period on NBN's systems before a dropout fault can be raised |

## FTTP

These are as-yet untested.

| Endpoint | Method | Name | Description |
|  --- | --- | --- | --- |
| `/nbn/{service_id}/connection` | Probably GET | Check Connection | Check to see if your service is currently connected |
| `/nbn/{service_id}/connection` | Probably POST | Kick Connection | Kick your current session and force your device to reauthenticate |
| `/tests/{service_id}/loopback` | Probably POST | Loopback Test | This will test the connectivity between the point NBN’s network transitions to ours and to the closest point to your property. Usually either the Network Termination Device or Node. |
| `/tests/{service_id}/portreset` | Probably POST | Port Reset | This will reset the connection from the Node and also clear errors that may be causing issues with gaining sync. |
| `/tests/{service_id}/unidstatus` | Probably POST | UNI-D Status | UNI-D Status will show if the UNI-D port you are currently using has a router connected to it. This will also provide the Link speed your router and UNI-D port are connected at Eg, 100mbit or 1gbit. You will also see the MAC address of the currently connected router. |

# Changelog

 * 0.0.3 - Added `get_service_plans` so the gigabit-desperate crowd can check for their new hotness.
 * 0.0.4 - Added `asyncio` submodule, split constants and exceptions out into their own files/modules.
 * 0.0.5/6 - Fixing rate limiting
 * 0.0.7 - Added the following new functions: `account_transactions`, `billing_invoice`, `service_outages`, `service_boltons`, `service_datablocks`, `support_tickets`, `account contacts`. Renamed `get_service_plans` to `service_plans`