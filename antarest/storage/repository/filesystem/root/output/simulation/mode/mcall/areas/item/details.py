from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
)
from antarest.storage.repository.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


class OutputSimulationModeMcAllAreasItemDetails(OutputSeriesMatrix):
    def __init__(self, config: StudyConfig, freq: str):
        super(OutputSimulationModeMcAllAreasItemDetails, self).__init__(
            config=config, date_serializer=FactoryDateSerializer.create(freq)
        )
