# CHANGELOG

## v0.0.3

The get_services function now has a "drop_unknown_types" flag which means you won't get a list of things we don't know about, hopefully that'll help some folks when AussieBB adds random things.

It also uses a central "handle response" thing so I can remove some duplicate code.

Added some more consts.

## v0.1.2

Bumped the minimum pydantic version to 2.0 - v0.1.1 had >v1.9 as a requirement and it looks like that might have allowed folks without poetry.lock files to catch old-pydantic.

Also using SecretStr for passwords now to avoid having them turn up in logs.

## v0.1.1

Stopped throwing errors on service type "Hardware" per [home-assistant/core#95665](https://github.com/home-assistant/core/issues/95665).

## v0.1.0

Update to Pydantic 2.x and a load of changes to support that.

## v0.0.19

Updating aiohttp dependency for CVE-2023-37276.

... don't use this, the Pydantic update broke things.

## v0.0.18

Added MFA support, example works with SMS, un-deprecated `service_plans`.

## v0.0.17

Adding download invoice functionality and handlers in `asyncio` module.

## v0.0.16

- Deprecated `service_plans` as it requires MFA or another auth method.
- `types.APIResponseMeta` now has optional `from` and `to` fields because the Aussie API was replying with them.

## v0.0.15

- Moved the `pydantic` dependency from dev to main, which shouldn't ever have been in dev...

## v0.0.14

- Moved the filtering by servicetypes in `get_services()` to its own function
- Added a new service type "Fetchtv"
- Added a way to drop types of services in `get_services()` so Home Assistant can ignore `FETCH_TYPES`
- Added some handling for FETCHTV types.

## v0.0.13

- Added service type of `FETCHTV` to `NBN_TYPES`
  - Fixed test for this handler.
  - Updated logging for error when it happens.

  Turns out this was the wrong way to handle it, so this version got yanked.

## v0.0.12

- Added `pydantic` as a dependency, which allows for better type checking.
- Rewrote a bunch of the tests because the bike shed needed to be green and driven by JSON.
- Added first run of handling for folks with more than 10 services - paginated calls
- Some things will return nicer pydantic-ish objects, typing is starting to be enforced on output
  - `account_contacts` is one, for example
- Added service type of `Opticomm` to `NBN_TYPES`

## v0.0.11

- Added `aussiebb.exceptions.UnrecognisedServiceType` and some quick validation when you run `get_usage` so it doesn't break.
- Added some more testing around this.
- Fixed it so you can pass a session object to the non-asyncio AussieBB
- Added "use_cached" to get_services calls
- Added some mock data in `aussiebb.const.TEST_MOCKDATA`

## v0.0.10

### Major change: Minimum supported Python is now 3.9

- re-defined the API Classes as children of a base class (aussiebb.baseclass.BaseClass).
- added significantly better typing to inputs/responses.
- removed all the usage of `inspect`.
- moved from setup.py to [Poetry](https://python-poetry.org) for build/packaging.
- removed loguru dependency, class init now takes a logger as an option or uses python default logging if not. Also removed _debug_print from async version.
- added NBN_TYPES and PHONE_TYPES to aussiebb.const, to allow one to check if the service matches a known identifier for "phone" (mobile/VOIP) or "NBN" (internet) types - this matters when parsing the resulting service info.
- added test and fixed result of the asyncio get_service_tests function

## v0.0.8

- renamed serviceid to service_id to match the api
- added request_get_json to the sync class
- added telephony_usage
- added get_appointment which gets service appointments
- updated get_usage so it checks the service list and will return telephony data if it's a PhoneMobile service
- abstracted how URLS are generated so I don't have to keep adding them twice
- added a filter on get_services which allows you to filter by type

## 0.0.7

- Added the following new functions: `account_transactions`, `billing_invoice`, `service_outages`, `service_boltons`, `service_datablocks`, `support_tickets`, `account contacts`. Renamed `get_service_plans` to `service_plans`

## v0.0.6

- Fixed rate limiting

## v0.0.5

- Fixing rate limiting
- Didn't actually fix it...

## 0.0.4

- Added `asyncio` submodule, split constants and exceptions out into their own files/modules.

## 0.0.3

- Added `get_service_plans` so the gigabit-desperate crowd can check for their new hotness.
