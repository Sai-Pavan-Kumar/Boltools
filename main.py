"""Boltools Desktop Application Root Entrypoint."""

import os
import sys

# Add software root to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.app import main

if __name__ == "__main__":
    main()
