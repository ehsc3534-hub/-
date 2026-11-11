# Run on your own PC:  pip install google-auth-oauthlib
#                      python get_refresh_token.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client_id = input("YT_CLIENT_ID: ").strip()
client_secret = input("YT_CLIENT_SECRET: ").strip()

config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(config, SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\n==== COPY THIS INTO GITHUB SECRET: YT_REFRESH_TOKEN ====")
print(creds.refresh_token)
print("========================================================")
