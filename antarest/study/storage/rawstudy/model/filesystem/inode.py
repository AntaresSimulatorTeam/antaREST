from abc import ABC, abstractmethod
from typing import List, Optional, Dict, TypeVar, Generic, Any

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


class INode(ABC, Generic[G, S, V]):
    """
    Abstract tree element, have to be implemented to create hub or left.
    """

    @abstractmethod
    def build(self, config: FileStudyTreeConfig) -> "TREE":
        """
        build children (next tree level) according to study config
        Args:
            config: current study configuration used to build tree

        Returns: children of current node

        """
        raise NotImplementedError()

    @abstractmethod
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        """
        Ask data inside tree.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion

        Returns: json

        """
        raise NotImplementedError()

    @abstractmethod
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Save data inside tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def check_errors(
        self, data: V, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        """
        List inconsistency error between data and study configuration.
        Args:
            data: data to compare
            url: data path to compare
            raising: raise error if inconsistency occurs

        Returns: list of errors belongs to this node or children

        """
        raise NotImplementedError()

    @abstractmethod
    def normalize(self) -> None:
        """
        Scan tree to send matrix in matrix store and replace by its links
        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def denormalize(self) -> None:
        """
        Scan tree to fetch matrix by its links
        Returns:

        """
        raise NotImplementedError()

    def _assert_url_end(self, url: Optional[List[str]] = None) -> None:
        """
        Raise error if elements remain in url
        Args:
            url: data path

        Returns:

        """
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )


TREE = Dict[str, INode[Any, Any, Any]]
