import time
import logging

import hashlib
import json
from typing import Any, Dict, List, Optional

import foxglove
from foxglove.websocket import Parameter, ServerListener, Capability

from pydoover.docker.device_agent import DeviceAgentInterface

from genson import SchemaBuilder


def generate_schema(path: List[str], value: Any):
    builder = SchemaBuilder()
    builder.add_object(value)
    schema = builder.to_schema()
    schema["title"] = f"{'-'.join(path)}"
    return schema

def _shape(value):
    if isinstance(value, dict):
        return ("object", tuple((k, _shape(v)) for k, v in sorted(value.items())))
    if isinstance(value, list):
        rep = _shape(value[0]) if value else ("empty_list",)
        return ("array", rep)
    return type(value).__name__

def schema_fingerprint(value) -> str:
    shape = _shape(value if isinstance(value, dict) else {"value": value})
    return hashlib.sha1(json.dumps(shape).encode("utf-8")).hexdigest()

class FoxgloveParameterManager(ServerListener):
    """Manages parameters for Foxglove, allowing real-time editing of topic values"""
    
    def __init__(self, converter: 'FoxgloveConverter'):
        self.converter = converter
        self.parameters: Dict[str, Parameter] = {}
        self.current_values: Dict[str, Any] = {}
    
    def log_parameter(self, path: List[str], value: Any):
        if isinstance(value, dict):
            for key, value in value.items():
                self.log_parameter(path + [key], value)
            return
        self.update_param(path, value)

    def update_param(self, path: List[str], value: Any):
        """Update or create a parameter for a specific value at the given path"""
        param_name = f"/{'/'.join(path)}"
        # logging.info(f"Updating parameter {param_name} to {value}")

        # Only create parameters for primitive values (not dictionaries)
        if not isinstance(value, dict):
            self.current_values[param_name] = value
            self.parameters[param_name] = Parameter(param_name, value=value)
            return self.parameters[param_name]
        return None
    
    def get_all_parameters(self) -> List[Parameter]:
        """Get all current parameters"""
        return list(self.parameters.values())
    
    def update_parameter_value(self, param_name: str, new_value: Any):
        """Update a parameter value and propagate to the data structure"""
        if param_name in self.parameters:
            self.current_values[param_name] = new_value
            self.parameters[param_name] = Parameter(param_name, value=new_value)
            # Update the actual data structure
            self.converter.update_value_from_parameter(param_name, new_value)
    
    # ServerListener implementation
    def on_get_parameters(self, client, param_names: List[str], request_id: Optional[str] = None) -> List[Parameter]:
        """Handle parameter get requests from Foxglove"""
        if not param_names:
            return self.get_all_parameters()
        result = []
        for name in param_names:
            if name in self.parameters:
                result.append(self.parameters[name])
        return result
    
    def on_set_parameters(self, client, parameters: List[Parameter], request_id: Optional[str] = None) -> List[Parameter]:
        """Handle parameter set requests from Foxglove"""
        logging.info(f"Setting parameters: {parameters}")
        for param in parameters:
            self.update_parameter_value(param.name, param.get_value())
        return self.get_all_parameters()
    
    def on_parameters_subscribe(self, param_names: List[str]) -> None:
        """Handle parameter subscription"""
        # logging.info(f"Client subscribed to parameters: {param_names}")
    
    def on_parameters_unsubscribe(self, param_names: List[str]) -> None:
        """Handle parameter unsubscription"""
        # logging.info(f"Client unsubscribed from parameters: {param_names}")
    
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
    """Takes data from a channel and converts it to Foxglove channels working out the schema based on the first value"""

    def __init__(self, device_agent: DeviceAgentInterface, channels: List[str], seperate_levels: int = 1, start_server: bool = True):
        """Creates a new FoxgloveConverter

        Args:
            topic (str): The topic to subscribe to
            seperate_levels (int, optional): The number of levels to seperate the channel data into different topics. Defaults to 1.
        """
        self.device_agent = device_agent
        self.subscribed_channels = channels
        self.seperate_levels = seperate_levels
        self.channels: Dict[str, Any] = {"channelValue": None}
    
        self.last_parameter_publish = time.time()
        self.parameter_publish_interval = 6
        self.parameter_manager = FoxgloveParameterManager(self)

        self.server = None
        if start_server:
            self.server = foxglove.start_server(
                host="0.0.0.0",
                port=8765,
            capabilities=[Capability.Parameters],
            server_listener=self.parameter_manager,
        )

        if self.device_agent is not None:
            for ch in self.subscribed_channels:
                self.device_agent.add_subscription(
                    ch, self.on_values_update
                )

    def on_values_update(self, channel_name: str, channel_values: Dict[str, Any]):
        self.handle_values(channel_name, [], channel_values)

    def handle_values(self, doover_channel: str, path: List[str], value: Any):
        # logging.info(f"handling {path} {value}")
        
        if len(path) >= self.seperate_levels:
            channel = self.get_foxglove_channel(doover_channel, path, value)
            if isinstance(value, dict):
                channel.log(value)
            else:
                channel.log({"value": value})
            self.parameter_manager.log_parameter([doover_channel] + path, value)
        elif isinstance(value, dict):
            for key, value in value.items():
                self.handle_values(doover_channel, path + [key], value)
        else:
            channel = self.get_foxglove_channel(doover_channel, path, value)
            if isinstance(value, dict):
                channel.log(value)
            else:
                channel.log({"value": value})
            self.parameter_manager.log_parameter([doover_channel] + path, value)

        ## Publish the parameters to the server
        if self.server is not None:
            if time.time() - self.last_parameter_publish > self.parameter_publish_interval:
                # logging.info(f"Publishing parameters to server: {self.parameter_manager.get_all_parameters()}")
                self.server.publish_parameter_values(self.parameter_manager.get_all_parameters())
                self.last_parameter_publish = time.time()

    def param_to_json(self, topic: str, value: Any) -> Dict[str, Any]:
        parts = [p for p in topic.split("/") if p]  # remove leading ''
        channel_name, *keys = parts
        nested = value
        for key in reversed(keys):
            nested = {key: nested}
        return channel_name, nested

    def get_foxglove_channel(self, doover_channel: str, path: List[str], value):
        channels_dict = self.channels
        for i in range(len(path)):
            # print(channels_dict)
            if channels_dict.get(path[i]) is None:
                channels_dict[path[i]] = {"channelValue": None, "schemaFingerprint": None}
            channels_dict = channels_dict[path[i]]

        # Compute current schema fingerprint, and check if it has changed
        current_fp = schema_fingerprint(value)
        if channels_dict["channelValue"] is None or channels_dict["schemaFingerprint"] != current_fp:
            ## If the channel already exists, remove it
            if channels_dict["channelValue"] is not None:
                channels_dict["channelValue"].close()

            if isinstance(value, dict):
                schema = generate_schema([doover_channel] + path, value)
            else:
                schema = generate_schema([doover_channel] + path, {"value": value})
            channels_dict["channelValue"] = foxglove.Channel(
                f"/{'/'.join([doover_channel] + path)}", schema=schema
            )
            channels_dict["schemaFingerprint"] = current_fp
        return channels_dict["channelValue"]
    
    def update_value_from_parameter(self, param_name: str, new_value: Any):
        """Update the data structure when a parameter value changes"""
        channel_name, json_obj = self.param_to_json(param_name, new_value)
        if self.device_agent is not None:
            self.device_agent.publish_to_channel(channel_name, json_obj, run_sync=True)


if __name__ == "__main__":
    foxglove.start_server(
        host="0.0.0.0",
        port=8765,
    )

    converter = FoxgloveConverter("/test")

    converter.on_values_update(
        "test",
        {
            "a": {
                "b": 1,
                "c": "234234",
                "d": {
                    "e": 3.324,
                    "f": 4,
                },
            },
            "g": 5,
            "h": 6,
        },
    )

    i = 0
    while True:
        converter.on_values_update(
            "test",
            {
                "a": {
                    "b": i,
                    "c": "234234",
                    "d": {
                        "e": 3.324 * i,
                        "f": 4,
                    },
                },
                "g": 5 + 1,
                "h": 6 - i,
            },
        )
        time.sleep(0.1)
        i += 1
