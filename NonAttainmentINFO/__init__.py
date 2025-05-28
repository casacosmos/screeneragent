#!/usr/bin/env python3
"""
NonAttainmentINFO Package

This package provides comprehensive access to EPA nonattainment areas data
for air quality standards violations under the Clean Air Act.

Main Components:
- NonAttainmentAreasClient: Client for accessing EPA nonattainment areas services
- NONATTAINMENT_TOOLS: LangChain-compatible tools for nonattainment analysis
"""

from .nonattainment_client import (
    NonAttainmentAreasClient,
    NonAttainmentAreaInfo,
    NonAttainmentAnalysisResult
)

from .tools import (
    NONATTAINMENT_TOOLS,
    analyze_nonattainment_areas,
    search_pollutant_areas
)

__version__ = "1.0.0"
__author__ = "Environmental Screening Agent"
__description__ = "EPA Nonattainment Areas Analysis Tools"

__all__ = [
    'NonAttainmentAreasClient',
    'NonAttainmentAreaInfo', 
    'NonAttainmentAnalysisResult',
    'NONATTAINMENT_TOOLS',
    'analyze_nonattainment_areas',
    'search_pollutant_areas'
] 