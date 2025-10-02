from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

class ServiceStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class ServiceResult:
    status: ServiceStatus
    data: Optional[Any] = None
    error: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == ServiceStatus.SUCCESS

class ServiceError(Exception):
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code

# Expose common symbols for wildcard imports
__all__ = ["ServiceStatus", "ServiceResult", "ServiceError"]