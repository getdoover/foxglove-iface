from pydoover.docker import run_app

from .application import FoxgloveIfaceApplication
from .app_config import FoxgloveIfaceConfig

def main():
    """
    Run the application.
    """
    run_app(FoxgloveIfaceApplication(config=FoxgloveIfaceConfig()))
