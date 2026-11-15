"""Official Instagram Graph API login and Reel publishing."""

from __future__ import annotations

import os
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

AUTH_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_URL = "https://graph.instagram.com"
SCOPES = "instagram_business_basic,instagram_business_content_publish"


def redirect_uri() -> str:
    return os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:5000/instagram/callback")


def login_url() -> str:
    params = {
        "client_id": os.getenv("INSTAGRAM_APP_ID", ""),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
    }
    query = "&".join(f"{key}={quote(value)}" for key, value in params.items())
    return f"{AUTH_URL}?{query}"


def exchange_code(code: str) -> dict:
    response = requests.post(TOKEN_URL, data={
        "client_id": os.getenv("INSTAGRAM_APP_ID", ""),
        "client_secret": os.getenv("INSTAGRAM_APP_SECRET", ""),
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri(),
        "code": code,
    }, timeout=30)
    response.raise_for_status()
    short_lived = response.json()
    token = short_lived.get("access_token")
    if not token:
        raise RuntimeError("Instagram did not return an access token")

    long_response = requests.get(f"{GRAPH_URL}/access_token", params={
        "grant_type": "ig_exchange_token",
        "client_secret": os.getenv("INSTAGRAM_APP_SECRET", ""),
        "access_token": token,
    }, timeout=30)
    long_response.raise_for_status()
    long_lived = long_response.json()
    long_lived["user_id"] = short_lived.get("user_id") or long_lived.get("user_id")
    return long_lived


class InstagramGraphUploader:
    def __init__(self, base_url: str | None = None):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.user_id = os.getenv("INSTAGRAM_USER_ID", "")
        self.base_url = (base_url or os.getenv("PUBLIC_BASE_URL", "")).rstrip("/")

    @property
    def ready(self) -> bool:
        return bool(self.access_token and self.user_id and self.base_url)

    def upload_video(self, video_path: str, caption: str = "") -> bool:
        if not self.ready:
            print("[INSTAGRAM GRAPH] Set INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, and PUBLIC_BASE_URL")
            return False
        filename = os.path.basename(video_path)
        video_url = f"{self.base_url}/instagram/media/{quote(filename)}"
        create = requests.post(f"{GRAPH_URL}/{self.user_id}/media", data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "access_token": self.access_token,
        }, timeout=30)
        create.raise_for_status()
        container_id = create.json().get("id")
        if not container_id:
            raise RuntimeError("Instagram did not return a Reel container ID")

        for _ in range(30):
            status = requests.get(f"{GRAPH_URL}/{container_id}", params={
                "fields": "status_code",
                "access_token": self.access_token,
            }, timeout=30).json().get("status_code")
            if status == "FINISHED":
                break
            if status in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Instagram Reel processing failed: {status}")
            time.sleep(5)
        else:
            raise TimeoutError("Instagram Reel processing timed out")

        publish = requests.post(f"{GRAPH_URL}/{self.user_id}/media_publish", data={
            "creation_id": container_id,
            "access_token": self.access_token,
        }, timeout=30)
        publish.raise_for_status()
        print(f"[INSTAGRAM GRAPH] Reel published: {publish.json().get('id', '')}")
        return True
