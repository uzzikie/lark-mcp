from ..identity import require_user_home, resolve_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def docs_search(query: str, page_size: str = "15") -> dict:
    """Search Lark docs, Wiki, and spreadsheet files by keyword. Always acts as the
    caller — lark-cli only supports this with a user identity."""
    home = await require_user_home()
    return await run_lark_cli(
        home,
        "docs",
        "+search",
        "--as",
        "user",
        "--query",
        query,
        "--page-size",
        page_size,
        "--format",
        "json",
    )


@mcp.tool
async def docs_get_content(
    doc: str,
    scope: str = "full",
    doc_format: str = "markdown",
    as_user: bool = True,
) -> dict:
    """Fetch a Lark document's content by URL or token. scope: full|outline|range|
    keyword|section. doc_format: xml (structure, block ids) or markdown (plain export).
    Defaults to the caller's own permissions (as_user=True) since doc access is usually
    permission-scoped to a specific person."""
    home = await resolve_home(as_user)
    return await run_lark_cli(
        home,
        "docs",
        "+fetch",
        "--doc",
        doc,
        "--scope",
        scope,
        "--doc-format",
        doc_format,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    )
