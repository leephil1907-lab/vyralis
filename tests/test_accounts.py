"""Tests for social platform OAuth connections.

No network is used: ``accounts.http_json`` is replaced with a fake transport, so the
tests pin the exact requests we send and how provider responses are parsed.
"""

import base64
import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app import accounts


class FakeTransport:
    """Records calls and replays canned responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, *, data=None, form=None, headers=None):
        self.calls.append({
            "method": method, "url": url, "data": data, "form": form, "headers": headers or {}
        })
        if not self.responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return 200, response


class EnvMixin(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        for name in (
            "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET",
            "META_APP_ID", "META_APP_SECRET", "X_CLIENT_ID", "X_CLIENT_SECRET", "VYRALIS_AUTH_SECRET",
        ):
            os.environ.pop(name, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def configure(self, platform, client_id="id-123", client_secret="secret-456"):
        provider = accounts.PROVIDERS[platform]
        os.environ[provider.client_id_env] = client_id
        os.environ[provider.client_secret_env] = client_secret


class ProviderRegistryTests(EnvMixin):
    def test_all_expected_platforms_exist(self):
        self.assertEqual(set(accounts.PROVIDERS), {"youtube", "tiktok", "instagram", "x"})

    def test_unconfigured_providers_report_missing_env_names(self):
        info = {item["key"]: item for item in accounts.provider_info()}
        self.assertFalse(info["youtube"]["configured"])
        self.assertEqual(info["youtube"]["client_id_env"], "GOOGLE_CLIENT_ID")
        self.assertTrue(info["youtube"]["setup_note"])

    def test_configured_provider_reports_true(self):
        self.configure("tiktok")
        info = {item["key"]: item for item in accounts.provider_info()}
        self.assertTrue(info["tiktok"]["configured"])

    def test_credentials_raise_when_missing(self):
        with self.assertRaises(accounts.ProviderNotConfigured) as caught:
            accounts.PROVIDERS["instagram"].credentials()
        self.assertIn("META_APP_ID", str(caught.exception))

    def test_unknown_platform_is_rejected(self):
        with self.assertRaises(accounts.AccountError):
            accounts.get_provider("myspace")


class PkceTests(unittest.TestCase):
    def test_challenge_is_s256_of_the_verifier(self):
        verifier, challenge = accounts.pkce_pair()
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        self.assertEqual(challenge, expected)
        self.assertNotIn("=", challenge)
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)

    def test_pairs_are_unique(self):
        self.assertNotEqual(accounts.pkce_pair()[0], accounts.pkce_pair()[0])


class StateTests(unittest.TestCase):
    def test_fresh_state_is_accepted(self):
        self.assertTrue(accounts.state_is_fresh(time.time()))

    def test_expired_and_garbage_states_are_rejected(self):
        self.assertFalse(accounts.state_is_fresh(time.time() - accounts.STATE_TTL_SECONDS - 5))
        self.assertFalse(accounts.state_is_fresh("not-a-number"))
        self.assertFalse(accounts.state_is_fresh(time.time() + 600))  # clock skew backwards


class AuthorizeUrlTests(EnvMixin):
    def test_youtube_url_has_offline_access_and_pkce(self):
        url = accounts.build_authorize_url(
            "youtube", client_id="cid", redirect_uri="https://app.test/api/oauth/youtube/callback",
            state="st4te", code_challenge="ch4llenge",
        )
        self.assertTrue(url.startswith("https://accounts.google.com/o/oauth2/v2/auth?"))
        query = dict(pair.split("=", 1) for pair in url.split("?", 1)[1].split("&"))
        self.assertEqual(query["client_id"], "cid")
        self.assertEqual(query["state"], "st4te")
        self.assertEqual(query["code_challenge"], "ch4llenge")
        self.assertEqual(query["code_challenge_method"], "S256")
        self.assertEqual(query["access_type"], "offline")
        self.assertEqual(query["response_type"], "code")
        self.assertIn("youtube.upload", query["scope"].replace("%2F", "/").replace("%3A", ":"))

    def test_tiktok_uses_client_key_and_comma_scopes(self):
        url = accounts.build_authorize_url(
            "tiktok", client_id="tiktok-key", redirect_uri="https://app.test/cb", state="s",
            code_challenge="c",
        )
        self.assertIn("client_key=tiktok-key", url)
        self.assertNotIn("client_id=", url)
        self.assertIn("scope=user.info.basic%2Cvideo.upload%2Cvideo.publish", url)

    def test_instagram_skips_pkce(self):
        url = accounts.build_authorize_url(
            "instagram", client_id="meta-id", redirect_uri="https://app.test/cb", state="s"
        )
        self.assertNotIn("code_challenge", url)
        self.assertIn("scope=instagram_basic%2Cinstagram_content_publish", url)

    def test_platform_requiring_pkce_refuses_without_challenge(self):
        with self.assertRaises(accounts.AccountError):
            accounts.build_authorize_url(
                "x", client_id="cid", redirect_uri="https://app.test/cb", state="s", code_challenge=None
            )

    def test_callback_url_uses_public_base_and_env_override(self):
        self.assertEqual(
            accounts.callback_url("https://api.test/", "youtube"),
            "https://api.test/api/oauth/youtube/callback",
        )
        os.environ["VYRALIS_YOUTUBE_REDIRECT_URI"] = "https://custom.test/cb"
        self.assertEqual(accounts.callback_url("https://api.test", "youtube"), "https://custom.test/cb")


class ExchangeTests(EnvMixin):
    def test_google_exchange_sends_an_authorization_code_form(self):
        self.configure("youtube")
        transport = FakeTransport([{
            "access_token": "at", "refresh_token": "rt", "expires_in": 3599,
            "scope": "https://www.googleapis.com/auth/youtube.upload", "token_type": "Bearer",
        }])
        with patch.object(accounts, "http_json", transport):
            tokens = accounts.exchange_code(
                "youtube", "auth-code", redirect_uri="https://app.test/cb", code_verifier="verifier"
            )
        call = transport.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["form"]["grant_type"], "authorization_code")
        self.assertEqual(call["form"]["code"], "auth-code")
        self.assertEqual(call["form"]["code_verifier"], "verifier")
        self.assertEqual(tokens["access_token"], "at")
        self.assertEqual(tokens["refresh_token"], "rt")
        self.assertTrue(tokens["expires_at"])
        self.assertEqual(tokens["scopes"], ["https://www.googleapis.com/auth/youtube.upload"])

    def test_tiktok_exchange_uses_client_key(self):
        self.configure("tiktok")
        transport = FakeTransport([{"access_token": "at", "refresh_token": "rt", "expires_in": 86400}])
        with patch.object(accounts, "http_json", transport):
            accounts.exchange_code("tiktok", "code", redirect_uri="https://app.test/cb", code_verifier="v")
        form = transport.calls[0]["form"]
        self.assertIn("client_key", form)
        self.assertNotIn("client_id", form)

    def test_missing_access_token_is_an_error_with_provider_detail(self):
        self.configure("youtube")
        transport = FakeTransport([{"error": "invalid_grant", "error_description": "Bad Request"}])
        with patch.object(accounts, "http_json", transport), self.assertRaises(accounts.OAuthError) as caught:
            accounts.exchange_code("youtube", "code", redirect_uri="https://app.test/cb")
        self.assertIn("invalid_grant", str(caught.exception))

    def test_unconfigured_platform_cannot_exchange(self):
        with self.assertRaises(accounts.ProviderNotConfigured):
            accounts.exchange_code("x", "code", redirect_uri="https://app.test/cb")

    def test_refresh_requires_a_refresh_token(self):
        self.configure("youtube")
        with self.assertRaises(accounts.OAuthError):
            accounts.refresh_access_token("youtube", "")

    def test_refresh_posts_grant_type(self):
        self.configure("x")
        transport = FakeTransport([{"access_token": "new", "refresh_token": "rotated", "expires_in": 7200}])
        with patch.object(accounts, "http_json", transport):
            tokens = accounts.refresh_access_token("x", "old-refresh")
        form = transport.calls[0]["form"]
        self.assertEqual(form["grant_type"], "refresh_token")
        self.assertEqual(form["refresh_token"], "old-refresh")
        self.assertEqual(tokens["access_token"], "new")


class IdentityTests(EnvMixin):
    def test_youtube_channel_metrics(self):
        transport = FakeTransport([{
            "items": [{
                "id": "UC123",
                "snippet": {"title": "Studio", "thumbnails": {"default": {"url": "https://img/yt.jpg"}}},
                "statistics": {"subscriberCount": "1234", "viewCount": "98765", "videoCount": "42"},
            }]
        }])
        with patch.object(accounts, "http_json", transport):
            identity = accounts.fetch_identity("youtube", "token")
        self.assertEqual(identity["external_id"], "UC123")
        self.assertEqual(identity["display_name"], "Studio")
        self.assertEqual(identity["metrics"], {"subscribers": 1234, "views": 98765, "videos": 42})
        self.assertEqual(transport.calls[0]["headers"]["Authorization"], "Bearer token")

    def test_youtube_account_without_channel_is_explained(self):
        transport = FakeTransport([{"items": []}])
        with patch.object(accounts, "http_json", transport), self.assertRaises(accounts.OAuthError) as caught:
            accounts.fetch_identity("youtube", "token")
        self.assertIn("no YouTube channel", str(caught.exception))

    def test_tiktok_metrics(self):
        transport = FakeTransport([{
            "data": {"user": {
                "open_id": "open-1", "display_name": "Creator", "avatar_url": "https://img/tt.jpg",
                "follower_count": 2000, "following_count": 30, "likes_count": 45000, "video_count": 12,
            }}
        }])
        with patch.object(accounts, "http_json", transport):
            identity = accounts.fetch_identity("tiktok", "token")
        self.assertEqual(identity["external_id"], "open-1")
        self.assertEqual(identity["metrics"]["followers"], 2000)
        self.assertEqual(identity["metrics"]["likes"], 45000)

    def test_instagram_picks_the_business_account(self):
        transport = FakeTransport([{
            "data": [
                {"name": "Personal Page"},
                {"name": "Studio Page", "id": "page-1", "instagram_business_account": {
                    "id": "ig-9", "username": "studio", "profile_picture_url": "https://img/ig.jpg",
                    "followers_count": 810, "media_count": 25,
                }},
            ]
        }])
        with patch.object(accounts, "http_json", transport):
            identity = accounts.fetch_identity("instagram", "token")
        self.assertEqual(identity["external_id"], "ig-9")
        self.assertEqual(identity["display_name"], "studio")
        self.assertEqual(identity["metrics"], {"followers": 810, "media": 25})
        self.assertEqual(identity["extra"]["page_name"], "Studio Page")

    def test_instagram_without_business_account_is_explained(self):
        transport = FakeTransport([{"data": [{"name": "No IG here"}]}])
        with patch.object(accounts, "http_json", transport), self.assertRaises(accounts.OAuthError) as caught:
            accounts.fetch_identity("instagram", "token")
        self.assertIn("Business account", str(caught.exception))

    def test_x_metrics(self):
        transport = FakeTransport([{"data": {
            "id": "42", "name": "Studio", "username": "studio", "profile_image_url": "https://img/x.jpg",
            "public_metrics": {"followers_count": 500, "following_count": 90, "tweet_count": 120},
        }}])
        with patch.object(accounts, "http_json", transport):
            identity = accounts.fetch_identity("x", "token")
        self.assertEqual(identity["metrics"], {"followers": 500, "following": 90, "posts": 120})

    def test_missing_metrics_stay_missing_not_zero(self):
        transport = FakeTransport([{
            "items": [{"id": "UC1", "snippet": {"title": "Hidden"}, "statistics": {"hiddenSubscriberCount": True}}]
        }])
        with patch.object(accounts, "http_json", transport):
            identity = accounts.fetch_identity("youtube", "token")
        self.assertIsNone(identity["metrics"]["subscribers"])


class TokenCipherTests(unittest.TestCase):
    def test_roundtrip_and_wrong_key(self):
        cipher = accounts.TokenCipher.from_secret("first-secret")
        encrypted = cipher.encrypt("ya29.token")
        self.assertNotIn("ya29", encrypted)
        self.assertEqual(cipher.decrypt(encrypted), "ya29.token")
        with self.assertRaises(Exception):
            accounts.TokenCipher.from_secret("other-secret").decrypt(encrypted)

    def test_empty_values_stay_empty(self):
        cipher = accounts.TokenCipher.from_secret("s")
        self.assertEqual(cipher.encrypt(""), "")
        self.assertEqual(cipher.decrypt(None), "")

    def test_secret_env_is_used_and_deterministic(self):
        os.environ["VYRALIS_AUTH_SECRET"] = "env-secret"
        try:
            first = accounts.load_cipher(tempfile.mkdtemp())
            second = accounts.load_cipher(tempfile.mkdtemp())
            self.assertEqual(first.decrypt(first.encrypt("token")), "token")
            self.assertEqual(first.decrypt(second.encrypt("token")), "token")
        finally:
            os.environ.pop("VYRALIS_AUTH_SECRET", None)

    def test_key_file_is_created_private_and_reused(self):
        directory = Path(tempfile.mkdtemp())
        first = accounts.load_cipher(directory)
        key_file = directory / ".token-key"
        self.assertTrue(key_file.exists())
        mode = key_file.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)
        second = accounts.load_cipher(directory)
        self.assertEqual(first.decrypt(second.encrypt("abc")), "abc")


class ExpiryTests(unittest.TestCase):
    def test_expiry_detection(self):
        past = accounts._iso(time.time() - 10)
        future = accounts._iso(time.time() + 3600)
        self.assertTrue(accounts.token_is_expired(past))
        self.assertFalse(accounts.token_is_expired(future))
        self.assertFalse(accounts.token_is_expired(""))
        self.assertFalse(accounts.token_is_expired("garbage"))


if __name__ == "__main__":
    unittest.main()
