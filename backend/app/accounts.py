"""OAuth connections to social platforms.

Every platform below uses a real authorization-code flow against the provider's own
endpoints, with PKCE where the provider supports it. Credentials come from the
environment; a provider without credentials is reported as *unconfigured* instead
of showing a button that cannot work.

Network access is funnelled through the module-level ``http_json`` function, so the
whole surface can be tested without network access by substituting a fake transport.

Nothing here invents data: profile and metric fetching parses exactly what the
provider returns, and a missing field stays missing.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

dictish = dict[str, Any]

STATE_TTL_SECONDS = 15 * 60
HTTP_TIMEOUT = 20


class AccountError(RuntimeError):
    """Base class for connection problems that are safe to show a user."""


class ProviderNotConfigured(AccountError):
    """The deployment has no OAuth client for this platform."""


class OAuthError(AccountError):
    """The provider rejected the request or returned an unusable response."""


@dataclass(frozen=True)
class Provider:
    key: str
    label: str
    authorize_url: str
    token_url: str
    client_id_env: str
    client_secret_env: str
    scopes: tuple[str, ...]
    scope_separator: str = " "
    uses_pkce: bool = True
    extra_authorize: dict[str, str] = field(default_factory=dict)
    setup_note: str = ""
    identity_url: str = ""

    @property
    def configured(self) -> bool:
        return bool(os.getenv(self.client_id_env) and os.getenv(self.client_secret_env))

    def credentials(self) -> tuple[str, str]:
        client_id = os.getenv(self.client_id_env, "").strip()
        client_secret = os.getenv(self.client_secret_env, "").strip()
        if not client_id or not client_secret:
            raise ProviderNotConfigured(
                f"{self.label} is not configured on this server. "
                f"Set {self.client_id_env} and {self.client_secret_env} to enable it."
            )
        return client_id, client_secret


PROVIDERS: dict[str, Provider] = {
    "youtube": Provider(
        key="youtube",
        label="YouTube",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        client_id_env="GOOGLE_CLIENT_ID",
        client_secret_env="GOOGLE_CLIENT_SECRET",
        scopes=(
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ),
        extra_authorize={
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        },
        identity_url="https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
        setup_note=(
            "Create an OAuth client (Web application) in Google Cloud, enable the YouTube Data API v3 "
            "and add the callback URL below as an authorised redirect URI."
        ),
    ),
    "tiktok": Provider(
        key="tiktok",
        label="TikTok",
        authorize_url="https://www.tiktok.com/v2/auth/authorize/",
        token_url="https://open.tiktokapis.com/v2/oauth/token/",
        client_id_env="TIKTOK_CLIENT_KEY",
        client_secret_env="TIKTOK_CLIENT_SECRET",
        scopes=("user.info.basic", "video.upload", "video.publish"),
        scope_separator=",",
        identity_url="https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,display_name,avatar_url,follower_count,following_count,likes_count,video_count",
        setup_note=(
            "Create a Login Kit app in the TikTok developer portal, add the callback URL as a redirect URI, "
            "and request the video.publish scope (it needs app review before direct posting works)."
        ),
    ),
    "instagram": Provider(
        key="instagram",
        label="Instagram",
        authorize_url="https://www.facebook.com/v21.0/dialog/oauth",
        token_url="https://graph.facebook.com/v21.0/oauth/access_token",
        client_id_env="META_APP_ID",
        client_secret_env="META_APP_SECRET",
        scopes=(
            "instagram_basic",
            "instagram_content_publish",
            "pages_show_list",
            "pages_read_engagement",
            "business_management",
        ),
        scope_separator=",",
        uses_pkce=False,
        identity_url="https://graph.facebook.com/v21.0/me/accounts?fields=instagram_business_account{id,username,profile_picture_url,followers_count,media_count},name",
        setup_note=(
            "Create a Meta app with the Instagram Graph API product, add the callback URL as a valid OAuth "
            "redirect URI, and connect an Instagram Business account that is linked to a Facebook Page."
        ),
    ),
    "x": Provider(
        key="x",
        label="X",
        authorize_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        client_id_env="X_CLIENT_ID",
        client_secret_env="X_CLIENT_SECRET",
        scopes=("tweet.read", "tweet.write", "users.read", "offline.access"),
        identity_url="https://api.twitter.com/2/users/me?user.fields=public_metrics,profile_image_url,username,name",
        setup_note=(
            "Create an OAuth 2.0 app in the X developer portal with a confidential client, enable the "
            "callback URL below, and request write access."
        ),
    ),
}


def provider_info() -> list[dict[str, Any]]:
    """Public description of each platform, safe to send to the browser."""
    return [
        {
            "key": provider.key,
            "label": provider.label,
            "configured": provider.configured,
            "scopes": list(provider.scopes),
            "client_id_env": provider.client_id_env,
            "client_secret_env": provider.client_secret_env,
            "uses_pkce": provider.uses_pkce,
            "setup_note": provider.setup_note,
        }
        for provider in PROVIDERS.values()
    ]


def get_provider(key: str) -> Provider:
    provider = PROVIDERS.get(key)
    if provider is None:
        raise AccountError(f"Unknown platform '{key}'.")
    return provider


# --------------------------------------------------------------------------- #
# HTTP transport (single place that touches the network)
# --------------------------------------------------------------------------- #


def http_json(
    method: str,
    url: str,
    *,
    data: dictish | None = None,
    form: dictish | None = None,
    headers: dictish | None = None,
) -> tuple[int, Any]:
    """Perform a JSON or form request and return ``(status, parsed_body)``."""
    body: bytes | None = None
    all_headers = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        body = json.dumps(data).encode()
        all_headers.setdefault("Content-Type", "application/json")
    elif form is not None:
        body = urllib.parse.urlencode(form).encode()
        all_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    request = urllib.request.Request(url, data=body, headers=all_headers, method=method.upper())
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, _parse_body(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        parsed = _parse_body(raw)
        message = _error_message(parsed, raw)
        raise OAuthError(f"Provider rejected the request ({exc.code}): {message}") from exc
    except urllib.error.URLError as exc:
        raise OAuthError(f"Could not reach the provider: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OAuthError("The provider did not answer in time.") from exc


def _parse_body(raw: str) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw[:500]}


def _error_message(parsed: Any, raw: str) -> str:
    """Human-readable provider error, keeping the machine code when there is one."""
    if isinstance(parsed, dict):
        code = parsed.get("error")
        if isinstance(code, dict):
            code = code.get("code") or code.get("type") or code.get("message")
        description = parsed.get("error_description") or parsed.get("error_message") or parsed.get("message")
        if isinstance(description, (dict, list)):
            description = None
        if code and description and str(code) not in str(description):
            return f"{code}: {description}"
        for value in (description, code):
            if isinstance(value, str) and value:
                return value
    return raw[:200] or "no details returned"


# --------------------------------------------------------------------------- #
# PKCE and state
# --------------------------------------------------------------------------- #


def pkce_pair() -> tuple[str, str]:
    """Return ``(verifier, challenge)`` for S256 PKCE."""
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def new_state() -> str:
    return secrets.token_urlsafe(32)


def state_is_fresh(created_at: str | float | int, now: float | None = None) -> bool:
    try:
        stamp = float(created_at)
    except (TypeError, ValueError):
        return False
    current = time.time() if now is None else now
    return 0 <= current - stamp <= STATE_TTL_SECONDS


# --------------------------------------------------------------------------- #
# Authorization URL and token exchange
# --------------------------------------------------------------------------- #


def callback_url(base_url: str, platform: str) -> str:
    override = os.getenv(f"VYRALIS_{platform.upper()}_REDIRECT_URI")
    if override:
        return override
    return f"{base_url.rstrip('/')}/api/oauth/{platform}/callback"


def build_authorize_url(
    platform: str,
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str | None = None,
) -> str:
    provider = get_provider(platform)
    params: dictish = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": provider.scope_separator.join(provider.scopes),
        "state": state,
        **provider.extra_authorize,
    }
    if provider.uses_pkce:
        if not code_challenge:
            raise AccountError("This platform requires PKCE, but no challenge was generated.")
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    if platform == "tiktok":
        # TikTok documents client_key rather than client_id.
        params["client_key"] = params.pop("client_id")
    return f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"


def exchange_code(platform: str, code: str, *, redirect_uri: str, code_verifier: str | None = None) -> dictish:
    provider = get_provider(platform)
    client_id, client_secret = provider.credentials()
    if platform == "tiktok":
        form = {
            "client_key": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            form["code_verifier"] = code_verifier
        _, payload = http_json("POST", provider.token_url, form=form)
    elif platform == "instagram":
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        _, payload = http_json("GET", f"{provider.token_url}?{urllib.parse.urlencode(params)}")
    else:
        form = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            form["code_verifier"] = code_verifier
        _, payload = http_json("POST", provider.token_url, form=form)
    return _normalise_tokens(payload)


def _normalise_tokens(payload: Any) -> dictish:
    if not isinstance(payload, dict):
        raise OAuthError("The provider returned an unexpected token response.")
    access = payload.get("access_token")
    if not access:
        raise OAuthError(_error_message(payload, json.dumps(payload))[:300])
    expires_in = payload.get("expires_in")
    expires_at = ""
    try:
        if expires_in:
            expires_at = _iso(time.time() + float(expires_in))
    except (TypeError, ValueError):
        expires_at = ""
    scopes = payload.get("scope")
    if isinstance(scopes, str):
        scopes = scopes.replace(",", " ").split()
    return {
        "access_token": str(access),
        "refresh_token": str(payload.get("refresh_token") or ""),
        "expires_at": expires_at,
        "token_type": payload.get("token_type"),
        "scopes": scopes if isinstance(scopes, list) else [],
        "open_id": payload.get("open_id") or "",
    }


def refresh_access_token(platform: str, refresh_token: str) -> dictish:
    """Exchange a refresh token for a new access token."""
    provider = get_provider(platform)
    client_id, client_secret = provider.credentials()
    if not refresh_token:
        raise OAuthError(f"{provider.label} did not provide a refresh token; reconnect the account.")
    if platform == "tiktok":
        form = {
            "client_key": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        _, payload = http_json("POST", provider.token_url, form=form)
    elif platform == "instagram":
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "fb_exchange_token": refresh_token,
        }
        _, payload = http_json("GET", f"{provider.token_url}?{urllib.parse.urlencode(params)}")
    else:
        form = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        _, payload = http_json("POST", provider.token_url, form=form)
    return _normalise_tokens(payload)


# --------------------------------------------------------------------------- #
# Identity and live metrics
# --------------------------------------------------------------------------- #


def fetch_identity(platform: str, access_token: str) -> dictish:
    """Fetch the connected account and its current public metrics."""
    provider = get_provider(platform)
    if platform == "tiktok":
        status, payload = http_json(
            "GET",
            provider.identity_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return _parse_tiktok(payload)
    if platform == "instagram":
        return _parse_instagram(access_token)
    if platform == "youtube":
        _, payload = http_json(
            "GET",
            provider.identity_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return _parse_youtube(payload)
    if platform == "x":
        _, payload = http_json(
            "GET",
            provider.identity_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return _parse_x(payload)
    raise AccountError(f"Unknown platform '{platform}'.")


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_youtube(payload: Any) -> dictish:
    items = payload.get("items") if isinstance(payload, dict) else None
    if not items:
        raise OAuthError("This Google account has no YouTube channel to connect.")
    channel = items[0]
    snippet = channel.get("snippet") or {}
    stats = channel.get("statistics") or {}
    thumbs = snippet.get("thumbnails") or {}
    avatar = (thumbs.get("default") or {}).get("url") or (thumbs.get("medium") or {}).get("url")
    return {
        "external_id": channel.get("id") or "",
        "display_name": snippet.get("title") or "YouTube channel",
        "avatar_url": avatar,
        "metrics": {
            "subscribers": _int(stats.get("subscriberCount")),
            "views": _int(stats.get("viewCount")),
            "videos": _int(stats.get("videoCount")),
        },
    }


def _parse_tiktok(payload: Any) -> dictish:
    data = (payload.get("data") or {}) if isinstance(payload, dict) else {}
    user = data.get("user") if isinstance(data, dict) else None
    if not user:
        raise OAuthError("TikTok did not return a user profile for this account.")
    return {
        "external_id": user.get("open_id") or user.get("union_id") or "",
        "display_name": user.get("display_name") or "TikTok account",
        "avatar_url": user.get("avatar_url"),
        "metrics": {
            "followers": _int(user.get("follower_count")),
            "following": _int(user.get("following_count")),
            "likes": _int(user.get("likes_count")),
            "videos": _int(user.get("video_count")),
        },
    }


def _parse_instagram(access_token: str) -> dictish:
    _, pages = http_json(
        "GET",
        f"{PROVIDERS['instagram'].identity_url}&access_token={urllib.parse.quote(access_token)}",
    )
    candidates = [page for page in (pages.get("data") or []) if page.get("instagram_business_account")]
    if not candidates:
        raise OAuthError(
            "No Instagram Business account is linked to a Facebook Page on this login. "
            "Link the account in Meta Business Suite and try again."
        )
    page = candidates[0]
    account = page["instagram_business_account"]
    return {
        "external_id": str(account.get("id") or ""),
        "display_name": account.get("username") or page.get("name") or "Instagram account",
        "avatar_url": account.get("profile_picture_url"),
        "metrics": {
            "followers": _int(account.get("followers_count")),
            "media": _int(account.get("media_count")),
        },
        "extra": {"page_id": page.get("id"), "page_name": page.get("name")},
    }


def _parse_x(payload: Any) -> dictish:
    data = (payload.get("data") or {}) if isinstance(payload, dict) else {}
    if not data.get("id"):
        raise OAuthError("X did not return a profile for this account.")
    metrics = data.get("public_metrics") or {}
    return {
        "external_id": str(data.get("id")),
        "display_name": data.get("name") or data.get("username") or "X account",
        "avatar_url": data.get("profile_image_url"),
        "metrics": {
            "followers": _int(metrics.get("followers_count")),
            "following": _int(metrics.get("following_count")),
            "posts": _int(metrics.get("tweet_count")),
        },
    }


# --------------------------------------------------------------------------- #
# Token encryption at rest
# --------------------------------------------------------------------------- #


class TokenCipher:
    """Fernet-backed encryption for provider tokens stored in the database."""

    def __init__(self, key: bytes):
        from cryptography.fernet import Fernet

        self._fernet = Fernet(key)

    @classmethod
    def from_secret(cls, secret: str) -> "TokenCipher":
        digest = hashlib.sha256(secret.encode()).digest()
        return cls(base64.urlsafe_b64encode(digest))

    @classmethod
    def from_key_file(cls, path: "os.PathLike[str] | str") -> "TokenCipher":
        from pathlib import Path

        key_path = Path(path)
        if not key_path.exists():
            from cryptography.fernet import Fernet

            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(Fernet.generate_key().decode())
            try:
                os.chmod(key_path, 0o600)
            except OSError:
                pass
        return cls(key_path.read_text().strip().encode())

    def encrypt(self, value: str | None) -> str:
        if not value:
            return ""
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str | None) -> str:
        if not value:
            return ""
        return self._fernet.decrypt(value.encode()).decode()


def load_cipher(data_dir: "os.PathLike[str] | str") -> TokenCipher:
    """Use VYRALIS_AUTH_SECRET when provided, else a 0600 key file in the data dir."""
    secret = os.getenv("VYRALIS_AUTH_SECRET", "").strip()
    if secret:
        return TokenCipher.from_secret(secret)
    from pathlib import Path

    return TokenCipher.from_key_file(Path(data_dir) / ".token-key")


def _iso(timestamp: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def token_is_expired(expires_at: str | None, skew_seconds: int = 60) -> bool:
    if not expires_at:
        return False
    try:
        from datetime import datetime, timezone

        expiry = datetime.fromisoformat(expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry.timestamp() - skew_seconds <= time.time()
    except ValueError:
        return False
