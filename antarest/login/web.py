import json
from datetime import timedelta
from typing import Any, Optional

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (  # type: ignore
    create_access_token,
    get_jwt_identity,
    create_refresh_token,
    jwt_required,
    JWTManager,
)

from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.login.model import (
    User,
    Group,
    Password,
    Role,
    BotCreateDTO,
    UserCreateDTO,
    RoleCreationDTO,
    BotDTO,
    BotRoleUpdateDTO,
)
from antarest.login.service import LoginService


def create_login_api(
    service: LoginService, config: Config, jwt: JWTManager
) -> Blueprint:
    bp = Blueprint(
        "create_login_api",
        __name__,
        template_folder=str(config.resources_path / "templates"),
    )

    auth = Auth(config)

    def generate_tokens(
        user: JWTUser, expire: Optional[timedelta] = None
    ) -> Any:
        access_token = create_access_token(
            identity=user.to_dict(), expires_delta=expire
        )
        refresh_token = create_refresh_token(identity=user.to_dict())
        return {
            "user": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @jwt.token_in_blocklist_loader  # type: ignore
    def check_if_token_is_revoked(jwt_header: Any, jwt_payload: JSON) -> bool:
        id = jwt_payload["sub"]["id"]
        type = jwt_payload["sub"]["type"]
        return type == "bots" and not service.exists_bot(id)

    @bp.route("/login", methods=["POST"])
    def login() -> Any:
        """
        Login
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                  $ref: '#/definitions/UserCredentials'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        consumes:
            - application/x-www-form-urlencoded
        parameters:
        - in: body
          name: body
          required: true
          description: user credentials
          schema:
            id: User
            required:
                - username
                - password
            properties:
                username:
                    type: string
                password:
                    type: string
        definitions:
            - schema:
                id: UserCredentials
                properties:
                  user:
                    type: string
                    description: User name
                  access_token:
                    type: string
                  refresh_token:
                    type: string
        tags:
          - User
        """
        username = request.form.get("username") or request.json.get("username")
        password = request.form.get("password") or request.json.get("password")

        if not username:
            return jsonify({"msg": "Missing username parameter"}), 400
        if not password:
            return jsonify({"msg": "Missing password parameter"}), 400

        user = service.authenticate(username, password)
        if not user:
            return jsonify({"msg": "Bad username or password"}), 401

        # Identity can be any data that is json serializable
        resp = generate_tokens(user)

        return (
            jsonify(resp),
            200,
        )

    @bp.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)  # type: ignore
    def refresh() -> Any:
        """
        Refresh access token
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                  $ref: '#/definitions/UserCredentials'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        consumes:
            - application/x-www-form-urlencoded
        parameters:
        - in: header
          name: Authorization
          required: true
          description: refresh token
          schema:
            type: string
            description: (Bearer {token}) Refresh token received from login or previous refreshes
        definitions:
            - schema:
                id: UserCredentials
                properties:
                  user:
                    type: string
                    description: User name
                  access_token:
                    type: string
                  refresh_token:
                    type: string
        tags:
          - User
        """
        identity = get_jwt_identity()
        user = service.get_jwt(identity["id"])
        if user:
            resp = generate_tokens(user)

            return (
                jsonify(resp),
                200,
            )
        else:
            return "Token invalid", 403

    @bp.route("/users", methods=["GET"])
    @auth.protected()
    def users_get_all() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        return jsonify([u.to_dict() for u in service.get_all_users(params)])

    @bp.route("/users/<int:id>", methods=["GET"])
    @auth.protected()
    def users_get_id(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        u = service.get_user(id, params)
        if u:
            return jsonify(u.to_dict())
        else:
            return "", 404

    @bp.route("/users/infos/<int:id>", methods=["GET"])
    @auth.protected()
    def users_get_infos(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        u = service.get_user_infos(id, params)
        if u:
            return jsonify(u.to_dict())
        else:
            return "", 404

    @bp.route("/users", methods=["POST"])
    @auth.protected()
    def users_create() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        create_user = UserCreateDTO.from_dict(json.loads(request.data))

        return jsonify(service.create_user(create_user, params).to_dict())

    @bp.route("/users/<int:id>", methods=["PUT"])
    @auth.protected()
    def users_update(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        u = User.from_dict(json.loads(request.data))

        if id != u.id:
            return "Id in path must be same id in body", 400

        return jsonify(service.save_user(u, params).to_dict())

    @bp.route("/users/<int:id>", methods=["DELETE"])
    @auth.protected()
    def users_delete(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        service.delete_user(id, params)
        return jsonify(id), 200

    @bp.route("/groups", methods=["GET"])
    @auth.protected()
    def groups_get_all() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        return jsonify([g.to_dict() for g in service.get_all_groups(params)])

    @bp.route("/groups/<int:id>", methods=["GET"])
    @auth.protected()
    def groups_get_id(id: str) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        group = service.get_group(id, params)
        if group:
            return jsonify(group.to_dict())
        else:
            return f"Group {id} not found", 404

    @bp.route("/groups", methods=["POST"])
    @auth.protected()
    def groups_create() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        group = Group.from_dict(json.loads(request.data))
        return jsonify(service.save_group(group, params).to_dict())

    @bp.route("/groups/<string:id>", methods=["DELETE"])
    @auth.protected()
    def groups_delete(id: str) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        service.delete_group(id, params)
        return jsonify(id), 200

    @bp.route("/roles/group/<string:group>", methods=["GET"])
    @auth.protected()
    def roles_get_all(group: str) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        return jsonify(
            [
                r.to_dict()
                for r in service.get_all_roles_in_group(
                    group=group, params=params
                )
            ]
        )

    @bp.route("/roles", methods=["POST"])
    @auth.protected()
    def role_create() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        role = RoleCreationDTO.from_dict(json.loads(request.data))
        return jsonify(service.save_role(role, params).to_dict())

    @bp.route("/roles/<string:group>/<int:user>", methods=["DELETE"])
    @auth.protected()
    def roles_delete(user: int, group: str) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        service.delete_role(user, group, params)
        return jsonify((user, group)), 200

    @bp.route("/bots", methods=["POST"])
    @auth.protected()
    def bots_create() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        create = BotDTO.from_dict(json.loads(request.data))
        bot = service.save_bot(create, params)

        if not bot:
            return UserHasNotPermissionError()

        return jsonify(bot.to_dict()), 200

    @bp.route("/bots", methods=["PUT"])
    @auth.protected()
    def bots_update() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        create = BotRoleUpdateDTO.from_dict(json.loads(request.data))
        bot = service.update_bot(create, params)
        if not bot:
            return UserHasNotPermissionError()
        return jsonify(bot.to_dict()), 200

    @bp.route("/bots", methods=["GET"])
    @auth.protected()
    def get_all_bots() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        owner = request.args.get("owner", default=None, type=int)
        bots = (
            service.get_all_bots_by_owner(owner, params)
            if owner
            else service.get_all_bots(params)
        )
        return jsonify([b.to_dict() for b in bots]), 200

    @bp.route("/bots/infos/<int:id>", methods=["GET"])
    @auth.protected()
    def bots_get_infos(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        b = service.get_bots_infos(id, params)
        if b:
            return jsonify(b.to_dict())
        else:
            return "", 404

    @bp.route("/bots/role", methods=["POST"])
    @auth.protected()
    def bots_create_role() -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        create = RoleCreationDTO.from_dict(json.loads(request.data))
        role = service.save_bot_role(create, params)

        if not role:
            return UserHasNotPermissionError()
        return jsonify(role.to_dict()), 200

    @bp.route("/bots/<int:id>", methods=["GET"])
    @auth.protected()
    def get_bot(id: int) -> Any:
        params = RequestParameters(user=Auth.get_current_user())
        bot = service.get_bot(id, params)
        return jsonify(bot.to_dict()), 200

    @bp.route("/bots/<int:id>", methods=["DELETE"])
    @auth.protected()
    def bots_delete(id: int) -> Any:
        """
        Revoke bot
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
          - in: path
            name: id
            required: true
            description: bot id
            schema:
              type: int
        tags:
          - Bot
        """
        params = RequestParameters(user=Auth.get_current_user())
        service.delete_bot(id, params)
        return jsonify(id), 200

    @bp.route("/protected")
    @auth.protected()
    def protected() -> Any:
        return f"user id={get_jwt_identity()}"

    @bp.route("/auth")
    @auth.protected()
    def auth_needed() -> Any:
        return "ok"

    return bp
