#!/usr/bin/env python3
"""
Nonattainment Areas Information Client

This module provides comprehensive access to EPA nonattainment areas data from USFWS services.
It can determine if a location intersects with nonattainment areas and provide
detailed information about air quality standards violations.
"""

import requests
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NonAttainmentAreaInfo:
    """Information about a nonattainment area"""
    pollutant_name: str
    area_name: str
    state_name: str
    state_abbreviation: str
    epa_region: int
    current_status: str  # 'Nonattainment' or 'Maintenance'
    classification: str
    designation_effective_date: Optional[str] = None
    statutory_attainment_date: Optional[str] = None
    design_value: Optional[float] = None
    design_value_units: Optional[str] = None
    meets_naaqs: Optional[str] = None
    population_2020: Optional[float] = None
    composite_id: Optional[str] = None

@dataclass
class NonAttainmentAnalysisResult:
    """Result of nonattainment analysis for a location"""
    location: Tuple[float, float]  # (longitude, latitude)
    has_nonattainment_areas: bool
    area_count: int
    nonattainment_areas: List[NonAttainmentAreaInfo]
    analysis_timestamp: str
    query_success: bool
    error_message: Optional[str] = None

class NonAttainmentAreasClient:
    """Client for accessing EPA Nonattainment Areas services"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NonAttainmentAreasClient/1.0'
        })
        
        # Primary EPA Nonattainment Areas service
        self.base_url = "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer"
        
        # Layer definitions based on EPA service exploration
        self.layers = {
            'ozone_8hr_1997': {
                'id': 0,
                'name': 'Ozone 8-hr (1997 standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (1997)',
                'status': 'revoked'
            },
            'ozone_8hr_2008': {
                'id': 1,
                'name': 'Ozone 8-hr (2008 standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (2008)',
                'status': 'active'
            },
            'ozone_8hr_2015': {
                'id': 2,
                'name': 'Ozone 8-hr (2015 Standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (2015)',
                'status': 'active'
            },
            'lead_2008': {
                'id': 3,
                'name': 'Lead (2008 standard)',
                'pollutant': 'Lead',
                'standard': '2008',
                'status': 'active'
            },
            'so2_1hr_2010': {
                'id': 4,
                'name': 'SO2 1-hr (2010 standard)',
                'pollutant': 'Sulfur Dioxide',
                'standard': '1-hour (2010)',
                'status': 'active'
            },
            'pm25_24hr_2006': {
                'id': 5,
                'name': 'PM2.5 24hr (2006 standard)',
                'pollutant': 'PM2.5',
                'standard': '24-hour (2006)',
                'status': 'active'
            },
            'pm25_annual_1997': {
                'id': 6,
                'name': 'PM2.5 Annual (1997 standard)',
                'pollutant': 'PM2.5',
                'standard': 'Annual (1997)',
                'status': 'active'
            },
            'pm25_annual_2012': {
                'id': 7,
                'name': 'PM2.5 Annual (2012 standard)',
                'pollutant': 'PM2.5',
                'standard': 'Annual (2012)',
                'status': 'active'
            },
            'pm10_1987': {
                'id': 8,
                'name': 'PM10 (1987 standard)',
                'pollutant': 'PM10',
                'standard': '1987',
                'status': 'active'
            },
            'co_1971': {
                'id': 9,
                'name': 'CO (1971 Standard)',
                'pollutant': 'Carbon Monoxide',
                'standard': '1971',
                'status': 'active'
            },
            'ozone_1hr_1979': {
                'id': 10,
                'name': 'Ozone 1-hr (1979 standard-revoked)',
                'pollutant': 'Ozone',
                'standard': '1-hour (1979)',
                'status': 'revoked'
            },
            'no2_1971': {
                'id': 11,
                'name': 'NO2 (1971 Standard)',
                'pollutant': 'Nitrogen Dioxide',
                'standard': '1971',
                'status': 'active'
            }
        }
        
        # Key field mappings
        self.field_mappings = {
            'pollutant_name': 'pollutant_name',
            'area_name': 'area_name',
            'state_name': 'state_name',
            'state_abbreviation': 'state_abbreviation',
            'epa_region': 'epa_region',
            'current_status': 'current_status',
            'classification': 'classification',
            'designation_effective_date': 'designation_effective_date',
            'statutory_attainment_date': 'statutory_attainment_date',
            'design_value': 'design_value',
            'design_value_units': 'dv_units',
            'meets_naaqs': 'meets_naaqs',
            'population_2020': 'populationtotalspl94_totpop20',
            'composite_id': 'composite_id'
        }
    
    def analyze_location(self, longitude: float, latitude: float, 
                        include_revoked: bool = False,
                        buffer_meters: float = 0,
                        pollutants: Optional[List[str]] = None) -> NonAttainmentAnalysisResult:
        """
        Analyze a location for nonattainment area intersections
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            include_revoked: Whether to include revoked standards
            buffer_meters: Buffer distance around point in meters
            pollutants: List of specific pollutants to check (None for all)
            
        Returns:
            NonAttainmentAnalysisResult with analysis results
        """
        logger.info(f"Analyzing nonattainment areas for location: {longitude}, {latitude}")
        
        try:
            # Determine which layers to query
            layers_to_query = []
            for layer_key, layer_info in self.layers.items():
                # Skip revoked standards unless requested
                if not include_revoked and layer_info['status'] == 'revoked':
                    continue
                
                # Filter by pollutants if specified
                if pollutants and layer_info['pollutant'] not in pollutants:
                    continue
                
                layers_to_query.append(layer_key)
            
            all_areas = []
            
            # Query each layer
            for layer_key in layers_to_query:
                layer_info = self.layers[layer_key]
                areas = self._query_layer_for_location(
                    layer_info, longitude, latitude, buffer_meters
                )
                all_areas.extend(areas)
            
            # Create result
            result = NonAttainmentAnalysisResult(
                location=(longitude, latitude),
                has_nonattainment_areas=len(all_areas) > 0,
                area_count=len(all_areas),
                nonattainment_areas=all_areas,
                analysis_timestamp=datetime.now().isoformat(),
                query_success=True
            )
            
            logger.info(f"Found {len(all_areas)} nonattainment areas at location")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing location: {e}")
            return NonAttainmentAnalysisResult(
                location=(longitude, latitude),
                has_nonattainment_areas=False,
                area_count=0,
                nonattainment_areas=[],
                analysis_timestamp=datetime.now().isoformat(),
                query_success=False,
                error_message=str(e)
            )
    
    def _query_layer_for_location(self, layer_info: Dict, longitude: float, 
                                 latitude: float, buffer_meters: float = 0) -> List[NonAttainmentAreaInfo]:
        """Query a specific layer for nonattainment information at a location"""
        
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
            areas = []
            
            for feature in features:
                area_info = self._process_area_feature(feature, layer_info)
                if area_info:
                    areas.append(area_info)
            
            logger.debug(f"Layer {layer_id} returned {len(areas)} nonattainment areas")
            return areas
            
        except Exception as e:
            logger.error(f"Error querying layer {layer_info.get('name', 'Unknown')}: {e}")
            return []
    
    def _process_area_feature(self, feature: Dict, layer_info: Dict) -> Optional[NonAttainmentAreaInfo]:
        """Process a nonattainment area feature into a NonAttainmentAreaInfo object"""
        
        try:
            attributes = feature.get('attributes', {})
            
            # Extract key information
            pollutant_name = attributes.get(self.field_mappings['pollutant_name'], layer_info['pollutant'])
            area_name = attributes.get(self.field_mappings['area_name'], 'Unknown Area')
            state_name = attributes.get(self.field_mappings['state_name'], 'Unknown')
            state_abbreviation = attributes.get(self.field_mappings['state_abbreviation'], 'Unknown')
            current_status = attributes.get(self.field_mappings['current_status'], 'Unknown')
            
            # Handle missing or null values
            if not pollutant_name or pollutant_name in ['', 'null', None]:
                pollutant_name = layer_info['pollutant']
            if not area_name or area_name in ['', 'null', None]:
                area_name = 'Unknown Area'
            if not state_name or state_name in ['', 'null', None]:
                state_name = 'Unknown'
            if not current_status or current_status in ['', 'null', None]:
                current_status = 'Unknown'
            
            # Create area info
            area_info = NonAttainmentAreaInfo(
                pollutant_name=pollutant_name,
                area_name=area_name,
                state_name=state_name,
                state_abbreviation=state_abbreviation,
                epa_region=attributes.get(self.field_mappings['epa_region'], 0),
                current_status=current_status,
                classification=attributes.get(self.field_mappings['classification'], 'Unknown'),
                designation_effective_date=self._format_date(attributes.get(self.field_mappings['designation_effective_date'])),
                statutory_attainment_date=self._format_date(attributes.get(self.field_mappings['statutory_attainment_date'])),
                design_value=attributes.get(self.field_mappings['design_value']),
                design_value_units=attributes.get(self.field_mappings['design_value_units']),
                meets_naaqs=attributes.get(self.field_mappings['meets_naaqs']),
                population_2020=attributes.get(self.field_mappings['population_2020']),
                composite_id=attributes.get(self.field_mappings['composite_id'])
            )
            
            return area_info
            
        except Exception as e:
            logger.error(f"Error processing area feature: {e}")
            return None
    
    def _format_date(self, timestamp: Optional[int]) -> Optional[str]:
        """Format timestamp to readable date string"""
        if timestamp is None:
            return None
        try:
            # Convert from milliseconds to seconds
            if timestamp > 1e10:  # Likely milliseconds
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return None
    
    def _create_buffer_ring(self, longitude: float, latitude: float, 
                           buffer_meters: float) -> List[List[float]]:
        """Create a simple circular buffer ring around a point"""
        
        import math
        
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
    
    def get_pollutant_areas(self, pollutant: str, 
                           include_revoked: bool = False) -> List[NonAttainmentAreaInfo]:
        """
        Get all nonattainment areas for a specific pollutant
        
        Args:
            pollutant: Name of the pollutant to search for
            include_revoked: Whether to include revoked standards
            
        Returns:
            List of NonAttainmentAreaInfo objects for the pollutant
        """
        logger.info(f"Searching for nonattainment areas for pollutant: {pollutant}")
        
        try:
            # Find matching layers
            matching_layers = []
            for layer_key, layer_info in self.layers.items():
                if layer_info['pollutant'].lower() == pollutant.lower():
                    if include_revoked or layer_info['status'] != 'revoked':
                        matching_layers.append(layer_key)
            
            all_areas = []
            
            # Query all matching layers
            for layer_key in matching_layers:
                layer_info = self.layers[layer_key]
                areas = self._query_layer_for_pollutant(layer_info, pollutant)
                all_areas.extend(areas)
            
            logger.info(f"Found {len(all_areas)} nonattainment areas for {pollutant}")
            return all_areas
            
        except Exception as e:
            logger.error(f"Error searching for pollutant areas: {e}")
            return []
    
    def _query_layer_for_pollutant(self, layer_info: Dict, pollutant: str) -> List[NonAttainmentAreaInfo]:
        """Query a layer for all areas of a specific pollutant"""
        
        try:
            # Create where clause for pollutant search
            where_clause = f"{self.field_mappings['pollutant_name']} LIKE '%{pollutant}%'"
            
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
                logger.warning(f"Pollutant query error for layer {layer_id}: {result['error']}")
                return []
            
            # Process features
            features = result.get('features', [])
            areas = []
            
            for feature in features:
                area_info = self._process_area_feature(feature, layer_info)
                if area_info:
                    areas.append(area_info)
            
            return areas
            
        except Exception as e:
            logger.error(f"Error querying pollutant in layer {layer_info.get('name', 'Unknown')}: {e}")
            return []
    
    def get_area_summary(self, result: NonAttainmentAnalysisResult) -> Dict[str, Any]:
        """Generate a summary of nonattainment analysis results"""
        
        if not result.query_success:
            return {
                "status": "error",
                "message": result.error_message,
                "location": result.location
            }
        
        if not result.has_nonattainment_areas:
            return {
                "status": "no_nonattainment",
                "message": "No nonattainment areas found at this location",
                "location": result.location,
                "analysis_timestamp": result.analysis_timestamp
            }
        
        # Analyze areas
        pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
        nonattainment_count = len([area for area in result.nonattainment_areas if area.current_status == 'Nonattainment'])
        maintenance_count = len([area for area in result.nonattainment_areas if area.current_status == 'Maintenance'])
        
        areas_list = []
        for area in result.nonattainment_areas:
            area_info = {
                "pollutant_name": area.pollutant_name,
                "area_name": area.area_name,
                "state_name": area.state_name,
                "current_status": area.current_status,
                "classification": area.classification,
                "design_value": area.design_value,
                "design_value_units": area.design_value_units,
                "meets_naaqs": area.meets_naaqs
            }
            areas_list.append(area_info)
        
        return {
            "status": "nonattainment_found",
            "location": result.location,
            "analysis_timestamp": result.analysis_timestamp,
            "summary": {
                "total_areas": result.area_count,
                "unique_pollutants": len(pollutants),
                "nonattainment_areas": nonattainment_count,
                "maintenance_areas": maintenance_count,
                "pollutants_affected": pollutants
            },
            "areas_details": areas_list,
            "recommendations": self._generate_recommendations(result)
        }
    
    def _generate_recommendations(self, result: NonAttainmentAnalysisResult) -> List[str]:
        """Generate recommendations based on nonattainment analysis"""
        
        recommendations = []
        
        if result.has_nonattainment_areas:
            recommendations.append(
                "⚠️  This location is within designated nonattainment areas for air quality standards. "
                "Development activities may be subject to additional air quality regulations."
            )
            
            nonattainment_areas = [area for area in result.nonattainment_areas if area.current_status == 'Nonattainment']
            if nonattainment_areas:
                recommendations.append(
                    f"🚫 {len(nonattainment_areas)} active nonattainment area(s) apply to this location. "
                    "These areas do not meet National Ambient Air Quality Standards (NAAQS)."
                )
            
            maintenance_areas = [area for area in result.nonattainment_areas if area.current_status == 'Maintenance']
            if maintenance_areas:
                recommendations.append(
                    f"🔧 {len(maintenance_areas)} maintenance area(s) apply to this location. "
                    "These areas previously violated NAAQS but now meet standards."
                )
            
            pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
            if len(pollutants) > 1:
                recommendations.append(
                    f"🌫️ Multiple pollutants ({len(pollutants)}) have nonattainment designations: {', '.join(pollutants)}. "
                    "Consider cumulative air quality impacts in planning."
                )
            
            recommendations.append(
                "📞 Contact EPA Regional Office and state air quality agency for project consultation and compliance guidance."
            )
            
            recommendations.append(
                "📋 Review Clean Air Act requirements and potential permit obligations for new sources or modifications."
            )
        
        return recommendations
    
    def save_nonattainment_data(self, analysis_result: NonAttainmentAnalysisResult,
                               filename: str = None,
                               use_output_manager: bool = True) -> bool:
        """
        Save nonattainment analysis data to file using output directory manager
        
        Args:
            analysis_result: NonAttainmentAnalysisResult object with analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare data for serialization
            save_data = {
                'analysis_timestamp': analysis_result.analysis_timestamp,
                'location': {
                    'longitude': analysis_result.location[0],
                    'latitude': analysis_result.location[1]
                },
                'query_success': analysis_result.query_success,
                'error_message': analysis_result.error_message,
                'summary': {
                    'has_nonattainment_areas': analysis_result.has_nonattainment_areas,
                    'area_count': analysis_result.area_count
                },
                'nonattainment_areas': [
                    {
                        'pollutant_name': area.pollutant_name,
                        'area_name': area.area_name,
                        'state_name': area.state_name,
                        'state_abbreviation': area.state_abbreviation,
                        'epa_region': area.epa_region,
                        'current_status': area.current_status,
                        'classification': area.classification,
                        'designation_effective_date': area.designation_effective_date,
                        'statutory_attainment_date': area.statutory_attainment_date,
                        'design_value': area.design_value,
                        'design_value_units': area.design_value_units,
                        'meets_naaqs': area.meets_naaqs,
                        'population_2020': area.population_2020,
                        'composite_id': area.composite_id
                    } for area in analysis_result.nonattainment_areas
                ]
            }
            
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    lon, lat = analysis_result.location
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"nonattainment_analysis_{lon}_{lat}_{timestamp}.json"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "data")
                
                # Save the data
                with open(file_path, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
                
                logger.info(f"Nonattainment data saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    lon, lat = analysis_result.location
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"nonattainment_analysis_{lon}_{lat}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
                
                logger.info(f"Nonattainment data saved to: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save nonattainment data: {e}")
            return False
    
    def export_nonattainment_summary_report(self, analysis_result: NonAttainmentAnalysisResult,
                                           filename: str = None,
                                           use_output_manager: bool = True) -> bool:
        """
        Export a human-readable summary report of nonattainment data
        
        Args:
            analysis_result: NonAttainmentAnalysisResult object with analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Generate report content
            lon, lat = analysis_result.location
            report_lines = [
                "NONATTAINMENT AREAS ANALYSIS REPORT",
                "=" * 50,
                f"Location: {lat:.6f}°N, {lon:.6f}°W",
                f"Analysis Date: {analysis_result.analysis_timestamp}",
                "",
                "SUMMARY",
                "-" * 20,
            ]
            
            if not analysis_result.query_success:
                report_lines.extend([
                    "❌ Analysis failed",
                    f"Error: {analysis_result.error_message or 'Unknown error'}",
                    ""
                ])
            elif not analysis_result.has_nonattainment_areas:
                report_lines.extend([
                    "✅ No nonattainment areas found at this location",
                    "This location appears to be in compliance with National Ambient Air Quality Standards (NAAQS).",
                    ""
                ])
            else:
                # Get summary statistics
                nonattainment_count = len([area for area in analysis_result.nonattainment_areas 
                                         if area.current_status == 'Nonattainment'])
                maintenance_count = len([area for area in analysis_result.nonattainment_areas 
                                       if area.current_status == 'Maintenance'])
                pollutants = list(set(area.pollutant_name for area in analysis_result.nonattainment_areas))
                
                report_lines.extend([
                    f"⚠️  NONATTAINMENT AREAS DETECTED",
                    f"Total Areas Found: {analysis_result.area_count}",
                    f"Active Nonattainment Areas: {nonattainment_count}",
                    f"Maintenance Areas: {maintenance_count}",
                    f"Pollutants Affected: {len(pollutants)}",
                    f"Pollutant Types: {', '.join(pollutants)}",
                    "",
                    "AREA DETAILS",
                    "-" * 20
                ])
                
                for i, area in enumerate(analysis_result.nonattainment_areas, 1):
                    status_icon = "🚫" if area.current_status == 'Nonattainment' else "🔧"
                    report_lines.extend([
                        f"{i}. {status_icon} {area.area_name}",
                        f"   Pollutant: {area.pollutant_name}",
                        f"   Status: {area.current_status}",
                        f"   Classification: {area.classification}",
                        f"   State: {area.state_name} (EPA Region {area.epa_region})",
                        f"   Design Value: {area.design_value or 'N/A'} {area.design_value_units or ''}",
                        f"   Meets NAAQS: {area.meets_naaqs or 'N/A'}",
                        ""
                    ])
                
                # Add recommendations
                summary = self.get_area_summary(analysis_result)
                if 'recommendations' in summary:
                    report_lines.extend([
                        "RECOMMENDATIONS",
                        "-" * 20
                    ])
                    for rec in summary['recommendations']:
                        report_lines.append(f"• {rec}")
                        report_lines.append("")
            
            # Save the report
            report_content = "\n".join(report_lines)
            
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"nonattainment_report_{lon}_{lat}_{timestamp}.txt"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "reports")
                
                # Save the report
                with open(file_path, 'w') as f:
                    f.write(report_content)
                
                logger.info(f"Nonattainment report saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"nonattainment_report_{lon}_{lat}_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(report_content)
                
                logger.info(f"Nonattainment report saved to: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to export nonattainment report: {e}")
            return False

# Import math for buffer calculations
import math 