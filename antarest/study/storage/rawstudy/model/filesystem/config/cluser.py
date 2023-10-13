"""
Common properties related to thermal and renewable clusters, and short-term storage.

In the near future, this set of classes may be used for solar, wind and hydro clusters.
"""
import functools
import typing as t

from pydantic import BaseModel, Extra, Field

__all__ = ("BaseClusterProperties", "ClusterProperties")


@functools.total_ordering
class BaseClusterProperties(
    BaseModel,
    extra=Extra.forbid,
    validate_assignment=True,
    allow_population_by_field_name=True,
):
    """
    Common properties related to thermal and renewable clusters, and short-term storage.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.cluser import BaseClusterProperties

    >>> cl1 = BaseClusterProperties(name="cluster-01", group="group-A")
    >>> cl2 = BaseClusterProperties(name="CLUSTER-01", group="Group-B")
    >>> cl3 = BaseClusterProperties(name="cluster-02", group="GROUP-A")
    >>> l = [cl1, cl2, cl3]
    >>> l.sort()
    >>> [(c.group, c.name) for c in l]
    [('group-A', 'cluster-01'), ('GROUP-A', 'cluster-02'), ('Group-B', 'CLUSTER-01')]
    """

    group: str = Field(default="", description="Cluster group")

    name: str = Field(description="Cluster name", regex=r"[a-zA-Z0-9_(),& -]+")

    def __lt__(self, other: t.Any) -> bool:
        """
        Compare two clusters by group and name.

        This method may be used to sort and group clusters by `group` and `name`.
        """
        if isinstance(other, BaseClusterProperties):
            return (self.group.upper(), self.name.upper()).__lt__((other.group.upper(), other.name.upper()))
        return NotImplemented


class ClusterProperties(BaseClusterProperties):
    """
    Properties of a thermal or renewable cluster read from the configuration files.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.cluser import ClusterProperties

    >>> cl1 = ClusterProperties(name="cluster-01", group="group-A", enabled=True, unit_count=2, nominal_capacity=100)
    >>> (cl1.installed_capacity, cl1.enabled_capacity)
    (200.0, 200.0)

    >>> cl2 = ClusterProperties(name="cluster-01", group="group-A", enabled=False, unit_count=2, nominal_capacity=100)
    >>> (cl2.installed_capacity, cl2.enabled_capacity)
    (200.0, 0.0)
    """

    # Activity status:
    # - True: the plant may generate.
    # - False: not yet commissioned, moth-balled, etc.
    enabled: bool = Field(default=True, description="Activity status")

    # noinspection SpellCheckingInspection
    unit_count: int = Field(default=1, ge=1, description="Unit count", alias="unitcount")

    # noinspection SpellCheckingInspection
    nominal_capacity: float = Field(
        default=0.0,
        ge=0,
        description="Nominal capacity (MW per unit)",
        alias="nominalcapacity",
    )

    @property
    def installed_capacity(self) -> float:
        """"""
        return self.unit_count * self.nominal_capacity

    @property
    def enabled_capacity(self) -> float:
        return self.enabled * self.installed_capacity
