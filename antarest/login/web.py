import json
from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import (  # type: ignore
    create_access_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
)

from antarest.common.config import Config
from antarest.login.model import User, Group
from antarest.login.service import LoginService


def create_login_api(service: LoginService, config: Config) -> Blueprint:
    bp = Blueprint(
        "create_login_api",
        __name__,
        template_folder=str(config["main.res"] / "templates"),
    )

    @bp.route("/auth", methods=["POST"])
    def auth() -> Any:
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
        access_token = create_access_token(identity=user.to_dict())
        resp = jsonify({"login": True})
        set_access_cookies(resp, access_token)
        return (
            jsonify(access_token=access_token) if request.is_json else resp,
            200,
        )

    @bp.route("/login", methods=["GET"])
    def login() -> Any:
        return render_template("login.html")

    @bp.route("/users", methods=["GET", "POST"], defaults={"id": None})
    @bp.route("/users/<int:id>", methods=["DELETE"])
    @jwt_required  # type: ignore
    def users(id: Optional[int]) -> Any:
        if get_jwt_identity()["role"] != "ADMIN":
            return "Only admin can manage user", 403

        if request.method == "GET":
            if id is not None:
                user = service.get_user(id)
                return jsonify(user.to_dict()) if user else "", 404
            else:
                return jsonify([u.to_dict() for u in service.get_all_users()])

        if request.method == "POST":
            user = User.from_dict(json.loads(request.data))
            return jsonify(service.save_user(user).to_dict())

        if id is not None and request.method == "DELETE":
            service.delete_user(id)
            return jsonify(id), 200

    @bp.route("/groups", methods=["GET", "POST"], defaults={"id": None})
    @bp.route("/groups/<int:id>", methods=["DELETE"])
    @jwt_required  # type: ignore
    def groups(id: Optional[int]) -> Any:
        if get_jwt_identity()["role"] != "ADMIN":
            return "Only admin can manage group", 403

        if request.method == "GET":
            if id is not None:
                group = service.get_group(id)
                return jsonify(group.to_dict()) if group else "", 404
            else:
                return jsonify([g.to_dict() for g in service.get_all_groups()])

        if request.method == "POST":
            group = Group.from_dict(json.loads(request.data))
            return jsonify(service.save_group(group).to_dict())

        if id is not None and request.method == "DELETE":
            service.delete_group(id)
            return jsonify(id), 200

    @bp.route("/protected")
    @jwt_required  # type: ignore
    def protected() -> Any:
        return f"user id={get_jwt_identity()}"

    return bp
