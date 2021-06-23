from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel

from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import RawStudy, PatchArea


class AreaType(Enum):
    AREA = "AREA"
    CLUSTER = "CLUSTER"


class AreaCreationDTO(BaseModel):
    name: str
    type: AreaType
    metadata: Optional[Dict[str, Optional[str]]]
    set: Optional[List[str]]


class AreaPatchUpdateDTO(BaseModel):
    type: AreaType
    name: Optional[str]
    metadata: Optional[Dict[str, Optional[str]]]
    set: Optional[List[str]]


class AreaInfoDTO(AreaCreationDTO):
    id: str


class AreaManager:
    def __init__(self, raw_study_service: RawStudyService) -> None:
        self.raw_study_service = raw_study_service

    def get_all_areas(
        self, study: RawStudy, area_type: Optional[AreaType] = None
    ) -> List[AreaInfoDTO]:
        config, study_tree = self.raw_study_service.get_study(study)
        metadata = self.raw_study_service.patch_service.get(study)
        areas_metadata: Dict[str, PatchArea] = metadata.areas or {}  # type: ignore
        result = []
        if area_type is None or area_type == AreaType.AREA:
            for area_name in config.areas:
                result.append(
                    AreaInfoDTO(
                        id=area_name,
                        name=area_name,
                        type=AreaType.AREA,
                        metadata=areas_metadata.get(
                            area_name, PatchArea()
                        ).dict(),
                    )
                )

        if area_type is None or area_type == AreaType.CLUSTER:
            for set_name in config.sets:
                result.append(
                    AreaInfoDTO(
                        id=set_name,
                        name=set_name,
                        type=AreaType.CLUSTER,
                        set=config.sets[set_name].areas,
                        metadata=areas_metadata.get(
                            set_name, PatchArea()
                        ).dict(),
                    )
                )

        return result

    def create_area(
        self, study: RawStudy, area_creation_info: AreaCreationDTO
    ) -> AreaInfoDTO:
        pass

    def update_area(
        self,
        study: RawStudy,
        area_id: str,
        area_creation_info: AreaPatchUpdateDTO,
    ) -> AreaInfoDTO:
        pass

    def delete_area(self, study: RawStudy, area_id: str) -> None:
        pass
