"""
MIPR Karst Module

This module provides functionality to check if coordinates, cadastral numbers, 
or groups of cadastrals fall within the PRAPEC (Plan y Reglamento del Área de 
Planificación Especial del Carso) karst areas in Puerto Rico.

Main Components:
- PrapecKarstChecker: Main class for karst area checking
- Convenience functions for direct usage
- LangGraph tools for agent integration
- Testing and exploration utilities
"""

from .prapec_karst_checker import (
    PrapecKarstChecker,
    check_coordinates_for_karst,
    check_cadastral_for_karst,
    check_multiple_cadastrals_for_karst
)

from .karst_tools import (
    KARST_TOOLS,
    check_cadastral_karst,
    check_multiple_cadastrals_karst,
    find_nearest_karst,
    analyze_cadastral_karst_proximity,
    get_karst_tool_descriptions
)

from .comprehensive_karst_analysis_tool import (
    COMPREHENSIVE_KARST_TOOLS,
    analyze_cadastral_karst_with_map,
    get_comprehensive_karst_tool_description
)

__all__ = [
    # Core functionality
    'PrapecKarstChecker',
    'check_coordinates_for_karst',
    'check_cadastral_for_karst',
    'check_multiple_cadastrals_for_karst',
    
    # LangGraph tools
    'KARST_TOOLS',
    'check_cadastral_karst',
    'check_multiple_cadastrals_karst',
    'find_nearest_karst',
    'analyze_cadastral_karst_proximity',
    'get_karst_tool_descriptions',

    # Comprehensive Karst Analysis Tool
    'COMPREHENSIVE_KARST_TOOLS',
    'analyze_cadastral_karst_with_map',
    'get_comprehensive_karst_tool_description'
]

__version__ = '1.0.0'
__author__ = 'MIPR Zoning System' 