"""HTTP tests for the platform connection flow and the live metrics endpoint.

Provider traffic is faked by replacing ``accounts.http_json``; everything else — state
handling, token encryption, database writes, redirects and the metrics query — is the
real implementation. Skipped when FastAPI/httpx are unavailable.
"""

import base64
import importlib.util
import json
import os
import tempfile
import unittest
import uuid

HAVE_FASTAPI = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))

if HAVE_FASTAPI:
    os.environ.setdefault("VYRALIS_DATA_DIR", tempfile.mkdtemp(prefix="vyralis-connections-tests-"))

    from fastapi.testclient import TestClient  # noqa: E402

    from backend.app import accounts, main  # noqa: E402

    main.init_db()


GOOGLE_TOKEN = {
    "access_token": "at-live", "refresh_token": "rt-live", "expires_in": 3599,
    "scope": "https://www.googleapis.com/auth/youtube.upload",
}
CHANNEL = {
    "items": [{
        "id": "UC-test",
        "snippet": {"title": "Test Channel", "thumbnails": {"default": {"url": "https://img/yt.jpg"}}},
        "statistics": {"subscriberCount": "1234", "viewCount": "56789", "videoCount": "10"},
    }]
}


def fake_transport(token_payload=None, channel_payload=None):
    """Replay the Google token and channel endpoints."""
    token_payload = token_payload or GOOGLE_TOKEN
    channel_payload = channel_payload or CHANNEL

    def transport(method, url, *, data=None, form=None, headers=None):
        if "oauth2.googleapis.com" in url:
            return 200, token_payload
        if "youtube/v3/channels" in url:
            return 200, channel_payload
        raise AssertionError(f"unexpected provider call: {method} {url}")

    return transport


@unittest.skipUnless(HAVE_FASTAPI, "FastAPI and httpx are required for API tests")
class ConnectionFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app, follow_redirects=False)

    def setUp(self):
        self._env = dict(os.environ)
        os.environ["GOOGLE_CLIENT_ID"] = "client-id"
        os.environ["GOOGLE_CLIENT_SECRET"] = "client-secret"
        os.environ.pop("TIKTOK_CLIENT_KEY", None)
        os.environ.pop("TIKTOK_CLIENT_SECRET", None)
        os.environ["VYRALIS_FRONTEND_URL"] = "https://studio.test"
        os.environ["VYRALIS_PUBLIC_URL"] = "https://api.test"
        self._http = accounts.http_json
        self._basic = main.BASIC_AUTH
        main.BASIC_AUTH = ""
        # Start each test from a clean account table so assertions stay independent.
        with main.connect() as db:
            db.execute("DELETE FROM platform_accounts")
            db.execute("DELETE FROM oauth_states")

    def tearDown(self):
        accounts.http_json = self._http
        main.BASIC_AUTH = self._basic
        os.environ.clear()
        os.environ.update(self._env)

    def start(self, platform="youtube"):
        response = self.client.post(f"/api/connections/{platform}/start", json={"next_path": "/connections"})
        return response

    def state_from(self, authorize_url):
        return authorize_url.split("state=")[1].split("&")[0]

    def connect(self):
        accounts.http_json = fake_transport()
        start = self.start()
        state = self.state_from(start.json()["authorize_url"])
        response = self.client.get(f"/api/oauth/youtube/callback?code=abc&state={state}")
        self.assertEqual(response.status_code, 303)
        return response

    # --- listing and starting ------------------------------------------

    def test_connections_lists_every_provider_with_callback(self):
        payload = self.client.get("/api/connections").json()
        providers = {p["key"]: p for p in payload["providers"]}
        self.assertEqual(set(providers), {"youtube", "tiktok", "instagram", "x"})
        self.assertTrue(providers["youtube"]["configured"])
        self.assertFalse(providers["tiktok"]["configured"])
        self.assertEqual(providers["youtube"]["callback_url"], "https://api.test/api/oauth/youtube/callback")
        self.assertEqual(providers["youtube"]["accounts"], [])

    def test_unconfigured_platform_cannot_start(self):
        response = self.start("tiktok")
        self.assertEqual(response.status_code, 409)
        self.assertIn("TIKTOK_CLIENT_KEY", response.json()["detail"])

    def test_unknown_platform_is_404(self):
        self.assertEqual(self.start("myspace").status_code, 404)

    def test_start_returns_provider_url_and_stores_one_time_state(self):
        response = self.start()
        self.assertEqual(response.status_code, 200)
        authorize_url = response.json()["authorize_url"]
        self.assertIn("accounts.google.com", authorize_url)
        self.assertIn("code_challenge_method=S256", authorize_url)
        state = self.state_from(authorize_url)
        with main.connect() as db:
            row = db.execute("SELECT * FROM oauth_states WHERE state=?", (state,)).fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(row["code_verifier"])

    # --- callback -------------------------------------------------------

    def test_callback_stores_encrypted_account_and_redirects(self):
        response = self.connect()
        self.assertEqual(response.headers["location"], "https://studio.test/connections?connected=youtube")
        payload = self.client.get("/api/connections").json()
        youtube = {p["key"]: p for p in payload["providers"]}["youtube"]
        account = youtube["accounts"][0]
        self.assertEqual(account["display_name"], "Test Channel")
        self.assertEqual(account["metrics"], {"subscribers": 1234, "views": 56789, "videos": 10})
        with main.connect() as db:
            row = db.execute("SELECT access_token, refresh_token FROM platform_accounts WHERE id=?", (account["id"],)).fetchone()
        self.assertNotIn("at-live", row["access_token"])
        self.assertEqual(main.CIPHER.decrypt(row["access_token"]), "at-live")
        self.assertEqual(main.CIPHER.decrypt(row["refresh_token"]), "rt-live")

    def test_state_cannot_be_replayed(self):
        self.connect()
        state = self.state_from(self.start().json()["authorize_url"])
        self.client.get(f"/api/oauth/youtube/callback?code=abc&state={state}")
        replay = self.client.get(f"/api/oauth/youtube/callback?code=abc&state={state}")
        self.assertEqual(replay.status_code, 303)
        self.assertIn("error=", replay.headers["location"])

    def test_provider_denial_redirects_with_message(self):
        response = self.client.get(
            "/api/oauth/youtube/callback?error=access_denied&error_description=User%20denied"
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("User", response.headers["location"])

    def test_missing_code_redirects_with_message(self):
        response = self.client.get("/api/oauth/youtube/callback?state=nothing")
        self.assertIn("error=", response.headers["location"])

    def test_callback_without_channel_does_not_create_an_account(self):
        accounts.http_json = fake_transport(channel_payload={"items": []})
        start = self.start()
        state = self.state_from(start.json()["authorize_url"])
        response = self.client.get(f"/api/oauth/youtube/callback?code=abc&state={state}")
        self.assertIn("error=", response.headers["location"])
        payload = self.client.get("/api/connections").json()
        youtube = {p["key"]: p for p in payload["providers"]}["youtube"]
        self.assertEqual(youtube["accounts"], [])

    # --- sync, disconnect, metrics -------------------------------------

    def test_sync_updates_metrics_and_status(self):
        self.connect()
        account_id = self.client.get("/api/connections").json()["providers"][0]["accounts"][0]["id"]
        updated_channel = json.loads(json.dumps(CHANNEL))
        updated_channel["items"][0]["statistics"]["subscriberCount"] = "9999"
        accounts.http_json = fake_transport(channel_payload=updated_channel)
        response = self.client.post(f"/api/connections/{account_id}/sync")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metrics"]["subscribers"], 9999)
        self.assertTrue(response.json()["metrics_synced_at"])

    def test_sync_failure_marks_the_account_and_returns_502(self):
        self.connect()
        account_id = self.client.get("/api/connections").json()["providers"][0]["accounts"][0]["id"]

        def broken(method, url, **kwargs):
            raise accounts.OAuthError("token revoked")

        accounts.http_json = broken
        self.assertEqual(self.client.post(f"/api/connections/{account_id}/sync").status_code, 502)
        with main.connect() as db:
            status = db.execute("SELECT status FROM platform_accounts WHERE id=?", (account_id,)).fetchone()["status"]
        self.assertEqual(status, "error")

    def test_disconnect_removes_tokens(self):
        self.connect()
        account_id = self.client.get("/api/connections").json()["providers"][0]["accounts"][0]["id"]
        response = self.client.delete(f"/api/connections/{account_id}")
        self.assertEqual(response.status_code, 200)
        with main.connect() as db:
            self.assertIsNone(db.execute("SELECT * FROM platform_accounts WHERE id=?", (account_id,)).fetchone())
        self.assertEqual(self.client.delete(f"/api/connections/{account_id}").status_code, 404)

    def test_metrics_endpoint_counts_real_rows(self):
        project_id, clip_id = uuid.uuid4().hex, uuid.uuid4().hex
        with main.connect() as db:
            asset_id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?)",
                (asset_id, "m.mp4", 2048, "video/mp4", "/tmp/none.mp4", main.now(), 5.0, 640, 360),
            )
            db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)",
                       (project_id, asset_id, "Metrics", "ready", main.now(), main.now()))
            db.execute(
                "INSERT INTO clips(id,project_id,rank,start_seconds,end_seconds,score,score_breakdown,reason,"
                "transcript,title,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (clip_id, project_id, 1, 0.0, 2.0, 70, "{}", "r", "t", "T", "ready", main.now()),
            )
            db.execute(
                "INSERT INTO clip_exports(id,clip_id,preset,status,quality_report,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, clip_id, "9:16", "ready", json.dumps({"status": "pass"}), main.now(), main.now()),
            )
        metrics = self.client.get("/api/metrics").json()
        self.assertGreaterEqual(metrics["studio"]["clips"], 1)
        self.assertGreaterEqual(metrics["studio"]["assets"], 1)
        self.assertGreaterEqual(metrics["studio"]["storage_bytes"], 2048)
        self.assertGreaterEqual(metrics["studio"]["exports"]["ready"], 1)
        self.assertGreaterEqual(metrics["studio"]["quality"]["pass"], 1)
        self.assertIn("generated_at", metrics)


@unittest.skipUnless(HAVE_FASTAPI, "FastAPI and httpx are required for API tests")
class BasicAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def setUp(self):
        self._basic = main.BASIC_AUTH

    def tearDown(self):
        main.BASIC_AUTH = self._basic

    def test_health_stays_open_but_api_is_gated(self):
        main.BASIC_AUTH = "studio:secret"
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        self.assertEqual(self.client.get("/api/connections").status_code, 401)

    def test_correct_credentials_pass(self):
        main.BASIC_AUTH = "studio:secret"
        token = base64.b64encode(b"studio:secret").decode()
        response = self.client.get("/api/connections", headers={"Authorization": f"Basic {token}"})
        self.assertEqual(response.status_code, 200)

    def test_wrong_credentials_fail(self):
        main.BASIC_AUTH = "studio:secret"
        token = base64.b64encode(b"studio:wrong").decode()
        response = self.client.get("/api/connections", headers={"Authorization": f"Basic {token}"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response.headers["www-authenticate"])

    def test_gate_is_off_when_unset(self):
        main.BASIC_AUTH = ""
        self.assertEqual(self.client.get("/api/connections").status_code, 200)


if __name__ == "__main__":
    unittest.main()
