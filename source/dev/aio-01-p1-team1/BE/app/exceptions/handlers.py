from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.external_error import ExternalServiceError


async def http_exception_handler(
    request: Request,
    exception: HTTPException,
) -> JSONResponse:
    content = {"success": False, "message": str(exception.detail)}
    if isinstance(exception, ExternalServiceError):
        content.update(service=exception.service, code=exception.reason)
    return JSONResponse(
        status_code=exception.status_code,
        content=content,
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "입력 내용을 확인해 주세요.",
            # Do not return submitted values or Pydantic ctx: they may contain secrets.
            "errors": [
                {"field": ".".join(str(part) for part in error["loc"] if part not in ("body", "query", "path")),
                 "message": "신청 종료일이 시작일보다 빠릅니다." if error["loc"][-1:] == ("application_end_date",) and error["type"] == "value_error" else "입력값의 형식과 범위를 확인해 주세요."}
                for error in exception.errors()
            ],
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(Exception, unexpected_exception_handler)


async def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={
        "success": False, "message": "처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    })
