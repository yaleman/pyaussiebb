# pyAussieBB

[![Build Status](https://droneio.yaleman.org/api/badges/yaleman/aussiebb/status.svg)](https://droneio.yaleman.org/yaleman/aussiebb)

This is a very simple module for interacting with the Aussie Broadband APIs.

I wrote this so I can pull a line test periodically and show the NBN how garbage they are.

## Usage

```
pip install --user pyaussiebb
python
>>> from aussiebb import AussieBB
>>> account = AussieBB(username, password)
>>> account.get_services()
[{allyourservicedetails}]
```

For more, check out the module.
