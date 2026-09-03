import json

from ..identity import LarkCliError, resolve_home, run_lark_cli
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


@mcp.tool
async def base_delete_records(
    base_token: str,
    table_id: str,
    record_ids: list[str],
    as_user: bool = False,
    confirm: bool = False,
) -> dict:
    """Permanently delete one or more Base records by ID. Irreversible — call
    base_list_records first to confirm the target IDs, then pass confirm=True to
    actually delete."""
    if not confirm:
        raise LarkCliError(
            "base_delete_records is irreversible — call again with confirm=True once "
            "the record_ids are confirmed correct"
        )
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-delete",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--as",
        "user" if as_user else "bot",
        "--yes",
        "--format",
        "json",
    ]
    for record_id in record_ids:
        args += ["--record-id", record_id]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_batch_create_records(
    base_token: str,
    table_id: str,
    records: list[dict],
    as_user: bool = False,
) -> dict:
    """Create up to 200 Base records in one call. `records` is a list of independent
    field-name/id -> value maps, e.g. [{"Name": "Task A", "Status": "Todo"}, {"Name":
    "Task B"}] — check base_list_fields first to confirm real writable field names."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-batch-create",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--json",
        json.dumps({"create_records": records}),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_batch_update_records(
    base_token: str,
    table_id: str,
    updates: dict[str, dict],
    as_user: bool = False,
) -> dict:
    """Update up to 200 existing Base records in one call. `updates` maps each record ID
    to its own field-name/id -> value map, e.g. {"recA": {"Status": "Done"}, "recB":
    {"Score": 20}} — check base_list_fields first to confirm real writable field names."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-batch-update",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--json",
        json.dumps({"update_records": updates}),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_list_tables(
    base_token: str,
    limit: int = 50,
    offset: int = 0,
    as_user: bool = False,
) -> dict:
    """List tables in a Base — use this to resolve a table_id from a table name."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+table-list",
        "--base-token",
        base_token,
        "--limit",
        str(limit),
        "--offset",
        str(offset),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_list_fields(
    base_token: str,
    table_id: str,
    limit: int = 100,
    offset: int = 0,
    as_user: bool = False,
) -> dict:
    """List fields (columns) in a Base table, including their real names, IDs, and
    types — check this before writing to confirm field names and to avoid writing to
    system/formula/lookup fields, which reject normal values."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+field-list",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--limit",
        str(limit),
        "--offset",
        str(offset),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_create_field(
    base_token: str,
    table_id: str,
    field: dict | list[dict],
    as_user: bool = False,
) -> dict:
    """Create a field (column) in a Base table. `field` is a field-property object, e.g.
    {"name": "Status", "type": "text"} or {"name": "Status", "type": "select",
    "multiple": false, "options": [{"name": "Todo"}, {"name": "Done"}]}. Pass a list of
    such objects to create several fields at once."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+field-create",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--json",
        json.dumps(field),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_create_base(
    name: str,
    table_name: str | None = None,
    fields: list[dict] | None = None,
    folder_token: str | None = None,
    time_zone: str | None = None,
    as_user: bool = False,
) -> dict:
    """Create a brand-new Base. Optionally define its first table's schema via
    table_name + fields (same field-object shape as base_create_field); otherwise Base
    creates one default-schema table. If created as bot (the default), the response may
    include a permission_grant field — check for it and tell the caller, since a
    bot-created Base isn't automatically visible/openable by a human until that's
    handled."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+base-create",
        "--name",
        name,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    if table_name:
        args += ["--table-name", table_name]
    if fields:
        args += ["--fields", json.dumps(fields)]
    if folder_token:
        args += ["--folder-token", folder_token]
    if time_zone:
        args += ["--time-zone", time_zone]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_get_base(base_token: str, as_user: bool = False) -> dict:
    """Get a Base's own metadata (name, revision, etc.) — not its tables/records. Use
    base_list_tables for tables, base_list_records for records."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+base-get",
        "--base-token",
        base_token,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_copy_base(
    base_token: str,
    name: str,
    folder_token: str | None = None,
    time_zone: str | None = None,
    without_content: bool = False,
    as_user: bool = False,
) -> dict:
    """Copy an existing Base to a new one. without_content=True copies structure
    (tables/fields/views) only, omitting records. If copied as bot (the default), the
    response may include a permission_grant field — check for it and tell the caller,
    since a bot-created Base isn't automatically visible/openable by a human until
    that's handled."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+base-copy",
        "--base-token",
        base_token,
        "--name",
        name,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    if folder_token:
        args += ["--folder-token", folder_token]
    if time_zone:
        args += ["--time-zone", time_zone]
    if without_content:
        args.append("--without-content")
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_get_records(
    base_token: str,
    table_id: str,
    record_ids: list[str],
    field_ids: list[str] | None = None,
    as_user: bool = False,
) -> dict:
    """Get specific Base records by ID. Use this when record IDs are already known
    (e.g. from a prior create/list/search call); otherwise use base_search_records or
    base_list_records. field_ids (optional) projects only the named fields, useful to
    avoid loading large cell values that aren't needed."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-get",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    for record_id in record_ids:
        args += ["--record-id", record_id]
    if field_ids:
        for field_id in field_ids:
            args += ["--field-id", field_id]
    return await run_lark_cli(home, *args)


@mcp.tool
async def base_search_records(
    base_token: str,
    table_id: str,
    keyword: str,
    search_fields: list[str],
    field_ids: list[str] | None = None,
    view_id: str | None = None,
    filter_json: str | None = None,
    sort_json: str | None = None,
    offset: int = 0,
    limit: int = 10,
    as_user: bool = False,
) -> dict:
    """Keyword-search records in a Base table. search_fields lists which field
    name/IDs to search within (1-20). field_ids (optional) projects the returned
    fields. filter_json (optional, e.g. {"logic":"and","conditions":[["Title","==",
    "Launch plan"]]}) narrows by structured conditions; sort_json (optional, e.g.
    [{"field":"Updated","desc":true}]) orders results. Use base_list_records instead
    for a plain unfiltered listing."""
    home = await resolve_home(as_user)
    args = [
        "base",
        "+record-search",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--keyword",
        keyword,
        "--offset",
        str(offset),
        "--limit",
        str(limit),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    for search_field in search_fields:
        args += ["--search-field", search_field]
    if field_ids:
        for field_id in field_ids:
            args += ["--field-id", field_id]
    if view_id:
        args += ["--view-id", view_id]
    if filter_json:
        args += ["--filter-json", filter_json]
    if sort_json:
        args += ["--sort-json", sort_json]
    return await run_lark_cli(home, *args)
