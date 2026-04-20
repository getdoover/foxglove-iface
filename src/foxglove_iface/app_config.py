from pathlib import Path

from pydoover import config


class FoxgloveIfaceConfig(config.Schema):
    host = config.String(
        "Server Host",
        name="host",
        default="0.0.0.0",
        description="Interface the Foxglove websocket server binds to.",
    )
    port = config.Integer(
        "Server Port",
        name="port",
        default=8765,
        description="Port the Foxglove websocket server listens on.",
    )
    channels = config.Array(
        "Subscribed Channels",
        name="channels",
        element=config.String("Channel Name"),
        default=["tag_values", "ui_cmds"],
        description="Doover channels to subscribe to and bridge into Foxglove.",
    )
    separate_levels = config.Integer(
        "Separate Levels",
        name="separate_levels",
        default=1,
        description="Depth at which nested channel data is split into separate Foxglove topics.",
    )
    parameter_publish_interval = config.Number(
        "Parameter Publish Interval",
        name="parameter_publish_interval",
        default=6.0,
        description="Seconds between publishing parameter values to connected Foxglove clients.",
    )


def export():
    FoxgloveIfaceConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "foxglove_iface"
    )
