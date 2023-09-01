from checksumdir import dirhash

from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import BindingConstraintOperator, TimeStep
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestRemoveCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        area_name = "Area_name"
        area_id = transform_name_to_id(area_name)
        cluster_name = "cluster_name"
        cluster_id = transform_name_to_id(cluster_name)

        CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        ).apply(empty_study)

        ################################################################################################
        hash_before_cluster = dirhash(empty_study.config.study_path, "md5")

        CreateCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters={
                "group": "group",
                "unitcount": "unitcount",
                "nominalcapacity": "nominalcapacity",
                "marginal-cost": "marginal-cost",
                "market-bid-cost": "market-bid-cost",
            },
            command_context=command_context,
            prepro=[[0]],
            modulation=[[0]],
        ).apply(empty_study)

        bind1_cmd = CreateBindingConstraint(
            name="BD 1",
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.LESS,
            coeffs={
                f"{area_id}.{cluster_id}": [800, 30],
            },
            comments="Hello",
            command_context=command_context,
        )
        output = bind1_cmd.apply(study_data=empty_study)
        assert output.status

        output = RemoveCluster(
            area_id=area_id,
            cluster_id=cluster_id,
            command_context=command_context,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5")
            == hash_before_cluster
        )

        output = RemoveCluster(
            area_id="non_existent_area",
            cluster_id=cluster_id,
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status

        output = RemoveCluster(
            area_id=area_name,
            cluster_id="non_existent_cluster",
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = RemoveCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_match = RemoveCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_not_match = RemoveCluster(
        area_id="foo", cluster_id="baz", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_cluster%bar%foo"
    assert base.get_inner_matrices() == []


def test_create_diff(command_context: CommandContext):
    base = RemoveCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_match = RemoveCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    assert base.create_diff(other_match) == []
