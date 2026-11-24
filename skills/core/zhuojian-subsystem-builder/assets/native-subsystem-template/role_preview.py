"""Serve the same native page with an isolated, static role preview."""
from pathlib import Path
from secrets import token_urlsafe

from fastapi import Request, Response
from fastapi.responses import HTMLResponse

PATH = "/__zhuojian/role-preview"
LIVE_ASSETS_START = "<!-- zhuojian:live-assets:start -->"
LIVE_ASSETS_END = "<!-- zhuojian:live-assets:end -->"


def reply(request: Request, *, page: Path, allowed_origins: set[str]) -> Response:
    nonce = token_urlsafe(24)
    ancestors = " ".join(sorted(allowed_origins)) or "'none'"
    headers = {
        "Content-Security-Policy": (
            f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
            f"style-src-attr 'unsafe-inline'; connect-src 'none'; form-action 'none'; "
            f"base-uri 'none'; frame-ancestors {ancestors}; sandbox allow-scripts"
        ),
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
        "Vary": "Origin",
        "X-ZhuoJian-Role-Preview": "1",
    }
    origin = request.headers.get("origin")
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Expose-Headers"] = "Content-Security-Policy, X-ZhuoJian-Role-Preview"
    if request.method == "HEAD":
        return Response(headers=headers)

    source = page.read_text(encoding="utf-8")
    before, marker, tail = source.partition(LIVE_ASSETS_START)
    _, end, after = tail.partition(LIVE_ASSETS_END)
    if not marker or not end:
        return Response(status_code=503, headers=headers)
    example = (before + after).replace("<script>", f'<script nonce="{nonce}">')
    example = example.replace("<style>", f'<style nonce="{nonce}">')
    return HTMLResponse(example, headers=headers)
