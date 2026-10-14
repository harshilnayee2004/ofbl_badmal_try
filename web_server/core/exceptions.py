class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Custom Exception
class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class UnauthorizedExceptionToMakeThisRequest(AppException):
    def __init__(self, message: str="User role not authorized to make this request"):
        super().__init__(message, status_code=401)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)


class ConflictException(AppException):
    def __init__(self, message="Conflict"):
        super().__init__(message, status_code=409)

class InvalidCredentialException(AppException):
    def __init__(self, message="Invalid Credentials"):
        super().__init__(message, status_code=401)

