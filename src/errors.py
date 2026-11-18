class AppError(Exception):
    """خطای قابل‌انتظار برنامه؛ به قالب { error: { code, message } } تبدیل می‌شود."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
