import configparser
from unittest.mock import Mock

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestCreateCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            ),
            matrix_service=matrix_service,
        )
        study_path = empty_study.config.study_path
        area_name = "Area"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "cluster_name"
        cluster_id = transform_name_to_id(cluster_name, lower=True)

        CreateArea.parse_obj(
            {
                "area_name": area_name,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        parameters = {
            "group": "Other",
            "unitcount": "1",
            "nominalcapacity": "1000000",
            "marginal-cost": "30",
            "market-bid-cost": "30",
        }

        command = CreateCluster.parse_obj(
            {
                "area_name": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        )

        output = command.apply(empty_study)
        assert output.status

        clusters = configparser.ConfigParser()
        clusters.read(
            study_path
            / "input"
            / "thermal"
            / "clusters"
            / area_id
            / "list.ini"
        )
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert str(clusters[cluster_name]["group"]) == parameters["group"]
        assert int(clusters[cluster_name]["unitcount"]) == int(
            parameters["unitcount"]
        )
        assert float(clusters[cluster_name]["nominalcapacity"]) == float(
            parameters["nominalcapacity"]
        )
        assert float(clusters[cluster_name]["marginal-cost"]) == float(
            parameters["marginal-cost"]
        )
        assert float(clusters[cluster_name]["market-bid-cost"]) == float(
            parameters["market-bid-cost"]
        )

        assert (
            study_path
            / "input"
            / "thermal"
            / "prepro"
            / area_id
            / cluster_id
            / "data.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "thermal"
            / "prepro"
            / area_id
            / cluster_id
            / "modulation.txt.link"
        ).exists()

        output = CreateCluster.parse_obj(
            {
                "area_name": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status

        output = CreateCluster.parse_obj(
            {
                "area_name": "non_existent_area",
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status
