from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from kefe_api.core.errors import DomainError


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        trace_id = request.headers.get("Trace-Id", str(uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            media_type="application/problem+json",
            content={
                "type": f"https://kefe.app/problems/{exc.code.lower()}",
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
                "code": exc.code,
                "trace_id": trace_id,
                "retryable": exc.retryable,
                "meta": exc.meta,
            },
        )
