from typing import Dict, List, Union, Any, Optional

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
    BindingConstraintOperator,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
)


class CreateBindingConstraint(ICommand):
    name: str
    enabled: bool = True
    time_step: TimeStep
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Optional[Union[List[List[float]], str]] = None
    comments: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    @validator("name")
    def validate_name(cls, value: str) -> str:
        valid_name = transform_name_to_id(value, lower=False)
        if valid_name != value:
            raise ValueError(
                "Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters"
            )
        return value

    @validator("values", always=True)
    def validate_series(
        cls, v: Optional[Union[List[List[float]], str]], values: Any
    ) -> Optional[Union[List[List[float]], str]]:
        if v is None:
            v = values[
                "command_context"
            ].generator_matrix_constants.get_null_matrix()
            return v
        else:
            return validate_matrix(v, values)

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        assert isinstance(self.values, str)
        binding_constraints = study_data.tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )

        new_key = len(binding_constraints.keys())
        bd_id = transform_name_to_id(self.name)
        binding_constraints[str(new_key)] = {
            "id": bd_id,
            "name": self.name,
            "enabled": self.enabled,
            "type": self.time_step.value,
            "operator": self.operator.value,
            "comments": self.comments,
        }

        for link_or_thermal in self.coeffs:
            if "%" in link_or_thermal:
                area_1, area_2 = link_or_thermal.split("%")
                if (
                    area_1 not in study_data.config.areas
                    or area_2 not in study_data.config.areas[area_1].links
                ):
                    return CommandOutput(
                        status=False,
                        message=f"Link {link_or_thermal} does not exist",
                    )
            else:
                area, thermal_id = link_or_thermal.split(".")
                if area not in study_data.config.areas and thermal_id not in [
                    thermal.id
                    for thermal in study_data.config.areas[area].thermals
                ]:
                    return CommandOutput(
                        status=False,
                        message=f"Thermal cluster {link_or_thermal} does not exist",
                    )

            binding_constraints[str(new_key)][link_or_thermal] = "%".join(
                [str(coeff_val) for coeff_val in self.coeffs[link_or_thermal]]
            )

        study_data.config.bindings.append(bd_id)
        study_data.tree.save(
            binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )
        study_data.tree.save(
            self.values, ["input", "bindingconstraints", bd_id]
        )

        return CommandOutput(status=True)

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
