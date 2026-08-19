# lark-mcp

A FastMCP (Python) server that wraps [`lark-cli`](https://github.com/larksuite/cli) to expose
Lark/Feishu (IM, calendar, contacts, docs, drive, base, task) as MCP tools, gated by OAuth 2.1.

- `PUBLIC_BASE_URL/authorize` federates to Lark's real login (`OAuthProxy`) purely to identify
  the caller by `open_id` — it does not grant any Lark API scope itself.
- Acting *as a specific person* (rather than the shared bot) is handled separately, via
  `lark-cli`'s own device-flow login (`lark_login_start` / `lark_login_confirm` tools), since
  `lark-cli` only trusts tokens it obtained itself.
- Each linked user gets an isolated `$HOME` on the shared PVC (`/data/homes/<open_id>`), so
  `lark-cli`'s per-user token store doesn't collide across identities under one app-id.

## Deploying

1. Build the image: `docker build -t <your-registry>/lark-mcp:latest .`
2. Fill in `lark-mcp-deployment.yaml`'s `Secret` (app-id/app-secret from the Lark Developer
   Console, and a signing key via `openssl rand -hex 32`) and your own hostname/TLS secret name.
3. Register `https://<your-hostname>/auth/callback` as a redirect URI for your Lark app.
4. `kubectl apply -f lark-mcp-deployment.yaml -n <namespace>`

## Using with Amazon Quick Desktop

Quick Desktop's **Remote** connection type (native HTTP + OAuth) has a track record of failing
against otherwise spec-compliant MCP servers with a bare `401` — several confirmed cases in
AWS's own Quick community forum, independent of this server. The reliable path is Quick's
**Local** connection type via [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) as a
stdio bridge: `mcp-remote` performs the full browser-based OAuth handshake itself, and Quick
just talks to it over stdio, never touching OAuth directly.

In Quick Desktop: **Settings → Capabilities → MCP Servers → Add → Local**

| Field | Value |
|---|---|
| Name | `lark-mcp` |
| Command | `npx` |
| Args | `-y mcp-remote@latest https://<your-hostname>/mcp --auth-timeout 300` |

`--auth-timeout 300` matters: the default is 30 seconds, which isn't enough time to click
through the consent screen and log into Lark interactively — the flow will otherwise fail
right at the final redirect with "site can't be reached," even though everything up to that
point worked.

The first tool call opens a real browser window to approve access once; `mcp-remote` caches
the resulting token in `~/.mcp-auth/` afterward.

### Known gotcha: stale local port on re-auth

`mcp-remote` reuses the same local callback port (e.g. `9210`) across runs. If Quick Desktop
doesn't cleanly kill a previous `mcp-remote` process before spawning a new one for re-auth,
the new one crashes with `EADDRINUSE` — the browser still shows "Authorization successful"
(caught by the old, orphaned process), but Quick never receives a working credential from its
own new attempt and just waits indefinitely.

Fix: find and kill the stale listener, then retry.

```bash
lsof -i :9210        # note the PID in LISTEN state
kill -9 <PID>
```

### Amazon Quick / Amazon Q Developer has a known bug in its OAuth state machine when handling re-authentication on expired tokens:

It spawns multiple overlapping authorization states (visible in the logs as duplicate /authorize requests with different state IDs).
When the browser sends the callback to localhost:9210, the local HTTP handler responds with success HTML to the browser, but fails to dispatch the event to the waiting MCP client thread.

# How to resolve it
1. Restart Amazon Quick / Reload IDE Window:
- Fully restart Amazon Quick (or in VS Code / JetBrains: Developer: Reload Window or restart the IDE).
- This kills the orphaned localhost:9210 listener and clears the stuck internal state.
2. Re-connect with a clean initial auth:
- Reconnect or click authorize after the restart. Fresh/initial authentication succeeds cleanly, unlike the in-place re-auth flow.

