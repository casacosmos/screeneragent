#!/usr/bin/env python3
"""
MIPR Cadastral Tools Package

This package provides comprehensive tools for working with Puerto Rico MIPR cadastral data,
including data retrieval, analysis, search capabilities, and map generation.

Main Components:
- CadastralDataProcessor: Core data processing and analysis utilities
- CadastralQueryBuilder: Query parameter construction for MIPR services
- MIPRCadastralSearch: Search cadastral data by numbers and classifications
- MIPRPointLookup: Point-based cadastral data lookup
- Cadastral tools for LangGraph agents

Dependencies:
- mapmaker.common: MapServerClient for MIPR service communication
- Standard libraries: sys, os, json, requests, math, datetime
- Type hints: typing module
- Data validation: pydantic
- Coordinate transformations: pyproj (optional)
- LangGraph: langchain_core.tools
"""

# Import main classes and functions for easy access
from .cadastral_utils import (
    CadastralDataProcessor,
    CadastralQueryBuilder,
    extract_cadastral_data,
    process_cadastral_features,
    analyze_cadastral_data
)

from .cadastral_search import MIPRCadastralSearch
from .point_lookup import MIPRPointLookup

# Import LangGraph tools
from .cadastral_data_tool import (
    get_cadastral_data_from_coordinates,
    get_cadastral_data_from_number,
    get_cadastral_tool_descriptions
)

from .cadastral_analysis_tool import analyze_cadastral_with_map

from .cadastral_center_point_tool import (
    calculate_cadastral_center_point,
    get_center_point_tool_description
)

# Import utility functions
from .get_cadastral_polygon_coords import (
    get_cadastral_polygon_coords,
    print_polygon_coords,
    calculate_polygon_area_approx
)

__version__ = "1.0.0"
__author__ = "MIPR Environmental Screening Agent"

__all__ = [
    # Core classes
    "CadastralDataProcessor",
    "CadastralQueryBuilder", 
    "MIPRCadastralSearch",
    "MIPRPointLookup",
    
    # Utility functions
    "extract_cadastral_data",
    "process_cadastral_features", 
    "analyze_cadastral_data",
    "get_cadastral_polygon_coords",
    "print_polygon_coords",
    "calculate_polygon_area_approx",
    
    # LangGraph tools
    "get_cadastral_data_from_coordinates",
    "get_cadastral_data_from_number",
    "analyze_cadastral_with_map",
    "calculate_cadastral_center_point",
    "get_cadastral_tool_descriptions",
    "get_center_point_tool_description"
] 