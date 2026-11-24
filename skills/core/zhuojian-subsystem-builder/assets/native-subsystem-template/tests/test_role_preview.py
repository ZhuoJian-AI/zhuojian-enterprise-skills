from pathlib import Path

from starlette.requests import Request

from role_preview import reply


def test_preview_reuses_the_rendered_page_and_removes_live_assets():
    source = Path(__file__).resolve().parents[1] / "static" / "index.html"
    origin = "https://workplace.example.test"

    def request(method, referrer):
        return Request({"type": "http", "method": method, "headers": [(b"origin", referrer.encode())]})

    response = reply(request("GET", origin), page=source, allowed_origins={origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["x-zhuojian-role-preview"] == "1"
    policy = response.headers["content-security-policy"]
    assert "connect-src 'none'" in policy and "sandbox allow-scripts" in policy
    nonce = policy.split("script-src 'nonce-", 1)[1].split("'", 1)[0].encode()
    assert b'<script nonce="' + nonce + b'">' in response.body
    assert b"zhuojian:role-preview-ready" in response.body
    assert b"zhuojian:live-assets" not in response.body
    rejected = reply(request("HEAD", "https://unrelated.example.test"), page=source, allowed_origins={origin})
    assert rejected.body == b""
    assert "access-control-allow-origin" not in rejected.headers
