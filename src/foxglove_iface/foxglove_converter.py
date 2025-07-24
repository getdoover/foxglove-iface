

import json
import time
from typing import Any, Dict, List

import foxglove

from genson import SchemaBuilder

def generate_schema(path: List[str], value: Any):
    builder = SchemaBuilder()
    builder.add_object(value)
    schema = builder.to_schema()
    schema["title"] = f"{'-'.join(path)}"
    return schema

class FoxgloveConverter:
    '''Takes data from a channel and converts it to Foxglove channels working out the schema based on the first value'''
    def __init__(self, topic: str, seperate_levels: int = 1):
        '''Creates a new FoxgloveConverter
        
        Args:
            topic (str): The topic to subscribe to
            seperate_levels (int, optional): The number of levels to seperate the channel data into different topics. Defaults to 1.
        '''
        self.topic = topic.split("/")[-1]
        self.seperate_levels = seperate_levels
        self.channels: Dict[str, Any] = {
            "channelValue": None
        }
        pass
    
    def on_values_update(self, channel_name: str, channel_values: Dict[str, Any]):
        self.handle_values([], channel_values)
        print(self.channels)
    
    def handle_values(self, path: List[str], value: Any):
        print("handling", path)
        if len(path) >= self.seperate_levels:
            channel = self.get_foxglove_channel(path, value)
            if isinstance(value, dict):
                channel.log(value)
            else:
                channel.log({"value": value})
        elif isinstance(value, dict):
            for key, value in value.items():
                self.handle_values(path + [key], value)
        else:
            channel = self.get_foxglove_channel(path, value)
            if isinstance(value, dict):
                channel.log(value)
            else:
                channel.log({"value": value})
        
            
    def get_foxglove_channel(self, path: List[str], value):
        channels_dict = self.channels
        for i in range(len(path)):
            print(channels_dict)
            if channels_dict.get(path[i]) is None:
                channels_dict[path[i]] = {
                    "channelValue": None
                }
            channels_dict = channels_dict[path[i]]
        if channels_dict["channelValue"] is None:
            if isinstance(value, dict):
                schema = generate_schema([self.topic] + path, value)
            else:
                schema = generate_schema([self.topic] + path, { "value": value })
            channels_dict["channelValue"] = foxglove.Channel(f"/{'/'.join([self.topic] + path)}", schema=schema)
        return channels_dict["channelValue"]
    
    
if __name__ == "__main__":
    
    foxglove.start_server()
    
    converter = FoxgloveConverter("/test")
    
    converter.on_values_update("test", {
        "a": {
            "b": 1,
            "c": "234234",
            "d": {
                "e": 3.324,
                "f": 4,
            }
        },
        "g": 5,
        "h": 6,
    })
    
    i = 0
    while True:
        converter.on_values_update("test", {
            "a": {
                "b": i,
                "c": "234234",
                "d": {
                    "e": 3.324 * i,
                    "f": 4,
                }
            },
            "g": 5 + 1,
            "h": 6 - i,
        })
        time.sleep(0.1)
        i += 1
