from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputThermalSeriesAreaThermalSeries(InputSeriesMatrix):
    def __init__(self, config: StudyConfig):
        super(InputThermalSeriesAreaThermalSeries, self).__init__(config)
