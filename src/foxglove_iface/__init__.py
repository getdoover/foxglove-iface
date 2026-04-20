from pydoover.docker import run_app

from .application import FoxgloveIfaceApplication


def main():
    """
    Run the application.
    """
    run_app(FoxgloveIfaceApplication())
