class DomainError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, detail: str):
        super().__init__(detail, 404)


class ConflictError(DomainError):
    def __init__(self, detail: str):
        super().__init__(detail, 409)
