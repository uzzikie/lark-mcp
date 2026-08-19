from ..identity import require_user_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def contact_search_user(query: str, page_size: int = 20) -> dict:
    """Search Lark/Feishu users by keyword to resolve an open_id. Always acts as the
    caller — lark-cli only supports this with a user identity."""
    home = await require_user_home()
    return await run_lark_cli(
        home,
        "contact",
        "+search-user",
        "--as",
        "user",
        "--query",
        query,
        "--page-size",
        str(page_size),
        "--format",
        "json",
    )
