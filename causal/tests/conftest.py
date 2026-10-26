import sys
from pathlib import Path

# The module under test lives in causal/, one level above this directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
