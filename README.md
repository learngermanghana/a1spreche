# A1Sprechen

## Brand Colors

| Name       | Hex       |
|------------|-----------|
| Background | `#f3f7fb` |
| Text       | `#1a2340` |
| Primary    | `#25317e` |
| Accent     | `#6366f1` |

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

- From the Dashboard, use **View class board** to jump to the class notes & Q&A section.

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

## Level-Based Admin Mapping

Administrative access is determined by combining the `roles.admins` list from
Streamlit secrets with the `ADMINS_BY_LEVEL` dictionary in `a1sprechen.py`. Each
entry maps a CEFR level to a set of teacher codes:

```python
ADMINS_BY_LEVEL = {
    "A1": {"felixa177"},
    "A2": {"felixa2"},
    # Extend with additional levels or codes as needed
}
```

Update this mapping whenever new levels or teachers require admin access.
