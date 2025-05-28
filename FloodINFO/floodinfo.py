#!/usr/bin/env python3
"""
FloodINFO Launcher Script

Simple launcher for the FloodINFO tool.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main query tool
from query_coordinates_data import main

if __name__ == "__main__":
    main() 