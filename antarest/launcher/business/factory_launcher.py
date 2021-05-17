from typing import Dict

from antarest.common.config import Config
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.storage.service import StorageService


class FactoryLauncher:
    def build_launcher(
        self, config: Config, storage_service: StorageService
    ) -> Dict[str, ILauncher]:
        dict_launchers: Dict[str, ILauncher] = dict()
        dict_launchers["local"] = LocalLauncher(config, storage_service)
        dict_launchers["slurm"] = SlurmLauncher(config, storage_service)
        return dict_launchers
