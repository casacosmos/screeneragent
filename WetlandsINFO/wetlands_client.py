#!/usr/bin/env python3
"""
Wetlands Client for EPA and USFWS Services

Provides functionality to query wetland data from multiple sources:
- EPA NEPAssist RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)
- USFWS National Wetlands Inventory (NWI)
- EPA Waters services for watershed boundaries
"""

import requests
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode
from datetime import datetime

# Add parent directory to path to import output_directory_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from output_directory_manager import get_output_manager

logger = logging.getLogger(__name__)


@dataclass
class WetlandInfo:
    """Information about a wetland feature"""
    wetland_id: str
    wetland_type: str
    wetland_code: str
    description: str
    area_acres: Optional[float] = None
    location: Optional[Tuple[float, float]] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class RiparianInfo:
    """Information about riparian areas"""
    feature_id: str
    feature_type: str
    description: str
    location: Optional[Tuple[float, float]] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class WatershedInfo:
    """Information about watershed boundaries"""
    huc_code: str
    huc_level: int  # 2, 4, 6, 8, 10, or 12
    name: str
    area_sqkm: Optional[float] = None
    location: Optional[Tuple[float, float]] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class WetlandHabitatInfo:
    """Comprehensive wetland and habitat information for a location"""
    location: Tuple[float, float]
    wetlands: List[WetlandInfo]
    riparian_areas: List[RiparianInfo]
    watersheds: List[WatershedInfo]
    has_wetland_data: bool = False
    has_riparian_data: bool = False
    has_watershed_data: bool = False


class WetlandsClient:
    """
    Comprehensive client for querying wetland data from multiple sources.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Wetlands-Client/1.0'
        })
        
        # Service URLs
        self.epa_base_url = "https://geopub.epa.gov/arcgis/rest/services"
        self.usfws_base_url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services"
        self.epa_waters_url = "https://watersgeo.epa.gov/arcgis/rest/services"
        
        # Service endpoints
        self.ribits_url = f"{self.epa_base_url}/NEPAssist/RIBITS/MapServer"
        self.nwi_url = f"{self.usfws_base_url}/Wetlands/MapServer"
        self.nwi_raster_url = f"{self.usfws_base_url}/WetlandsRaster/ImageServer"
        self.riparian_url = f"{self.usfws_base_url}/Riparian/MapServer"
        self.watershed_url = f"{self.epa_waters_url}/NHDPlus_NP21/WBD_NP21_Simplified/MapServer"
    
    def query_point_wetland_info(self, longitude: float, latitude: float, 
                                include_riparian: bool = True, 
                                include_watershed: bool = True) -> WetlandHabitatInfo:
        """
        Query comprehensive wetland information at a specific point.
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            include_riparian: Whether to include riparian area data
            include_watershed: Whether to include watershed boundary data
            
        Returns:
            WetlandHabitatInfo object with comprehensive information
        """
        location = (longitude, latitude)
        wetlands = []
        riparian_areas = []
        watersheds = []
        
        # Query NWI wetlands data
        try:
            nwi_wetlands = self._query_nwi_wetlands(longitude, latitude)
            wetlands.extend(nwi_wetlands)
        except Exception as e:
            logger.warning(f"Failed to query NWI wetlands: {e}")
        
        # Query EPA RIBITS data
        try:
            ribits_data = self._query_ribits_data(longitude, latitude)
            wetlands.extend(ribits_data)
        except Exception as e:
            logger.warning(f"Failed to query RIBITS data: {e}")
        
        # Query riparian areas if requested
        if include_riparian:
            try:
                riparian_data = self._query_riparian_data(longitude, latitude)
                riparian_areas.extend(riparian_data)
            except Exception as e:
                logger.warning(f"Failed to query riparian data: {e}")
        
        # Query watershed boundaries if requested
        if include_watershed:
            try:
                watershed_data = self._query_watershed_data(longitude, latitude)
                watersheds.extend(watershed_data)
            except Exception as e:
                logger.warning(f"Failed to query watershed data: {e}")
        
        return WetlandHabitatInfo(
            location=location,
            wetlands=wetlands,
            riparian_areas=riparian_areas,
            watersheds=watersheds,
            has_wetland_data=len(wetlands) > 0,
            has_riparian_data=len(riparian_areas) > 0,
            has_watershed_data=len(watersheds) > 0
        )
    
    def query_polygon_wetland_info(self, polygon_coords: List[Tuple[float, float]], 
                                  include_riparian: bool = True, 
                                  include_watershed: bool = True) -> WetlandHabitatInfo:
        """
        Query comprehensive wetland information within a polygon.
        
        Args:
            polygon_coords: List of (longitude, latitude) tuples defining the polygon
            include_riparian: Whether to include riparian area data
            include_watershed: Whether to include watershed boundary data
            
        Returns:
            WetlandHabitatInfo object with comprehensive information
        """
        # Calculate centroid for location reference
        lon_sum = sum(coord[0] for coord in polygon_coords)
        lat_sum = sum(coord[1] for coord in polygon_coords)
        centroid = (lon_sum / len(polygon_coords), lat_sum / len(polygon_coords))
        
        wetlands = []
        riparian_areas = []
        watersheds = []
        
        # Query NWI wetlands data
        try:
            nwi_wetlands = self._query_nwi_wetlands_polygon(polygon_coords)
            wetlands.extend(nwi_wetlands)
        except Exception as e:
            logger.warning(f"Failed to query NWI wetlands for polygon: {e}")
        
        # Query EPA RIBITS data
        try:
            ribits_data = self._query_ribits_data_polygon(polygon_coords)
            wetlands.extend(ribits_data)
        except Exception as e:
            logger.warning(f"Failed to query RIBITS data for polygon: {e}")
        
        # Query riparian areas if requested
        if include_riparian:
            try:
                riparian_data = self._query_riparian_data_polygon(polygon_coords)
                riparian_areas.extend(riparian_data)
            except Exception as e:
                logger.warning(f"Failed to query riparian data for polygon: {e}")
        
        # Query watershed boundaries if requested
        if include_watershed:
            try:
                watershed_data = self._query_watershed_data_polygon(polygon_coords)
                watersheds.extend(watershed_data)
            except Exception as e:
                logger.warning(f"Failed to query watershed data for polygon: {e}")
        
        return WetlandHabitatInfo(
            location=centroid,
            wetlands=wetlands,
            riparian_areas=riparian_areas,
            watersheds=watersheds,
            has_wetland_data=len(wetlands) > 0,
            has_riparian_data=len(riparian_areas) > 0,
            has_watershed_data=len(watersheds) > 0
        )
    
    def _query_nwi_wetlands(self, longitude: float, latitude: float) -> List[WetlandInfo]:
        """Query USFWS National Wetlands Inventory data"""
        wetlands = []
        
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            # Query layer 0 (Wetlands layer)
            response = self.session.get(f"{self.nwi_url}/0/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                # Handle both prefixed and non-prefixed attribute names
                objectid = attributes.get('OBJECTID') or attributes.get('Wetlands.OBJECTID', '')
                wetland_type = attributes.get('WETLAND_TYPE') or attributes.get('Wetlands.WETLAND_TYPE', 'Unknown')
                attribute_code = attributes.get('ATTRIBUTE') or attributes.get('Wetlands.ATTRIBUTE', '')
                acres = attributes.get('ACRES') or attributes.get('Wetlands.ACRES')
                
                wetland = WetlandInfo(
                    wetland_id=str(objectid),
                    wetland_type=wetland_type,
                    wetland_code=attribute_code,
                    description=self._decode_nwi_attribute(attribute_code),
                    area_acres=acres,
                    location=(longitude, latitude),
                    attributes=attributes
                )
                wetlands.append(wetland)
                
        except Exception as e:
            logger.error(f"Failed to query NWI wetlands: {e}")
        
        return wetlands
    
    def _query_ribits_data(self, longitude: float, latitude: float) -> List[WetlandInfo]:
        """Query EPA RIBITS wetland data"""
        wetlands = []
        
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            response = self.session.get(f"{self.ribits_url}/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                wetland = WetlandInfo(
                    wetland_id=str(attributes.get('OBJECTID', '')),
                    wetland_type=attributes.get('TYPE', 'RIBITS'),
                    wetland_code=attributes.get('CODE', ''),
                    description=attributes.get('DESCRIPTION', ''),
                    area_acres=attributes.get('ACRES'),
                    location=(longitude, latitude),
                    attributes=attributes
                )
                wetlands.append(wetland)
                
        except Exception as e:
            logger.error(f"Failed to query RIBITS data: {e}")
        
        return wetlands
    
    def _query_riparian_data(self, longitude: float, latitude: float) -> List[RiparianInfo]:
        """Query USFWS riparian area data"""
        riparian_areas = []
        
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            response = self.session.get(f"{self.riparian_url}/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                riparian = RiparianInfo(
                    feature_id=str(attributes.get('OBJECTID', '')),
                    feature_type=attributes.get('RIPARIAN_TYPE', 'Riparian'),
                    description=attributes.get('DESCRIPTION', ''),
                    location=(longitude, latitude),
                    attributes=attributes
                )
                riparian_areas.append(riparian)
                
        except Exception as e:
            logger.error(f"Failed to query riparian data: {e}")
        
        return riparian_areas
    
    def _query_watershed_data(self, longitude: float, latitude: float) -> List[WatershedInfo]:
        """Query EPA watershed boundary data"""
        watersheds = []
        
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        # Query different HUC levels (HUC8, HUC10, HUC12)
        huc_layers = [
            (2, 'Subbasins (HUC8)'),
            (1, 'Watersheds (HUC10)'),
            (0, 'Subwatersheds (HUC12)')
        ]
        
        for layer_id, layer_name in huc_layers:
            try:
                layer_params = params.copy()
                layer_params['layers'] = f"visible:{layer_id}"
                
                response = self.session.get(f"{self.watershed_url}/query", params=layer_params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for feature in data.get('features', []):
                    attributes = feature.get('attributes', {})
                    
                    # Determine HUC level from layer
                    if 'HUC8' in layer_name:
                        huc_level = 8
                        huc_code = attributes.get('HUC8', '')
                    elif 'HUC10' in layer_name:
                        huc_level = 10
                        huc_code = attributes.get('HUC10', '')
                    else:  # HUC12
                        huc_level = 12
                        huc_code = attributes.get('HUC12', '')
                    
                    watershed = WatershedInfo(
                        huc_code=huc_code,
                        huc_level=huc_level,
                        name=attributes.get('NAME', ''),
                        area_sqkm=attributes.get('AREASQKM'),
                        location=(longitude, latitude),
                        attributes=attributes
                    )
                    watersheds.append(watershed)
                    
            except Exception as e:
                logger.warning(f"Failed to query {layer_name}: {e}")
        
        return watersheds
    
    def query_wetlands_by_bbox(self, min_lon: float, min_lat: float, 
                              max_lon: float, max_lat: float,
                              source: str = 'nwi') -> List[WetlandInfo]:
        """
        Query wetlands within a bounding box.
        
        Args:
            min_lon: Minimum longitude
            min_lat: Minimum latitude
            max_lon: Maximum longitude
            max_lat: Maximum latitude
            source: Data source ('nwi', 'ribits', or 'both')
            
        Returns:
            List of WetlandInfo objects
        """
        wetlands = []
        
        # Create bounding box geometry
        geometry = {
            'xmin': min_lon,
            'ymin': min_lat,
            'xmax': max_lon,
            'ymax': max_lat,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryEnvelope',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        if source in ['nwi', 'both']:
            try:
                # Query layer 0 (Wetlands layer)
                response = self.session.get(f"{self.nwi_url}/0/query", params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for feature in data.get('features', []):
                    attributes = feature.get('attributes', {})
                    
                    wetland = WetlandInfo(
                        wetland_id=str(attributes.get('OBJECTID', '')),
                        wetland_type=attributes.get('WETLAND_TYPE', 'Unknown'),
                        wetland_code=attributes.get('ATTRIBUTE', ''),
                        description=self._decode_nwi_attribute(attributes.get('ATTRIBUTE', '')),
                        area_acres=attributes.get('ACRES'),
                        attributes=attributes
                    )
                    wetlands.append(wetland)
                    
            except Exception as e:
                logger.error(f"Failed to query NWI wetlands by bbox: {e}")
        
        if source in ['ribits', 'both']:
            try:
                response = self.session.get(f"{self.ribits_url}/query", params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for feature in data.get('features', []):
                    attributes = feature.get('attributes', {})
                    
                    wetland = WetlandInfo(
                        wetland_id=str(attributes.get('OBJECTID', '')),
                        wetland_type=attributes.get('TYPE', 'RIBITS'),
                        wetland_code=attributes.get('CODE', ''),
                        description=attributes.get('DESCRIPTION', ''),
                        area_acres=attributes.get('ACRES'),
                        attributes=attributes
                    )
                    wetlands.append(wetland)
                    
            except Exception as e:
                logger.error(f"Failed to query RIBITS wetlands by bbox: {e}")
        
        return wetlands
    
    def _query_nwi_wetlands_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[WetlandInfo]:
        """Query USFWS National Wetlands Inventory data within a polygon"""
        wetlands = []
        
        # Create polygon geometry
        rings = [[list(coord) for coord in polygon_coords]]
        # Close the polygon if not already closed
        if rings[0][0] != rings[0][-1]:
            rings[0].append(rings[0][0])
        
        geometry = {
            'rings': rings,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            # Query layer 0 (Wetlands layer)
            response = self.session.get(f"{self.nwi_url}/0/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                wetland = WetlandInfo(
                    wetland_id=str(attributes.get('OBJECTID', '')),
                    wetland_type=attributes.get('WETLAND_TYPE', 'Unknown'),
                    wetland_code=attributes.get('ATTRIBUTE', ''),
                    description=self._decode_nwi_attribute(attributes.get('ATTRIBUTE', '')),
                    area_acres=attributes.get('ACRES'),
                    attributes=attributes
                )
                wetlands.append(wetland)
                
        except Exception as e:
            logger.error(f"Failed to query NWI wetlands for polygon: {e}")
        
        return wetlands
    
    def _query_ribits_data_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[WetlandInfo]:
        """Query EPA RIBITS wetland data within a polygon"""
        wetlands = []
        
        # Create polygon geometry
        rings = [[list(coord) for coord in polygon_coords]]
        # Close the polygon if not already closed
        if rings[0][0] != rings[0][-1]:
            rings[0].append(rings[0][0])
        
        geometry = {
            'rings': rings,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            response = self.session.get(f"{self.ribits_url}/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                wetland = WetlandInfo(
                    wetland_id=str(attributes.get('OBJECTID', '')),
                    wetland_type=attributes.get('TYPE', 'RIBITS'),
                    wetland_code=attributes.get('CODE', ''),
                    description=attributes.get('DESCRIPTION', ''),
                    area_acres=attributes.get('ACRES'),
                    attributes=attributes
                )
                wetlands.append(wetland)
                
        except Exception as e:
            logger.error(f"Failed to query RIBITS data for polygon: {e}")
        
        return wetlands
    
    def _query_riparian_data_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[RiparianInfo]:
        """Query USFWS riparian area data within a polygon"""
        riparian_areas = []
        
        # Create polygon geometry
        rings = [[list(coord) for coord in polygon_coords]]
        # Close the polygon if not already closed
        if rings[0][0] != rings[0][-1]:
            rings[0].append(rings[0][0])
        
        geometry = {
            'rings': rings,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        try:
            response = self.session.get(f"{self.riparian_url}/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get('features', []):
                attributes = feature.get('attributes', {})
                
                riparian = RiparianInfo(
                    feature_id=str(attributes.get('OBJECTID', '')),
                    feature_type=attributes.get('RIPARIAN_TYPE', 'Riparian'),
                    description=attributes.get('DESCRIPTION', ''),
                    attributes=attributes
                )
                riparian_areas.append(riparian)
                
        except Exception as e:
            logger.error(f"Failed to query riparian data for polygon: {e}")
        
        return riparian_areas
    
    def _query_watershed_data_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[WatershedInfo]:
        """Query EPA watershed boundary data within a polygon"""
        watersheds = []
        
        # Create polygon geometry
        rings = [[list(coord) for coord in polygon_coords]]
        # Close the polygon if not already closed
        if rings[0][0] != rings[0][-1]:
            rings[0].append(rings[0][0])
        
        geometry = {
            'rings': rings,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        # Query different HUC levels (HUC8, HUC10, HUC12)
        huc_layers = [
            (2, 'Subbasins (HUC8)'),
            (1, 'Watersheds (HUC10)'),
            (0, 'Subwatersheds (HUC12)')
        ]
        
        for layer_id, layer_name in huc_layers:
            try:
                layer_params = params.copy()
                layer_params['layers'] = f"visible:{layer_id}"
                
                response = self.session.get(f"{self.watershed_url}/query", params=layer_params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for feature in data.get('features', []):
                    attributes = feature.get('attributes', {})
                    
                    # Determine HUC level from layer
                    if 'HUC8' in layer_name:
                        huc_level = 8
                        huc_code = attributes.get('HUC8', '')
                    elif 'HUC10' in layer_name:
                        huc_level = 10
                        huc_code = attributes.get('HUC10', '')
                    else:  # HUC12
                        huc_level = 12
                        huc_code = attributes.get('HUC12', '')
                    
                    watershed = WatershedInfo(
                        huc_code=huc_code,
                        huc_level=huc_level,
                        name=attributes.get('NAME', ''),
                        area_sqkm=attributes.get('AREASQKM'),
                        attributes=attributes
                    )
                    watersheds.append(watershed)
                    
            except Exception as e:
                logger.warning(f"Failed to query {layer_name} for polygon: {e}")
        
        return watersheds
    
    def _decode_nwi_attribute(self, attribute_code: str) -> str:
        """
        Decode NWI attribute codes to human-readable descriptions.
        
        This is a simplified decoder - full NWI classification is complex.
        """
        if not attribute_code:
            return "Unknown wetland type"
        
        # Basic NWI code patterns
        descriptions = {
            'PEM': 'Palustrine Emergent Wetland',
            'PFO': 'Palustrine Forested Wetland',
            'PSS': 'Palustrine Scrub-Shrub Wetland',
            'PUB': 'Palustrine Unconsolidated Bottom',
            'PAB': 'Palustrine Aquatic Bed',
            'POW': 'Palustrine Open Water',
            'L1': 'Lacustrine Limnetic',
            'L2': 'Lacustrine Littoral',
            'R1': 'Riverine Tidal',
            'R2': 'Riverine Lower Perennial',
            'R3': 'Riverine Upper Perennial',
            'R4': 'Riverine Intermittent',
            'R5': 'Riverine Unknown Perennial',
            'E1': 'Estuarine Subtidal',
            'E2': 'Estuarine Intertidal',
            'M1': 'Marine Subtidal',
            'M2': 'Marine Intertidal'
        }
        
        # Try to match the beginning of the code
        for code, description in descriptions.items():
            if attribute_code.startswith(code):
                return description
        
        return f"Wetland ({attribute_code})"
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available wetland services"""
        services = {
            'nwi': {
                'name': 'USFWS National Wetlands Inventory',
                'url': self.nwi_url,
                'description': 'Primary source for wetland mapping data',
                'data_type': 'Wetland polygons with classification codes'
            },
            'nwi_raster': {
                'name': 'USFWS NWI Raster',
                'url': self.nwi_raster_url,
                'description': 'Rasterized wetland data for visualization',
                'data_type': 'Raster wetland data'
            },
            'ribits': {
                'name': 'EPA RIBITS',
                'url': self.ribits_url,
                'description': 'Regulatory wetland banking and mitigation data',
                'data_type': 'Wetland mitigation and banking sites'
            },
            'riparian': {
                'name': 'USFWS Riparian Data',
                'url': self.riparian_url,
                'description': 'Riparian area mapping',
                'data_type': 'Riparian zone polygons'
            },
            'watershed': {
                'name': 'EPA Watershed Boundaries',
                'url': self.watershed_url,
                'description': 'Hydrologic unit boundaries (HUC)',
                'data_type': 'Watershed boundary polygons'
            }
        }
        
        return services
    
    def generate_wetland_urls_for_location(self, longitude: float, latitude: float) -> Dict[str, str]:
        """Generate direct query URLs for a specific location"""
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json'
        }
        
        param_string = urlencode(params)
        
        urls = {
            'nwi_query': f"{self.nwi_url}/query?{param_string}",
            'ribits_query': f"{self.ribits_url}/query?{param_string}",
            'riparian_query': f"{self.riparian_url}/query?{param_string}",
            'watershed_query': f"{self.watershed_url}/query?{param_string}"
        }
        
        return urls
    
    def save_wetland_data(self, wetland_data: WetlandHabitatInfo, 
                         filename: str = None, 
                         use_output_manager: bool = True) -> bool:
        """
        Save wetland analysis data to file using output directory manager
        
        Args:
            wetland_data: WetlandHabitatInfo object with analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare data for serialization
            save_data = {
                'analysis_timestamp': datetime.now().isoformat(),
                'location': {
                    'longitude': wetland_data.location[0],
                    'latitude': wetland_data.location[1]
                },
                'summary': {
                    'has_wetland_data': wetland_data.has_wetland_data,
                    'has_riparian_data': wetland_data.has_riparian_data,
                    'has_watershed_data': wetland_data.has_watershed_data,
                    'total_wetlands': len(wetland_data.wetlands),
                    'total_riparian_areas': len(wetland_data.riparian_areas),
                    'total_watersheds': len(wetland_data.watersheds)
                },
                'wetlands': [
                    {
                        'wetland_id': w.wetland_id,
                        'wetland_type': w.wetland_type,
                        'wetland_code': w.wetland_code,
                        'description': w.description,
                        'area_acres': w.area_acres,
                        'location': w.location,
                        'attributes': w.attributes
                    } for w in wetland_data.wetlands
                ],
                'riparian_areas': [
                    {
                        'feature_id': r.feature_id,
                        'feature_type': r.feature_type,
                        'description': r.description,
                        'location': r.location,
                        'attributes': r.attributes
                    } for r in wetland_data.riparian_areas
                ],
                'watersheds': [
                    {
                        'huc_code': w.huc_code,
                        'huc_level': w.huc_level,
                        'name': w.name,
                        'area_sqkm': w.area_sqkm,
                        'location': w.location,
                        'attributes': w.attributes
                    } for w in wetland_data.watersheds
                ]
            }
            
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    lon, lat = wetland_data.location
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"wetland_analysis_{lon}_{lat}_{timestamp}.json"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "data")
                
                # Save the data
                with open(file_path, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
                
                logger.info(f"Wetland data saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    lon, lat = wetland_data.location
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"wetland_analysis_{lon}_{lat}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
                
                logger.info(f"Wetland data saved to: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save wetland data: {e}")
            return False
    
    def export_wetland_summary_report(self, wetland_data: WetlandHabitatInfo,
                                     filename: str = None,
                                     use_output_manager: bool = True) -> bool:
        """
        Export a human-readable summary report of wetland data
        
        Args:
            wetland_data: WetlandHabitatInfo object with analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Generate report content
            lon, lat = wetland_data.location
            report_lines = [
                "WETLAND AND HABITAT ANALYSIS REPORT",
                "=" * 50,
                f"Location: {lat:.6f}°N, {lon:.6f}°W",
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "SUMMARY",
                "-" * 20,
                f"Wetlands Found: {len(wetland_data.wetlands)}",
                f"Riparian Areas Found: {len(wetland_data.riparian_areas)}",
                f"Watershed Units Found: {len(wetland_data.watersheds)}",
                "",
            ]
            
            # Add wetland details
            if wetland_data.wetlands:
                report_lines.extend([
                    "WETLAND DETAILS",
                    "-" * 20
                ])
                for i, wetland in enumerate(wetland_data.wetlands, 1):
                    report_lines.extend([
                        f"{i}. {wetland.description}",
                        f"   Type: {wetland.wetland_type}",
                        f"   Code: {wetland.wetland_code}",
                        f"   Area: {wetland.area_acres or 'N/A'} acres",
                        ""
                    ])
            
            # Add riparian details
            if wetland_data.riparian_areas:
                report_lines.extend([
                    "RIPARIAN AREA DETAILS",
                    "-" * 20
                ])
                for i, riparian in enumerate(wetland_data.riparian_areas, 1):
                    report_lines.extend([
                        f"{i}. {riparian.description}",
                        f"   Type: {riparian.feature_type}",
                        ""
                    ])
            
            # Add watershed details
            if wetland_data.watersheds:
                report_lines.extend([
                    "WATERSHED DETAILS",
                    "-" * 20
                ])
                for i, watershed in enumerate(wetland_data.watersheds, 1):
                    report_lines.extend([
                        f"{i}. {watershed.name}",
                        f"   HUC{watershed.huc_level}: {watershed.huc_code}",
                        f"   Area: {watershed.area_sqkm or 'N/A'} sq km",
                        ""
                    ])
            
            # Save the report
            report_content = "\n".join(report_lines)
            
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"wetland_report_{lon}_{lat}_{timestamp}.txt"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "reports")
                
                # Save the report
                with open(file_path, 'w') as f:
                    f.write(report_content)
                
                logger.info(f"Wetland report saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"wetland_report_{lon}_{lat}_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(report_content)
                
                logger.info(f"Wetland report saved to: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to export wetland report: {e}")
            return False 