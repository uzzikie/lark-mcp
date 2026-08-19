import os


def _env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value or ""


# "lark" (larksuite.com, international) or "feishu" (feishu.cn, China) — must match
# the brand the LARK_APP_ID/LARK_APP_SECRET pair was registered under.
BRAND = _env("LARK_BRAND", "lark")
_ACCOUNTS_HOST = "accounts.larksuite.com" if BRAND == "lark" else "accounts.feishu.cn"
_OPEN_HOST = "open.larksuite.com" if BRAND == "lark" else "open.feishu.cn"

LARK_APP_ID = _env("LARK_APP_ID", required=True)
LARK_APP_SECRET = _env("LARK_APP_SECRET", required=True)

LARK_AUTHORIZATION_ENDPOINT = f"https://{_ACCOUNTS_HOST}/open-apis/authen/v1/authorize"
LARK_TOKEN_ENDPOINT = f"https://{_OPEN_HOST}/open-apis/authen/v2/oauth/token"
LARK_USERINFO_ENDPOINT = f"https://{_OPEN_HOST}/open-apis/authen/v1/user_info"

# Externally-reachable HTTPS origin for this server, e.g. https://lark-mcp.systemditor.com
# — used to build the OAuth redirect_uri and MCP discovery metadata. Must not be an
# internal/pod address: it has to match what's registered as a redirect URI in the Lark
# Developer Console (PUBLIC_BASE_URL + "/auth/callback").
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", required=True)

# Stable across restarts and replicas — generate once with `openssl rand -hex 32` and
# store in the k8s Secret. Rotating it invalidates all previously-issued MCP client tokens.
FASTMCP_JWT_SIGNING_KEY = _env("FASTMCP_JWT_SIGNING_KEY", required=True)

# Root of the persistent volume. lark-cli's entire $HOME (config + the encrypted
# app-secret/token store under ~/.local/share/lark-cli) lives under DATA_DIR/home so it
# survives pod restarts; the OAuthProxy client_storage lives alongside it.
DATA_DIR = _env("DATA_DIR", "/data")
LARK_CLI_HOME = f"{DATA_DIR}/home"
OAUTH_STORE_DIR = f"{DATA_DIR}/oauth-proxy-store"

LARK_CLI_BIN = _env("LARK_CLI_BIN", "lark-cli")

# Domains a freshly-linked personal profile requests scopes for. Kept intentionally
# narrow to match the curated tool surface — extend when a new domains/*.py module needs
# a scope that isn't covered yet.
LARK_CLI_LOGIN_DOMAINS = ["im", "calendar", "contact", "docs", "drive", "base", "task"]
