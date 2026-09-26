"""Vercel Serverless Function entrypoint for Aletheia FastAPI Backend."""

import os
import sys
from pathlib import Path
from fastapi import Request

# Add project root and src/ to sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from aletheia.api.app import app as fastapi_app


@fastapi_app.get("/")
def root_info():
    """Root endpoint for Vercel deployment health."""
    return {
        "status": "healthy",
        "service": "aletheia-backend",
        "docs": "/docs",
        "health": "/health",
        "incidents": "/api/v1/investigation/incidents",
        "version": "0.1.0",
    }


@fastapi_app.get("/api/debug-headers")
def debug_headers(request: Request):
    """Debug endpoint inspecting Vercel proxy headers."""
    return {
        "path": request.url.path,
        "headers": dict(request.headers),
    }


class VercelPathMiddleware:
    """Ensure original request path is preserved when deployed on Vercel."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            if matched_path and matched_path != "/api/index.py":
                scope["path"] = matched_path.split("?")[0]
            elif scope.get("path", "").startswith("/api/index.py/"):
                scope["path"] = scope["path"][len("/api/index.py"):]
            elif scope.get("path") == "/api/index.py":
                for hdr in [b"x-forwarded-uri", b"x-envoy-original-path"]:
                    val = headers.get(hdr, b"").decode("utf-8")
                    if val and val != "/api/index.py":
                        scope["path"] = val.split("?")[0]
                        break
                else:
                    # If root / was requested and rewritten to /api/index.py
                    scope["path"] = "/"
        await self.app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
