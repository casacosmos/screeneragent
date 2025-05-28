"""
HabitatINFO - Critical Habitat Analysis Module

A comprehensive Python module for analyzing critical habitat areas designated 
under the U.S. Endangered Species Act (ESA). Provides tools to determine if 
geographic locations intersect with protected species habitats and offers 
detailed regulatory guidance.

Main Components:
- habitat_client: Core client for USFWS critical habitat services
- tools: LangChain-compatible tools for habitat analysis
- Data classes for structured habitat information

Example Usage:
    from HabitatINFO.tools import analyze_critical_habitat
    
    result = analyze_critical_habitat.invoke({
        "longitude": -122.4194,
        "latitude": 37.7749
    })
"""

__version__ = "1.0.0"
__author__ = "HabitatINFO Development Team"
__description__ = "Critical Habitat Analysis Module for ESA Compliance"

# Import main components for easy access
from .habitat_client import (
    CriticalHabitatClient,
    CriticalHabitatInfo,
    HabitatAnalysisResult
)

from .tools import (
    analyze_critical_habitat,
    habitat_tools
)

from .map_tools import (
    generate_critical_habitat_map,
    generate_adaptive_critical_habitat_map,
    critical_habitat_map_tools
)

# Package metadata
__all__ = [
    # Client classes
    "CriticalHabitatClient",
    "CriticalHabitatInfo", 
    "HabitatAnalysisResult",
    
    # Analysis Tools
    "analyze_critical_habitat",
    "habitat_tools",
    
    # Map Generation Tools
    "generate_critical_habitat_map",
    "generate_adaptive_critical_habitat_map",
    "critical_habitat_map_tools",
    
    # Metadata
    "__version__",
    "__author__",
    "__description__"
] 