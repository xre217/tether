#!/usr/bin/env python3
"""
Quick runner for the Tether red-teaming harness.

Usage:
    python run_redteam.py

This will test the current sacred prompt against all characters
in src/tether/redteam/characters/ and save results to results/.
"""

import sys
from pathlib import Path

# Make sure we can import from src
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tether.redteam.harness import run_full_redteam_suite

if __name__ == "__main__":
    base = Path(__file__).parent / "src" / "tether" / "redteam"
    chars = base / "characters"
    results = base / "results"

    run_full_redteam_suite(chars, results, turns=6)
