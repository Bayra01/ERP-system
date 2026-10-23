"""Neg tsagiin aldaanii format: {"error": {"code":..., "message":...}}"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str = ""):
        self.message = message or self.code
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code, code = 404, "not_found"


class ConflictError(AppError):
    status_code, code = 409, "conflict"


class ForbiddenError(AppError):
    status_code, code = 403, "forbidden"


class UnprocessableError(AppError):
    status_code, code = 422, "validation_error"


class UnauthorizedError(AppError):
    status_code, code = 401, "unauthorized"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )
