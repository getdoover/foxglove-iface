def test_converter():
    from foxglove_iface.foxglove_converter import FoxgloveConverter

    converter = FoxgloveConverter(None, ["/test"], 1, start_server=False)

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

    assert converter.channels["a"]["channelValue"] is not None
    assert converter.channels["g"]["channelValue"] is not None
    assert converter.channels["h"]["channelValue"] is not None

    converter2 = FoxgloveConverter(None, ["/test"], 3, start_server=False)

    converter2.on_values_update(
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

    assert converter2.channels["a"]["b"]["channelValue"] is not None
    assert converter2.channels["a"]["c"]["channelValue"] is not None
    assert converter2.channels["a"]["d"]["e"]["channelValue"] is not None
    assert converter2.channels["a"]["d"]["f"]["channelValue"] is not None
    assert converter2.channels["g"]["channelValue"] is not None
    assert converter2.channels["h"]["channelValue"] is not None
