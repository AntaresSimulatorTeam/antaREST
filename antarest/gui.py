# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import argparse
import multiprocessing

from antarest import __version__
from antarest.core.cli import PathType


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=PathType(exists=True, file_ok=True),
        dest="config_file",
        help="path to the config file [default: '%(default)s']",
        default="./config.yaml",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Display the server version and exit",
        version=__version__,
    )
    return parser.parse_args()


def main() -> None:
    multiprocessing.freeze_support()

    arguments = parse_arguments()

    # VERY important to keep this import here in order to have fast startup
    # when only getting version
    from antarest.desktop.systray_app import run_systray_app

    run_systray_app(arguments.config_file)


if __name__ == "__main__":
    main()
