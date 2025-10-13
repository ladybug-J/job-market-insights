import sys
from pathlib import Path

print(f"Add root path for importing modules to tests: {str(Path(__file__).resolve().parent.parent)}")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))