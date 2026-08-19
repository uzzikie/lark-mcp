import json

from ..identity import resolve_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def base_list_records(
    base_token: str,
    table_id: str,
    filter_json: str | None = None,
    limit: int = 100,
    as_user: bool = False,
) -> dict:
    """List records in a Base table. filter_json (optional) narrows results, e.g.
    {"logic":"and","conditions":[["Title","==","Launch plan"]]}."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-list",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--limit",
        str(limit),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    if filter_json:
        args += ["--filter-json", filter_json]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_create_record(
    base_token: str,
    table_id: str,
    fields: dict,
    record_id: str | None = None,
    as_user: bool = False,
) -> dict:
    """Create a Base record (omit record_id) or update one (pass record_id). `fields` is
    a field-name/id -> value map, e.g. {"Name": "Alice", "Status": "Todo"} — check
    base_list_records or the table's field list first to confirm real field names."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-upsert",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--json",
        json.dumps(fields),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    if record_id:
        args += ["--record-id", record_id]
    return await run_lark_cli(home, *args)
