import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier

from . import config


class LarkTokenVerifier(TokenVerifier):
    """Validates the Lark user_access_token OAuthProxy obtained via the upstream
    authorization_code exchange. Lark tokens are opaque (not JWTs), so verification
    means calling Lark's userinfo endpoint rather than checking a signature.

    The returned AccessToken.subject/claims become the caller's durable identity for the
    lifetime of the FastMCP-minted session token — identity.py uses `claims["open_id"]`
    to route tool calls to that person's linked lark-cli profile.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(
                    config.LARK_USERINFO_ENDPOINT,
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.HTTPError:
                return None

        if response.status_code != 200:
            return None

        body = response.json()
        if body.get("code") != 0:
            return None

        data = body.get("data", {})
        open_id = data.get("open_id")
        if not open_id:
            return None

        return AccessToken(
            token=token,
            client_id=open_id,
            scopes=[],
            subject=open_id,
            claims={
                "open_id": open_id,
                "union_id": data.get("union_id"),
                "name": data.get("name"),
                "email": data.get("email"),
            },
        )
