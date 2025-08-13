"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from foxglove_iface.application import FoxgloveIfaceApplication

    assert FoxgloveIfaceApplication


def test_config():
    from foxglove_iface.app_config import FoxgloveIfaceConfig

    config = FoxgloveIfaceConfig()
    assert isinstance(config.to_dict(), dict)