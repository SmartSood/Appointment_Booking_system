#!/usr/bin/env python3
"""
One-time script to get a Google OAuth refresh token for Calendar API.
Use this when your org blocks service account key creation.

1. In GCP Console: APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID.
2. Application type: "Desktop app" (or "Web application" with redirect URI http://localhost:8080/).
3. Set env vars and run:
   GOOGLE_OAUTH_CLIENT_ID=xxx GOOGLE_OAUTH_CLIENT_SECRET=xxx python scripts/get_google_refresh_token.py
4. Sign in in the browser; copy the printed refresh token into backend/.env as GOOGLE_OAUTH_REFRESH_TOKEN.
"""
import os
import sys

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def main():
    client_id = (os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        print("Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET (from GCP OAuth 2.0 Client ID).")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install: pip install google-auth-oauthlib")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=scopes,
    )
    creds = flow.run_local_server(port=8080)
    refresh_token = getattr(creds, "refresh_token", None)
    if not refresh_token:
        print("No refresh_token in response. Try running again or use a Desktop app client.")
        sys.exit(1)
    print("\nAdd this to backend/.env:\n")
    print(f"GOOGLE_OAUTH_REFRESH_TOKEN={refresh_token}")
    print("\nAlso set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in .env.")
    print("Leave GOOGLE_CREDENTIALS_FILE empty to use OAuth instead of a service account.")


if __name__ == "__main__":
    main()
