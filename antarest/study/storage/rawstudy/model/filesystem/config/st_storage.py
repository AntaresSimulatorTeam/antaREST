from typing import Dict, Any

from pydantic import BaseModel, Extra, Field, root_validator

from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class STStorageGroup(EnumIgnoreCase):
    """
    This class defines the specific energy storage systems.

    Enum values:

        - PSP_OPEN: Represents an open pumped storage plant.
        - PSP_CLOSED: Represents a closed pumped storage plant.
        - PONDAGE: Represents a pondage storage system (reservoir storage system).
        - BATTERY: Represents a battery storage system.
        - OTHER: Represents other energy storage systems.
    """

    PSP_OPEN = "PSP_open"
    PSP_CLOSED = "PSP_closed"
    PONDAGE = "Pondage"
    BATTERY = "Battery"
    OTHER = "Other"


# noinspection SpellCheckingInspection
class STStorageConfig(BaseModel):
    """
    Manage the configuration files in the context of Short-Term Storage.
    It provides a convenient way to read and write configuration data from/to an INI file format.
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    # The `id` field is a calculated field that is excluded when converting
    # the model to a dictionary or JSON format (`model_dump`).
    id: str = Field(
        description="Short-term storage ID",
        regex=r"[a-zA-Z0-9_(),& -]+",
        exclude=True,
    )
    name: str = Field(
        description="Short-term storage name",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )
    group: STStorageGroup = Field(
        ...,
        description="Energy storage system group (mandatory)",
    )
    injection_nominal_capacity: float = Field(
        0,
        description="Injection nominal capacity (MW)",
        ge=0,
        alias="injectionnominalcapacity",
    )
    withdrawal_nominal_capacity: float = Field(
        0,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
        alias="withdrawalnominalcapacity",
    )
    reservoir_capacity: float = Field(
        0,
        description="Reservoir capacity (MWh)",
        ge=0,
        alias="reservoircapacity",
    )
    efficiency: float = Field(
        1,
        description="Efficiency of the storage system",
        ge=0,
        le=1,
    )
    initial_level: float = Field(
        0,
        description="Initial level of the storage system",
        ge=0,
        alias="initiallevel",
    )
    initial_level_optim: bool = Field(
        False,
        description="Flag indicating if the initial level is optimized",
        alias="initialleveloptim",
    )

    @root_validator(pre=True)
    def calculate_storage_id(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the short-term storage ID based on the storage name, if not provided.

        Args:
            values: values used to construct the object.

        Returns:
            The updated values.
        """
        # Avoid circular imports
        from antarest.study.storage.rawstudy.model.filesystem.config.model import (
            transform_name_to_id,
        )

        if values.get("id") or not values.get("name"):
            return values
        storage_name = values["name"]
        if storage_id := transform_name_to_id(storage_name):
            values["id"] = storage_id
        else:
            raise ValueError(
                f"Invalid short term storage name '{storage_name}'."
            )
        return values
