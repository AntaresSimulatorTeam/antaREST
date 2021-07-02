import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from checksumdir import dirhash

from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)


@pytest.mark.unit_test
@pytest.mark.parametrize("outputs", [True, False])
def test_export_file(tmp_path: Path, outputs: bool):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

    export_path = tmp_path / "study.zip"

    Exporter().export_file(root, export_path, outputs)
    zipf = ZipFile(export_path)

    assert "file.txt" in zipf.namelist()
    assert "test/" in zipf.namelist()
    assert "test/file.txt" in zipf.namelist()
    assert ("output/" in zipf.namelist()) == outputs
    assert ("output/file.txt" in zipf.namelist()) == outputs


@pytest.mark.unit_test
def test_export_flat(tmp_path: Path):
    root = tmp_path / "folder-with-output"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "test/output").mkdir()
    (root / "test/output/file.txt").write_text("Test")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

    root_without_output = tmp_path / "folder-without-output"
    root_without_output.mkdir()
    (root_without_output / "test").mkdir()
    (root_without_output / "test/file.txt").write_text("Bonjour")
    (root_without_output / "test/output").mkdir()
    (root_without_output / "test/output/file.txt").write_text("Test")
    (root_without_output / "file.txt").write_text("Hello, World")

    root_hash = dirhash(root, "md5")
    root_without_output_hash = dirhash(root_without_output, "md5")
    Exporter().export_flat(root, tmp_path / "copy_with_output", outputs=True)

    copy_with_output_hash = dirhash(tmp_path / "copy_with_output", "md5")

    assert root_hash == copy_with_output_hash

    Exporter().export_flat(
        root, tmp_path / "copy_without_output", outputs=False
    )

    copy_without_output_hash = dirhash(tmp_path / "copy_without_output", "md5")

    assert root_without_output_hash == copy_without_output_hash
