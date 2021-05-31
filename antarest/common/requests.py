from typing import Optional

from dataclasses import dataclass
from markupsafe import escape

from fastapi import HTTPException

from antarest.common.jwt import JWTUser


@dataclass
class RequestParameters:
    """
    DTO object to handle data inside request to send to service
    """

    user: Optional[JWTUser] = None

    def get_user_id(self) -> str:
        return str(escape(str(self.user.id))) if self.user else "Unknown"


class UserHasNotPermissionError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Permission denied")
