"""Entry point for executing the module directly.

This module allows CCG to be run as a Python module using:
    python -m ccg

It simply delegates to the main() function in ccg.cli, which handles
all command-line argument parsing and workflow orchestration.
"""

from ccg.cli import main

if __name__ == "__main__":  # pragma: no cover
    main()
