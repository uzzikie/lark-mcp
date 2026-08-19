from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from key_value.aio.stores.disk import DiskStore
from starlette.routing import Route

from . import config
from .auth import LarkTokenVerifier
from .identity import ensure_bot_identity

client_storage = DiskStore(directory=config.OAUTH_STORE_DIR)


class LarkOAuthProxy(OAuthProxy):
    def _prepare_scopes_for_token_exchange(self, scopes: list[str]) -> list[str]:
        # Mirrors the extra_authorize_params scope override below, but for the second,
        # independent place OAuthProxy forwards client-requested scopes upstream: the
        # authorization-code-for-token exchange. Lark's token endpoint hard-rejects
        # "profile"/"openid"/"email" here too ("invalid_scope: ... Not permitted
        # scopes"), and unlike /authorize it isn't overridable via extra_token_params
        # without risking Lark treating an explicit empty scope="" differently from no
        # scope param at all — returning [] here omits the key entirely (see call site:
        # `if exchange_scopes: token_params["scope"] = ...`).
        return []

    def _prepare_scopes_for_upstream_refresh(self, scopes: list[str]) -> list[str]:
        # Same as _prepare_scopes_for_token_exchange above: when Lark access tokens expire
        # (~2h), FastMCP attempts a transparent refresh against Lark's token endpoint.
        # Lark's refresh endpoint also rejects OIDC scopes ("invalid_scope"), so returning []
        # ensures no scope parameter is sent during refresh, allowing Lark to seamlessly
        # refresh the token in the background without interrupting the client.
        return []


auth = LarkOAuthProxy(
    upstream_authorization_endpoint=config.LARK_AUTHORIZATION_ENDPOINT,
    upstream_token_endpoint=config.LARK_TOKEN_ENDPOINT,
    upstream_client_id=config.LARK_APP_ID,
    upstream_client_secret=config.LARK_APP_SECRET,
    token_verifier=LarkTokenVerifier(),
    base_url=config.PUBLIC_BASE_URL,
    redirect_path="/auth/callback",
    jwt_signing_key=config.FASTMCP_JWT_SIGNING_KEY,
    client_storage=client_storage,
    # Real access control is by caller identity (open_id, via lark-cli's per-user $HOME),
    # not by OAuth scope — but some MCP clients (mcp-remote, Amazon Quick) request these
    # standard OIDC scopes by default regardless of what the server advertises, and the
    # underlying MCP SDK's Dynamic Client Registration hard-rejects any scope outside
    # valid_scopes with 400 invalid_client_metadata. Declaring them here is pure client
    # compatibility scaffolding; it grants no additional capability.
    valid_scopes=["openid", "profile", "email"],
    # OAuthProxy forwards the client-requested scope straight through to the upstream
    # authorize URL by default — but "openid"/"profile"/"email" mean nothing to Lark's
    # own OAuth server (its scopes look like "im:message", "calendar:calendar", etc.) and
    # it rejects them outright ("email openid profile error", code 20043) on the consent
    # page. This is purely a login-for-identity flow (we only ever call Lark's userinfo
    # endpoint for open_id) — it never needed a Lark scope, so force it empty upstream.
    extra_authorize_params={"scope": ""},
    # Lark's own access tokens are short-lived (~2h), and by default the FastMCP-issued
    # client-facing token mirrors that lifetime — forcing clients to re-auth every couple
    # hours. Some clients (mcp-remote, and transitively Amazon Quick's native re-auth
    # path, which has its own unreliable local-callback handling) can't refresh
    # gracefully, turning routine expiry into a broken full re-auth. This only widens the
    # client-facing token's TTL; the real Lark session is still re-validated and silently
    # refreshed on every request internally, so a revoked/expired Lark session still
    # forces re-auth regardless of this value.
    fastmcp_access_token_expiry_seconds=60 * 60 * 24 * 90,  # 90 days
)


@asynccontextmanager
async def lifespan(server: FastMCP):
    await ensure_bot_identity()
    yield {}


mcp = FastMCP(name="lark-mcp", auth=auth, lifespan=lifespan)

# Each module registers its own @mcp.tool functions on import.
from . import tools_account  # noqa: E402,F401
from .domains import base, calendar, contact, docs, drive, im, task  # noqa: E402,F401

app = mcp.http_app(path="/mcp", stateless_http=False)

# FastMCP only registers protected-resource metadata at the path-specific location
# matching the mount path (/.well-known/oauth-protected-resource/mcp), which is what our
# 401's WWW-Authenticate header correctly points clients to per RFC 9728. Amazon Quick's
# MCP client doesn't follow that — per AWS's own docs, "Well-known URI discovery uses the
# server root path only. Path-specific metadata locations (path-insertion discovery) are
# not supported" — so it only ever checks the bare root and silently fails discovery,
# surfacing a raw 401 instead of starting the OAuth flow. Mirror the same handler at the
# bare root so both discovery styles work; the resource/scopes it returns are unaffected
# since it's the identical function, not a hand-copied duplicate that could drift.
_protected_resource_route = next(
    r
    for r in app.routes
    if getattr(r, "path", None) == "/.well-known/oauth-protected-resource/mcp"
)
app.routes.append(
    Route(
        "/.well-known/oauth-protected-resource",
        _protected_resource_route.endpoint,
        methods=["GET"],
    )
)
