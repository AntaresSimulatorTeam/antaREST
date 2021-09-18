import logging
from typing import List, Optional, Union, Tuple

from antarest.core.custom_types import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.model import MatrixData
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    TimeStep,
    BindingConstraintOperator,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class VariantCommandsExtractor:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(
            self.matrix_service
        )
        self.command_context = CommandContext(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
        )
        self.null_matrix_id = strip_matrix_protocol(
            self.generator_matrix_constants.get_null_matrix()
        )

    def extract(self, study: FileStudy) -> List[CommandDTO]:
        stopwatch = StopWatch()
        study_tree = study.tree
        study_config = study.config
        study_commands: List[ICommand] = []

        study_commands.append(
            self._generate_update_config(
                study_tree, ["settings", "generaldata"]
            )
        )
        study_commands.append(
            self._generate_update_config(
                study_tree,
                ["settings", "scenariobuilder"],
            )
        )
        study_commands.append(
            self._generate_update_config(study_tree, ["layers", "layers"])
        )
        # todo create something out of variant manager commands to replace single rawnode files ?
        # study_commands.append(
        #     self._generate_update_config(
        #         study_tree, ["settings", "comments"]
        #     )
        # )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"General command extraction done in {x}s")
        )

        all_links_commands: List[ICommand] = []
        for area_id in study_config.areas:
            area_commands, links_commands = self.extract_area(study, area_id)
            study_commands += area_commands
            all_links_commands += links_commands
        study_commands += all_links_commands

        # correlations
        for type in ["load", "wind", "solar", "hydro"]:
            study_commands.append(
                self._generate_update_config(
                    study_tree,
                    ["input", type, "prepro", "correlation"],
                )
            )

        # sets and all area config (weird it is found in thermal..)
        study_commands.append(
            self._generate_update_config(
                study_tree,
                ["input", "thermal", "areas"],
            )
        )
        for set_id in study_config.sets:
            study_commands += self.extract_district(study, set_id)

        # binding constraints
        binding_config = study_tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        for binding_id, binding_data in binding_config.items():
            study_commands += self.extract_binding_constraint(
                study, binding_id, binding_data
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Binding command extraction done in {x}s")
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command extraction done in {x}s"), True
        )
        return [command.to_dto() for command in study_commands]

    def extract_area(
        self, study: FileStudy, area_id: str
    ) -> Tuple[List[ICommand], List[ICommand]]:
        stopwatch = StopWatch()
        study_commands: List[ICommand] = []
        links_commands: List[ICommand] = []
        study_tree = study.tree
        study_config = study.config
        area = study_config.areas[area_id]
        optimization_data = study_tree.get(
            ["input", "areas", area_id, "optimization"]
        )
        ui_data = study_tree.get(["input", "areas", area_id, "ui"])
        area_command = CreateArea(
            area_name=area.name,
            metadata={},
            command_context=self.command_context,
        )
        study_commands.append(area_command)
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/optimization",
                data=optimization_data,
                command_context=self.command_context,
            )
        )
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/ui",
                data=ui_data,
                command_context=self.command_context,
            )
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Area command extraction done in {x}s")
        )

        links_data = study_tree.get(["input", "links", area_id, "properties"])
        for link in area.links:
            links_commands += self.extract_link(
                study, area_id, link, links_data
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Link command extraction done in {x}s")
        )
        for thermal in area.thermals:
            study_commands += self.extract_cluster(study, area_id, thermal.id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Thermal command extraction done in {x}s")
        )

        # load, wind, solar
        for type in ["load", "wind", "solar"]:
            for matrix in ["conversion", "data", "k", "translation"]:
                study_commands.append(
                    self._generate_replace_matrix(
                        study_tree,
                        ["input", type, "prepro", area_id, matrix],
                    )
                )
            study_commands.append(
                self._generate_update_config(
                    study_tree,
                    ["input", type, "prepro", area_id, "settings"],
                )
            )
            study_commands.append(
                self._generate_replace_matrix(
                    study_tree,
                    ["input", type, "series", f"{type}_{area_id}"],
                    self.null_matrix_id,
                )
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Prepro command extraction done in {x}s")
        )

        # misc gen / reserves
        study_commands.append(
            self._generate_replace_matrix(
                study_tree, ["input", "reserves", area_id]
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "misc-gen", f"miscgen-{area_id}"],
            )
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Misc command extraction done in {x}s")
        )
        # hydro
        study_commands += self.extract_hydro(study, area_id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Hydro command extraction done in {x}s")
        )
        return study_commands, links_commands

    def extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: Optional[JSON] = None,
    ) -> List[ICommand]:
        commands: List[ICommand] = []
        study_tree = study.tree
        link_command = CreateLink(
            area1=area1,
            area2=area2,
            parameters={},
            command_context=self.command_context,
        )
        link_data = (
            links_data.get(area2)
            if links_data is not None
            else study_tree.get(["input", "links", area1, area2])
        )
        link_config_command = UpdateConfig(
            target=f"input/links/{area1}/properties/{area2}",
            data=link_data,
            command_context=self.command_context,
        )
        commands.append(link_command)
        commands.append(link_config_command)
        commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "links", area1, area2],
                self.null_matrix_id,
            )
        )
        return commands

    def extract_cluster(
        self, study: FileStudy, area_id: str, thermal_id: str
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
        study_tree = study.tree
        thermal_name = thermal_id
        for thermal in study.config.areas[area_id].thermals:
            if thermal.id == thermal_id:
                thermal_name = thermal.name
                break
        assert thermal_name is not None
        study_commands.append(
            CreateCluster(
                area_id=area_id,
                cluster_name=thermal_name,
                parameters={},
                command_context=self.command_context,
            )
        )
        study_commands.append(
            self._generate_update_config(
                study_tree,
                [
                    "input",
                    "thermal",
                    "clusters",
                    area_id,
                    "list",
                    thermal_name,
                ],
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "prepro",
                    area_id,
                    thermal_id,
                    "data",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "prepro",
                    area_id,
                    thermal_id,
                    "modulation",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "series",
                    area_id,
                    thermal_id,
                    "series",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        return study_commands

    def extract_hydro(self, study: FileStudy, area_id: str) -> List[ICommand]:
        study_tree = study.tree
        commands = [
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"maxpower_{area_id}",
                ],
            ),
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"reservoir_{area_id}",
                ],
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "prepro", area_id, "energy"]
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "mod"]
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "ror"]
            ),
            self._generate_update_config(
                study_tree, ["input", "hydro", "prepro", area_id, "prepro"]
            ),
            self._generate_update_config(
                study_tree, ["input", "hydro", "allocation", area_id]
            ),
        ]

        if study_tree.config.version > 650:
            commands += [
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"creditmodulations_{area_id}",
                    ],
                ),
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"inflowPattern_{area_id}",
                    ],
                ),
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"waterValues_{area_id}",
                    ],
                ),
            ]

        hydro_config = study_tree.get(["input", "hydro", "hydro"])
        for key in hydro_config:
            if area_id in hydro_config[key]:
                commands.append(
                    self._generate_update_config(
                        study_tree,
                        ["input", "hydro", "hydro", key, area_id],
                    )
                )

        return commands

    def extract_district(
        self, study: FileStudy, district_id: str
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
        study_config = study.config
        study_tree = study.tree
        district_config = study_config.sets[district_id]
        district_fetched_config = study_tree.get(
            ["input", "areas", "sets", district_id]
        )
        study_commands.append(
            CreateDistrict(
                name=district_config.name,
                metadata={},
                base_filter=DistrictBaseFilter.add_all
                if district_config.inverted_set
                else DistrictBaseFilter.remove_all,
                filter_items=district_config.areas or [],
                output=district_config.output,
                comments=district_fetched_config.get("comments", None),
                command_context=self.command_context,
            )
        )
        return study_commands

    def extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: Optional[JSON] = None,
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
        study_tree = study.tree
        binding = bindings_data
        if not bindings_data:
            for binding_config in study_tree.get(
                ["input", "bindingconstraints", "bindingconstraints"]
            ).values():
                if binding_config["id"] == binding_id:
                    binding = binding_config
                    break
        assert binding is not None
        binding_constraint_command = CreateBindingConstraint(
            name=binding["name"],
            enabled=binding["enabled"],
            time_step=TimeStep(binding["type"]),
            operator=BindingConstraintOperator(binding["operator"]),
            coeffs={
                coeff: [float(el) for el in str(value).split("%")]
                for coeff, value in binding.items()
                if "%" in coeff or "." in coeff
            },
            comments=binding.get("comments", None),
            command_context=self.command_context,
        )
        study_commands.append(binding_constraint_command)
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "bindingconstraints", binding["id"]],
            )
        )
        return study_commands

    def diff(
        self, base: List[CommandDTO], variant: List[CommandDTO]
    ) -> List[ICommand]:
        stopwatch = StopWatch()
        command_factory = CommandFactory(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
        )
        logger.info("Parsing commands")
        base_commands: List[ICommand] = []
        for command in base:
            base_commands += command_factory.to_icommand(command)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Base commands parsed in {x}s")
        )
        variant_commands: List[ICommand] = []
        for command in variant:
            variant_commands += command_factory.to_icommand(command)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Variant commands parsed in {x}s")
        )

        logger.info("Computing commands diff")
        added_commands: List[Tuple[int, ICommand]] = []
        missing_commands: List[Tuple[int, ICommand]] = []
        modified_commands: List[Tuple[int, ICommand, ICommand]] = []
        order = 0
        for variant_command in variant_commands:
            order += 1
            found = False
            for base_command in base_commands:
                if variant_command.match(base_command):
                    if not variant_command.match(base_command, True):
                        modified_commands.append(
                            (order, variant_command, base_command)
                        )
                    found = True
                    break
            if not found:
                added_commands.append((order, variant_command))
        stopwatch.log_elapsed(
            lambda x: logger.info(f"First diff pass done in {x}s")
        )
        logger.info(f"Found {len(added_commands)} added commands")
        logger.info(f"Found {len(modified_commands)} modified commands")
        order = 0
        for base_command in base_commands:
            found = False
            for variant_command in variant_commands:
                if base_command.match(variant_command):
                    found = True
                    break
            if not found:
                missing_commands.append((order, base_command))
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Second diff pass done in {x}s")
        )
        logger.info(f"Found {len(missing_commands)} missing commands")

        first_priority_commands: List[ICommand] = []
        second_priority_commands: List[ICommand] = []
        third_priority_commands: List[ICommand] = []
        other_commands: List[Tuple[int, ICommand]] = []
        logger.info(f"Computing new diff commands")
        for order, command_obj in missing_commands:
            logger.info(f"Reverting {command_obj.match_signature()}")
            if command_obj.command_name == CommandName.REMOVE_AREA:
                first_priority_commands += command_obj.revert(base_commands)
            elif (
                command_obj.command_name == CommandName.REMOVE_LINK
                or command_obj.command_name == CommandName.REMOVE_CLUSTER
            ):
                second_priority_commands += command_obj.revert(base_commands)
            elif (
                command_obj.command_name == CommandName.UPDATE_CONFIG
                or command_obj.command_name == CommandName.REPLACE_MATRIX
            ):
                third_priority_commands += command_obj.revert(base_commands)
            else:
                other_commands += [
                    (0, command)
                    for command in command_obj.revert(base_commands)
                ]
        for order, variant_command, base_command in modified_commands:
            logger.info(
                f"Generating diff command for {variant_command.match_signature()}"
            )
            other_commands += [
                (order, command)
                for command in base_command.create_diff(variant_command)
            ]
        for ordered_command in added_commands:
            other_commands.append(ordered_command)

        diff_commands = (
            first_priority_commands
            + second_priority_commands
            + third_priority_commands
            + [ordered_command[1] for ordered_command in other_commands]
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Diff commands generation done in {x}s"),
            since_start=True,
        )
        logger.info(f"Diff commands total : {len(diff_commands)}")
        return diff_commands

    def _generate_update_config(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> ICommand:
        data = study_tree.get(url)
        return UpdateConfig(
            target="/".join(url),
            data=data,
            command_context=self.command_context,
        )

    def _generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: List[str],
        default_value: Optional[str] = None,
    ) -> ICommand:
        data = study_tree.get(url)
        matrix = VariantCommandsExtractor.get_matrix(
            data, default_value is None
        )
        return ReplaceMatrix(
            target="/".join(url),
            matrix=matrix or default_value,
            command_context=self.command_context,
        )

    @staticmethod
    def get_matrix(
        data: Union[JSON, str], raise_on_missing: Optional[bool] = False
    ) -> Optional[Union[str, List[List[MatrixData]]]]:
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            if "data" in data:
                assert isinstance(data["data"], list)
                return data["data"]
            else:
                return [[]]
        elif raise_on_missing:
            raise ValueError("Invalid matrix")
        return None
