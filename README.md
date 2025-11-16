# A1Sprechen

## Brand Colors

| Name       | Hex       |
|------------|-----------|
| Background | `#f3f7fb` |
| Text       | `#1a2340` |
| Primary    | `#25317e` |
| Accent     | `#6366f1` |

## Deployment
The app uses `streamlit-cookies-controller` to persist session and student-code
cookies. The controller transparently handles encryption and browser
synchronisation.

### Authentication configuration

- Set the `JWT_SECRET` environment variable. A fallback development value is
  used when running locally, but deploying with the default secret raises a
  runtime error. Pick a long, random string for production.
- Provide user login credentials via one of the following environment
  variables:
  - `AUTH_USER_CREDENTIALS`: JSON mapping of login identifiers to hashed
    passwords.
  - `AUTH_USER_CREDENTIALS_FILE`: Path to a JSON file with the same structure.

  Hash passwords before storing them. The Flask helper can generate suitable
  hashes:

  ```bash
  python - <<'PY'
  from werkzeug.security import generate_password_hash
  print(generate_password_hash("super-secret-password"))
  PY
  ```

  Store the resulting string in the JSON payload, for example:

  ```json
  {"admin@example.com": "pbkdf2:sha256:600000$..."}
  ```

### Refresh token storage

Authentication refresh tokens are persisted in a small SQLite database. The
database path can be configured via the `REFRESH_DB_PATH` environment variable;
it defaults to `refresh_tokens.db` in the project root. Initialize the database
table with:

```bash
python scripts/init_refresh_db.py
```

This creates a `refresh_tokens` table storing refresh tokens per device so
multiple logins can remain active simultaneously.

## Usage


### Vocab Sheet Format

The vocabulary sheet must include the following columns:

- `Level`
- `German`
- `English`

| Level | German | English |
|-------|--------|---------|
| A1    | Haus   | house   |

#### Configuring the source sheet

By default the app reads from the shared sheet used during development.
Deployments can point to another document by providing configuration at runtime:

- Environment variables: set `VOCAB_SHEET_ID` and `VOCAB_SHEET_GID`.
- Streamlit secrets: add `vocab_sheet_id`/`vocab_sheet_gid` (or the upper-case
  variants) to `st.secrets`.

The sheet *id* identifies the document while the *gid* selects a specific tab
within the workbook. The gid must be an integer. Any configuration mechanism can
override one or both values; unspecified fields fall back to the built-in
defaults.

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

Set the ``SESSION_MAX_AGE_DAYS`` environment variable to control how long the
refresh cookie remains valid (defaults to 90 days). Increasing this window can
help keep rarely-used accounts signed in longer while still allowing periodic
rotation through the refresh endpoint.

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

## Course Calendar (iPhone iCloud Import)

Students who need to add the course calendar to the native iOS Calendar app can
follow these steps on their iPhone:

1. Download the provided `.iso` calendar file and ensure it is saved to the
   device (Files app or iCloud Drive both work).
2. Open Safari and sign in to [iCloud.com](https://www.icloud.com/).
3. Locate the downloaded calendar file within iCloud Drive and tap to open it.
4. If the file does not open, redownload it from the same iCloud Drive page and
   try opening it again.
5. Once the file opens, choose the Calendar option on iCloud.com and select
   **Add All** to import every event into the Calendar app.

## Blog Feed

The dashboard displays new posts pulled from a JSON feed at
`https://blog.falowen.app/feed.json`. The `fetch_blog_feed` helper in
`src/blog_feed.py` downloads the feed, caches the result for an hour, and
returns a list of dictionaries containing the post title, description, and
link.

## Debug Logging

Enable debug logging when you need deeper insight into roster lookups or
authentication flows:

1. Run Streamlit with debug logging locally:

   ```bash
   streamlit run a1sprechen.py --logger.level=debug
   ```

2. Alternatively, set the configuration in a `.streamlit/config.toml` file or
   via environment variable for deployed environments:

   ```toml
   # .streamlit/config.toml
   [logger]
   level = "debug"
   ```

   ```bash
   export STREAMLIT_LOG_LEVEL=debug
   ```

The debug logs include the student code used for roster lookups, the number of
rows returned from the roster, and whether a matching row was found.
