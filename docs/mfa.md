# Multi-Factor Authentication

This is a work in progress.

## Requesting an MFA token

URL: `https://myaussie-api.aussiebroadband.com.au/2fa/send`

POST body: `{"method":"sms"}` OR `{"method":"email"}`

Headers:

```json
{ "x-two-factor-auth-capable-client": "true" }
```

## Submitting the Token

URL: `https://myaussie-api.aussiebroadband.com.au/2fa/verify`

POST body: `{"token":"<value>"}`

Headers:

```json
{ "x-two-factor-auth-capable-client": "true" }
```

As far as I can tell this just updates the session/cookies so you're "approved" for MFA things after that.
