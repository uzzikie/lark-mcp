import os

from . import config, identity
from .identity import LarkCliError, run_lark_cli, user_home
from .server import mcp


@mcp.tool
async def lark_whoami() -> dict:
    """Show the caller's authenticated Lark identity and whether it's linked to lark-cli
    (required for any tool that acts as "you" rather than the shared bot)."""
    open_id = identity.caller_open_id()
    linked = await identity.identity_is_linked(open_id)
    return {"open_id": open_id, "lark_cli_linked": linked}


@mcp.tool
async def lark_login_start() -> dict:
    """Start linking your Lark identity to lark-cli so personal-scope tools (e.g. reading
    your own calendar, sending messages as you) can act on your behalf. Returns a
    verification URL/QR to open in a browser and a device_code — after approving access
    there, call lark_login_confirm with the same device_code."""
    open_id = identity.caller_open_id()
    home = user_home(open_id)

    async with identity.login_lock(open_id):
        try:
            await run_lark_cli(
                home,
                "config",
                "init",
                "--app-id",
                config.LARK_APP_ID,
                "--app-secret-stdin",
                "--brand",
                config.BRAND,
                stdin=config.LARK_APP_SECRET,
            )
        except LarkCliError:
            pass  # tolerate: might already be configured from an earlier call

        if not os.path.isfile(f"{home}/.lark-cli/config.json"):
            raise LarkCliError(
                "lark-cli config init did not produce a config file — this usually means "
                "a concurrent lark_login_start call for the same identity raced this one; "
                "please retry"
            )

        result = await run_lark_cli(
            home,
            "auth",
            "login",
            "--no-wait",
            "--json",
            "--domain",
            ",".join(config.LARK_CLI_LOGIN_DOMAINS),
        )

    data = result.get("data") or result
    return {
        "verification_url": data.get("verification_url"),
        "device_code": data.get("device_code"),
        "instructions": "Open verification_url in a browser, approve access, then call "
        "lark_login_confirm with this device_code.",
    }


@mcp.tool
async def lark_login_confirm(device_code: str) -> dict:
    """Complete a lark_login_start flow after approving access in the browser."""
    open_id = identity.caller_open_id()
    async with identity.login_lock(open_id):
        await run_lark_cli(user_home(open_id), "auth", "login", "--device-code", device_code, "--json")
        linked = await identity.identity_is_linked(open_id)

    if not linked:
        raise LarkCliError(
            "lark-cli reported the device-code login completed, but the identity still "
            "doesn't show as linked — call lark_login_start again for a fresh link"
        )
    return {"open_id": open_id, "lark_cli_linked": True}
