"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from foxglove_iface.application import FoxgloveIfaceApplication

    assert FoxgloveIfaceApplication
    assert FoxgloveIfaceApplication.config_cls is not None


def test_config():
    from foxglove_iface.app_config import FoxgloveIfaceConfig

    schema = FoxgloveIfaceConfig.to_schema()
    assert isinstance(schema, dict)