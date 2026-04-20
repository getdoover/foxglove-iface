"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from foxglove_iface.application import FoxgloveIfaceApplication

    assert FoxgloveIfaceApplication
    assert FoxgloveIfaceApplication.config_cls is not None


def test_config_schema():
    from foxglove_iface.app_config import FoxgloveIfaceConfig

    schema = FoxgloveIfaceConfig.to_schema()
    assert isinstance(schema, dict)

    expected_keys = {
        "host",
        "port",
        "channels",
        "separate_levels",
        "parameter_publish_interval",
    }
    assert expected_keys.issubset(schema["properties"].keys())


def test_config_defaults():
    from foxglove_iface.app_config import FoxgloveIfaceConfig

    schema = FoxgloveIfaceConfig.to_schema()
    props = schema["properties"]
    assert props["host"]["default"] == "0.0.0.0"
    assert props["port"]["default"] == 8765
    assert props["channels"]["default"] == ["tag_values", "ui_cmds"]
    assert props["separate_levels"]["default"] == 1
    assert props["parameter_publish_interval"]["default"] == 6.0
