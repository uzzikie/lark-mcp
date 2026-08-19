import base64
import tempfile
from pathlib import Path

from ..identity import LarkCliError, resolve_home, run_lark_cli
from ..server import mcp

# lark-cli's upload/download work against server-local paths; over MCP the caller has no
# filesystem of its own, so these tools carry file bytes as base64 instead. Kept small —
# this is a remote HTTP round-trip, not a bulk file-transfer channel.
_MAX_BYTES = 10 * 1024 * 1024


def _safe_filename(name: str) -> str:
    """Strip any directory components so a caller-supplied name can't escape the
    tempdir it's joined into — `Path(tmp) / name` alone doesn't protect against this,
    since joining with an absolute path (e.g. "/etc/passwd") discards `tmp` entirely."""
    safe = Path(name).name
    if not safe or safe in (".", ".."):
        raise LarkCliError(f"invalid file name: {name!r}")
    return safe


@mcp.tool
async def drive_upload(
    file_name: str,
    content_base64: str,
    folder_token: str | None = None,
    as_user: bool = False,
) -> dict:
    """Upload a file to Drive. content_base64 is the file's raw bytes, base64-encoded
    (max 10MB). Omit folder_token to upload to the caller's/bot's Drive root."""
    raw = base64.b64decode(content_base64)
    if len(raw) > _MAX_BYTES:
        raise LarkCliError(f"file too large ({len(raw)} bytes) — max {_MAX_BYTES}")

    home = await resolve_home(as_user)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / _safe_filename(file_name)
        path.write_bytes(raw)
        args = [
            "drive",
            "+upload",
            "--file",
            str(path),
            "--name",
            file_name,
            "--as",
            "user" if as_user else "bot",
            "--format",
            "json",
        ]
        if folder_token:
            args += ["--folder-token", folder_token]
        return await run_lark_cli(home, *args)


@mcp.tool
async def drive_download(file_token: str, as_user: bool = False) -> dict:
    """Download a file from Drive (max 10MB). Returns its name and base64-encoded bytes."""
    home = await resolve_home(as_user)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / _safe_filename(file_token)
        await run_lark_cli(
            home,
            "drive",
            "+download",
            "--file-token",
            file_token,
            "--output",
            str(path),
            "--overwrite",
            "--as",
            "user" if as_user else "bot",
            "--format",
            "json",
        )
        raw = path.read_bytes()
        if len(raw) > _MAX_BYTES:
            raise LarkCliError(f"file too large ({len(raw)} bytes) — max {_MAX_BYTES}")
        return {
            "file_token": file_token,
            "size": len(raw),
            "content_base64": base64.b64encode(raw).decode(),
        }
