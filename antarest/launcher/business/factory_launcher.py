import logging
from typing import Dict

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import IEventBus
from antarest.launcher.business.abstractlauncher import (
    AbstractLauncher,
    LauncherCallbacks,
)
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.storage.service import StorageService

logger = logging.getLogger(__name__)


class FactoryLauncher:
    def build_launcher(
        self,
        config: Config,
        storage_service: StorageService,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ) -> Dict[str, AbstractLauncher]:
        dict_launchers: Dict[str, AbstractLauncher] = dict()
        if config.launcher.local is not None:
            dict_launchers["local"] = LocalLauncher(
                config, storage_service, callbacks
            )
        if config.launcher.slurm is not None:
            dict_launchers["slurm"] = SlurmLauncher(
                config, storage_service, callbacks, event_bus
            )
        return dict_launchers
