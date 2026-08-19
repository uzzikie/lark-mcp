import asyncio
import json
import os
import re

from fastmcp.server.dependencies import get_access_token

from . import config

# lark-cli's `--profile` mechanism requires a UNIQUE app-id per profile — it's meant for
# juggling several different registered apps, not several human users of the same app.
# Since every user here shares one Lark app, per-user isolation instead comes from giving
# each person their own $HOME (lark-cli's entire state — config.json plus the encrypted
# token store under ~/.local/share/lark-cli — is scoped by $HOME). BOT_HOME is the shared
# identity set up once at container startup; each linked user gets their own directory
# under HOMES_ROOT, each running its own independent `config init` against the same
# app-id/secret.
BOT_HOME = config.LARK_CLI_HOME
HOMES_ROOT = f"{config.DATA_DIR}/homes"

_SAFE_OPEN_ID = re.compile(r"^[A-Za-z0-9_-]+$")

# lark-cli's config.json is a non-atomic read-modify-write; two concurrent
# lark_login_start calls for the same person (e.g. an MCP client retrying) can corrupt or
# blank it out. Serialize per-user login setup with one lock per open_id.
_login_locks: dict[str, asyncio.Lock] = {}


class LarkCliError(RuntimeError):
    def __init__(self, message: str, detail: dict | None = None):
        super().__init__(message)
        self.detail = detail or {}


def user_home(open_id: str) -> str:
    if not _SAFE_OPEN_ID.match(open_id):
        raise LarkCliError(f"unsafe open_id: {open_id!r}")
    return f"{HOMES_ROOT}/{open_id}"


def login_lock(open_id: str) -> asyncio.Lock:
    return _login_locks.setdefault(open_id, asyncio.Lock())


async def run_lark_cli(
    home: str,
    *args: str,
    stdin: str | None = None,
    timeout: float = 30.0,
) -> dict:
    """Run `lark-cli <args>` with $HOME set to `home` and return the parsed body.

    Callers are responsible for passing whatever output-format flag their specific
    command needs (most "+"-prefixed API commands take `--format json`; management
    commands like `auth`/`config` mostly don't accept one at all and already emit JSON —
    except a few, like `profile add`, whose success path is a plain "OK: ..." line rather
    than JSON, which is handled below).

    The exit code is authoritative: a non-zero exit always raises, regardless of what
    (if anything) came out on stdout — lark-cli sometimes writes its `{"ok": false, ...}`
    error body to stderr rather than stdout, and an empty stdout parses "successfully" as
    `{}`, which used to be misread as an empty-but-successful result.
    """
    cmd = [config.LARK_CLI_BIN, *args]

    env = os.environ.copy()
    env["HOME"] = home
    os.makedirs(home, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(stdin.encode() if stdin is not None else None),
            timeout=timeout,
        )
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise LarkCliError(f"lark-cli timed out after {timeout}s: {' '.join(args)}")

    text = stdout.decode()
    err_text = stderr.decode()

    def _try_parse(raw: str) -> dict | None:
        try:
            return json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            return None

    body = _try_parse(text) or _try_parse(err_text)

    if proc.returncode != 0:
        if body and body.get("error"):
            error = body["error"]
            raise LarkCliError(error.get("message", "lark-cli command failed"), detail=error)
        raise LarkCliError(
            f"lark-cli failed (exit {proc.returncode}): {(err_text or text)[:500]}"
        )

    if body is None:
        if text.strip().upper().startswith("OK"):
            return {"ok": True, "message": text.strip()}
        raise LarkCliError(f"lark-cli produced non-JSON output (exit 0): {text[:500]}")

    if body.get("ok") is False:
        error = body.get("error", {})
        raise LarkCliError(error.get("message", "lark-cli command failed"), detail=error)

    return body


def caller_open_id() -> str:
    token = get_access_token()
    open_id = token.claims.get("open_id") if token else None
    if not open_id:
        raise LarkCliError("no authenticated Lark identity on this request")
    return open_id


async def identity_is_linked(open_id: str) -> bool:
    try:
        await run_lark_cli(user_home(open_id), "auth", "status")
    except LarkCliError:
        return False
    return True


async def require_user_home() -> str:
    """Resolve the caller's own lark-cli $HOME, or raise with guidance to link one."""
    open_id = caller_open_id()
    if not await identity_is_linked(open_id):
        raise LarkCliError(
            "Your Lark identity isn't linked to lark-cli yet. Call lark_login_start, "
            "open the verification URL it returns, approve access, then call "
            "lark_login_confirm with the same device_code."
        )
    return user_home(open_id)


async def resolve_home(as_user: bool) -> str:
    """Bot identity's shared $HOME when as_user is False, else the caller's own $HOME —
    raises via require_user_home() if they haven't linked one."""
    return await require_user_home() if as_user else BOT_HOME


async def ensure_bot_identity() -> None:
    """Idempotently initialize the bot's $HOME from LARK_APP_ID/SECRET so as_user=False
    tool calls work. Safe to call on every pod start: if a previous pod already ran this
    against the same PVC, `config init` re-running is a no-op in effect (bot identity is
    derived from app-id/secret, not stateful login) even if the command itself errors on
    being re-run."""
    try:
        await run_lark_cli(
            BOT_HOME,
            "config",
            "init",
            "--app-id",
            config.LARK_APP_ID,
            "--app-secret-stdin",
            "--brand",
            config.BRAND,
            stdin=config.LARK_APP_SECRET,
        )
        return
    except LarkCliError:
        pass

    status = await run_lark_cli(BOT_HOME, "doctor", "--offline")
    bot_ready = any(
        c.get("name") == "bot_identity" and c.get("status") == "pass"
        for c in status.get("checks", [])
    )
    if not bot_ready:
        raise LarkCliError(
            "lark-cli bot identity is not configured and `config init` failed — check "
            "LARK_APP_ID/LARK_APP_SECRET"
        )
