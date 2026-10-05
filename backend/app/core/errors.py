"""Application-level errors mapped to HTTP responses."""


class AppError(Exception):
    """Raised by services; converted to a JSON error by the API layer."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
