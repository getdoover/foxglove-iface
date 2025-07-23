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

def test_ui():
    from foxglove_iface.app_ui import FoxgloveIfaceUI
    assert FoxgloveIfaceUI

def test_state():
    from foxglove_iface.app_state import FoxgloveIfaceState
    assert FoxgloveIfaceState