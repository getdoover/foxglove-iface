import logging

from pydoover.docker import Application

from .foxglove_converter import FoxgloveConverter
from .app_config import FoxgloveIfaceConfig

log = logging.getLogger()


class FoxgloveIfaceApplication(Application):
    config_cls = FoxgloveIfaceConfig

    async def setup(self):
        channels = [c.value for c in self.config.channels.elements]
        self.foxglove_server = FoxgloveConverter(
            self.device_agent,
            channels=channels,
            host=self.config.host.value,
            port=int(self.config.port.value),
            separate_levels=int(self.config.separate_levels.value),
            parameter_publish_interval=self.config.parameter_publish_interval.value,
        )

    async def main_loop(self):
        log.debug("Mainloop is running")
