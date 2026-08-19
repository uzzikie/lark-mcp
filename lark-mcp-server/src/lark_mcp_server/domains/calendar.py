from ..identity import resolve_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def calendar_agenda(
    start_time: str | None = None,
    end_time: str | None = None,
    calendar_id: str = "primary",
    as_user: bool = True,
) -> dict:
    """View calendar agenda. start_time/end_time are ISO 8601 (e.g.
    2026-08-11T00:00:00+08:00); omit both for today only. Defaults to the caller's own
    calendar (as_user=True) since an agenda is inherently personal."""
    home = await resolve_home(as_user)
    args = [
        "calendar",
        "+agenda",
        "--calendar-id",
        calendar_id,
        "--as",
        "user" if as_user else "bot",
    ]
    if start_time:
        args += ["--start", start_time]
    if end_time:
        args += ["--end", end_time]
    args += ["--format", "json"]
    return await run_lark_cli(home, *args)


@mcp.tool
async def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str | None = None,
    attendee_ids: str | None = None,
    calendar_id: str = "primary",
    as_user: bool = True,
) -> dict:
    """Create a calendar event. start_time/end_time are ISO 8601 (e.g.
    2026-08-11T14:00:00+08:00). Optionally invite attendees (comma-separated open_id
    ou_xxx / chat oc_xxx / room omm_xxx). Defaults to the caller's own calendar."""
    home = await resolve_home(as_user)
    args = [
        "calendar",
        "+create",
        "--calendar-id",
        calendar_id,
        "--summary",
        summary,
        "--start",
        start_time,
        "--end",
        end_time,
        "--as",
        "user" if as_user else "bot",
    ]
    if description:
        args += ["--description", description]
    if attendee_ids:
        args += ["--attendee-ids", attendee_ids]
    args += ["--format", "json"]
    return await run_lark_cli(home, *args)
