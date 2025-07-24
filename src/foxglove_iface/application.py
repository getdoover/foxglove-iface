import logging
import time
from typing import Any

import foxglove.channels
from pydoover.docker import Application
from pydoover import ui

import foxglove

from .foxglove_converter import FoxgloveConverter

from .app_config import FoxgloveIfaceConfig
from .app_ui import FoxgloveIfaceUI
from .app_state import FoxgloveIfaceState

log = logging.getLogger()

TAG_CHANNEL_NAME = "tag_values"


class FoxgloveIfaceApplication(Application):
    config: (
        FoxgloveIfaceConfig  # not necessary, but helps your IDE provide autocomplete!
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: FoxgloveIfaceUI = None
        self.state: FoxgloveIfaceState = None
        # self.foxglove_channels: dict[str, foxglove.Channel] = {}
        self.server = None
        self.foxglove_tag_values = FoxgloveConverter("/tag_values")

    async def setup(self):
        self.ui = FoxgloveIfaceUI()
        self.state = FoxgloveIfaceState()
        self.ui_manager.add_children(*self.ui.fetch())
        self.server = foxglove.start_server()

        self.device_agent.add_subscription(
            TAG_CHANNEL_NAME, self.foxglove_tag_values.on_values_update
        )

    async def main_loop(self):
        log.info("Mainloop is running")
