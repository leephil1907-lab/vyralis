# Connecting social accounts

VYRALIS connects to YouTube, TikTok, Instagram and X with each platform's own OAuth 2.0
authorization-code flow. There is no shared password, no scraping of your session and no
stored browser cookies.

Set the credentials in the API environment (see `.env.example`). A platform with no
credentials appears on the Connections page as **Not configured**, with the exact
variable names and redirect URI to register — it never shows a button that cannot work.

## Redirect URI

For every platform, register this exact URL in the provider console:

```
https://<your-api-host>/api/oauth/<platform>/callback
```

Example for a Render API host: `https://vyralis-api.onrender.com/api/oauth/youtube/callback`.
You can override any platform's URI with `VYRALIS_<PLATFORM>_REDIRECT_URI`
(for example `VYRALIS_YOUTUBE_REDIRECT_URI`) if the provider requires a different host.

## Platform setup

### YouTube

1. Google Cloud Console → **APIs & Services** → enable **YouTube Data API v3**.
2. **OAuth consent screen** → External → add yourself as a test user while in testing.
3. **Credentials** → Create credentials → OAuth client ID → **Web application**.
4. Authorised redirect URI: `https://<api-host>/api/oauth/youtube/callback`.
5. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

Scopes requested: `youtube.readonly`, `youtube.upload`, `yt-analytics.readonly`.
Google's verification matters for *public* uploads from unverified apps; a personal
"testing" client can upload to a channel you own but tokens expire after 7 days in
testing mode. Publish the app (or use an internal Workspace client) for long-lived use.

### TikTok

1. TikTok for Developers → **Manage apps** → create an app → add **Login Kit**.
2. Add the redirect URI `https://<api-host>/api/oauth/tiktok/callback`.
3. Request scopes `user.info.basic`, `video.upload`, `video.publish`.
4. Set `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET`.

`video.publish` requires TikTok's app review before direct posting is permitted.
Until then the connection reads profile metrics and `video.upload` can send a draft.

### Instagram (Meta)

1. Meta for Developers → create an app → add the **Instagram Graph API** product.
2. Facebook Login → Settings → add `https://<api-host>/api/oauth/instagram/callback`
   as a valid OAuth redirect URI.
3. Set `META_APP_ID` and `META_APP_SECRET`.
4. The Instagram account must be a **Business or Creator** account linked to a
   Facebook Page you administer.

Scopes requested: `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
`pages_read_engagement`, `business_management`. Public posting also requires Meta app
review for `instagram_content_publish` and a public video URL for the media container.

### X

1. X developer portal → create a project and app with **OAuth 2.0** (confidential client).
2. Add `https://<api-host>/api/oauth/x/callback` as a callback URL.
3. Set `X_CLIENT_ID` and `X_CLIENT_SECRET`.

Scopes requested: `tweet.read`, `tweet.write`, `users.read`, `offline.access`
(`offline.access` is what lets the server refresh tokens without you re-approving).

## What a connection does

- Stores the provider's access and refresh tokens **encrypted** (Fernet, key derived from
  `VYRALIS_AUTH_SECRET`, or a `0600` key file in the data directory for local use).
- Reads the account profile and the public numbers the provider returns: subscribers,
  views, videos, followers, likes, posts. Missing fields stay empty rather than becoming
  zero.
- Refreshes access tokens automatically when they expire (where the provider supports it).
- Lets you refresh metrics or disconnect at any time. Disconnect deletes the tokens.

## What a connection does **not** do

Connecting does not publish anything. Each platform requires an approved app for
programmatic posting, and the studio deliberately has no "post now" button until a
publishing adapter exists for that platform and is approved. The delivery flow remains a
validated download you upload yourself.

## Verifying a connection

1. Open **Connections** in the studio sidebar.
2. Click **Connect** on a configured platform and approve the scopes.
3. You land back on `/connections` with the account, avatar and real metrics.
4. Press **Refresh metrics** to confirm the stored token still works.
5. If something fails, the error text comes from the provider (for example
   `invalid_grant: Bad Request`) and the account is marked as needing attention.

Provider traffic is the only untested part of this flow in CI: the tests substitute a
fake transport, so the request shapes, state handling, encryption and database writes are
covered, but the first real connection must be made by you against a live provider.
