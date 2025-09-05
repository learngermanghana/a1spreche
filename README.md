# A1Sprechen

## Deployment

Set the cookie encryption password either in Streamlit secrets or via an environment variable:

```
[secrets]
cookie_password = "<strong-secret>"
```

or

```
export COOKIE_PASSWORD=<strong-secret>
```

This value is required for secure cookie management.

## Usage

- From the Dashboard, use **View all class announcements** to jump to the full classroom announcements feed.

### Vocab Sheet Format

The vocabulary sheet must include the following columns:

- `Level`
- `German`
- `English`

| Level | German | English |
|-------|--------|---------|
| A1    | Haus   | house   |

## Keychain Helper

The application uses a small Swift utility to read and write OAuth tokens from
the macOS or iOS Keychain.  The helper lives at `KeychainHelper.swift` in the
repository root.  Include this file in the Xcode project or build process so it
is compiled and bundled with the app.  The Python bridge executes the helper via
`swift KeychainHelper.swift -` and sends short snippets that call `saveToken` and
`deleteToken`.

## Session Refresh

The iOS app proactively refreshes its session cookie. Safari's Intelligent
Tracking Prevention shortens cookie lifetimes to about a week when they aren't
updated. A daily refresh ensures the cookie expiry is extended well before the
platform can discard it.

## Authentication API

Clients authenticate by POSTing JSON to `/auth/login`:

```json
{
  "email": "name@example.com",
  "password": "hunter2"
}
```

Both `email` (or `user_id`) and `password` are required. Missing fields result in
a `400` response, while an incorrect password yields `401`. Successful requests
return an access token and refresh token pair.
