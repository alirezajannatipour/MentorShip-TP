from typing import Any


class AppError(Exception):
    """خطای قابل‌انتظار برنامه؛ به قالب { error: { code, message } } تبدیل می‌شود."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
