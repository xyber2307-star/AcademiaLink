class DomainError(Exception):
 def __init__(self,detail,status_code=400):self.detail=detail;self.status_code=status_code
class NotFoundError(DomainError):
 def __init__(self,detail):super().__init__(detail,404)
class ConflictError(DomainError):
 def __init__(self,detail):super().__init__(detail,409)
