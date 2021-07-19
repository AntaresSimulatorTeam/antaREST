import enum
import logging

from antarest.core.jwt import JWTUser
from antarest.core.roles import RoleType
from antarest.study.model import PublicMode, Study

logger = logging.getLogger(__name__)


class StudyPermissionType(enum.Enum):
    """
    User permission belongs to Study
    """

    READ = "READ"
    RUN = "RUN"
    WRITE = "WRITE"
    DELETE = "DELETE"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


permission_matrix = {
    StudyPermissionType.READ: {
        "roles": [
            RoleType.ADMIN,
            RoleType.RUNNER,
            RoleType.WRITER,
            RoleType.READER,
        ],
        "public_modes": [
            PublicMode.FULL,
            PublicMode.EDIT,
            PublicMode.EXECUTE,
            PublicMode.READ,
        ],
    },
    StudyPermissionType.RUN: {
        "roles": [RoleType.ADMIN, RoleType.RUNNER, RoleType.WRITER],
        "public_modes": [PublicMode.FULL, PublicMode.EDIT, PublicMode.EXECUTE],
    },
    StudyPermissionType.WRITE: {
        "roles": [RoleType.ADMIN, RoleType.WRITER],
        "public_modes": [PublicMode.FULL, PublicMode.EDIT],
    },
    StudyPermissionType.DELETE: {
        "roles": [RoleType.ADMIN],
        "public_modes": [PublicMode.FULL],
    },
    StudyPermissionType.MANAGE_PERMISSIONS: {
        "roles": [RoleType.ADMIN],
        "public_modes": [],
    },
}


def check_permission(
    user: JWTUser, study: Study, permission: StudyPermissionType
) -> bool:
    """
    Check user permission on study. User has permission if
    - user is site admin
    - user is the study owner
    - user has correct role of one group linked to study
    - study is public

    Args:
        user: user logged
        study: study to check
        permission: user permission to check

    Returns: true if user match permission requirements, false else.

    """
    if user.is_site_admin():
        logger.debug(f"user {user.id} accepted on study {study.id} as admin")
        return True

    if study.owner is not None and user.impersonator == study.owner.id:
        logger.debug(f"user {user.id} accepted on study {study.id} as owner")
        return True

    study_group_id = [g.id for g in study.groups]
    group_permission = any(
        role in permission_matrix[permission]["roles"]  # type: ignore
        for role in [
            group.role
            for group in (user.groups or [])
            if group.id in study_group_id
        ]
    )
    if group_permission:
        logger.debug(
            f"user {user.id} accepted on study {study.id} as admin of at least one group"
        )
        return True

    return study.public_mode in permission_matrix[permission]["public_modes"]  # type: ignore
