"""
spotify_client.py
Minimal Spotify Web API client using the Client Credentials flow -
enough to search the public catalog and get a track's Spotify URI.
This does NOT require the user to log into Spotify or grant any
permission; it's app-only auth, completely free, no partnership
approval needed (unlike Amazon Music's API).

One-time setup:
1. Go to https://developer.spotify.com/dashboard and log in.
2. Click "Create app". Any name/description is fine. For "Redirect
   URI" put http://127.0.0.1:8888/callback (required field, unused
   by this script - Spotify no longer accepts "localhost" here,
   it must be the literal loopback IP).
3. Open the app you just created -> Settings -> copy the Client ID
   and Client Secret.
4. Create a file called .env in this same folder (copy .env.example
   and rename it) and fill in your real values:
       SPOTIFY_CLIENT_ID=your-real-client-id
       SPOTIFY_CLIENT_SECRET=your-real-client-secret

   .env is listed in .gitignore - never commit it or share it, even
   though this app can only search, not access anyone's account.
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env in the current working directory into os.environ

_token = None
_token_expires_at = 0.0


def _load_credentials():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    return client_id, client_secret


def _get_access_token():
    """App-only access token (Client Credentials flow). Cached until
    it's about to expire, so we're not requesting a new one every search."""
    global _token, _token_expires_at

    if _token and time.time() < _token_expires_at:
        return _token

    client_id, client_secret = _load_credentials()
    if not client_id or not client_secret:
        return None

    try:
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    _token = data["access_token"]
    _token_expires_at = time.time() + data.get("expires_in", 3600) - 30
    return _token


def search_track(query: str):
    """Returns a Spotify track URI (e.g. 'spotify:track:3n3Ppam...')
    for the best match to `query`, or None if not found / not
    configured yet."""
    token = _get_access_token()
    if not token:
        return None

    try:
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "track", "limit": 1},
            timeout=10,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    items = response.json().get("tracks", {}).get("items", [])
    if not items:
        return None

    return items[0]["uri"]