import logging
from typing import Any, List

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.xpansion_management import (
    XpansionSettingsDTO,
    XpansionCandidateDTO,
)
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_study_routes(
    study_service: StudyService, ftm: FileTransferManager, config: Config
) -> APIRouter:
    """
    Endpoint implementation for xpansion studies management
    Args:
        study_service: study service facade to handle request
        ftm: file transfer manager
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1/")
    auth = Auth(config)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/create",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Configuration",
    )
    def create_xpansion_configuration(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating Xpansion Configuration for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.create_xpansion_configuration(uuid=uuid, params=params)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/delete",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Configuration",
    )
    def delete_xpansion_configuration(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting Xpansion Configuration for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_xpansion_configuration(uuid=uuid, params=params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Settings",
        response_model=XpansionSettingsDTO,
    )
    def get_settings(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching Xpansion Settings of the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_xpansion_settings(uuid=uuid, params=params)

    #
    @bp.post(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Settings",
        response_model=XpansionSettingsDTO,
    )
    def update_settings(
        uuid: str,
        xpansion_settings_dto: XpansionSettingsDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating Xpansion Settings Of Study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_xpansion_settings(
            uuid, xpansion_settings_dto, params
        )

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates/add",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Candidate",
    )
    def add_candidate(
        uuid: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Adding new candidate {xpansion_candidate_dto.dict(by_alias=True)} to study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.add_candidate(
            uuid, xpansion_candidate_dto, params
        )

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidate",
        response_model=XpansionCandidateDTO,
    )
    def get_candidate(
        uuid: str,
        candidate_name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching study list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return study_service.get_candidate(uuid, candidate_name, params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates/",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidates",
        response_model=List[XpansionCandidateDTO],
    )
    def get_candidates(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching study list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return study_service.get_candidates(uuid, params)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Candidate",
    )
    def update_candidate(
        uuid: str,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        # maybe just do one endpoint for both add and update and remove the name from the DTO ? or remove it from the URL ?
        logger.info(
            f"Updating xpansion candidate {xpansion_candidate_dto.name} of the study {uuid}",
            extra={"user": current_user.id},
        )
        assert (
            candidate_name == xpansion_candidate_dto.name
        )  # Not sure about this. Should we keep the name in the endpoint if it is in the DTO ?
        params = RequestParameters(user=current_user)
        return study_service.update_xpansion_candidate(
            uuid, xpansion_candidate_dto, params
        )

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}/delete",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Candidate",
    )
    def delete_candidate(
        uuid: str,
        candidate_name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting candidate {candidate_name}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.delete_candidate(uuid, candidate_name, params)

    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/constraints",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Delete Xpansion Candidate",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def update_constraints(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies

    return bp
