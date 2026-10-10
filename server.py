import hashlib
import os
from contextvars import ContextVar

import uvicorn
from mcp.server.fastmcp import FastMCP

challenge_header = ContextVar("challenge_header", default=None)

mcp = FastMCP(
    "Exam Challenge Server",
    json_response=True,
    stateless_http=True,
)


@mcp.tool()
def solve_challenge() -> str:
    """Solve the current exam challenge using the HTTP request header."""
    challenge = challenge_header.get()

    if not challenge:
        raise ValueError("Missing X-Exam-Challenge header")

    email = "24f3005284@ds.study.iitm.ac.in"
    message = f"{challenge}:{email}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


class HeaderMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        token = challenge_header.set(headers.get("x-exam-challenge"))
        try:
            await self.app(scope, receive, send)
        finally:
            challenge_header.reset(token)


app = HeaderMiddleware(mcp.streamable_http_app())


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
    )


