from datetime import timedelta
from functools import wraps
from typing import List, Optional, Dict, Any, Callable, cast

from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, decode_token  # type: ignore

from antarest.common.config import Config
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.login.config import get_config


class Auth:
    ACCESS_TOKEN_DURATION = timedelta(minutes=15)
    REFRESH_TOKEN_DURATION = timedelta(hours=30)

    def __init__(
        self,
        config: Config,
        verify: Callable[[], None] = verify_jwt_in_request,  # Test only
        get_identity: Callable[
            [], Dict[str, Any]
        ] = get_jwt_identity,  # Test only
    ):

        self.disabled = get_config(config).disabled
        self.verify = verify
        self.get_identity = get_identity

    @staticmethod
    def get_current_user() -> Optional[JWTUser]:
        if "user" in g:
            return cast(JWTUser, g.user)

        return None

    @staticmethod
    def get_user_from_token(token: str) -> Optional[JWTUser]:
        token_data = decode_token(token)
        return JWTUser.from_dict(token_data["sub"])

    @staticmethod
    def invalidate() -> None:
        g.pop("user", None)

    def protected(
        self, admin: bool = False
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def auth_nested(fn: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(fn)
            def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
                if self.disabled:
                    a = JWTUser(
                        id=1,
                        name="admin",
                        groups=[
                            JWTGroup(
                                id="admin", name="admin", role=RoleType.ADMIN
                            )
                        ],
                    )
                    g.user = a
                    return fn(*args, **kwargs)

                self.verify()
                user = JWTUser.from_dict(self.get_identity())

                if not admin:
                    g.user = user
                    return fn(*args, **kwargs)

                if user.is_site_admin():
                    g.user = user
                    return fn(*args, **kwargs)
                else:
                    return "User unauthorized", 403

            return wrapper

        return auth_nested
