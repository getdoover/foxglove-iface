


def test_converter():
    from foxglove_iface.foxglove_converter import FoxgloveConverter
    converter = FoxgloveConverter("/test", 1)
    
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
    
    assert converter.channels["a"]["channelValue"].log.call_count == 1
    assert converter.channels["g"]["channelValue"].log.call_count == 1
    assert converter.channels["h"]["channelValue"].log.call_count == 1
    
    converter.on_values_update("test", {
        "a": {
            "b": 2,
            "c": "234234",
            "d": {
                "e": 3.324 * 2,
                "f": 4,
            }
        },
        "g": 5 + 1,
        "h": 6 - 1,
    })
    
    assert converter.channels["a"]["channelValue"].log.call_count == 2
    assert converter.channels["g"]["channelValue"].log.call_count == 2
    assert converter.channels["h"]["channelValue"].log.call_count == 2
    
    converter2 = FoxgloveConverter("/test", 3)
    
    converter2.on_values_update("test", {
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
    
    assert converter2.channels["a"]["b"]["channelValue"].log.call_count == 1
    assert converter2.channels["a"]["c"]["channelValue"].log.call_count == 1
    assert converter2.channels["a"]["d"]["e"]["channelValue"].log.call_count == 1
    assert converter2.channels["a"]["d"]["f"]["channelValue"].log.call_count == 1
    assert converter2.channels["g"]["channelValue"].log.call_count == 1
    assert converter2.channels["h"]["channelValue"].log.call_count == 1
    
    converter2.on_values_update("test", {
        "a": {
            "b": 2,
            "c": "234234",
            "d": {
                "e": 3.324 * 2,
                "f": 4,
            }
        },
        "g": 5 + 1,
        "h": 6 - 1,
    })
    
    assert converter2.channels["a"]["b"].log.call_count == 2
    assert converter2.channels["a"]["c"].log.call_count == 2
    assert converter2.channels["a"]["d"]["e"].log.call_count == 2
    assert converter2.channels["a"]["d"]["f"].log.call_count == 2
    assert converter2.channels["g"].log.call_count == 2
    assert converter2.channels["h"].log.call_count == 2
    

    