import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def _service():
    # scopes intentionally NOT passed: the refresh token keeps its own scopes.
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"].strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"].strip(),
        client_secret=os.environ["YT_CLIENT_SECRET"].strip(),
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(path, meta):
    yt = _service()
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "27",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp, tries = None, 0
    while resp is None:
        try:
            _, resp = req.next_chunk()
        except Exception as e:
            if "invalid_scope" in str(e) or "invalid_grant" in str(e):
                raise SystemExit(
                    "TOKEN ERROR: create a NEW refresh token with get_refresh_token.py "
                    "and update the YT_REFRESH_TOKEN secret. Details: " + str(e))
            tries += 1
            if tries > 5:
                raise
            print("upload retry:", e)
            time.sleep(5 * tries)
    print("Uploaded! Video ID:", resp.get("id"))
    return resp.get("id")
