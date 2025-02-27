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

import copy
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, create_model

from antarest.core.utils.string import to_camel_case

ModelClass = TypeVar("ModelClass", bound=BaseModel)


def all_optional_model(model: Type[ModelClass]) -> Type[ModelClass]:
    """
    This decorator can be used to make all fields of a pydantic model optionals.

    Args:
        model: The pydantic model to modify.

    Returns:
        The modified model.
    """
    kwargs = {}
    for field_name, field_info in model.model_fields.items():
        new = copy.deepcopy(field_info)
        new.default = None
        new.annotation = Optional[field_info.annotation]  # type: ignore
        kwargs[field_name] = (new.annotation, new)

    return create_model(f"Partial{model.__name__}", __base__=model, __module__=model.__module__, **kwargs)  # type: ignore


def camel_case_model(model: Type[BaseModel]) -> Type[BaseModel]:
    """
    This decorator can be used to modify a model to use camel case aliases.

    Args:
        model: The pydantic model to modify.

    Returns:
        The modified model.
    """
    model.model_config["alias_generator"] = to_camel_case

    # Manually overriding already defined alias names (in base classes),
    # otherwise they have precedence over generated ones.
    # TODO There is probably a better way to handle those cases
    for field_name, field in model.model_fields.items():
        new_alias = to_camel_case(field_name)
        field.alias = new_alias
        field.validation_alias = new_alias
        field.serialization_alias = new_alias
    return model
