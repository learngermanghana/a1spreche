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

## Keychain Helper

The application uses a small Swift utility to read and write OAuth tokens from
the macOS or iOS Keychain.  The helper lives at `KeychainHelper.swift` in the
repository root.  Include this file in the Xcode project or build process so it
is compiled and bundled with the app.  The Python bridge executes the helper via
`swift KeychainHelper.swift -` and sends short snippets that call `saveToken` and
`deleteToken`.
