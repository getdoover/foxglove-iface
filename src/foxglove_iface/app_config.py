from pathlib import Path

from pydoover import config


class FoxgloveIfaceConfig(config.Schema):
    pass


def export():
    FoxgloveIfaceConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "foxglove_iface"
    )
