#!/usr/bin/env python3
"""
Wetland Data Query Tool - Simplified Interface

A concise tool to query wetland data and generate reports for any coordinate.
Supports wetland analysis, map generation, and comprehensive reporting.
"""

import sys
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_wetland_location import WetlandLocationAnalyzer, save_results_to_file, generate_summary_report
from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

class WetlandDataQuery:
    """Simplified interface for wetland data queries and map generation"""
    
    def __init__(self):
        self.analyzer = WetlandLocationAnalyzer()
        self.map_generator = WetlandMapGeneratorV3()
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
    
    def query(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Query all wetland data for given coordinates
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            
        Returns:
            Dictionary with all wetland analysis results
        """
        print(f"🌿 Querying wetland data for ({longitude}, {latitude})")
        
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        results = self.analyzer.analyze_location(longitude, latitude, location_name)
        
        # Auto-save results
        save_results_to_file(results)
        
        return results
    
    def generate_detailed_map(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Generate detailed wetland map (0.3 mile buffer, high resolution)
        
        Returns:
            (success: bool, message: str)
        """
        if location_name is None:
            location_name = f"Detailed Wetland Map at ({longitude}, {latitude})"
        
        print(f"🗺️  Generating detailed wetland map for {location_name}")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = f"detailed_wetland_map_{safe_name}_{timestamp}.pdf"
        
        try:
            map_path = self.map_generator.generate_detailed_wetland_map(
                longitude=longitude,
                latitude=latitude,
                location_name=location_name,
                wetland_transparency=0.75
            )
            
            if map_path:
                return True, f"Detailed wetland map saved as: {map_path}"
            else:
                return False, "Failed to generate detailed wetland map"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_overview_map(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Generate overview wetland map with 0.5-mile radius circle and 1.0-mile context area
        
        Returns:
            (success: bool, message: str)
        """
        if location_name is None:
            location_name = f"Wetland Map with 0.5 Mile Circle at ({longitude}, {latitude})"
        
        print(f"🗺️  Generating overview wetland map with 0.5-mile circle for {location_name}")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = f"overview_wetland_map_circle_{safe_name}_{timestamp}.pdf"
        
        try:
            map_path = self.map_generator.generate_overview_wetland_map(
                longitude=longitude,
                latitude=latitude,
                location_name=location_name,
                wetland_transparency=0.8
            )
            
            if map_path:
                return True, f"Overview wetland map with 0.5-mile circle saved as: {map_path}"
            else:
                return False, "Failed to generate overview wetland map with circle"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_adaptive_map(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Generate adaptive wetland map with intelligent buffer sizing based on wetland analysis
        
        Returns:
            (success: bool, message: str)
        """
        if location_name is None:
            location_name = f"Adaptive Wetland Map at ({longitude}, {latitude})"
        
        print(f"🗺️  Generating adaptive wetland map for {location_name}")
        
        try:
            # First analyze the location to determine optimal settings
            print(f"🔍 Analyzing location to determine optimal map settings...")
            results = self.analyzer.analyze_location(longitude, latitude, location_name)
            
            # Determine optimal settings based on analysis results
            if results['is_in_wetland']:
                # If wetlands are present at exact location, use smaller buffer for detail
                buffer_miles = 0.5
                wetland_transparency = 0.75
                base_map = "World_Imagery"
                print(f"🌿 Wetlands at exact location - using detailed view ({buffer_miles} mile buffer)")
            else:
                # If no wetlands at exact location, use buffer based on search results
                search_radius = results['search_summary']['search_radius_used']
                wetlands_found = len(results.get('nearest_wetlands', []))
                
                if wetlands_found > 0:
                    # Calculate buffer based on actual distance to nearest wetland
                    nearest_wetland = results['nearest_wetlands'][0]
                    nearest_distance = nearest_wetland['distance_miles']
                    
                    # Add 1.5 miles to the nearest wetland distance to ensure it's visible with good context
                    buffer_miles = nearest_distance + 1.5
                    
                    # Ensure minimum buffer for good context (at least 1.5 miles)
                    if buffer_miles < 1.5:
                        buffer_miles = 1.5
                    
                    # Ensure maximum buffer for reasonable scale (no more than 4.0 miles)
                    if buffer_miles > 4.0:
                        buffer_miles = 4.0
                    
                    wetland_transparency = 0.8
                    base_map = "World_Imagery"
                    print(f"🔍 Nearest wetland at {nearest_distance} miles - using {buffer_miles} mile buffer")
                else:
                    # No wetlands found even after expanded search, use larger buffer to show regional context
                    buffer_miles = 2.0
                    wetland_transparency = 0.8
                    base_map = "World_Topo_Map"
                    print(f"🔍 No wetlands found within {search_radius} miles - using regional view ({buffer_miles} mile buffer)")
            
            # Generate the map with adaptive configuration
            map_path = self.map_generator.generate_wetland_map_pdf(
                longitude=longitude,
                latitude=latitude,
                location_name=location_name,
                buffer_miles=buffer_miles,
                base_map=base_map,
                dpi=300,
                output_size=(1224, 792),
                include_legend=True,
                wetland_transparency=wetland_transparency
            )
            
            if map_path:
                return True, f"Adaptive wetland map saved as: {map_path} (buffer: {buffer_miles} miles)"
            else:
                return False, "Failed to generate adaptive wetland map"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_custom_map(self, longitude: float, latitude: float, 
                           location_name: Optional[str] = None,
                           buffer_miles: float = 0.5,
                           base_map: str = "World_Imagery",
                           wetland_transparency: float = 0.8) -> Tuple[bool, str]:
        """
        Generate custom wetland map with specified parameters
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            buffer_miles: Buffer radius in miles
            base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
            wetland_transparency: Wetland layer transparency (0.0-1.0)
        
        Returns:
            (success: bool, message: str)
        """
        if location_name is None:
            location_name = f"Custom Wetland Map at ({longitude}, {latitude})"
        
        print(f"🗺️  Generating custom wetland map for {location_name}")
        print(f"📏 Buffer: {buffer_miles} miles, Base: {base_map}, Transparency: {wetland_transparency}")
        
        try:
            map_path = self.map_generator.generate_wetland_map_pdf(
                longitude=longitude,
                latitude=latitude,
                location_name=location_name,
                buffer_miles=buffer_miles,
                base_map=base_map,
                dpi=300,
                output_size=(1224, 792),
                include_legend=True,
                wetland_transparency=wetland_transparency
            )
            
            if map_path:
                return True, f"Custom wetland map saved as: {map_path}"
            else:
                return False, "Failed to generate custom wetland map"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_all_maps(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Tuple[bool, str]]:
        """
        Generate all available map types for the coordinates
        
        Returns:
            Dictionary with results for each map type
        """
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        print(f"🎯 Generating all wetland maps for {location_name}")
        
        results = {}
        
        # Generate each map type
        results['detailed'] = self.generate_detailed_map(longitude, latitude, f"Detailed - {location_name}")
        results['overview'] = self.generate_overview_map(longitude, latitude, f"Overview - {location_name}")
        results['adaptive'] = self.generate_adaptive_map(longitude, latitude, f"Adaptive - {location_name}")
        
        # Summary
        successful = sum(1 for success, _ in results.values() if success)
        print(f"\n✅ Generated {successful}/3 maps successfully")
        
        return results
    
    def comprehensive_analysis(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive wetland analysis including data query and map generation
        
        Returns:
            Dictionary with analysis results and map generation status
        """
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        print(f"🎯 Performing comprehensive wetland analysis for {location_name}")
        
        # Query wetland data
        analysis_results = self.query(longitude, latitude, location_name)
        
        # Generate adaptive map based on analysis
        map_success, map_message = self.generate_adaptive_map(longitude, latitude, location_name)
        
        # Combine results
        comprehensive_results = {
            'analysis': analysis_results,
            'map_generation': {
                'success': map_success,
                'message': map_message
            },
            'summary': {
                'wetlands_found': analysis_results['search_summary']['total_wetlands_analyzed'],
                'is_in_wetland': analysis_results['is_in_wetland'],
                'search_radius_used': analysis_results['search_summary']['search_radius_used'],
                'map_generated': map_success
            }
        }
        
        return comprehensive_results

def main():
    """Command line interface"""
    
    print("🌿 Wetland Data Query Tool")
    print("=" * 40)
    
    # Parse command line arguments
    if len(sys.argv) >= 3:
        try:
            longitude = float(sys.argv[1])
            latitude = float(sys.argv[2])
            location_name = sys.argv[3] if len(sys.argv) > 3 else None
            
            # Check for operation type argument
            operation_type = sys.argv[4].lower() if len(sys.argv) > 4 else 'comprehensive'
            
        except (ValueError, IndexError):
            print("❌ Usage: python main.py <longitude> <latitude> [location_name] [operation_type]")
            print("   Operation types: comprehensive, query, detailed, overview, adaptive, custom, all_maps")
            print("   • overview: Generates map with 0.5-mile radius circle for regulatory buffer analysis")
            return
    else:
        # Interactive mode
        try:
            longitude_input = input("Enter longitude (or press Enter for Puerto Rico default): ").strip()
            longitude = float(longitude_input) if longitude_input else -66.199399
            
            latitude_input = input("Enter latitude (or press Enter for Puerto Rico default): ").strip()
            latitude = float(latitude_input) if latitude_input else 18.408303
            
            location_name = input("Enter location name (optional): ").strip() or None
            if not location_name and longitude == -66.199399 and latitude == 18.408303:
                location_name = "Bayamón, Puerto Rico"
            
            print("\nOperation types:")
            print("  1. Comprehensive analysis (query + adaptive map)")
            print("  2. Query only (wetland data)")
            print("  3. Detailed map (0.3 mile buffer)")
            print("  4. Overview map (0.5 mile circle + 1.0 mile context)")
            print("  5. Adaptive map (intelligent buffer)")
            print("  6. Custom map (specify parameters)")
            print("  7. All maps")
            
            choice = input("Select option (1-7, default=1): ").strip() or "1"
            operation_type = {
                "1": "comprehensive", "2": "query", "3": "detailed", 
                "4": "overview", "5": "adaptive", "6": "custom", "7": "all_maps"
            }.get(choice, "comprehensive")
            
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\n❌ Invalid input or interrupted. Using defaults.")
            longitude, latitude = -66.199399, 18.408303
            location_name = "Bayamón, Puerto Rico"
            operation_type = "comprehensive"
    
    # Initialize query tool
    wetland_query = WetlandDataQuery()
    
    # Execute based on operation type
    if operation_type == "query":
        # Query data only
        results = wetland_query.query(longitude, latitude, location_name)
        generate_summary_report(results)
        print(f"\n✅ Query completed. Found {results['search_summary']['total_wetlands_analyzed']} wetland(s).")
        
    elif operation_type == "detailed":
        success, message = wetland_query.generate_detailed_map(longitude, latitude, location_name)
        print(f"\n{'✅' if success else '❌'} Detailed Map: {message}")
        
    elif operation_type == "overview":
        success, message = wetland_query.generate_overview_map(longitude, latitude, location_name)
        print(f"\n{'✅' if success else '❌'} Overview Map: {message}")
        
    elif operation_type == "adaptive":
        success, message = wetland_query.generate_adaptive_map(longitude, latitude, location_name)
        print(f"\n{'✅' if success else '❌'} Adaptive Map: {message}")
        
    elif operation_type == "custom":
        # Get custom parameters
        try:
            buffer_miles = float(input("Buffer radius in miles (default 0.5): ") or "0.5")
            
            print("Base map options: World_Imagery, World_Topo_Map, World_Street_Map")
            base_map = input("Base map (default World_Imagery): ").strip() or "World_Imagery"
            
            wetland_transparency = float(input("Wetland transparency 0.0-1.0 (default 0.8): ") or "0.8")
            
            success, message = wetland_query.generate_custom_map(
                longitude, latitude, location_name, buffer_miles, base_map, wetland_transparency
            )
            print(f"\n{'✅' if success else '❌'} Custom Map: {message}")
            
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\n❌ Invalid custom parameters. Using defaults.")
            success, message = wetland_query.generate_custom_map(longitude, latitude, location_name)
            print(f"\n{'✅' if success else '❌'} Custom Map: {message}")
        
    elif operation_type == "all_maps":
        # Query data first
        results = wetland_query.query(longitude, latitude, location_name)
        generate_summary_report(results)
        
        # Generate all maps
        map_results = wetland_query.generate_all_maps(longitude, latitude, location_name)
        
        print(f"\n📋 Map Generation Summary:")
        for map_type, (success, message) in map_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {map_type.title()}: {message}")
        
    else:  # "comprehensive"
        # Comprehensive analysis
        comprehensive_results = wetland_query.comprehensive_analysis(longitude, latitude, location_name)
        
        # Display analysis summary
        generate_summary_report(comprehensive_results['analysis'])
        
        # Display map generation result
        map_result = comprehensive_results['map_generation']
        status = "✅" if map_result['success'] else "❌"
        print(f"\n{status} Map Generation: {map_result['message']}")
        
        # Display overall summary
        summary = comprehensive_results['summary']
        print(f"\n📋 Comprehensive Analysis Summary:")
        print(f"   🌿 Wetlands found: {summary['wetlands_found']}")
        print(f"   📍 Location in wetland: {'Yes' if summary['is_in_wetland'] else 'No'}")
        print(f"   📏 Search radius used: {summary['search_radius_used']} miles")
        print(f"   🗺️  Map generated: {'Yes' if summary['map_generated'] else 'No'}")
    
    # Provide additional resources
    print(f"\n📚 Additional Resources:")
    print(f"   • USFWS Wetlands Mapper: https://www.fws.gov/wetlands/data/mapper.html")
    print(f"   • EPA Wetlands Information: https://www.epa.gov/wetlands")
    print(f"   • Clean Water Act Info: https://www.epa.gov/cwa-404")
    print(f"   • Wetland Delineation Manual: https://www.usace.army.mil/Missions/Civil-Works/Regulatory-Program-and-Permits/reg_supp/")
    
    print(f"\n🎯 All operations completed!")

if __name__ == "__main__":
    main() 