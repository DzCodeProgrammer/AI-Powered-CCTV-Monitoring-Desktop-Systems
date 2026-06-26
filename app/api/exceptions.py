from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import RedirectResponse, Response

from app.utils.logging import log_exception

logger = logging.getLogger(__name__)


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept or request.url.path.startswith("/dashboard")


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> Response:
    log_exception("database", f"Unhandled database error on {request.url.path}", exc)
    if _wants_html(request):
        return RedirectResponse(url="/dashboard?error=server", status_code=303)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable. Please try again."},
    )
