from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from pydantic import Field, validator

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.business.utils_binding_constraint import apply_binding_constraint
from antarest.study.storage.variantstudy.model.command.common import (
    BindingConstraintOperator,
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

MatrixType = List[List[MatrixData]]


class UpdateBindingConstraint(ICommand):
    """
    Command used to update a binding constraint.
    """

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str
    enabled: bool = True
    time_step: BindingConstraintFrequency
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Optional[Union[MatrixType, str]] = Field(None, description="2nd member matrix")
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None
    comments: Optional[str] = None

    @validator("values", always=True)
    def validate_series(
        cls,
        v: Optional[Union[MatrixType, str]],
        values: Dict[str, Any],
    ) -> Optional[Union[MatrixType, str]]:
        time_step = values["time_step"]
        if v is None:
            # The matrix is not updated
            return None
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, values)
        if isinstance(v, list):
            shapes = {
                BindingConstraintFrequency.HOURLY: (8760, 3),
                BindingConstraintFrequency.DAILY: (365, 3),
                BindingConstraintFrequency.WEEKLY: (52, 3),
            }
            # Check the matrix values and create the corresponding matrix link
            array = np.array(v, dtype=np.float64)
            if array.shape != shapes[time_step]:
                raise ValueError(f"Invalid matrix shape {array.shape}, expected {shapes[time_step]}")
            if np.isnan(array).any():
                raise ValueError("Matrix values cannot contain NaN")
            v = cast(MatrixType, array.tolist())
            return validate_matrix(v, values)
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        binding: Optional[JSON] = None
        new_key: Optional[str] = None
        for key, binding_config in binding_constraints.items():
            if binding_config["id"] == self.id:
                binding = binding_config
                new_key = key
                break
        if binding is None or new_key is None:
            return CommandOutput(
                status=False,
                message="Failed to retrieve existing binding constraint",
            )

        return apply_binding_constraint(
            study_data,
            binding_constraints,
            new_key,
            self.id,
            binding["name"],
            self.comments,
            self.enabled,
            self.time_step,
            self.operator,
            self.coeffs,
            self.values,
            self.filter_year_by_year,
            self.filter_synthesis,
        )

    def to_dto(self) -> CommandDTO:
        args = {
            "id": self.id,
            "enabled": self.enabled,
            "time_step": self.time_step.value,
            "operator": self.operator.value,
            "coeffs": self.coeffs,
            "comments": self.comments,
            "filter_year_by_year": self.filter_year_by_year,
            "filter_synthesis": self.filter_synthesis,
        }
        if self.values is not None:
            args["values"] = strip_matrix_protocol(self.values)
        return CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args=args,
        )

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateBindingConstraint):
            return False
        simple_match = self.id == other.id
        if not equal:
            return simple_match
        return (
            simple_match
            and self.enabled == other.enabled
            and self.time_step == other.time_step
            and self.operator == other.operator
            and self.coeffs == other.coeffs
            and self.values == other.values
            and self.comments == other.comments
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        if self.values is not None:
            assert_this(isinstance(self.values, str))
            return [strip_matrix_protocol(self.values)]
        return []
