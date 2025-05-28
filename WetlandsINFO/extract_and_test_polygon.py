#!/usr/bin/env python3
"""
Extract polygon from EPA NEPAssist data and test wetland analysis
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_wetland_location import WetlandLocationAnalyzer

# The provided data
data = [{"extent":{"spatialReference":{"latestWkid":3857,"wkid":102100},"xmin":-7370365.25011708,"ymin":2084823.7874285087,"xmax":-7368326.531253234,"ymax":2085815.0801391082},"basemap":"Imagery","layers":[{"id":"Boundaries_2295","title":"Boundaries","type":"map-image","url":"https://geopub.epa.gov/arcgis/rest/services/NEPAssist/Boundaries/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"NonattainmentAreas_1475","title":"Non-attainment Areas","type":"map-image","url":"https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"ejscreen_indexes_usa_2024_public_6969","title":"EJScreen Indexes (2024 National)","type":"map-image","url":"https://geopub.epa.gov/arcgis/rest/services/ejscreen/ejscreen_indexes_usa_2024_public/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"Water_4435","title":"Water","type":"map-image","url":"https://geopub.epa.gov/arcgis/rest/services/NEPAssist/Water/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"Transportation_913","title":"Transportation","type":"map-image","url":"https://geopub.epa.gov/arcgis/rest/services/NEPAssist/Transportation/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"Places_3388","title":"Places","type":"map-image","url":"https://geopub.epa.gov/arcgis/rest/services/NEPAssist/Places/MapServer","visible":True,"opacity":1,"layers":[],"layerType":"webmaplayer"},{"id":"imageLayer","type":"graphics","title":None,"visible":True,"graphics":[]},{"id":"templayer","type":"graphics","title":None,"visible":True,"graphics":[]},{"id":"identifyLayer","type":"graphics","title":None,"visible":True,"graphics":[]},{"id":"tempidlayer","type":"graphics","title":None,"visible":True,"graphics":[]},{"id":"Project2","title":"Site","type":"feature","visible":True,"opacity":1,"objectIdField":"id","geometryType":"polyline","fields":[{"alias":"id","editable":True,"length":-1,"name":"id","nullable":True,"type":"esriFieldTypeOID"},{"alias":"gtype","editable":True,"length":-1,"name":"gtype","nullable":True,"type":"esriFieldTypeString"},{"alias":"descinfo","editable":True,"length":-1,"name":"descinfo","nullable":True,"type":"esriFieldTypeString"},{"alias":"radius","editable":True,"length":-1,"name":"radius","nullable":True,"type":"esriFieldTypeString"},{"alias":"unit","editable":True,"length":-1,"name":"unit","nullable":True,"type":"esriFieldTypeString"},{"alias":"hasBuffer","editable":True,"length":-1,"name":"hasBuffer","nullable":True,"type":"esriFieldTypeString"},{"alias":"ptitle","editable":True,"length":-1,"name":"ptitle","nullable":True,"type":"esriFieldTypeString"}],"layerType":"digitize","renderer":{"type":"simple","symbol":{"type":"esriSLS","color":[255,0,0,255],"width":2,"style":"esriSLSSolid"}},"source":[{"geometry":{"spatialReference":{"latestWkid":3857,"wkid":102100},"paths":[[[-7369356.4405632,2085122.7676554795],[-7369404.213705879,2085290.769898201],[-7369449.598191424,2085360.8371255335],[-7369418.545648683,2085356.856054609],[-7369391.474176866,2085350.4863265504],[-7369371.568749347,2085342.524111805],[-7369354.848149409,2085342.524111805],[-7369338.127549471,2085342.524111805],[-7369326.184263801,2085347.301426073],[-7369316.629635265,2085352.0787403411],[-7369305.482520043,2085356.856054609],[-7369295.13172106,2085356.856054609],[-7369280.799778256,2085356.0598112657],[-7369267.264005899,2085349.690083207],[-7369252.135892648,2085348.0976694163],[-7369225.860664174,2085348.8938398638],[-7369206.751407103,2085349.690083207],[-7369187.6421500305,2085354.467397475],[-7369170.921550093,2085360.8371255335],[-7369149.423635887,2085371.1879974129],[-7369089.707207538,2085147.4504701626],[-7369356.4405632,2085123.5638988228]]]},"symbol":{"type":"esriSLS","color":[255,0,0,255],"width":2,"style":"esriSLSSolid"},"attributes":{"id":2,"gtype":"polyline","descinfo":"Length 0.63 miles","radius":"","unit":"miles","hasBuffer":"true","ptitle":"Site"}}]}],"graphics":[],"name":"Thermo Warehouse"}]

def convert_web_mercator_to_wgs84(x, y):
    """Convert Web Mercator (EPSG:3857) coordinates to WGS84 (EPSG:4326)"""
    import math
    
    # Constants for Web Mercator to WGS84 conversion
    EARTH_RADIUS = 6378137.0  # Earth's radius in meters
    
    # Convert x (longitude)
    lon = (x / EARTH_RADIUS) * (180.0 / math.pi)
    
    # Convert y (latitude)
    lat = (y / EARTH_RADIUS) * (180.0 / math.pi)
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    
    return lon, lat

def extract_polygon_from_data(data):
    """Extract polygon coordinates from the provided data structure"""
    
    # Find the Site layer
    for item in data:
        if 'layers' in item:
            for layer in item['layers']:
                if layer.get('id') == 'Project2' and layer.get('title') == 'Site':
                    # Extract the polyline coordinates
                    if 'source' in layer and len(layer['source']) > 0:
                        geometry = layer['source'][0]['geometry']
                        if 'paths' in geometry and len(geometry['paths']) > 0:
                            # Get the first path (polyline)
                            path = geometry['paths'][0]
                            
                            # Convert Web Mercator to WGS84
                            wgs84_coords = []
                            for coord in path:
                                lon, lat = convert_web_mercator_to_wgs84(coord[0], coord[1])
                                wgs84_coords.append((lon, lat))
                            
                            # The polyline is already closed (first and last points are the same)
                            # So we can use it as a polygon
                            # Get the site name from the top level
                            site_name = item.get('name', 'Unknown Site')
                            return wgs84_coords, site_name
    
    return None, None

def main():
    """Extract polygon and run wetland analysis"""
    
    print("🔍 Extracting polygon from EPA NEPAssist data...")
    
    # Extract polygon coordinates
    polygon_coords, site_name = extract_polygon_from_data(data)
    
    if polygon_coords:
        print(f"✅ Successfully extracted polygon for: {site_name}")
        print(f"📐 Polygon has {len(polygon_coords)} vertices")
        
        # Show first few coordinates
        print("\n📍 First 5 coordinates (WGS84):")
        for i, (lon, lat) in enumerate(polygon_coords[:5]):
            print(f"   {i+1}. Longitude: {lon:.6f}, Latitude: {lat:.6f}")
        
        # Calculate extent
        lons = [coord[0] for coord in polygon_coords]
        lats = [coord[1] for coord in polygon_coords]
        
        print(f"\n📊 Polygon extent:")
        print(f"   West:  {min(lons):.6f}")
        print(f"   East:  {max(lons):.6f}")
        print(f"   South: {min(lats):.6f}")
        print(f"   North: {max(lats):.6f}")
        
        # Run wetland analysis
        print(f"\n{'='*80}")
        print("🌿 Running wetland analysis for the polygon...")
        print(f"{'='*80}")
        
        analyzer = WetlandLocationAnalyzer()
        results = analyzer.analyze_polygon(polygon_coords, site_name)
        
        # Generate summary report
        from query_wetland_location import generate_summary_report, save_results_to_file
        generate_summary_report(results)
        
        # Save results
        print("\n💾 Saving results...")
        filepath = save_results_to_file(results)
        
        print(f"\n✅ Analysis complete!")
        
    else:
        print("❌ Could not extract polygon from the provided data")

if __name__ == "__main__":
    main() 