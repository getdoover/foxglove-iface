import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import foxglove
from foxglove.websocket import Capability, Parameter, ServerListener

from genson import SchemaBuilder

from pydoover.docker.device_agent import DeviceAgentInterface
from pydoover.models import AggregateUpdateEvent, EventSubscription


log = logging.getLogger(__name__)


def generate_schema(path: List[str], value: Any) -> Dict[str, Any]:
    builder = SchemaBuilder()
    builder.add_object(value)
    schema = builder.to_schema()
    schema["title"] = f"{'-'.join(path)}"
    return convert_schema_types_to_float(schema)


def convert_schema_types_to_float(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert boolean and integer types to float in the schema."""
    if isinstance(schema, dict):
        if schema.get("type") in ("boolean", "integer"):
            schema["type"] = "number"
            for bound in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                if bound in schema and isinstance(schema[bound], int):
                    schema[bound] = float(schema[bound])

        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                schema["properties"][prop_name] = convert_schema_types_to_float(prop_schema)

        if "items" in schema:
            schema["items"] = convert_schema_types_to_float(schema["items"])

        for key in ("oneOf", "anyOf", "allOf"):
            if key in schema and isinstance(schema[key], list):
                schema[key] = [convert_schema_types_to_float(item) for item in schema[key]]

    return schema


def _shape(value):
    if isinstance(value, dict):
        return ("object", tuple((k, _shape(v)) for k, v in sorted(value.items())))
    if isinstance(value, list):
        rep = _shape(value[0]) if value else ("empty_list",)
        return ("array", rep)
    if isinstance(value, (int, float, bool)):
        return ("number",)
    return type(value).__name__


def schema_fingerprint(value) -> str:
    shape = _shape(value if isinstance(value, dict) else {"value": value})
    return hashlib.sha1(json.dumps(shape).encode("utf-8")).hexdigest()


class FoxgloveParameterManager(ServerListener):
    """Manages parameters for Foxglove, allowing real-time editing of topic values."""

    def __init__(self, converter: "FoxgloveConverter"):
        self.converter = converter
        self.parameters: Dict[str, Parameter] = {}
        self.current_values: Dict[str, Any] = {}

    def log_parameter(self, path: List[str], value: Any):
        if isinstance(value, dict):
            for key, sub_value in value.items():
                self.log_parameter(path + [key], sub_value)
            return
        self.update_param(path, value)

    def update_param(self, path: List[str], value: Any) -> Optional[Parameter]:
        """Update or create a parameter for a primitive value at the given path."""
        param_name = f"/{'/'.join(path)}"

        if isinstance(value, dict):
            return None

        self.current_values[param_name] = value
        self.parameters[param_name] = Parameter(param_name, value=value)
        return self.parameters[param_name]

    def get_all_parameters(self) -> List[Parameter]:
        return list(self.parameters.values())

    def update_parameter_value(self, param_name: str, new_value: Any):
        """Update a parameter value and propagate to the data structure."""
        if param_name in self.parameters:
            self.current_values[param_name] = new_value
            self.parameters[param_name] = Parameter(param_name, value=new_value)
            self.converter.update_value_from_parameter(param_name, new_value)

    # ServerListener implementation
    def on_get_parameters(self, client, param_names: List[str], request_id: Optional[str] = None) -> List[Parameter]:
        if not param_names:
            return self.get_all_parameters()
        return [self.parameters[name] for name in param_names if name in self.parameters]

    def on_set_parameters(self, client, parameters: List[Parameter], request_id: Optional[str] = None) -> List[Parameter]:
        log.info("Setting parameters: %s", parameters)
        for param in parameters:
            self.update_parameter_value(param.name, param.get_value())
        return self.get_all_parameters()

    def on_parameters_subscribe(self, param_names: List[str]) -> None:
        pass

    def on_parameters_unsubscribe(self, param_names: List[str]) -> None:
        pass

    # Required but unused ServerListener methods
    def on_subscribe(self, client, channel) -> None:
        pass

    def on_unsubscribe(self, client, channel) -> None:
        pass

    def on_client_advertise(self, client, channel) -> None:
        pass

    def on_client_unadvertise(self, client, client_channel_id: int) -> None:
        pass

    def on_message_data(self, client, client_channel_id: int, data: bytes) -> None:
        pass

    def on_connection_graph_subscribe(self) -> None:
        pass

    def on_connection_graph_unsubscribe(self) -> None:
        pass


class FoxgloveConverter:
    """Bridges Doover channel data to Foxglove topics, deriving schemas from observed values."""

    def __init__(
        self,
        device_agent: Optional[DeviceAgentInterface],
        channels: List[str],
        separate_levels: int = 1,
        parameter_publish_interval: float = 6.0,
        host: str = "0.0.0.0",
        port: int = 8765,
        start_server: bool = True,
    ):
        self.device_agent = device_agent
        self.subscribed_channels = channels
        self.separate_levels = separate_levels
        self.channels: Dict[str, Any] = {"channelValue": None}

        self.last_parameter_publish = time.time()
        self.parameter_publish_interval = parameter_publish_interval
        self.parameter_manager = FoxgloveParameterManager(self)

        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

        self.server = None
        if start_server:
            self.server = foxglove.start_server(
                host=host,
                port=port,
                capabilities=[Capability.Parameters],
                server_listener=self.parameter_manager,
            )

        if self.device_agent is not None:
            for ch in self.subscribed_channels:
                self.device_agent.add_event_callback(
                    ch,
                    self._make_event_handler(ch),
                    EventSubscription.aggregate_update,
                )

    def _make_event_handler(self, channel_name: str):
        async def handler(event: AggregateUpdateEvent):
            self.on_values_update(channel_name, event.aggregate.data)

        return handler

    def on_values_update(self, channel_name: str, channel_values: Dict[str, Any]):
        self.handle_values(channel_name, [], channel_values)

    def handle_values(self, doover_channel: str, path: List[str], value: Any):
        if len(path) >= self.separate_levels or not isinstance(value, dict):
            channel = self.get_foxglove_channel(doover_channel, path, value)
            channel.log(value if isinstance(value, dict) else {"value": value})
            self.parameter_manager.log_parameter([doover_channel] + path, value)
        else:
            for key, sub_value in value.items():
                self.handle_values(doover_channel, path + [key], sub_value)

        if self.server is not None:
            now = time.time()
            if now - self.last_parameter_publish > self.parameter_publish_interval:
                self.server.publish_parameter_values(self.parameter_manager.get_all_parameters())
                self.last_parameter_publish = now

    def param_to_json(self, topic: str, value: Any) -> Tuple[str, Any]:
        parts = [p for p in topic.split("/") if p]
        channel_name, *keys = parts
        nested: Any = value
        for key in reversed(keys):
            nested = {key: nested}
        return channel_name, nested

    def get_foxglove_channel(self, doover_channel: str, path: List[str], value):
        channels_dict = self.channels
        for segment in path:
            if channels_dict.get(segment) is None:
                channels_dict[segment] = {"channelValue": None, "schemaFingerprint": None}
            channels_dict = channels_dict[segment]

        current_fp = schema_fingerprint(value)
        if channels_dict["channelValue"] is None or channels_dict.get("schemaFingerprint") != current_fp:
            if channels_dict["channelValue"] is not None:
                channels_dict["channelValue"].close()

            payload_for_schema = value if isinstance(value, dict) else {"value": value}
            schema = generate_schema([doover_channel] + path, payload_for_schema)
            channels_dict["channelValue"] = foxglove.Channel(
                f"/{'/'.join([doover_channel] + path)}", schema=schema
            )
            channels_dict["schemaFingerprint"] = current_fp
        return channels_dict["channelValue"]

    def update_value_from_parameter(self, param_name: str, new_value: Any):
        """Push a Foxglove parameter edit back to the source Doover channel.

        Called by the Foxglove SDK from a background thread, so the coroutine
        is scheduled onto the captured main loop with run_coroutine_threadsafe.
        """
        if self.device_agent is None or self._main_loop is None:
            return

        channel_name, json_obj = self.param_to_json(param_name, new_value)
        asyncio.run_coroutine_threadsafe(
            self.device_agent.update_channel_aggregate(channel_name, json_obj),
            self._main_loop,
        )


if __name__ == "__main__":
    converter = FoxgloveConverter(None, channels=["/test"], separate_levels=1)

    converter.on_values_update(
        "test",
        {
            "a": {"b": 1, "c": "234234", "d": {"e": 3.324, "f": 4}},
            "g": 5,
            "h": 6,
        },
    )

    i = 0
    while True:
        converter.on_values_update(
            "test",
            {
                "a": {"b": i, "c": "234234", "d": {"e": 3.324 * i, "f": 4}},
                "g": 5 + 1,
                "h": 6 - i,
            },
        )
        time.sleep(0.1)
        i += 1
