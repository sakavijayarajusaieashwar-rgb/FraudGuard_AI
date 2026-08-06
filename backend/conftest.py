import os
import sys

# Ensure backend package imports work when pytest is run from the repository root.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
