import logging
import time

from pydoover.docker import Application

from .foxglove_converter import FoxgloveConverter
from .app_config import FoxgloveIfaceConfig

log = logging.getLogger()

DOOVER_CHANNELS = [
    "tag_values",
    "ui_cmds"
]


class FoxgloveIfaceApplication(Application):
    config: (
        FoxgloveIfaceConfig  # not necessary, but helps your IDE provide autocomplete!
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started: float = time.time()

    async def setup(self):
        self.foxglove_server = FoxgloveConverter(
            self.device_agent,
            channels=DOOVER_CHANNELS,
        )

    async def main_loop(self):
        logging.debug("Mainloop is running")
