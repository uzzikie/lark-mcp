from ..identity import require_user_home, resolve_home, run_lark_cli
from ..server import mcp


@mcp.tool
async def im_send_message(
    text: str,
    chat_id: str | None = None,
    user_id: str | None = None,
    as_user: bool = False,
) -> dict:
    """Send a plain-text message to a chat (chat_id, oc_xxx) or direct message
    (user_id, ou_xxx) — exactly one of the two must be given. Defaults to the shared
    bot identity; pass as_user=True to send as the caller."""
    if bool(chat_id) == bool(user_id):
        raise ValueError("exactly one of chat_id or user_id must be given")
    home = await resolve_home(as_user)
    args = ["im", "+messages-send", "--text", text, "--as", "user" if as_user else "bot", "--format", "json"]
    args += ["--chat-id", chat_id] if chat_id else ["--user-id", user_id]
    return await run_lark_cli(home, *args)


@mcp.tool
async def im_reply_message(
    message_id: str,
    text: str,
    reply_in_thread: bool = False,
    as_user: bool = False,
) -> dict:
    """Reply to a message (om_xxx) with plain text."""
    home = await resolve_home(as_user)
    args = [
        "im",
        "+messages-reply",
        "--message-id",
        message_id,
        "--text",
        text,
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    if reply_in_thread:
        args.append("--reply-in-thread")
    return await run_lark_cli(home, *args)


@mcp.tool
async def im_search_messages(
    query: str | None = None,
    chat_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    page_size: int = 20,
) -> dict:
    """Search the caller's own messages across chats (keyword and/or time range).
    Always acts as the caller — lark-cli only supports this with a user identity."""
    home = await require_user_home()
    args = ["im", "+messages-search", "--as", "user", "--page-size", str(page_size), "--format", "json"]
    if query:
        args += ["--query", query]
    if chat_id:
        args += ["--chat-id", chat_id]
    if start:
        args += ["--start", start]
    if end:
        args += ["--end", end]
    return await run_lark_cli(home, *args)


@mcp.tool
async def im_search_chats(query: str, page_size: int = 20, as_user: bool = False) -> dict:
    """Search visible group chats by name/keyword — useful for resolving a chat_id from
    a group name before sending a message."""
    home = await resolve_home(as_user)
    args = [
        "im",
        "+chat-search",
        "--query",
        query,
        "--page-size",
        str(page_size),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)


@mcp.tool
async def im_list_chats(page_size: int = 20, as_user: bool = False) -> dict:
    """List chats/groups the bot (or, with as_user=True, the caller) is a member of."""
    home = await resolve_home(as_user)
    args = [
        "im",
        "+chat-list",
        "--page-size",
        str(page_size),
        "--as",
        "user" if as_user else "bot",
        "--format",
        "json",
    ]
    return await run_lark_cli(home, *args)
