from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputHydroSeriesAreaRor(InputSeriesMatrix):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super(InputHydroSeriesAreaRor, self).__init__(context, config)
