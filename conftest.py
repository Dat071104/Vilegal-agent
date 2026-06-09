"""
Root conftest.py — adds src/ to sys.path so tests can import `vilegal`.
"""
import sys
from pathlib import Path

# Insert src/ at position 0 so `from vilegal.xxx import yyy` resolves correctly.
sys.path.insert(0, str(Path(__file__).parent / "src"))
