import typing as t

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.areas import (
    OutputSimulationAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.binding_const import (
    OutputSimulationBindingConstraintItem,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.links import (
    OutputSimulationLinks,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid import (
    OutputSimulationModeMcAllGrid,
)

OUTPUT_SIMULATION_TYPE = t.Type[
    t.Union[
        OutputSimulationAreas,
        OutputSimulationModeMcAllGrid,
        OutputSimulationLinks,
        OutputSimulationBindingConstraintItem,
    ]
]
OUTPUT_MAPPING: t.Dict[str, OUTPUT_SIMULATION_TYPE] = {
    "areas": OutputSimulationAreas,
    "grid": OutputSimulationModeMcAllGrid,
    "links": OutputSimulationLinks,
    "binding_constraints": OutputSimulationBindingConstraintItem,
}


class OutputSimulationModeCommon(FolderNode):
    def build(self) -> TREE:
        if not self.config.output_path:
            return {}
        children: TREE = {}
        for key, simulation_class in OUTPUT_MAPPING.items():
            if (self.config.path / key).exists():
                children[key] = simulation_class(self.context, self.config.next_file(key))
        return children
