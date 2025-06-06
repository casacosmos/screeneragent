#!/usr/bin/env python3
"""
Comprehensive Karst Analysis Tool

This script analyzes both the PRAPEC karst areas and the associated buffer zones:
1. PRAPEC (Carso) layer - the primary karst regulatory area (Layer 15)
2. Zona de Amortiguamiento Reglamentada - regulated buffer zones (Layer 0)

This provides a complete picture of karst regulations including buffer zones.
"""

import requests
import json
import urllib3
import os
import sys
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ComprehensiveKarstAnalyzer:
    """Comprehensive analyzer for PRAPEC karst and buffer zones."""
    
    def __init__(self):
        self.base_url = "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer"
        self.prapec_layer_id = 15  # PRAPEC (Carso) layer
        self.buffer_layer_id = 0   # Zona de Amortiguamiento Reglamentada layer
        self.session = requests.Session()
        self.session.verify = False
        
    def analyze_comprehensive_karst(self, longitude: float, latitude: float, 
                                  search_radius_miles: float = 2.0) -> Dict[str, Any]:
        """
        Perform comprehensive karst analysis including PRAPEC areas and buffer zones.
        
        Args:
            longitude: Longitude in WGS84
            latitude: Latitude in WGS84
            search_radius_miles: Search radius in miles
            
        Returns:
            Comprehensive analysis including all karst-related regulations
        """
        print(f"🏔️ Comprehensive karst analysis at ({longitude:.6f}, {latitude:.6f})")
        
        analysis = {
            "success": True,
            "query_location": {"longitude": longitude, "latitude": latitude},
            "search_radius_miles": search_radius_miles,
            "query_time": datetime.now().isoformat(),
            "prapec_analysis": {},
            "buffer_zone_analysis": {},
            "combined_assessment": {},
            "regulatory_implications": []
        }
        
        try:
            # 1. Analyze PRAPEC karst areas
            print("   🗿 Analyzing PRAPEC karst areas...")
            prapec_result = self._analyze_prapec_karst(longitude, latitude, search_radius_miles)
            analysis["prapec_analysis"] = prapec_result
            
            # 2. Analyze buffer zones
            print("   📏 Analyzing regulated buffer zones...")
            buffer_result = self._analyze_buffer_zones(longitude, latitude, search_radius_miles)
            analysis["buffer_zone_analysis"] = buffer_result
            
            # 3. Combined assessment
            analysis["combined_assessment"] = self._generate_combined_assessment(
                prapec_result, buffer_result
            )
            
            # 4. Regulatory implications
            analysis["regulatory_implications"] = self._generate_regulatory_implications(
                prapec_result, buffer_result
            )
            
            return analysis
            
        except Exception as e:
            analysis["success"] = False
            analysis["error"] = str(e)
            return analysis
    
    def _analyze_prapec_karst(self, longitude: float, latitude: float, 
                            search_radius_miles: float) -> Dict[str, Any]:
        """Analyze PRAPEC karst areas."""
        
        search_radius_meters = search_radius_miles * 1609.34
        
        # Point geometry in WGS84
        point_geometry = f"{longitude},{latitude}"
        
        # Query PRAPEC layer
        params = {
            "geometry": point_geometry,
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": search_radius_meters,
            "units": "esriSRUnit_Meter",
            "inSR": "4326",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/{self.prapec_layer_id}/query", 
                                      params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            
            if features:
                feature = features[0]
                attrs = feature.get("attributes", {})
                
                return {
                    "success": True,
                    "karst_found": True,
                    "karst_info": {
                        "object_id": attrs.get("OBJECTID_1"),
                        "nombre": attrs.get("Nombre"),
                        "regla": attrs.get("Regla"),
                        "area_sq_meters": attrs.get("Shape.STArea()"),
                        "perimeter_meters": attrs.get("Shape.STLength()"),
                        "area_hectares": attrs.get("Shape.STArea()", 0) / 10000
                    },
                    "proximity": "within_search_radius",
                    "regulation_type": "PRAPEC",
                    "description": f"Plan y Reglamento del Área de Planificación Especial del Carso - Regulation {attrs.get('Regla', 'Unknown')}"
                }
            else:
                return {
                    "success": True,
                    "karst_found": False,
                    "proximity": "none",
                    "message": f"No PRAPEC karst area found within {search_radius_miles} miles"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "karst_found": False
            }
    
    def _analyze_buffer_zones(self, longitude: float, latitude: float, 
                            search_radius_miles: float) -> Dict[str, Any]:
        """Analyze regulated buffer zones."""
        
        search_radius_meters = search_radius_miles * 1609.34
        
        # Point geometry in WGS84
        point_geometry = f"{longitude},{latitude}"
        
        # Query buffer zone layer
        params = {
            "geometry": point_geometry,
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": search_radius_meters,
            "units": "esriSRUnit_Meter",
            "inSR": "4326",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/{self.buffer_layer_id}/query", 
                                      params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            
            buffer_zones = []
            for feature in features:
                attrs = feature.get("attributes", {})
                
                buffer_info = {
                    "object_id": attrs.get("OBJECTID"),
                    "project": attrs.get("Proyecto"),
                    "classification": attrs.get("CALI_SOBRE"),
                    "description": attrs.get("DES_SOBRE"),
                    "validity": attrs.get("V_SOBRE"),
                    "resolution": attrs.get("R_SOBRE"),
                    "regulation_rule": attrs.get("REGLASOBRE"),
                    "buffer_distance_meters": attrs.get("BUFF_DIST"),
                    "buffer_distance_miles": attrs.get("BUFF_DIST", 0) / 1609.34 if attrs.get("BUFF_DIST") else None,
                    "type": attrs.get("TIPO"),
                    "area_sq_meters": attrs.get("Shape.STArea()"),
                    "perimeter_meters": attrs.get("Shape.STLength()")
                }
                
                buffer_zones.append(buffer_info)
            
            if buffer_zones:
                return {
                    "success": True,
                    "buffer_zones_found": True,
                    "total_buffer_zones": len(buffer_zones),
                    "buffer_zones": buffer_zones,
                    "proximity": "within_search_radius"
                }
            else:
                return {
                    "success": True,
                    "buffer_zones_found": False,
                    "proximity": "none",
                    "message": f"No regulated buffer zones found within {search_radius_miles} miles"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "buffer_zones_found": False
            }
    
    def _generate_combined_assessment(self, prapec_result: Dict[str, Any], 
                                    buffer_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate combined assessment of karst and buffer zone findings."""
        
        assessment = {
            "overall_karst_impact": "none",
            "regulatory_zones_identified": [],
            "primary_concerns": [],
            "development_implications": [],
            "required_assessments": []
        }
        
        # PRAPEC karst assessment
        if prapec_result.get("karst_found"):
            assessment["overall_karst_impact"] = "high"
            assessment["regulatory_zones_identified"].append("PRAPEC Karst Area")
            assessment["primary_concerns"].append("Direct impact on karst geological features")
            assessment["development_implications"].append("Karst-specific engineering requirements")
            assessment["required_assessments"].append("Comprehensive karst geological assessment")
        
        # Buffer zone assessment
        if buffer_result.get("buffer_zones_found"):
            buffer_zones = buffer_result.get("buffer_zones", [])
            
            for zone in buffer_zones:
                zone_type = zone.get("type", "Unknown")
                project = zone.get("project", "Unknown")
                buffer_dist = zone.get("buffer_distance_miles", 0)
                
                assessment["regulatory_zones_identified"].append(
                    f"Buffer Zone: {project} ({zone_type})"
                )
                
                if buffer_dist:
                    assessment["primary_concerns"].append(
                        f"Within {buffer_dist:.2f}-mile regulated buffer zone"
                    )
                
                assessment["development_implications"].append(
                    f"Subject to buffer zone regulations: {zone.get('description', 'Unknown')}"
                )
        
        # Determine overall impact level
        if prapec_result.get("karst_found"):
            assessment["overall_karst_impact"] = "high"
        elif buffer_result.get("buffer_zones_found"):
            assessment["overall_karst_impact"] = "moderate" 
        else:
            assessment["overall_karst_impact"] = "low"
        
        return assessment
    
    def _generate_regulatory_implications(self, prapec_result: Dict[str, Any], 
                                        buffer_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate regulatory implications based on findings."""
        
        implications = []
        
        # PRAPEC implications
        if prapec_result.get("karst_found"):
            karst_info = prapec_result.get("karst_info", {})
            regulation = karst_info.get("regla", "Unknown")
            
            implications.append({
                "regulation_type": "PRAPEC Karst",
                "regulation_number": f"Regulation {regulation}",
                "authority": "Puerto Rico Planning Board",
                "impact_level": "high",
                "requirements": [
                    "Environmental Impact Assessment required",
                    "Karst geological study required",
                    "Special construction techniques may be required",
                    "Groundwater protection measures required",
                    "Enhanced environmental monitoring"
                ],
                "permits_needed": [
                    "PRAPEC development permit",
                    "Environmental compliance certification",
                    "Geological assessment approval"
                ]
            })
        
        # Buffer zone implications
        if buffer_result.get("buffer_zones_found"):
            buffer_zones = buffer_result.get("buffer_zones", [])
            
            for zone in buffer_zones:
                implications.append({
                    "regulation_type": "Regulated Buffer Zone",
                    "regulation_number": f"Rule {zone.get('regulation_rule', 'Unknown')}",
                    "authority": "Puerto Rico Planning Board",
                    "project_name": zone.get("project", "Unknown"),
                    "buffer_distance_miles": zone.get("buffer_distance_miles"),
                    "impact_level": "moderate",
                    "requirements": [
                        f"Compliance with buffer zone regulations",
                        f"Development restrictions may apply",
                        f"Special permitting may be required"
                    ],
                    "description": zone.get("description", "Buffer zone regulations apply")
                })
        
        return implications
    
    def get_all_karst_types(self) -> Dict[str, Any]:
        """Get all available karst and buffer zone types from both layers."""
        print("📊 Analyzing all karst and buffer zone types...")
        
        analysis = {
            "success": True,
            "query_time": datetime.now().isoformat(),
            "prapec_types": {},
            "buffer_zone_types": {},
            "summary": {}
        }
        
        try:
            # 1. Get all PRAPEC features
            print("   🗿 Querying all PRAPEC features...")
            prapec_params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            prapec_response = self.session.get(f"{self.base_url}/{self.prapec_layer_id}/query",
                                             params=prapec_params, timeout=30)
            prapec_response.raise_for_status()
            prapec_data = prapec_response.json()
            
            prapec_features = prapec_data.get("features", [])
            analysis["prapec_types"] = self._analyze_prapec_features(prapec_features)
            
            # 2. Get all buffer zone features
            print("   📏 Querying all buffer zone features...")
            buffer_params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            buffer_response = self.session.get(f"{self.base_url}/{self.buffer_layer_id}/query",
                                             params=buffer_params, timeout=30)
            buffer_response.raise_for_status()
            buffer_data = buffer_response.json()
            
            buffer_features = buffer_data.get("features", [])
            analysis["buffer_zone_types"] = self._analyze_buffer_features(buffer_features)
            
            # 3. Generate summary
            analysis["summary"] = self._generate_karst_summary(
                analysis["prapec_types"], analysis["buffer_zone_types"]
            )
            
            return analysis
            
        except Exception as e:
            analysis["success"] = False
            analysis["error"] = str(e)
            return analysis
    
    def _analyze_prapec_features(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze PRAPEC features to understand types and characteristics."""
        
        analysis = {
            "total_features": len(features),
            "unique_attributes": {}, # Store unique values for all attributes
            "total_area_hectares": 0,
            "features_details": []
        }
        
        if not features:
            return analysis

        # Initialize unique_attributes with empty sets for each field
        all_field_names = features[0].get("attributes", {}).keys()
        for field_name in all_field_names:
            analysis["unique_attributes"][field_name] = set()

        for feature in features:
            attrs = feature.get("attributes", {})
            area = attrs.get("Shape.STArea()", 0)
            analysis["total_area_hectares"] += (area / 10000) if area else 0
            
            feature_detail = {"object_id": attrs.get("OBJECTID_1")}
            for field_name, value in attrs.items():
                analysis["unique_attributes"][field_name].add(value)
                feature_detail[field_name] = value
            
            analysis["features_details"].append(feature_detail)
        
        # Convert sets to lists for JSON serialization
        for field_name in analysis["unique_attributes"]:
            analysis["unique_attributes"][field_name] = sorted(list(
                # Make items hashable for set, then convert back if needed (e.g. for None)
                item if isinstance(item, (str, int, float, bool)) else str(item) 
                for item in analysis["unique_attributes"][field_name]
                if item is not None # Exclude None from sorted list for cleaner output, though it was added to set
            ))
            # If original set had None and it's not in list, add it back for completeness if desired
            # For now, excluding None from the sorted list output.

        # For backward compatibility with existing printout, add specific unique_names and unique_regulations
        analysis["unique_names"] = analysis["unique_attributes"].get("Nombre", [])
        analysis["unique_regulations"] = analysis["unique_attributes"].get("Regla", [])
        
        return analysis
    
    def _analyze_buffer_features(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze buffer zone features (Layer 0) to understand types and characteristics, collecting all unique attribute values."""
        
        analysis = {
            "total_features": len(features),
            "unique_attributes": {}, # Store unique values for all attributes
            "buffer_distances_meters": [], # Store raw buffer distances in meters
            "features_details": []
        }

        if not features:
            return analysis

        # Initialize unique_attributes with empty sets for each field from the first feature
        all_field_names = features[0].get("attributes", {}).keys()
        for field_name in all_field_names:
            analysis["unique_attributes"][field_name] = set()

        for feature in features:
            attrs = feature.get("attributes", {})
            buffer_dist_meters = attrs.get("BUFF_DIST")
            if buffer_dist_meters is not None:
                analysis["buffer_distances_meters"].append(buffer_dist_meters)
            
            feature_detail = {"object_id": attrs.get("OBJECTID")}
            for field_name, value in attrs.items():
                analysis["unique_attributes"][field_name].add(value)
                feature_detail[field_name] = value
            
            # Add derived buffer distance in miles for convenience in details
            if buffer_dist_meters is not None:
                feature_detail["buffer_distance_miles"] = buffer_dist_meters / 1609.34
            else:
                feature_detail["buffer_distance_miles"] = None

            analysis["features_details"].append(feature_detail)
        
        # Convert sets to lists for JSON serialization and cleaner output
        for field_name in analysis["unique_attributes"]:
            analysis["unique_attributes"][field_name] = sorted(list(
                item if isinstance(item, (str, int, float, bool)) else str(item) 
                for item in analysis["unique_attributes"][field_name]
                if item is not None # Exclude None from sorted list for cleaner output
            ))

        # For backward compatibility and direct access in printout
        analysis["unique_projects"] = analysis["unique_attributes"].get("Proyecto", [])
        analysis["unique_types"] = analysis["unique_attributes"].get("TIPO", [])
        analysis["unique_classifications"] = analysis["unique_attributes"].get("CALI_SOBRE", [])
        
        raw_buffer_distances = analysis["buffer_distances_meters"] # Use the raw meter values
        if raw_buffer_distances:
            # Filter out Nones if any somehow got in, though initial check should prevent it
            valid_distances_m = [d for d in raw_buffer_distances if d is not None]
            if valid_distances_m:
                analysis["buffer_statistics"] = {
                    "min_distance_meters": min(valid_distances_m),
                    "max_distance_meters": max(valid_distances_m),
                    "avg_distance_meters": sum(valid_distances_m) / len(valid_distances_m),
                    "min_distance_miles": min(valid_distances_m) / 1609.34,
                    "max_distance_miles": max(valid_distances_m) / 1609.34,
                    "avg_distance_miles": (sum(valid_distances_m) / len(valid_distances_m)) / 1609.34,
                    "unique_distances_meters": sorted(list(set(valid_distances_m)))
                }
            else:
                 analysis["buffer_statistics"] = {"message": "No valid buffer distances found to calculate statistics."}
        else:
            analysis["buffer_statistics"] = {"message": "No buffer distances found in features."}

        # Remove the temporary list of meter distances if preferred to keep schema clean
        # del analysis["buffer_distances_meters"] 
        
        return analysis
    
    def _generate_karst_summary(self, prapec_analysis: Dict[str, Any], 
                              buffer_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of all karst-related regulations."""
        
        return {
            "total_regulatory_areas": prapec_analysis["total_features"] + buffer_analysis["total_features"],
            "prapec_karst_areas": {
                "count": prapec_analysis["total_features"],
                "total_area_hectares": prapec_analysis["total_area_hectares"],
                "regulations": prapec_analysis["unique_regulations"],
                "area_names": prapec_analysis["unique_names"]
            },
            "regulated_buffer_zones": {
                "count": buffer_analysis["total_features"],
                "projects": buffer_analysis["unique_projects"],
                "zone_types": buffer_analysis["unique_types"],
                "classifications": buffer_analysis["unique_classifications"],
                "buffer_statistics": buffer_analysis.get("buffer_statistics", {})
            },
            "regulatory_framework": {
                "primary_authority": "Puerto Rico Planning Board (Junta de Planificación)",
                "applicable_regulations": prapec_analysis["unique_regulations"],
                "coverage_areas": ["PRAPEC Karst Areas", "Regulated Buffer Zones"],
                "development_impact": "High for direct karst areas, Moderate for buffer zones"
            }
        }

    def find_nearest_karst_features(self, longitude: float, latitude: float, 
                                   max_search_radius_miles: float = 5.0) -> Dict[str, Any]:
        """
        Find the nearest PRAPEC (Layer 15) and specific karst/buffer zones (Layer 0) 
        to a given coordinate if it's not directly within them.
        Searches up to max_search_radius_miles.
        """
        print(f"🔍 Searching for nearest karst features to ({longitude:.6f}, {latitude:.6f}) within {max_search_radius_miles} miles...")
        results = {
            "search_coordinates": {"longitude": longitude, "latitude": latitude},
            "max_search_radius_miles": max_search_radius_miles,
            "nearest_prapec_l15": None, # Details of nearest Layer 15 feature
            "nearest_zone_l0": None    # Details of nearest Layer 0 feature (APE-ZC or ZA)
        }
        search_radius_meters = max_search_radius_miles * 1609.34

        # --- Find nearest PRAPEC Layer 15 feature ---
        try:
            prapec_query_params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326", # Input is WGS84
                "spatialRel": "esriSpatialRelContains", # We want features that contain the point (inverse logic for distance)
                                                      # Actually, for nearest, we use a buffer and sort by distance.
                                                      # The ArcGIS REST API is a bit tricky for direct "nearest" if not using an extension.
                                                      # A common approach is to buffer and find the one with the smallest distance attribute if available,
                                                      # or query features within a large buffer and then calculate distances client-side.
                                                      # For simplicity here, we'll query with a buffer and if features are returned, 
                                                      # assume the service might have some internal prioritization or take the first one.
                                                      # A more robust solution would fetch geometries and calculate true nearest.
                # Let's try finding features within a large buffer first
                # and then try to get distance if the service supports it.
                "distance": search_radius_meters,
                "units": "esriSRUnit_Meter",
                "outFields": "OBJECTID_1,Nombre,Regla,Shape.STArea(),Shape.STLength()",
                "returnGeometry": "false", # Set to true if client-side distance calc is needed
                "orderByFields": "DISTANCE ASC", # Request server to sort by distance if supported
                "f": "json",
                "resultRecordCount": 1 # Get only the closest one if ordered by distance
            }
            # Forcing esriSpatialRelIntersects as esriSpatialRelContains on point to polygon is not what we want for nearest
            prapec_query_params["spatialRel"] = "esriSpatialRelIntersects" 

            response_l15 = self.session.get(f"{self.base_url}/{self.prapec_layer_id}/query", params=prapec_query_params, timeout=20)
            response_l15.raise_for_status()
            data_l15 = response_l15.json()
            features_l15 = data_l15.get("features", [])

            if features_l15:
                # Assuming the first feature is the closest due to orderByFields or just taking the first intersecting within buffer
                attrs_l15 = features_l15[0].get("attributes", {})
                # Actual distance is not directly returned by this query type easily without geometry or specific server caps
                # We know it's within max_search_radius_miles. For more precise, geometry + client-side calc needed.
                results["nearest_prapec_l15"] = {
                    "found_within_radius": True,
                    "estimated_distance_note": f"Found within {max_search_radius_miles} miles. Precise distance requires geometry analysis.",
                    "OBJECTID_1": attrs_l15.get("OBJECTID_1"),
                    "Nombre": attrs_l15.get("Nombre"),
                    "Regla": attrs_l15.get("Regla")
                }
        except Exception as e:
            print(f"   Error finding nearest PRAPEC L15: {e}")
            results["nearest_prapec_l15"] = {"found_within_radius": False, "error": str(e)}

        # --- Find nearest Zone Layer 0 feature (APE-ZC or ZA) ---
        try:
            zone_l0_query_params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "distance": search_radius_meters,
                "units": "esriSRUnit_Meter",
                "outFields": "OBJECTID,Proyecto,CALI_SOBRE,DES_SOBRE,REGLASOBRE,BUFF_DIST,TIPO",
                "returnGeometry": "false",
                "orderByFields": "DISTANCE ASC",
                "f": "json",
                "resultRecordCount": 1
            }
            response_l0 = self.session.get(f"{self.base_url}/{self.buffer_layer_id}/query", params=zone_l0_query_params, timeout=20)
            response_l0.raise_for_status()
            data_l0 = response_l0.json()
            features_l0 = data_l0.get("features", [])

            if features_l0:
                attrs_l0 = features_l0[0].get("attributes", {})
                results["nearest_zone_l0"] = {
                    "found_within_radius": True,
                    "estimated_distance_note": f"Found within {max_search_radius_miles} miles. Precise distance requires geometry analysis.",
                    "OBJECTID": attrs_l0.get("OBJECTID"),
                    "Proyecto": attrs_l0.get("Proyecto"),
                    "CALI_SOBRE": attrs_l0.get("CALI_SOBRE"),
                    "DES_SOBRE": attrs_l0.get("DES_SOBRE"),
                    "REGLASOBRE": attrs_l0.get("REGLASOBRE")
                }
        except Exception as e:
            print(f"   Error finding nearest Zone L0: {e}")
            results["nearest_zone_l0"] = {"found_within_radius": False, "error": str(e)}

        return results

    def save_karst_data(self, analysis_result: Dict[str, Any],
                       filename: str = None,
                       use_output_manager: bool = True) -> bool:
        """
        Save karst analysis data to file using output directory manager
        
        Args:
            analysis_result: Dictionary with karst analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    location = analysis_result.get("query_location", {})
                    lon = location.get("longitude", 0)
                    lat = location.get("latitude", 0)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"karst_analysis_{lon}_{lat}_{timestamp}.json"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "data")
                
                # Save the data
                with open(file_path, 'w') as f:
                    json.dump(analysis_result, f, indent=2, default=str)
                
                print(f"💾 Karst data saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    location = analysis_result.get("query_location", {})
                    lon = location.get("longitude", 0)
                    lat = location.get("latitude", 0)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"karst_analysis_{lon}_{lat}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(analysis_result, f, indent=2, default=str)
                
                print(f"💾 Karst data saved to: {filename}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to save karst data: {e}")
            return False
    
    def export_karst_summary_report(self, analysis_result: Dict[str, Any],
                                   filename: str = None,
                                   use_output_manager: bool = True) -> bool:
        """
        Export a human-readable summary report of karst data
        
        Args:
            analysis_result: Dictionary with karst analysis results
            filename: Optional filename (auto-generated if not provided)
            use_output_manager: Whether to use output directory manager (default: True)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Generate report content
            location = analysis_result.get("query_location", {})
            lon = location.get("longitude", 0)
            lat = location.get("latitude", 0)
            
            report_lines = [
                "COMPREHENSIVE KARST ANALYSIS REPORT",
                "=" * 50,
                f"Location: {lat:.6f}°N, {lon:.6f}°W",
                f"Analysis Date: {analysis_result.get('query_time', 'Unknown')}",
                f"Search Radius: {analysis_result.get('search_radius_miles', 'Unknown')} miles",
                "",
                "SUMMARY",
                "-" * 20,
            ]
            
            if not analysis_result.get("success", False):
                report_lines.extend([
                    "❌ Analysis failed",
                    f"Error: {analysis_result.get('error', 'Unknown error')}",
                    ""
                ])
            else:
                # PRAPEC Analysis
                prapec_result = analysis_result.get("prapec_analysis", {})
                report_lines.extend([
                    "🗿 PRAPEC KARST AREAS",
                    "-" * 20
                ])
                
                if prapec_result.get("karst_found", False):
                    karst_info = prapec_result.get("karst_info", {})
                    report_lines.extend([
                        "✅ PRAPEC karst area detected!",
                        f"   Name: {karst_info.get('nombre', 'N/A')}",
                        f"   Regulation: {karst_info.get('regla', 'N/A')}",
                        f"   Area: {karst_info.get('area_hectares', 0):,.1f} hectares",
                        f"   Area: {karst_info.get('area_sq_meters', 0):,.1f} square meters",
                        ""
                    ])
                else:
                    report_lines.extend([
                        "❌ No PRAPEC karst areas found within search radius",
                        ""
                    ])
                
                # Buffer Zone Analysis
                buffer_result = analysis_result.get("buffer_zone_analysis", {})
                report_lines.extend([
                    "📏 REGULATED BUFFER ZONES",
                    "-" * 20
                ])
                
                if buffer_result.get("buffer_zones_found", False):
                    buffer_zones = buffer_result.get("buffer_zones", [])
                    report_lines.extend([
                        f"✅ {len(buffer_zones)} regulated buffer zone(s) detected!",
                        ""
                    ])
                    
                    for i, zone in enumerate(buffer_zones, 1):
                        report_lines.extend([
                            f"{i}. Buffer Zone",
                            f"   Project: {zone.get('project', 'N/A')}",
                            f"   Type: {zone.get('type', 'N/A')}",
                            f"   Classification: {zone.get('classification', 'N/A')}",
                            f"   Description: {zone.get('description', 'N/A')}",
                            f"   Buffer Distance: {zone.get('buffer_distance_miles', 0):.2f} miles",
                            f"   Regulation Rule: {zone.get('regulation_rule', 'N/A')}",
                            ""
                        ])
                else:
                    report_lines.extend([
                        "❌ No regulated buffer zones found within search radius",
                        ""
                    ])
                
                # Combined Assessment
                assessment = analysis_result.get("combined_assessment", {})
                if assessment:
                    report_lines.extend([
                        "⚖️ COMBINED ASSESSMENT",
                        "-" * 20,
                        f"Overall Karst Impact: {assessment.get('overall_karst_impact', 'Unknown').upper()}",
                        f"Regulatory Zones Identified: {len(assessment.get('regulatory_zones_identified', []))}",
                        ""
                    ])
                    
                    for zone in assessment.get("regulatory_zones_identified", []):
                        report_lines.append(f"   • {zone}")
                    
                    report_lines.append("")
                
                # Regulatory Implications
                implications = analysis_result.get("regulatory_implications", [])
                if implications:
                    report_lines.extend([
                        "📜 REGULATORY IMPLICATIONS",
                        "-" * 20
                    ])
                    
                    for impl in implications:
                        report_lines.extend([
                            f"• {impl.get('regulation_type', 'Unknown')} - {impl.get('impact_level', 'Unknown').upper()} Impact",
                            f"  Authority: {impl.get('authority', 'Unknown')}",
                            f"  Description: {impl.get('description', 'N/A')}",
                            ""
                        ])
                        
                        if impl.get('requirements'):
                            report_lines.append("  Requirements:")
                            for req in impl['requirements']:
                                report_lines.append(f"    - {req}")
                            report_lines.append("")
            
            # Save the report
            report_content = "\n".join(report_lines)
            
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"karst_report_{lon}_{lat}_{timestamp}.txt"
                
                # Get the file path using output manager
                file_path = output_manager.get_file_path(filename, "reports")
                
                # Save the report
                with open(file_path, 'w') as f:
                    f.write(report_content)
                
                print(f"📄 Karst report saved to: {file_path}")
                return True
            else:
                # Fallback to current directory
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"karst_report_{lon}_{lat}_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(report_content)
                
                print(f"📄 Karst report saved to: {filename}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to export karst report: {e}")
            return False

def main():
    """Run comprehensive karst analysis demonstration."""
    print("🏔️ COMPREHENSIVE KARST ANALYSIS TOOL")
    print("=" * 70)
    print("Analyzing PRAPEC karst areas AND regulated buffer zones...")
    
    analyzer = ComprehensiveKarstAnalyzer()
    
    # 1. Get overview of all karst types
    print("\n" + "="*50)
    print("📊 ANALYZING ALL KARST AND BUFFER ZONE TYPES")
    print("="*50)
    
    all_types = analyzer.get_all_karst_types()
    
    if all_types["success"]:
        print("✅ Comprehensive karst analysis completed")
        
        # PRAPEC Summary
        prapec = all_types["prapec_types"]
        print(f"\n🗿 PRAPEC KARST AREAS (Layer 15 - {prapec.get('total_features', 0)} features):")
        print(f"   • Total Area: {prapec.get('total_area_hectares', 0):,.1f} hectares")
        
        print(f"\n   🔍 Unique Attribute Values for PRAPEC Layer 15:")
        unique_prapec_attrs = prapec.get("unique_attributes", {})
        if unique_prapec_attrs:
            for field, values in unique_prapec_attrs.items():
                if values: # Only print if there are non-None unique values
                    print(f"      • {field}: {values[:20]}") # Print up to 20 unique values
                    if len(values) > 20:
                        print(f"        ... and {len(values) - 20} more.")
        else:
            print("      No attributes found or all values are None.")

        # Buffer Zone Summary
        buffer_zones_data = all_types["buffer_zone_types"]
        print(f"\n📏 REGULATED BUFFER ZONES (Layer 0 - {buffer_zones_data.get('total_features', 0)} features):")
        
        print(f"\n   🔍 Unique Attribute Values for Buffer Zone Layer 0:")
        unique_buffer_attrs = buffer_zones_data.get("unique_attributes", {})
        if unique_buffer_attrs:
            for field, values in unique_buffer_attrs.items():
                if values: # Only print if there are non-None unique values
                    print(f"      • {field}: {values[:20]}") # Print up to 20 unique values
                    if len(values) > 20:
                        print(f"        ... and {len(values) - 20} more.")
        else:
            print("      No attributes found or all values are None.")

        if "buffer_statistics" in buffer_zones_data and buffer_zones_data["buffer_statistics"].get("min_distance_miles") is not None:
            stats = buffer_zones_data["buffer_statistics"]
            print(f"   📈 Buffer Distances (from BUFF_DIST field):")
            print(f"      Min: {stats['min_distance_miles']:.2f} miles ({stats['min_distance_meters']:.2f} m)")
            print(f"      Max: {stats['max_distance_miles']:.2f} miles ({stats['max_distance_meters']:.2f} m)")
            print(f"      Avg: {stats['avg_distance_miles']:.2f} miles ({stats['avg_distance_meters']:.2f} m)")
            print(f"      Unique Values (meters): {stats.get('unique_distances_meters', [])}")
        elif buffer_zones_data.get("buffer_statistics") and buffer_zones_data["buffer_statistics"].get("message"):
            print(f'   📈 Buffer Distances: {buffer_zones_data["buffer_statistics"].get("message")}')
        else:
            print("   📈 Buffer Distances: Statistics not available or no BUFF_DIST values found.")

        # Show some examples
        print(f"\n📋 BUFFER ZONE EXAMPLES (First 5):")
        for detail in buffer_zones_data.get("features_details", [])[:5]:  # Show first 5
            project = detail.get("project", "N/A") # Added .get for safety
            zone_type = detail.get("type", "N/A")
            buffer_miles = detail.get("buffer_distance_miles")
            cali_sobre = detail.get("classification", "N/A")
            desc_sobre = detail.get("description", "N/A")
            print(f"   • Project: {project}, Type: {zone_type}, Classification (CALI_SOBRE): {cali_sobre}")
            if buffer_miles is not None: # Check for None explicitly
                print(f"     Buffer: {buffer_miles:.2f} miles, Description: {desc_sobre}")
            else:
                print(f"     Buffer: Not specified, Description: {desc_sobre}")
    else:
        print(f"❌ Analysis failed: {all_types['error']}")
    
    # 2. Test specific location
    print(f"\n" + "="*50)
    print("📍 TESTING SPECIFIC LOCATION")
    print("="*50)
    
    test_coords = (-66.209931, 18.414997)  # Arecibo area - known karst region
    print(f"Testing coordinates: {test_coords}")
    
    location_analysis = analyzer.analyze_comprehensive_karst(
        longitude=test_coords[0], 
        latitude=test_coords[1], 
        search_radius_miles=2.0
    )
    
    if location_analysis["success"]:
        print("✅ Location analysis completed")
        
        # PRAPEC results
        prapec_result = location_analysis["prapec_analysis"]
        print(f"\n🗿 PRAPEC KARST FINDINGS:")
        if prapec_result.get("karst_found"):
            karst_info = prapec_result["karst_info"]
            print(f"   ✅ KARST AREA DETECTED!")
            print(f"   • Name: {karst_info['nombre']}")
            print(f"   • Regulation: {karst_info['regla']}")
            print(f"   • Area: {karst_info['area_hectares']:,.1f} hectares")
        else:
            print(f"   ❌ No PRAPEC karst found within search radius")
        
        # Buffer zone results
        buffer_result = location_analysis["buffer_zone_analysis"]
        print(f"\n📏 BUFFER ZONE FINDINGS:")
        if buffer_result.get("buffer_zones_found"):
            buffer_zones = buffer_result["buffer_zones"]
            print(f"   ✅ {len(buffer_zones)} BUFFER ZONE(S) DETECTED!")
            for zone in buffer_zones:
                print(f"   • Project: {zone['project']}")
                print(f"     Type: {zone['type']}")
                print(f"     Buffer: {zone['buffer_distance_miles']:.2f} miles")
                print(f"     Description: {zone['description']}")
        else:
            print(f"   ❌ No buffer zones found within search radius")
        
        # Combined assessment
        assessment = location_analysis["combined_assessment"]
        print(f"\n⚖️ COMBINED ASSESSMENT:")
        print(f"   • Overall Impact: {assessment['overall_karst_impact'].upper()}")
        print(f"   • Regulatory Zones: {len(assessment['regulatory_zones_identified'])}")
        for zone in assessment["regulatory_zones_identified"]:
            print(f"     - {zone}")
        
        # Regulatory implications
        implications = location_analysis["regulatory_implications"]
        print(f"\n📜 REGULATORY IMPLICATIONS:")
        for impl in implications:
            print(f"   • {impl['regulation_type']} - {impl['impact_level'].upper()} impact")
            print(f"     Authority: {impl['authority']}")
            if 'requirements' in impl:
                print(f"     Requirements: {len(impl['requirements'])} items")
    else:
        print(f"❌ Location analysis failed: {location_analysis['error']}")
    
    print(f"\n" + "="*70)
    print("📊 ANALYSIS COMPLETE")
    print("="*70)
    print("💡 KEY FINDINGS:")
    print("   • Puerto Rico has TWO types of karst regulations:")
    print("     1. PRAPEC (Carso) - Direct karst area regulation")
    print("     2. Zona de Amortiguamiento - Regulated buffer zones") 
    print("   • Buffer zones extend regulatory requirements beyond primary karst areas")
    print("   • Comprehensive analysis requires checking BOTH layer types")
    print("   • Development projects must consider both direct and buffer zone impacts")

if __name__ == "__main__":
    main() 