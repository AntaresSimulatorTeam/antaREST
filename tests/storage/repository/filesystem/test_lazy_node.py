from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import V, S, G, TREE
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MockLazyNode(LazyNode[str, str, str]):
    def __init__(self, context: ContextServer, config: StudyConfig) -> None:
        super().__init__(
            config=config,
            context=context,
            url_prefix="file",
        )

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return "Hello"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_get_no_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.touch()

    uri = "studyfile://my-study/lazy.txt"
    uri_resolver = Mock()
    uri_resolver.build_studyfile_uri.return_value = uri

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockLazyNode(
        context=ContextServer(matrix=Mock(), resolver=uri_resolver),
        config=config,
    )
    assert uri == node.get(expanded=True)


def test_get_no_expanded_link(tmp_path: Path):
    pass


def test_get_expanded_txt(tmp_path: Path):
    pass


def test_get_expanded_link(tmp_path: Path):
    pass


def test_save(tmp_path: Path):
    file = tmp_path / "lazy.txt"
    file.touch()

    src = tmp_path / "src.txt"
    src.write_text("Lazy")

    node = MockLazyNode(file)

    node.save(f"file://{src.absolute()}")
    assert file.read_text() == "Lazy"

    node.save("Not Lazy")
    assert file.read_text() == "Not Lazy"
