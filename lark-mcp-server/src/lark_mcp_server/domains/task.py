from ..identity import require_user_home, resolve_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def task_create(
    summary: str,
    description: str | None = None,
    due: str | None = None,
    assignee: str | None = None,
    tasklist_id: str | None = None,
    as_user: bool = False,
) -> dict:
    """Create a task. due accepts ISO 8601, date:YYYY-MM-DD, relative (+2d), or a ms
    timestamp. assignee is an open_id (ou_xxx) for a person or app id (cli_xxx) for an
    app."""
    home = await resolve_home(as_user)
    args = ["task", "+create", "--summary", summary, "--as", "user" if as_user else "bot"]
    if description:
        args += ["--description", description]
    if due:
        args += ["--due", due]
    if assignee:
        args += ["--assignee", assignee]
    if tasklist_id:
        args += ["--tasklist-id", tasklist_id]
    args += ["--format", "json"]
    return await run_lark_cli(home, *args)


@mcp.tool
async def task_list(
    query: str | None = None,
    complete: bool | None = None,
    page_size: int = 20,
) -> dict:
    """List tasks assigned to the caller. Always acts as the caller — lark-cli only
    supports this with a user identity."""
    home = await require_user_home()
    args = ["task", "+get-my-tasks", "--as", "user", "--page-limit", str(page_size), "--format", "json"]
    if query:
        args += ["--query", query]
    if complete is not None:
        args += [f"--complete={'true' if complete else 'false'}"]
    return await run_lark_cli(home, *args)
