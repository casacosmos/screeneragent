#!/usr/bin/env python3
"""
Critical Habitat Map Generation Tools

LangChain-compatible tools for generating critical habitat maps using USFWS data.
"""

import json
import logging
import os
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool
import requests
import math
from datetime import datetime

from .generate_critical_habitat_map_pdf import CriticalHabitatMapGenerator
from .habitat_client import CriticalHabitatClient

# Import output directory manager
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from output_directory_manager import get_output_manager

logger = logging.getLogger(__name__)


def calculate_distance_miles(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula"""
    R = 3959  # Earth radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def _convert_coordinates_to_wgs84(x: float, y: float) -> tuple:
    """Convert coordinates from Web Mercator to WGS84 if needed"""
    if abs(x) > 180:  # Likely Web Mercator (EPSG:3857)
        lon = x / 20037508.34 * 180
        lat = y / 20037508.34 * 180
        lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
        return lon, lat
    else:
        return x, y


def _distance_to_polygon_boundary(px: float, py: float, rings: list) -> float:
    """Calculate the shortest distance from a point to a polygon boundary in miles"""
    
    min_distance = float('inf')
    
    for ring in rings:
        if not ring or len(ring) < 3:  # Skip invalid rings
            continue
            
        for i in range(len(ring)):
            # Get current and next point (wrap around for last point)
            current_point = ring[i]
            next_point = ring[(i + 1) % len(ring)]
            
            if len(current_point) >= 2 and len(next_point) >= 2:
                # Convert coordinates to WGS84
                x1, y1 = _convert_coordinates_to_wgs84(current_point[0], current_point[1])
                x2, y2 = _convert_coordinates_to_wgs84(next_point[0], next_point[1])
                
                # Calculate distance to both endpoints of the segment
                dist1 = calculate_distance_miles(px, py, x1, y1)
                dist2 = calculate_distance_miles(px, py, x2, y2)
                
                # Use minimum distance to either endpoint
                min_distance = min(min_distance, dist1, dist2)
    
    return min_distance if min_distance != float('inf') else 0.0


def _distance_to_linear_feature(px: float, py: float, paths: list) -> float:
    """Calculate the shortest distance from a point to a linear feature in miles"""
    
    min_distance = float('inf')
    
    for path in paths:
        if not path or len(path) < 2:  # Skip invalid paths
            continue
            
        for i in range(len(path) - 1):
            current_point = path[i]
            next_point = path[i + 1]
            
            if len(current_point) >= 2 and len(next_point) >= 2:
                # Convert coordinates to WGS84
                x1, y1 = _convert_coordinates_to_wgs84(current_point[0], current_point[1])
                x2, y2 = _convert_coordinates_to_wgs84(next_point[0], next_point[1])
                
                # Calculate distance to both endpoints of the segment
                dist1 = calculate_distance_miles(px, py, x1, y1)
                dist2 = calculate_distance_miles(px, py, x2, y2)
                
                # Use minimum distance to either endpoint
                min_distance = min(min_distance, dist1, dist2)
    
    return min_distance if min_distance != float('inf') else 0.0


def _distance_to_line_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate the shortest distance from a point to a line segment in miles"""
    
    # For simplicity and accuracy, calculate distance to both endpoints and return the minimum
    # This is a conservative approximation but avoids complex geometric calculations
    dist1 = calculate_distance_miles(px, py, x1, y1)
    dist2 = calculate_distance_miles(px, py, x2, y2)
    
    # For a more accurate calculation, we could implement proper point-to-line-segment distance
    # but for now, return the minimum distance to either endpoint
    return min(dist1, dist2)


def find_nearest_critical_habitat(longitude: float, latitude: float, search_radius_miles: float = 50) -> Dict[str, Any]:
    """Find the nearest critical habitat area to a given location"""
    
    habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
    session = requests.Session()
    session.headers.update({'User-Agent': 'CriticalHabitatFinder/1.0'})
    
    # Convert search radius to degrees (approximate)
    search_radius_degrees = search_radius_miles / 69.0
    
    # Create search envelope
    envelope = {
        "xmin": longitude - search_radius_degrees,
        "ymin": latitude - search_radius_degrees,
        "xmax": longitude + search_radius_degrees,
        "ymax": latitude + search_radius_degrees,
        "spatialReference": {"wkid": 4326}
    }
    
    nearest_habitat = None
    min_distance = float('inf')
    
    # Search in all habitat layers (0=Final Polygons, 1=Final Linear, 2=Proposed Polygons, 3=Proposed Linear)
    for layer_id in [0, 1, 2, 3]:
        try:
            params = {
                "geometry": json.dumps(envelope),
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",  # Get all fields to see what's available
                "returnGeometry": "true",
                "f": "json"
            }
            
            response = session.get(f"{habitat_service_url}/{layer_id}/query", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                for feature in data.get('features', []):
                    geometry = feature.get('geometry', {})
                    attributes = feature.get('attributes', {})
                    
                    # Calculate distance to nearest point on the habitat boundary using standardized methods
                    min_dist_to_feature = float('inf')
                    geometry_type = "Unknown"
                    
                    if 'rings' in geometry and geometry['rings']:
                        # Polygon feature - calculate distance to polygon boundary
                        geometry_type = "Polygon"
                        min_dist_to_feature = _distance_to_polygon_boundary(longitude, latitude, geometry['rings'])
                    
                    elif 'paths' in geometry and geometry['paths']:
                        # Linear feature - calculate distance to linear feature
                        geometry_type = "Linear"
                        min_dist_to_feature = _distance_to_linear_feature(longitude, latitude, geometry['paths'])
                    
                    if min_dist_to_feature < min_distance:
                        min_distance = min_dist_to_feature
                        
                        # Determine layer type based on layer_id
                        if layer_id in [0, 1]:
                            layer_type = "Final"
                        else:
                            layer_type = "Proposed"
                        
                        nearest_habitat = {
                            "distance_miles": min_dist_to_feature,
                            "species_common_name": attributes.get('comname', 'Unknown'),
                            "species_scientific_name": attributes.get('sciname', 'Unknown'),
                            "unit_name": attributes.get('unitname', 'Unknown'),
                            "status": attributes.get('status', 'Unknown'),
                            "layer_type": layer_type,
                            "geometry_type": geometry_type,
                            "layer_id": layer_id,
                            "objectid": attributes.get('OBJECTID'),
                            "spcode": attributes.get('spcode', 'Unknown')
                        }
                            
        except Exception as e:
            logger.warning(f"Error searching layer {layer_id}: {e}")
            continue
    
    return nearest_habitat


def _format_critical_habitat_analysis_response(
    habitat_analysis, 
    habitat_summary: Dict[str, Any], 
    nearest_habitat: Optional[Dict[str, Any]] = None,
    distance_to_habitat: Optional[float] = None,
    habitat_status: str = "unknown"
) -> Dict[str, Any]:
    """Format the critical habitat analysis response to match analyze_critical_habitat structure"""
    
    if habitat_summary["status"] == "error":
        return {
            "critical_habitat_analysis": {
                "status": "error",
                "location": habitat_summary["location"],
                "error": habitat_summary["message"]
            }
        }
    
    if habitat_summary["status"] == "no_habitat" and not nearest_habitat:
        return {
            "critical_habitat_analysis": {
                "status": "no_critical_habitat",
                "location": habitat_summary["location"],
                "message": "No critical habitat areas found at this location",
                "analysis_timestamp": habitat_summary["analysis_timestamp"],
                "regulatory_status": "No ESA critical habitat restrictions apply"
            }
        }
    
    # Handle case where location is within critical habitat
    if habitat_analysis.has_critical_habitat and habitat_analysis.critical_habitats:
        # Format species details for within-habitat case
        species_details = []
        species_groups = {}
        
        for habitat in habitat_analysis.critical_habitats:
            key = habitat.species_common_name
            if key not in species_groups:
                species_groups[key] = {
                    "common_name": habitat.species_common_name,
                    "scientific_name": habitat.species_scientific_name,
                    "habitat_units": set(),
                    "designation_types": set(),
                    "geometry_types": set()
                }
            
            species_groups[key]["habitat_units"].add(habitat.unit_name)
            species_groups[key]["designation_types"].add(habitat.habitat_type)
            species_groups[key]["geometry_types"].add(habitat.geometry_type)
        
        # Format grouped species
        for species_data in species_groups.values():
            species_details.append({
                "common_name": species_data["common_name"],
                "scientific_name": species_data["scientific_name"],
                "habitat_units": list(species_data["habitat_units"]),
                "designation_types": list(species_data["designation_types"]),
                "geometry_types": list(species_data["geometry_types"]),
                "unit_count": len(species_data["habitat_units"])
            })
        
        return {
            "critical_habitat_analysis": {
                "status": "critical_habitat_found",
                "location": habitat_summary["location"],
                "analysis_timestamp": habitat_summary["analysis_timestamp"],
                "summary": habitat_summary["summary"],
                "regulatory_implications": {
                    "esa_consultation_required": True,
                    "final_designations": habitat_summary["summary"]["final_designations"],
                    "proposed_designations": habitat_summary["summary"]["proposed_designations"],
                    "total_species_affected": habitat_summary["summary"]["unique_species"]
                },
                "affected_species": species_details,
                "recommendations": habitat_summary["recommendations"],
                "next_steps": [
                    "Contact USFWS for formal consultation",
                    "Review project impacts on critical habitat",
                    "Consider alternative locations if possible",
                    "Develop mitigation measures if needed"
                ]
            }
        }
    
    # Handle case where location is near critical habitat
    elif nearest_habitat and distance_to_habitat is not None:
        return {
            "critical_habitat_analysis": {
                "status": "near_critical_habitat",
                "location": habitat_summary["location"],
                "analysis_timestamp": habitat_summary["analysis_timestamp"],
                "distance_to_nearest_habitat_miles": distance_to_habitat,
                "nearest_habitat": {
                    "species_common_name": nearest_habitat["species_common_name"],
                    "species_scientific_name": nearest_habitat["species_scientific_name"],
                    "unit_name": nearest_habitat["unit_name"],
                    "status": nearest_habitat["status"],
                    "layer_type": nearest_habitat["layer_type"],
                    "geometry_type": nearest_habitat["geometry_type"],
                    "distance_miles": distance_to_habitat
                },
                "regulatory_implications": {
                    "esa_consultation_required": distance_to_habitat < 2.0,
                    "impact_assessment_recommended": distance_to_habitat < 5.0,
                    "distance_category": _get_distance_category(distance_to_habitat)
                },
                "recommendations": _generate_distance_based_recommendations(distance_to_habitat, nearest_habitat),
                "next_steps": [
                    "Assess potential indirect effects on nearby habitat",
                    "Consider project scale and regional impacts",
                    "Contact USFWS if consultation is recommended",
                    "Document analysis for environmental compliance"
                ]
            }
        }
    
    # Fallback case
    return {
        "critical_habitat_analysis": {
            "status": "no_critical_habitat",
            "location": habitat_summary["location"],
            "analysis_timestamp": habitat_summary["analysis_timestamp"],
            "message": "No critical habitat areas found within search radius",
            "regulatory_status": "No ESA critical habitat restrictions apply"
        }
    }


def _get_distance_category(distance_miles: float) -> str:
    """Get distance category for regulatory assessment"""
    if distance_miles < 0.5:
        return "Very Close (< 0.5 miles)"
    elif distance_miles < 2.0:
        return "Close (0.5-2 miles)"
    elif distance_miles < 5.0:
        return "Moderate Distance (2-5 miles)"
    else:
        return f"Distant (> 5 miles, {distance_miles:.1f} miles)"


def _generate_distance_based_recommendations(distance_miles: float, nearest_habitat: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on distance to critical habitat"""
    recommendations = []
    
    if distance_miles < 0.5:
        recommendations.extend([
            "⚠️  Very close to critical habitat - high potential for impacts",
            "📋 Formal ESA Section 7 consultation strongly recommended",
            "🔍 Conduct detailed impact assessment for indirect effects"
        ])
    elif distance_miles < 2.0:
        recommendations.extend([
            "📏 Close proximity to critical habitat",
            "🔍 Assess potential for indirect impacts on habitat and species",
            "💧 Consider water quality and connectivity effects"
        ])
    elif distance_miles < 5.0:
        recommendations.extend([
            "📍 Moderate distance to critical habitat",
            "🌍 Consider regional and cumulative impacts for large projects",
            "🔍 Assess watershed-level effects if applicable"
        ])
    else:
        recommendations.extend([
            "✅ Distant from critical habitat",
            "📋 Direct critical habitat impacts unlikely",
            "🔍 Focus on local environmental compliance requirements"
        ])
    
    # Add species-specific recommendations
    species = nearest_habitat["species_common_name"]
    if species != 'Unknown':
        recommendations.append(f"🦎 Nearest habitat protects {species}")
    
    return recommendations


def _save_critical_habitat_analysis_json(analysis_data: Dict[str, Any], location_name: str) -> Optional[str]:
    """Save critical habitat analysis data to JSON file in the correct project directory"""
    try:
        # Get output manager
        output_manager = get_output_manager()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"critical_habitat_analysis_{timestamp}.json"
        
        # Get file path in data subdirectory
        json_path = output_manager.get_file_path(filename, "data")
        
        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"💾 Critical habitat analysis data saved to: {json_path}")
        return json_path
        
    except Exception as e:
        logger.warning(f"Failed to save critical habitat analysis JSON: {e}")
        return None


@tool
def generate_adaptive_critical_habitat_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    base_map: str = "World_Imagery",
    include_proposed: bool = True,
    include_legend: bool = True,
    habitat_transparency: float = 0.8
) -> str:
    """
    Generate a critical habitat map with adaptive buffer based on habitat proximity.
    
    This tool first determines if the location lies within critical habitat. If not,
    it finds the nearest critical habitat area, calculates the distance, and uses
    that distance plus 1 mile as the map buffer to ensure the habitat is visible.
    
    The tool provides the same comprehensive analysis data as analyze_critical_habitat
    plus additional map generation and adaptive buffer capabilities.
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        location_name: Optional location name for the map title
        base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
        include_proposed: Whether to include proposed critical habitat designations
        include_legend: Whether to include a legend in the map
        habitat_transparency: Transparency of habitat layers (0.0-1.0)
        
    Returns:
        JSON string with comprehensive critical habitat analysis and map generation results
    """
    
    try:
        # Create map generator and habitat analysis client instances
        map_generator = CriticalHabitatMapGenerator()
        habitat_client = CriticalHabitatClient()
        
        # Perform detailed habitat analysis at the location
        print(f"🔍 Performing detailed critical habitat analysis...")
        habitat_analysis = habitat_client.analyze_location(
            longitude=longitude,
            latitude=latitude,
            include_proposed=include_proposed,
            buffer_meters=0  # Point analysis first
        )
        
        # Get habitat summary
        habitat_summary = habitat_client.get_habitat_summary(habitat_analysis)
        
        # Determine buffer strategy based on analysis results
        nearest_habitat = None
        distance_to_habitat = None
        
        if habitat_analysis.has_critical_habitat:
            # Location is within critical habitat - use small buffer
            buffer_miles = 3.5
            habitat_status = "within_critical_habitat"
            distance_to_habitat = 0.0
            print(f"✅ Location is within critical habitat - using standard buffer")
            print(f"   Found {habitat_analysis.habitat_count} habitat feature(s)")
        else:
            # Location is not within critical habitat - find nearest
            print(f"📏 Location not in critical habitat - finding nearest habitat...")
            nearest_habitat = find_nearest_critical_habitat(longitude, latitude, 50)
            
            if nearest_habitat:
                distance_to_habitat = nearest_habitat["distance_miles"]
                buffer_miles = distance_to_habitat + 13.0  # Add 1 mile buffer
                habitat_status = "near_critical_habitat"
                print(f"📍 Nearest habitat: {distance_to_habitat:.2f} miles away")
                print(f"🦎 Species: {nearest_habitat['species_common_name']}")
                print(f"🏷️  Unit: {nearest_habitat['unit_name']}")
                print(f"📊 Status: {nearest_habitat['status']} ({nearest_habitat['layer_type']})")
                print(f"🗺️  Using adaptive buffer: {buffer_miles:.2f} miles")
            else:
                # No habitat found within search radius
                buffer_miles = 3.0  # Default buffer for regional view
                distance_to_habitat = None
                habitat_status = "no_nearby_habitat"
                print(f"❌ No critical habitat found within 50 miles - using regional buffer")
        
        # Generate the map with calculated buffer
        if location_name is None:
            location_name = f"Critical_Habitat_Analysis_{latitude:.4f}_{longitude:.4f}"
        
        pdf_path = map_generator.generate_critical_habitat_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            include_proposed=include_proposed,
            include_legend=include_legend,
            habitat_transparency=habitat_transparency
        )
        
        if pdf_path:
            # Format critical habitat analysis data using the same structure as analyze_critical_habitat
            critical_habitat_data = _format_critical_habitat_analysis_response(
                habitat_analysis=habitat_analysis,
                habitat_summary=habitat_summary,
                nearest_habitat=nearest_habitat,
                distance_to_habitat=distance_to_habitat,
                habitat_status=habitat_status
            )
            
            # Save critical habitat analysis data to JSON file
            json_path = _save_critical_habitat_analysis_json(critical_habitat_data, location_name)
            
            # Prepare comprehensive response
            response = {
                "status": "success",
                "message": "Adaptive critical habitat map generated successfully with comprehensive analysis",
                "pdf_path": pdf_path,
                "json_data_path": json_path,
                "location": {
                    "longitude": longitude,
                    "latitude": latitude,
                    "location_name": location_name
                },
                "adaptive_map_details": {
                    "habitat_status": habitat_status,
                    "distance_to_nearest_habitat_miles": distance_to_habitat,
                    "adaptive_buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "include_proposed": include_proposed,
                    "include_legend": include_legend,
                    "habitat_transparency": habitat_transparency
                },
                # Include the same critical habitat analysis structure as analyze_critical_habitat
                **critical_habitat_data
            }
            
            return json.dumps(response, indent=2)
        else:
            error_response = {
                "status": "error",
                "message": "Failed to generate adaptive critical habitat map",
                "location": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "error": "Map generation service failed"
            }
            return json.dumps(error_response, indent=2)
            
    except Exception as e:
        logger.error(f"Error generating adaptive critical habitat map: {e}")
        error_response = {
            "status": "error",
            "message": "Error generating adaptive critical habitat map",
            "location": {
                "longitude": longitude,
                "latitude": latitude
            },
            "error": str(e)
        }
        return json.dumps(error_response, indent=2)


@tool
def generate_critical_habitat_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    buffer_miles: float = 0.5,
    base_map: str = "World_Imagery",
    include_proposed: bool = True,
    include_legend: bool = True,
    habitat_transparency: float = 0.8
) -> str:
    """
    Generate a professional PDF map showing critical habitat areas designated for 
    threatened and endangered species under the Endangered Species Act.
    
    This tool creates high-quality maps that include:
    - Critical habitat polygons and linear features
    - Final and proposed habitat designations
    - Base map imagery or topographic data
    - Location markers and scale bars
    - Professional legend and attribution
    
    Use this tool when you need to:
    - Create maps for ESA compliance documentation
    - Visualize critical habitat around project sites
    - Generate maps for environmental assessments
    - Produce professional habitat maps for reports
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        location_name: Optional location name for the map title
        buffer_miles: Buffer radius around the point in miles (default 0.5)
        base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
        include_proposed: Whether to include proposed critical habitat designations
        include_legend: Whether to include a legend in the map
        habitat_transparency: Transparency of habitat layers (0.0-1.0)
        
    Returns:
        JSON string with map generation results
    """
    
    try:
        # Create map generator instance
        map_generator = CriticalHabitatMapGenerator()
        
        # Generate the map
        pdf_path = map_generator.generate_critical_habitat_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            include_proposed=include_proposed,
            include_legend=include_legend,
            habitat_transparency=habitat_transparency
        )
        
        if pdf_path:
            # Check if critical habitat was found
            habitats_found = map_generator._check_critical_habitat_in_area(
                longitude, latitude, buffer_miles, include_proposed
            )
            
            response = {
                "status": "success",
                "message": "Critical habitat map generated successfully",
                "pdf_path": pdf_path,
                "location": {
                    "longitude": longitude,
                    "latitude": latitude,
                    "location_name": location_name or f"Location at {latitude:.4f}, {longitude:.4f}"
                },
                "map_details": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "include_proposed": include_proposed,
                    "include_legend": include_legend,
                    "habitat_transparency": habitat_transparency,
                    "critical_habitat_found": habitats_found > 0,
                    "habitat_features_count": habitats_found
                },
                "recommendations": _generate_map_recommendations(habitats_found, include_proposed)
            }
            
            return json.dumps(response, indent=2)
        else:
            error_response = {
                "status": "error",
                "message": "Failed to generate critical habitat map",
                "location": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "error": "Map generation service failed"
            }
            return json.dumps(error_response, indent=2)
            
    except Exception as e:
        logger.error(f"Error generating critical habitat map: {e}")
        error_response = {
            "status": "error",
            "message": "Error generating critical habitat map",
            "location": {
                "longitude": longitude,
                "latitude": latitude
            },
            "error": str(e)
        }
        return json.dumps(error_response, indent=2)


def _generate_map_recommendations(habitats_found: int, include_proposed: bool) -> list:
    """Generate recommendations based on map results"""
    recommendations = []
    
    if habitats_found > 0:
        recommendations.append(
            "⚠️  Critical habitat areas are present at this location. "
            "Review the map for specific habitat boundaries and affected species."
        )
        recommendations.append(
            "📋 Use this map for ESA Section 7 consultation documentation "
            "and project planning purposes."
        )
        if include_proposed:
            recommendations.append(
                "🔍 Map includes both final and proposed critical habitat. "
                "Monitor proposed designations for potential finalization."
            )
        recommendations.append(
            "📞 Contact USFWS for detailed project consultation if activities "
            "may affect critical habitat areas shown on the map."
        )
    else:
        recommendations.append(
            "✅ No critical habitat areas found at this location within the specified buffer."
        )
        recommendations.append(
            "📋 This map can be used to document the absence of critical habitat "
            "for environmental compliance purposes."
        )
        recommendations.append(
            "🔍 Consider expanding the search radius if the project area is larger "
            "or if nearby critical habitat may be relevant."
        )
    
    return recommendations


def _get_detailed_habitat_info(nearest_habitat: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about a specific critical habitat"""
    
    try:
        habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
        session = requests.Session()
        session.headers.update({'User-Agent': 'CriticalHabitatAnalyzer/1.0'})
        
        # Determine layer based on designation type
        layer_id = 0 if nearest_habitat['layer_type'] == 'Final' else 2
        
        # Query for detailed attributes
        params = {
            "where": f"OBJECTID = {nearest_habitat['objectid']}",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json"
        }
        
        response = session.get(f"{habitat_service_url}/{layer_id}/query", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            if features:
                feature = features[0]
                attributes = feature.get('attributes', {})
                geometry = feature.get('geometry', {})
                
                # Calculate habitat area if polygon
                area_info = {}
                if 'rings' in geometry:
                    # Simplified area calculation (not geodesically accurate)
                    total_points = sum(len(ring) for ring in geometry['rings'])
                    area_info = {
                        "geometry_type": "Polygon",
                        "ring_count": len(geometry['rings']),
                        "total_vertices": total_points,
                        "note": "Complex polygon geometry - area calculation requires specialized tools"
                    }
                elif 'paths' in geometry:
                    total_points = sum(len(path) for path in geometry['paths'])
                    area_info = {
                        "geometry_type": "Polyline",
                        "path_count": len(geometry['paths']),
                        "total_vertices": total_points,
                        "note": "Linear habitat feature (e.g., stream, corridor)"
                    }
                
                return {
                    "habitat_attributes": {
                        "common_name": attributes.get('comname', 'Unknown'),
                        "scientific_name": attributes.get('sciname', 'Unknown'),
                        "unit_name": attributes.get('unitname', 'Unknown'),
                        "status": attributes.get('status', 'Unknown'),
                        "lead_office": attributes.get('leadoffice', 'Unknown'),
                        "species_code": attributes.get('spcode', 'Unknown'),
                        "federal_register": attributes.get('fedreg', 'Unknown'),
                        "publication_date": attributes.get('pubdate', 'Unknown'),
                        "effective_date": attributes.get('effectdate', 'Unknown'),
                        "listing_status": attributes.get('listing_status', 'Unknown')
                    },
                    "geometry_details": area_info,
                    "data_source": "USFWS Critical Habitat Service",
                    "layer_id": layer_id,
                    "feature_objectid": nearest_habitat['objectid']
                }
        
        # Fallback if detailed query fails
        return {
            "habitat_attributes": {
                "common_name": nearest_habitat['species_common_name'],
                "scientific_name": nearest_habitat['species_scientific_name'],
                "unit_name": nearest_habitat['unit_name'],
                "status": nearest_habitat['status']
            },
            "note": "Limited details available - detailed query failed",
            "data_source": "USFWS Critical Habitat Service (basic)"
        }
        
    except Exception as e:
        logger.warning(f"Error getting detailed habitat info: {e}")
        return {
            "habitat_attributes": {
                "common_name": nearest_habitat['species_common_name'],
                "scientific_name": nearest_habitat['species_scientific_name'],
                "unit_name": nearest_habitat['unit_name'],
                "status": nearest_habitat['status']
            },
            "note": f"Error retrieving detailed information: {str(e)}",
            "data_source": "USFWS Critical Habitat Service (error fallback)"
        }


def _assess_distance_based_implications(distance_miles: float) -> Dict[str, Any]:
    """Assess regulatory implications based on distance to critical habitat"""
    
    implications = {
        "distance_category": "",
        "esa_consultation_likely": False,
        "impact_assessment_recommended": False,
        "mitigation_considerations": [],
        "consultation_guidance": ""
    }
    
    if distance_miles < 0.5:
        implications.update({
            "distance_category": "Very Close (< 0.5 miles)",
            "esa_consultation_likely": True,
            "impact_assessment_recommended": True,
            "mitigation_considerations": [
                "Direct impacts possible despite being outside habitat boundary",
                "Noise, lighting, and construction impacts may affect habitat",
                "Water quality and hydrology impacts should be assessed",
                "Consider cumulative effects with other nearby projects"
            ],
            "consultation_guidance": "Formal ESA consultation strongly recommended due to proximity"
        })
    elif distance_miles < 2.0:
        implications.update({
            "distance_category": "Close (0.5-2 miles)",
            "esa_consultation_likely": True,
            "impact_assessment_recommended": True,
            "mitigation_considerations": [
                "Indirect impacts possible through habitat connectivity",
                "Water quality impacts may extend to critical habitat",
                "Consider species movement corridors and foraging areas",
                "Assess potential for habitat fragmentation"
            ],
            "consultation_guidance": "ESA consultation recommended - assess indirect effects"
        })
    elif distance_miles < 5.0:
        implications.update({
            "distance_category": "Moderate Distance (2-5 miles)",
            "esa_consultation_likely": False,
            "impact_assessment_recommended": True,
            "mitigation_considerations": [
                "Watershed-level impacts should be considered",
                "Large-scale projects may have regional effects",
                "Species with large home ranges may be affected",
                "Consider cumulative regional impacts"
            ],
            "consultation_guidance": "Consultation may be needed for large projects with regional impacts"
        })
    else:
        implications.update({
            "distance_category": f"Distant (> 5 miles, {distance_miles:.1f} miles)",
            "esa_consultation_likely": False,
            "impact_assessment_recommended": False,
            "mitigation_considerations": [
                "Direct impacts unlikely at this distance",
                "Consider only for very large regional projects",
                "Focus on local environmental compliance"
            ],
            "consultation_guidance": "ESA consultation unlikely unless project has regional scope"
        })
    
    return implications


def _generate_nearest_habitat_recommendations(nearest_habitat: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on nearest habitat analysis"""
    
    recommendations = []
    distance = nearest_habitat['distance_miles']
    species = nearest_habitat['species_common_name']
    designation_type = nearest_habitat['layer_type']
    
    # Distance-based recommendations
    if distance < 0.5:
        recommendations.extend([
            f"⚠️  Very close to critical habitat ({distance:.2f} miles) - high potential for impacts",
            "📋 Formal ESA Section 7 consultation strongly recommended",
            "🔍 Conduct detailed impact assessment for indirect effects"
        ])
    elif distance < 2.0:
        recommendations.extend([
            f"📏 Close proximity to critical habitat ({distance:.2f} miles)",
            "🔍 Assess potential for indirect impacts on habitat and species",
            "💧 Consider water quality and connectivity effects"
        ])
    elif distance < 5.0:
        recommendations.extend([
            f"📍 Moderate distance to critical habitat ({distance:.2f} miles)",
            "🌍 Consider regional and cumulative impacts for large projects",
            "🔍 Assess watershed-level effects if applicable"
        ])
    else:
        recommendations.extend([
            f"✅ Distant from critical habitat ({distance:.2f} miles)",
            "📋 Direct critical habitat impacts unlikely",
            "🔍 Focus on local environmental compliance requirements"
        ])
    
    # Species-specific recommendations
    if species != 'Unknown':
        recommendations.append(f"🦎 Nearest habitat protects {species}")
        
        # Add species-specific guidance based on common species
        if 'crane' in species.lower():
            recommendations.append("🦅 Whooping cranes are sensitive to noise and human disturbance")
        elif 'fish' in species.lower() or 'salmon' in species.lower():
            recommendations.append("🐟 Aquatic species habitat - assess water quality impacts")
        elif 'turtle' in species.lower():
            recommendations.append("🐢 Sea turtle habitat - consider lighting and coastal impacts")
        elif 'bird' in species.lower():
            recommendations.append("🐦 Bird habitat - assess noise, lighting, and flight path impacts")
    
    # Designation type recommendations
    if designation_type == 'Proposed':
        recommendations.extend([
            "📊 Nearest habitat is proposed (not yet final)",
            "⏰ Monitor for finalization of proposed designation",
            "📋 Consider potential future regulatory requirements"
        ])
    else:
        recommendations.append("📊 Nearest habitat is final designation with full regulatory protection")
    
    # General recommendations
    recommendations.extend([
        "📞 Contact USFWS for project-specific guidance if needed",
        "🗺️  Use adaptive habitat mapping tool for visual context",
        "📋 Document analysis for environmental compliance records"
    ])
    
    return recommendations


# Tool list for easy import
critical_habitat_map_tools = [
    generate_critical_habitat_map,
    generate_adaptive_critical_habitat_map
] 