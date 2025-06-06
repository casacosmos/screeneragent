#!/usr/bin/env python3
"""
Comprehensive Wetland Analysis Tool

This tool provides comprehensive wetland analysis capabilities following
the same pattern as other environmental analysis tools:
- NWI wetland identification and classification
- Proximity analysis with distance calculations
- Regulatory jurisdiction assessment
- Buffer zone analysis

Supports US locations including Puerto Rico.
"""

import json
import math
from WetlandsINFO.generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3
import shutil

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WetlandArea:
    """Wetland area information"""
    wetland_id: str
    nwi_code: str
    wetland_type: str
    system: str
    subsystem: Optional[str]
    wetland_class: str
    water_regime: str
    area_acres: float
    jurisdiction: str
    habitat_value: str
    vegetation: str
    coordinates: Tuple[float, float]

class WetlandAnalysisTool:
    """Comprehensive wetland analysis tool"""
    
    def __init__(self):
        """Initialize wetland analysis tool"""
        
        # NWI classification system reference
        self.nwi_systems = {
            'E': 'Estuarine',
            'P': 'Palustrine', 
            'L': 'Lacustrine',
            'R': 'Riverine',
            'M': 'Marine'
        }
        
        self.nwi_classes = {
            'EM': 'Emergent Wetland',
            'FO': 'Forested Wetland',
            'SS': 'Scrub-Shrub Wetland',
            'UB': 'Unconsolidated Bottom',
            'AB': 'Aquatic Bed',
            'OW': 'Open Water'
        }
        
        self.water_regimes = {
            'A': 'Temporarily Flooded',
            'B': 'Saturated',
            'C': 'Seasonally Flooded',
            'F': 'Semipermanently Flooded',
            'G': 'Intermittently Exposed',
            'H': 'Permanently Flooded',
            'J': 'Intermittently Flooded',
            'K': 'Artificially Flooded',
            'P': 'Irregularly Flooded',
            'Q': 'Regularly Flooded',
            'R': 'Seasonally Flooded',
            'S': 'Continuously Saturated',
            'T': 'Temporarily Flooded',
            'V': 'Permanently Flooded'
        }
        
        # Mock wetland database
        self._initialize_wetland_database()
        
        logger.info("🌿 Wetland Analysis Tool initialized")
    
    def _initialize_wetland_database(self):
        """Initialize mock wetland database with detailed NWI attributes"""
        self.wetland_areas = [
            WetlandArea(
                wetland_id="NWI_PR_001",
                nwi_code="E2EM1P",
                wetland_type="Estuarine Emergent Wetland",
                system="Estuarine",
                subsystem="Intertidal",
                wetland_class="Emergent Wetland", 
                water_regime="Irregularly Flooded",
                area_acres=2.3,
                jurisdiction="Federal - USACE",
                habitat_value="High - Migratory bird habitat",
                vegetation="Salt marsh cordgrass dominant",
                coordinates=(-66.715, 18.403)
            ),
            WetlandArea(
                wetland_id="NWI_PR_002", 
                nwi_code="PFO1A",
                wetland_type="Palustrine Forested Wetland",
                system="Palustrine",
                subsystem=None,
                wetland_class="Forested Wetland",
                water_regime="Temporarily Flooded",
                area_acres=1.8,
                jurisdiction="State/Federal",
                habitat_value="High - Forest wetland habitat",
                vegetation="Mixed forested wetland",
                coordinates=(-66.720, 18.410)
            ),
            WetlandArea(
                wetland_id="NWI_PR_003",
                nwi_code="PUBHh", 
                wetland_type="Palustrine Unconsolidated Bottom",
                system="Palustrine",
                subsystem=None,
                wetland_class="Unconsolidated Bottom",
                water_regime="Permanently Flooded",
                area_acres=0.9,
                jurisdiction="Federal - USACE",
                habitat_value="Medium - Waterfowl habitat",
                vegetation="Open water with submerged vegetation",
                coordinates=(-66.705, 18.400)
            ),
            WetlandArea(
                wetland_id="NWI_PR_004",
                nwi_code="E2FO1N",
                wetland_type="Estuarine Forested Wetland",
                system="Estuarine", 
                subsystem="Intertidal",
                wetland_class="Forested Wetland",
                water_regime="Regularly Flooded",
                area_acres=4.2,
                jurisdiction="Federal - USACE",
                habitat_value="Very High - Critical mangrove ecosystem",
                vegetation="Mangrove forest",
                coordinates=(-66.650, 18.450)
            )
        ]
    
    async def analyze_wetland_location(self, lat: float, lng: float, 
                                     buffer_miles: float = 0.5) -> Dict[str, Any]:
        """
        Analyze wetland location with comprehensive assessment
        
        Args:
            lat: Latitude
            lng: Longitude
            buffer_miles: Search buffer radius in miles
            
        Returns:
            Dictionary with wetland analysis results
        """
        logger.info(f"🌿 Analyzing wetland location at {lat:.6f}, {lng:.6f}")
        
        try:
            # Step 1: Check if coordinates are directly in wetlands
            logger.info("   🔍 Step 1: Checking for wetlands at exact coordinates...")
            wetlands_at_location = await self._check_wetlands_at_coordinates(lat, lng)
            
            # Step 2: Search within 0.5 mile radius if not at exact location
            nearby_wetlands = []
            if not wetlands_at_location:
                logger.info("   🔍 Step 2: Searching for wetlands within 0.5 mile radius...")
                nearby_wetlands = await self._find_wetlands_in_radius(lat, lng, 0.5)
            
            # Step 3: Find nearest wetland if none in standard radius
            nearest_wetland = None
            if not wetlands_at_location and not nearby_wetlands:
                logger.info("   🔍 Step 3: Searching for nearest wetland...")
                nearest_wetland = await self._find_nearest_wetland(lat, lng)
            
            # Analyze results
            analysis = self._analyze_wetland_results(
                wetlands_at_location, nearby_wetlands, nearest_wetland, lat, lng, buffer_miles
            )
            
            return {
                'location': {
                    'latitude': lat,
                    'longitude': lng
                },
                'wetland_analysis': analysis,
                'query_timestamp': datetime.now().isoformat(),
                'generated_files': []
            }
            
        except Exception as e:
            logger.error(f"❌ Error in wetland analysis: {e}")
            raise
    
    async def _check_wetlands_at_coordinates(self, lat: float, lng: float) -> List[Dict[str, Any]]:
        """Check if coordinates intersect with wetland areas"""
        await asyncio.sleep(0.2)  # Simulate API delay
        
        intersecting_wetlands = []
        tolerance = 0.005  # ~500m tolerance
        
        for wetland in self.wetland_areas:
            wetland_lng, wetland_lat = wetland.coordinates
            if (abs(wetland_lat - lat) < tolerance and 
                abs(wetland_lng - lng) < tolerance):
                intersecting_wetlands.append(self._format_wetland_data(wetland, 0.0, "At location"))
        
        return intersecting_wetlands
    
    async def _find_wetlands_in_radius(self, lat: float, lng: float, 
                                     radius_miles: float) -> List[Dict[str, Any]]:
        """Find wetlands within specified radius"""
        await asyncio.sleep(0.3)  # Simulate API delay
        
        wetlands_in_radius = []
        
        for wetland in self.wetland_areas:
            wetland_lng, wetland_lat = wetland.coordinates
            distance = self._calculate_distance_miles(lat, lng, wetland_lat, wetland_lng)
            
            if distance <= radius_miles:
                bearing = self._calculate_bearing(lat, lng, wetland_lat, wetland_lng)
                wetlands_in_radius.append(self._format_wetland_data(wetland, distance, bearing))
        
        # Sort by distance
        wetlands_in_radius.sort(key=lambda x: x['distance_miles'])
        return wetlands_in_radius
    
    async def _find_nearest_wetland(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """Find the nearest wetland beyond standard search radius"""
        await asyncio.sleep(0.2)  # Simulate API delay
        
        extended_search_radius = 5.0  # miles
        nearest = None
        min_distance = float('inf')
        
        for wetland in self.wetland_areas:
            wetland_lng, wetland_lat = wetland.coordinates
            distance = self._calculate_distance_miles(lat, lng, wetland_lat, wetland_lng)
            
            if distance < min_distance and distance <= extended_search_radius:
                min_distance = distance
                bearing = self._calculate_bearing(lat, lng, wetland_lat, wetland_lng)
                nearest = self._format_wetland_data(wetland, distance, bearing)
        
        return nearest
    
    def _format_wetland_data(self, wetland: WetlandArea, distance: float, bearing: str) -> Dict[str, Any]:
        """Format wetland data for output"""
        return {
            'wetland_details': {
                'wetland_id': wetland.wetland_id,
                'nwi_code': wetland.nwi_code,
                'wetland_type': wetland.wetland_type,
                'system': wetland.system,
                'subsystem': wetland.subsystem,
                'wetland_class': wetland.wetland_class,
                'water_regime': wetland.water_regime,
                'area_acres': wetland.area_acres,
                'jurisdiction': wetland.jurisdiction,
                'habitat_value': wetland.habitat_value,
                'vegetation': wetland.vegetation
            },
            'distance_miles': round(distance, 2),
            'bearing': bearing,
            'coordinates': [wetland.coordinates[0], wetland.coordinates[1]]
        }
    
    def _analyze_wetland_results(self, wetlands_at_location: List, nearby_wetlands: List, 
                               nearest_wetland: Optional[Dict], lat: float, lng: float,
                               buffer_miles: float) -> Dict[str, Any]:
        """Analyze wetland results and generate assessment"""
        
        if wetlands_at_location:
            analysis_type = "direct_intersection"
            environmental_significance = "High - Direct wetland intersection"
            regulatory_assessment = {
                "clean_water_act_section_404": True,
                "usace_jurisdiction": True,
                "permit_requirements": ["Section 404 permit required for any disturbance"],
                "impact_level": "High - Direct wetland impacts"
            }
            recommendations = [
                "🚨 DIRECT WETLAND IMPACT: Location intersects with wetland boundaries",
                "⚖️ Federal jurisdiction applies - permits required before any development",
                "📋 Immediate wetland delineation study required",
                "📞 Contact USACE for Section 404 permit pre-application consultation",
                "🌱 Consider project redesign to avoid wetland impacts"
            ]
        
            return {
                    "location_coordinates": [lng, lat],
                "analysis_timestamp": datetime.now().isoformat(),
                    "query_buffer_miles": buffer_miles,
                    "analysis_type": analysis_type,
                    "is_in_wetland": True,
                    "wetlands_at_location": wetlands_at_location,
                    "nearby_wetlands": [],
                    "nearest_wetland": None,
                    "environmental_significance": environmental_significance,
                    "regulatory_assessment": regulatory_assessment,
                    "recommendations": recommendations
            }
            
        elif nearby_wetlands:
            nearest_distance = min(w["distance_miles"] for w in nearby_wetlands)
            analysis_type = "proximity_within_buffer"
            environmental_significance = f"Medium-High - Wetlands within {nearest_distance:.2f} miles"
            regulatory_assessment = {
                "clean_water_act_section_404": False,
                "usace_jurisdiction": False,
                "permit_requirements": ["Potential buffer requirements", "Impact assessment recommended"],
                "impact_level": f"Medium - Wetlands within {nearest_distance:.2f} miles"
            }
            recommendations = [
                f"📏 {len(nearby_wetlands)} wetland(s) identified within 0.5 mile radius",
                f"⚠️ Nearest wetland: {nearest_distance:.2f} miles away",
                "📋 Consider wetland buffer requirements during project planning",
                "🔍 Assess potential indirect impacts to nearby wetlands",
                "📞 Consult with environmental specialists for project-specific guidance"
            ]
            
            return {
                "location_coordinates": [lng, lat],
                "analysis_timestamp": datetime.now().isoformat(),
                "query_buffer_miles": buffer_miles,
                "analysis_type": analysis_type,
                "is_in_wetland": False,
                "wetlands_at_location": [],
                "nearby_wetlands": nearby_wetlands,
                "nearest_wetland": None,
                "environmental_significance": environmental_significance,
                "regulatory_assessment": regulatory_assessment,
                "recommendations": recommendations
            }
            
        elif nearest_wetland:
            analysis_type = "nearest_wetland_identified"
            environmental_significance = f"Low-Medium - Nearest wetland {nearest_wetland['distance_miles']:.2f} miles away"
            regulatory_assessment = {
                "clean_water_act_section_404": False,
                "usace_jurisdiction": False,
                "permit_requirements": [],
                "impact_level": "Low - No immediate wetland concerns"
            }
            recommendations = [
                f"📏 Nearest wetland: {nearest_wetland['distance_miles']:.2f} miles to the {nearest_wetland['bearing']}",
                f"🌿 Wetland type: {nearest_wetland['wetland_details']['wetland_type']}",
                "✅ No immediate wetland regulatory concerns identified",
                "📋 Standard environmental due diligence recommended",
                "🔍 Site-specific assessment may still be advisable for large projects"
            ]
            
            return {
                "location_coordinates": [lng, lat],
                "analysis_timestamp": datetime.now().isoformat(),
                "query_buffer_miles": buffer_miles,
                "analysis_type": analysis_type,
                "is_in_wetland": False,
                "wetlands_at_location": [],
                "nearby_wetlands": [],
                "nearest_wetland": nearest_wetland,
                "environmental_significance": environmental_significance,
                "regulatory_assessment": regulatory_assessment,
                "recommendations": recommendations
            }
            
        else:
            analysis_type = "no_wetlands_found"
            environmental_significance = "Low - No wetlands identified in search area"
            regulatory_assessment = {
            "clean_water_act_section_404": False,
            "usace_jurisdiction": False,
                "permit_requirements": [],
                "impact_level": "Low - No wetland impacts expected"
            }
            recommendations = [
                "✅ No wetlands identified within extended search radius",
                "📋 Standard environmental assessment recommended",
                "🔍 Professional wetland delineation may still be advisable for regulatory certainty",
                "💧 Implement stormwater best management practices"
            ]
            
            return {
                "location_coordinates": [lng, lat],
                "analysis_timestamp": datetime.now().isoformat(),
                "query_buffer_miles": buffer_miles,
                "analysis_type": analysis_type,
                "is_in_wetland": False,
                "wetlands_at_location": [],
                "nearby_wetlands": [],
                "nearest_wetland": None,
                "environmental_significance": environmental_significance,
                "regulatory_assessment": regulatory_assessment,
                "recommendations": recommendations
            }
    
    def _calculate_distance_miles(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lng1: float, lat2: float, lng2: float) -> str:
        """Calculate compass bearing from point 1 to point 2"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng = math.radians(lng2 - lng1)
        
        x = math.sin(delta_lng) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng))
        
        bearing = math.degrees(math.atan2(x, y))
        bearing = (bearing + 360) % 360
        
        # Convert to compass direction
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(bearing / 22.5) % 16
        
        return directions[index]
    
    async def generate_wetland_map(self, lat: float, lng: float, output_dir: Path) -> Optional[str]:
        """Generate adaptive wetland map using WetlandMapGeneratorV3"""
        logger.info(f"🗺️ Generating wetland map for {lat:.6f}, {lng:.6f}")
        try:
            map_generator = WetlandMapGeneratorV3()
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{lat:.5f}_{lng:.5f}".replace('.', 'p').replace('-', 'neg')
            map_filename = output_dir / f"wetland_map_{safe_name}_{timestamp}.png"

            generated_map_path = map_generator.generate_wetland_map_pdf(
                longitude=lng,
                latitude=lat,
                location_name=f"Wetland Map {safe_name}",
                buffer_miles=0.5,
                base_map="World_Imagery",
                dpi=300,
                output_size=(1224, 792),
                include_legend=True,
                wetland_transparency=0.75,
                output_format="PNG",
                output_filename=map_filename.name
            )

            # Move the file to target location if needed
            if generated_map_path and Path(generated_map_path) != map_filename:
                try:
                    shutil.move(generated_map_path, map_filename)
                    return str(map_filename)
                except Exception as e:
                    logger.warning(f"⚠️ Could not move file to maps dir: {e}")
                    return str(generated_map_path)
            return str(map_filename)
        except Exception as e:
            logger.error(f"❌ Map generation failed: {e}")
            return None


async def main():
    """Test the wetland analysis tool"""
    tool = WetlandAnalysisTool()
    
    # Test Puerto Rico coordinates
    result = await tool.analyze_wetland_location(18.4058, -66.7135)
    
    print("🌿 Wetland Analysis Results:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

COMPREHENSIVE_WETLAND_TOOL = WetlandAnalysisTool() 