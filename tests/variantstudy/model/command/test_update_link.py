# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from unittest.mock import Mock

import numpy as np
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from antarest.core.exceptions import LinkValidationError
from antarest.study.business.link_management import LinkInternal
from antarest.study.model import STUDY_VERSION_8_8, LinksParametersTsGeneration, RawStudy
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from db_statement_recorder import DBStatementRecorder
from study.storage.variantstudy.model.command.update_link import UpdateLink


class TestUpdateLink:
    def test_apply(self, empty_study: FileStudy, command_context: CommandContext, db_session: Session):
        # =============================
        #  SET UP
        # =============================

        study_version = empty_study.config.version
        study_path = empty_study.config.study_path
        study_id = empty_study.config.study_id
        raw_study = RawStudy(id=study_id, version=str(study_version), path=str(study_path))
        db_session.add(raw_study)
        db_session.commit()

        area1_id = "area1"
        area2_id = "area2"

        CreateArea.model_validate(
            {"area_name": area1_id, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        CreateArea.model_validate(
            {"area_name": area2_id, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        # =============================
        #  NOMINAL CASES
        # =============================

        # Link creation
        parameters = {
            "hurdles-cost": True,
            "asset-type": "dc",
            "link-width": 12,
            "colorr": 120,
            "unit_count": 56,
            "law_planned": "geometric",
        }

        command_parameters = {
            "area1": area2_id,
            "area2": area1_id,
            "command_context": command_context,
            "study_version": study_version,
        }
        creation_parameters = {"parameters": parameters, **command_parameters}
        CreateLink.model_validate(creation_parameters).apply(study_data=empty_study)

        # Updating a Ini properties
        new_parameters = {"colorb": 35}
        update_parameters = {"parameters": new_parameters, **command_parameters}

        with DBStatementRecorder(db_session.bind) as db_recorder:
            UpdateLink.model_validate(update_parameters).apply(study_data=empty_study)
        # We shouldn't call the DB as no DB parameter were given
        assert len(db_recorder.sql_statements) == 0

        # Asserts the ini file is well modified (new value + old values unmodified)
        link = IniReader()
        link_data = link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert link_data[area2_id]["hurdles-cost"] == parameters["hurdles-cost"]
        assert link_data[area2_id]["asset-type"] == parameters["asset-type"]
        assert link_data[area2_id]["colorb"] == new_parameters["colorb"]
