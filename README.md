# A1Sprechen

## Brand Colors

| Name       | Hex       |
|------------|-----------|
| Background | `#f3f7fb` |
| Text       | `#1a2340` |
| Primary    | `#25317e` |
| Accent     | `#6366f1` |

## Deployment

Set the cookie encryption password either in Streamlit secrets or via an environment variable. The password **must be a long, random value** (32+ characters) – short phrases are insecure:

```
[secrets]
cookie_password = "<strong-secret>"
```

or

```
export COOKIE_PASSWORD=<strong-secret>
```

This value is required for secure cookie management. If it is omitted the app falls back to a built-in password intended only for tests and logs a warning. Never rely on the fallback in production.

### Refresh token storage

Authentication refresh tokens are persisted in a small SQLite database. The
database path can be configured via the `REFRESH_DB_PATH` environment variable;
it defaults to `refresh_tokens.db` in the project root. Initialize the database
table with:

```bash
python scripts/init_refresh_db.py
```

This creates a `refresh_tokens` table mapping `user_id` to the latest issued
refresh token.

## Usage


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

## Styling

Global CSS variables and layout helpers live in `src/styles.py`. These styles are
loaded at app start and expose reusable class names such as `flex-center`,
`btn`, and `btn-google`.

To style a new widget, call the classes in your HTML snippet:

```python
from src.styles import inject_global_styles  # already called in a1sprechen.py

st.markdown(
    """
    <div class="flex-center">
      <button class="btn">Example</button>
    </div>
    """,
    unsafe_allow_html=True,
)
```

Extend `src/styles.py` with additional variables or classes and reuse them across
components.

## Blog Feed

The dashboard displays new posts pulled from a JSON feed at
`https://blog.falowen.app/feed.json`. The `fetch_blog_feed` helper in
`src/blog_feed.py` downloads the feed, caches the result for an hour, and
returns a list of dictionaries containing the post title, description, and
link.
