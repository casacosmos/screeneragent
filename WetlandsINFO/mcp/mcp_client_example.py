#!/usr/bin/env python3
"""
Example MCP Client for WetlandsINFO

This script demonstrates how to use the WetlandsINFO MCP server
to query wetland data and generate maps.

Usage:
    python mcp_client_example.py
"""

import asyncio
import json
from typing import Dict, Any

# This is a simple example - in practice you'd use an MCP client library
# or connect via the transport protocol

async def simulate_mcp_calls():
    """Simulate MCP tool calls (replace with actual MCP client implementation)"""
    
    print("🌿 WetlandsINFO MCP Client Example")
    print("=" * 50)
    
    # Example coordinates (Puerto Rico)
    test_coordinates = {
        "longitude": -66.199399,
        "latitude": 18.408303,
        "location_name": "Bayamón, Puerto Rico"
    }
    
    print(f"Testing with coordinates: {test_coordinates}")
    
    # Simulate tool calls (in actual implementation, these would be MCP calls)
    print("\n1. Querying wetland data...")
    print("   Tool: query_wetland_data")
    print("   Expected: Comprehensive wetland analysis with NWI data")
    
    print("\n2. Generating overview map...")
    print("   Tool: generate_overview_wetland_map")
    print("   Expected: Regional map with 1.0 mile buffer")
    
    print("\n3. Generating adaptive map...")
    print("   Tool: generate_adaptive_wetland_map")
    print("   Expected: Intelligent map with optimal buffer sizing")
    
    print("\n4. Generating custom map...")
    print("   Tool: generate_custom_wetland_map")
    print("   Parameters: buffer_miles=0.8, base_map='World_Topo_Map'")
    print("   Expected: Custom map with specified parameters")
    
    print("\n" + "=" * 50)
    print("📋 MCP Server Integration Guide:")
    print("\n1. Start the MCP server:")
    print("   cd WetlandsINFO")
    print("   python mcp_server.py --transport stdio")
    print("   # or for HTTP:")
    print("   python mcp_server.py --transport streamable-http --port 8001")
    
    print("\n2. Connect MCP client:")
    print("   # For stdio transport:")
    print("   subprocess.run(['python', 'mcp_server.py', '--transport', 'stdio'])")
    print("   # For HTTP transport:")
    print("   # Connect to http://localhost:8001/mcp")
    
    print("\n3. Available tools:")
    tools = [
        "query_wetland_data", 
        "generate_overview_wetland_map",
        "generate_adaptive_wetland_map",
        "generate_custom_wetland_map"
    ]
    for tool in tools:
        print(f"   • {tool}")
    
    print("\n4. Tool parameters:")
    print("   All tools accept: longitude, latitude, location_name (optional)")
    print("   Custom map also accepts: buffer_miles, base_map, wetland_transparency")
    
    print("\n5. Expected outputs:")
    print("   • JSON responses with success status and details")
    print("   • Generated PDF maps in output/ directory")
    print("   • Saved analysis data in logs/ directory")
    
    print("\n6. Data sources integrated:")
    print("   • USFWS National Wetlands Inventory (NWI)")
    print("   • EPA RIBITS")
    print("   • EPA National Hydrography Dataset (NHD)")
    print("   • USFWS Riparian Mapping")

def main():
    """Main function"""
    asyncio.run(simulate_mcp_calls())

if __name__ == "__main__":
    main() 