#!/usr/bin/env python3
"""
Critical Habitat Information Client

This module provides comprehensive access to critical habitat data from USFWS services.
It can determine if a location intersects with critical habitat areas and provide
detailed information about threatened and endangered species habitats.
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CriticalHabitatInfo:
    """Information about a critical habitat area"""
    species_common_name: str
    species_scientific_name: str
    unit_name: str
    status: str
    habitat_type: str  # 'Final' or 'Proposed'
    geometry_type: str  # 'Polygon' or 'Linear'
    designation_date: Optional[str] = None
    area_acres: Optional[float] = None
    description: Optional[str] = None

@dataclass
class HabitatAnalysisResult:
    """Result of habitat analysis for a location"""
    location: Tuple[float, float]  # (longitude, latitude)
    has_critical_habitat: bool
    habitat_count: int
    critical_habitats: List[CriticalHabitatInfo]
    analysis_timestamp: str
    query_success: bool
    error_message: Optional[str] = None

class CriticalHabitatClient:
    """Client for accessing USFWS Critical Habitat services"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CriticalHabitatClient/1.0'
        })
        
        # Primary USFWS Critical Habitat service
        self.base_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
        
        # Layer definitions based on exploration
        self.layers = {
            'final_polygon': {
                'id': 0,
                'name': 'Critical Habitat - Polygon Features - Final',
                'geometry_type': 'Polygon',
                'habitat_type': 'Final'
            },
            'final_linear': {
                'id': 1,
                'name': 'Critical Habitat - Linear Features - Final',
                'geometry_type': 'Linear',
                'habitat_type': 'Final'
            },
            'proposed_polygon': {
                'id': 2,
                'name': 'Critical Habitat - Polygon Features - Proposed',
                'geometry_type': 'Polygon',
                'habitat_type': 'Proposed'
            },
            'proposed_linear': {
                'id': 3,
                'name': 'Critical Habitat - Linear Features - Proposed',
                'geometry_type': 'Linear',
                'habitat_type': 'Proposed'
            }
        }
        
        # Key field mappings
        self.field_mappings = {
            'species_common': 'comname',
            'species_scientific': 'sciname',
            'unit_name': 'unitname',
            'status': 'status',
            'designation_date': 'designationdate',
            'area_acres': 'area_acres'
        }
    
    def analyze_location(self, longitude: float, latitude: float, 
                        include_proposed: bool = True,
                        buffer_meters: float = 0) -> HabitatAnalysisResult:
        """
        Analyze a location for critical habitat intersections
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            include_proposed: Whether to include proposed critical habitats
            buffer_meters: Buffer distance around point in meters
            
        Returns:
            HabitatAnalysisResult with analysis results
        """
        logger.info(f"Analyzing critical habitat for location: {longitude}, {latitude}")
        
        try:
            # Determine which layers to query
            layers_to_query = ['final_polygon', 'final_linear']
            if include_proposed:
                layers_to_query.extend(['proposed_polygon', 'proposed_linear'])
            
            all_habitats = []
            
            # Query each layer
            for layer_key in layers_to_query:
                layer_info = self.layers[layer_key]
                habitats = self._query_layer_for_location(
                    layer_info, longitude, latitude, buffer_meters
                )
                all_habitats.extend(habitats)
            
            # Create result
            result = HabitatAnalysisResult(
                location=(longitude, latitude),
                has_critical_habitat=len(all_habitats) > 0,
                habitat_count=len(all_habitats),
                critical_habitats=all_habitats,
                analysis_timestamp=datetime.now().isoformat(),
                query_success=True
            )
            
            logger.info(f"Found {len(all_habitats)} critical habitat areas at location")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing location: {e}")
            return HabitatAnalysisResult(
                location=(longitude, latitude),
                has_critical_habitat=False,
                habitat_count=0,
                critical_habitats=[],
                analysis_timestamp=datetime.now().isoformat(),
                query_success=False,
                error_message=str(e)
            )
    
    def _query_layer_for_location(self, layer_info: Dict, longitude: float, 
                                 latitude: float, buffer_meters: float = 0) -> List[CriticalHabitatInfo]:
        """Query a specific layer for habitat information at a location"""
        
        try:
            # Create geometry for query
            if buffer_meters > 0:
                # Create buffer geometry (simplified circle approximation)
                geometry = {
                    "rings": [self._create_buffer_ring(longitude, latitude, buffer_meters)],
                    "spatialReference": {"wkid": 4326}
                }
                geometry_type = "esriGeometryPolygon"
            else:
                geometry = {
                    "x": longitude,
                    "y": latitude,
                    "spatialReference": {"wkid": 4326}
                }
                geometry_type = "esriGeometryPoint"
            
            # Query parameters
            query_params = {
                "geometry": json.dumps(geometry),
                "geometryType": geometry_type,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            # Execute query
            layer_id = layer_info['id']
            response = self.session.get(
                f"{self.base_url}/{layer_id}/query",
                params=query_params,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                logger.warning(f"Query error for layer {layer_id}: {result['error']}")
                return []
            
            # Process features
            features = result.get('features', [])
            habitats = []
            
            for feature in features:
                habitat_info = self._process_habitat_feature(feature, layer_info)
                if habitat_info:
                    habitats.append(habitat_info)
            
            logger.debug(f"Layer {layer_id} returned {len(habitats)} habitat areas")
            return habitats
            
        except Exception as e:
            logger.error(f"Error querying layer {layer_info.get('name', 'Unknown')}: {e}")
            return []
    
    def _process_habitat_feature(self, feature: Dict, layer_info: Dict) -> Optional[CriticalHabitatInfo]:
        """Process a habitat feature into a CriticalHabitatInfo object"""
        
        try:
            attributes = feature.get('attributes', {})
            
            # Extract key information
            species_common = attributes.get(self.field_mappings['species_common'], 'Unknown')
            species_scientific = attributes.get(self.field_mappings['species_scientific'], 'Unknown')
            unit_name = attributes.get(self.field_mappings['unit_name'], 'Unknown')
            status = attributes.get(self.field_mappings['status'], 'Unknown')
            
            # Handle missing or null values
            if not species_common or species_common in ['', 'null', None]:
                species_common = 'Unknown Species'
            if not species_scientific or species_scientific in ['', 'null', None]:
                species_scientific = 'Unknown'
            if not unit_name or unit_name in ['', 'null', None]:
                unit_name = 'Unknown Unit'
            if not status or status in ['', 'null', None]:
                status = 'Unknown'
            
            # Create habitat info
            habitat_info = CriticalHabitatInfo(
                species_common_name=species_common,
                species_scientific_name=species_scientific,
                unit_name=unit_name,
                status=status,
                habitat_type=layer_info['habitat_type'],
                geometry_type=layer_info['geometry_type'],
                designation_date=attributes.get(self.field_mappings.get('designation_date')),
                area_acres=attributes.get(self.field_mappings.get('area_acres'))
            )
            
            return habitat_info
            
        except Exception as e:
            logger.error(f"Error processing habitat feature: {e}")
            return None
    
    def _create_buffer_ring(self, longitude: float, latitude: float, 
                           buffer_meters: float) -> List[List[float]]:
        """Create a simple circular buffer ring around a point"""
        
        # Simple approximation: convert meters to degrees
        # This is approximate and works better near the equator
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * abs(math.cos(math.radians(latitude)))
        
        buffer_deg_lat = buffer_meters / meters_per_degree_lat
        buffer_deg_lon = buffer_meters / meters_per_degree_lon
        
        # Create a simple square buffer (could be improved to circle)
        ring = [
            [longitude - buffer_deg_lon, latitude - buffer_deg_lat],
            [longitude + buffer_deg_lon, latitude - buffer_deg_lat],
            [longitude + buffer_deg_lon, latitude + buffer_deg_lat],
            [longitude - buffer_deg_lon, latitude + buffer_deg_lat],
            [longitude - buffer_deg_lon, latitude - buffer_deg_lat]  # Close the ring
        ]
        
        return ring
    
    def get_species_habitats(self, species_name: str, 
                           search_type: str = 'common') -> List[CriticalHabitatInfo]:
        """
        Get all critical habitat areas for a specific species
        
        Args:
            species_name: Name of the species to search for
            search_type: 'common' for common name, 'scientific' for scientific name
            
        Returns:
            List of CriticalHabitatInfo objects for the species
        """
        logger.info(f"Searching for habitats of species: {species_name}")
        
        try:
            # Determine field to search
            if search_type == 'common':
                search_field = self.field_mappings['species_common']
            else:
                search_field = self.field_mappings['species_scientific']
            
            all_habitats = []
            
            # Query all layers
            for layer_key, layer_info in self.layers.items():
                habitats = self._query_layer_for_species(layer_info, search_field, species_name)
                all_habitats.extend(habitats)
            
            logger.info(f"Found {len(all_habitats)} habitat areas for {species_name}")
            return all_habitats
            
        except Exception as e:
            logger.error(f"Error searching for species habitats: {e}")
            return []
    
    def _query_layer_for_species(self, layer_info: Dict, search_field: str, 
                                species_name: str) -> List[CriticalHabitatInfo]:
        """Query a layer for a specific species"""
        
        try:
            # Create where clause for species search
            where_clause = f"{search_field} LIKE '%{species_name}%'"
            
            query_params = {
                "where": where_clause,
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            layer_id = layer_info['id']
            response = self.session.get(
                f"{self.base_url}/{layer_id}/query",
                params=query_params,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                logger.warning(f"Species query error for layer {layer_id}: {result['error']}")
                return []
            
            # Process features
            features = result.get('features', [])
            habitats = []
            
            for feature in features:
                habitat_info = self._process_habitat_feature(feature, layer_info)
                if habitat_info:
                    habitats.append(habitat_info)
            
            return habitats
            
        except Exception as e:
            logger.error(f"Error querying species in layer {layer_info.get('name', 'Unknown')}: {e}")
            return []
    
    def get_habitat_summary(self, result: HabitatAnalysisResult) -> Dict[str, Any]:
        """Generate a summary of habitat analysis results"""
        
        if not result.query_success:
            return {
                "status": "error",
                "message": result.error_message,
                "location": result.location
            }
        
        if not result.has_critical_habitat:
            return {
                "status": "no_habitat",
                "message": "No critical habitat areas found at this location",
                "location": result.location,
                "analysis_timestamp": result.analysis_timestamp
            }
        
        # Analyze habitats
        species_count = len(set(h.species_common_name for h in result.critical_habitats))
        final_count = len([h for h in result.critical_habitats if h.habitat_type == 'Final'])
        proposed_count = len([h for h in result.critical_habitats if h.habitat_type == 'Proposed'])
        
        species_list = []
        for habitat in result.critical_habitats:
            species_info = {
                "common_name": habitat.species_common_name,
                "scientific_name": habitat.species_scientific_name,
                "unit_name": habitat.unit_name,
                "status": habitat.status,
                "habitat_type": habitat.habitat_type,
                "geometry_type": habitat.geometry_type
            }
            species_list.append(species_info)
        
        return {
            "status": "habitat_found",
            "location": result.location,
            "analysis_timestamp": result.analysis_timestamp,
            "summary": {
                "total_habitat_areas": result.habitat_count,
                "unique_species": species_count,
                "final_designations": final_count,
                "proposed_designations": proposed_count
            },
            "species_details": species_list,
            "recommendations": self._generate_recommendations(result)
        }
    
    def _generate_recommendations(self, result: HabitatAnalysisResult) -> List[str]:
        """Generate recommendations based on habitat analysis"""
        
        recommendations = []
        
        if result.has_critical_habitat:
            recommendations.append(
                "⚠️  This location intersects with designated critical habitat areas. "
                "Any development or activities may require consultation with USFWS."
            )
            
            final_habitats = [h for h in result.critical_habitats if h.habitat_type == 'Final']
            if final_habitats:
                recommendations.append(
                    f"🏛️  {len(final_habitats)} final critical habitat designation(s) apply to this location. "
                    "These have full regulatory protection under the Endangered Species Act."
                )
            
            proposed_habitats = [h for h in result.critical_habitats if h.habitat_type == 'Proposed']
            if proposed_habitats:
                recommendations.append(
                    f"📋 {len(proposed_habitats)} proposed critical habitat designation(s) may apply. "
                    "Monitor for final designation status."
                )
            
            species_count = len(set(h.species_common_name for h in result.critical_habitats))
            if species_count > 1:
                recommendations.append(
                    f"🌿 Multiple species ({species_count}) have critical habitat at this location. "
                    "Consider cumulative impacts in planning."
                )
            
            recommendations.append(
                "📞 Contact USFWS for project consultation and compliance guidance."
            )
        
        return recommendations

# Import math for buffer calculations
import math 