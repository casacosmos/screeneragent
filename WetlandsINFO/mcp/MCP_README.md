# WetlandsINFO MCP Server

A Model Context Protocol (MCP) server that provides comprehensive wetland data analysis and map generation tools for use with MCP-compliant clients and AI agents.

## 🌿 **Overview**

The WetlandsINFO MCP Server exposes powerful wetland analysis capabilities through the Model Context Protocol, enabling AI agents and applications to:

- Query comprehensive wetland data from authoritative sources
- Generate various types of wetland maps with intelligent formatting
- Perform progressive wetland searches with adaptive buffer sizing
- Access detailed NWI (National Wetlands Inventory) classifications
- Generate regulatory compliance reports

## 🚀 **Quick Start**

### **Starting the Server**

```bash
# Navigate to WetlandsINFO directory
cd WetlandsINFO

# Start with stdio transport (default)
python mcp_server.py

# Start with HTTP transport
python mcp_server.py --transport streamable-http --port 8001
```

### **Basic Usage Example**

```python
# Example coordinates (Puerto Rico wetlands)
coordinates = {
    "longitude": -66.199399,
    "latitude": 18.408303,
    "location_name": "Bayamón, Puerto Rico"
}

# Call wetland analysis tool
result = await client.call_tool("query_wetland_data", coordinates)

# Generate adaptive wetland map
map_result = await client.call_tool("generate_adaptive_wetland_map", coordinates)
```

## 🛠️ **Available Tools**

### **1. `query_wetland_data`**

Query comprehensive wetland data for specific coordinates.

**Parameters:**
- `longitude` (float): Longitude coordinate (-180 to 180)
- `latitude` (float): Latitude coordinate (-90 to 90)  
- `location_name` (string, optional): Descriptive name for the location

**Returns:**
```json
{
  "location": "Location identifier",
  "coordinates": [longitude, latitude],
  "is_in_wetland": true/false,
  "search_summary": {
    "total_wetlands_analyzed": 5,
    "search_radius_used": 0.5
  },
  "key_findings": {
    "wetlands_found": true,
    "wetland_types": ["Emergent", "Forested"],
    "environmental_significance": "High - Critical habitat",
    "regulatory_status": "Direct wetland impacts - permits likely required"
  },
  "data_sources": ["USFWS NWI", "EPA RIBITS", "EPA NHD", "USFWS Riparian"]
}
```

**Search Strategy:**
1. Checks for wetlands at exact coordinates
2. If none found, searches within 0.5 mile radius
3. If still none found, expands to 1.0 mile radius

### **2. `generate_detailed_wetland_map`**

Generate high-resolution detailed wetland map with 0.3 mile buffer.

**Parameters:**
- `longitude` (float): Longitude coordinate
- `latitude` (float): Latitude coordinate
- `location_name` (string, optional): Descriptive name

**Features:**
- High-resolution imagery background
- 0.3 mile buffer radius
- 300 DPI resolution
- Professional legend with wetland symbols
- Scale bar in miles and kilometers

**Use Cases:** Site analysis, regulatory submissions, environmental assessments

### **3. `generate_overview_wetland_map`**

Generate regional overview wetland map with 1.0 mile buffer.

**Parameters:**
- `longitude` (float): Longitude coordinate
- `latitude` (float): Latitude coordinate
- `location_name` (string, optional): Descriptive name

**Features:**
- Topographic background
- 1.0 mile buffer radius
- 250 DPI resolution
- Regional wetland context

**Use Cases:** Regional planning, context analysis, preliminary assessments

### **4. `generate_adaptive_wetland_map`**

Generate intelligent adaptive wetland map with automatic buffer sizing.

**Parameters:**
- `longitude` (float): Longitude coordinate
- `latitude` (float): Latitude coordinate
- `location_name` (string, optional): Descriptive name

**Intelligence:**
- Analyzes wetland presence at location
- Calculates optimal buffer based on nearest wetland distance
- Selects appropriate base map and transparency

**Buffer Logic:**
- Wetlands at exact location: 0.5 mile buffer
- Wetlands found at 0.5 miles: Nearest distance + 1.5 miles buffer
- No wetlands found: 2.0 mile regional view

**Use Cases:** Optimal wetland visualization, context-aware mapping, automated analysis

### **5. `generate_custom_wetland_map`**

Generate custom wetland map with user-specified parameters.

**Parameters:**
- `longitude` (float): Longitude coordinate
- `latitude` (float): Latitude coordinate
- `location_name` (string, optional): Descriptive name
- `buffer_miles` (float): Buffer radius in miles (0.1 to 5.0)
- `base_map` (string): Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
- `wetland_transparency` (float): Wetland layer transparency (0.0 to 1.0)

**Use Cases:** Specific requirements, custom analysis, tailored presentations

## 🌍 **Data Sources**

The MCP server integrates data from multiple authoritative sources:

### **Primary Sources**
- **USFWS National Wetlands Inventory (NWI)**: Comprehensive wetland mapping with standardized classification
- **EPA RIBITS**: Regulatory tracking system for mitigation banks and in-lieu fee programs
- **EPA National Hydrography Dataset (NHD)**: Surface water features and watershed boundaries
- **USFWS Riparian Mapping**: Riparian corridor identification and habitat connectivity

### **Geographic Coverage**
- **United States**: Complete NWI coverage
- **Puerto Rico**: Full wetland inventory (optimized support)
- **US Territories**: Comprehensive data available
- **International**: Limited to available datasets

## ⚙️ **Server Configuration**

### **Transport Options**

**STDIO Transport (Default)**
```bash
python mcp_server.py --transport stdio
```
- Direct process communication
- Ideal for local agents and tools
- Lower latency

**HTTP Transport**
```bash
python mcp_server.py --transport streamable-http --port 8001
```
- Web-based communication
- Accessible via HTTP at `http://localhost:8001/mcp`
- Better for distributed systems

### **Environment Variables**

```bash
# Optional: Configure output directories
export WETLANDS_OUTPUT_DIR="/custom/output/path"
export WETLANDS_LOGS_DIR="/custom/logs/path"

# Optional: Configure service timeouts
export WETLANDS_TIMEOUT=60
export WETLANDS_RETRY_COUNT=3
```

## 📁 **Output Files**

### **Analysis Data**
- **Location**: `WetlandsINFO/logs/`
- **Format**: JSON files with detailed analysis
- **Naming**: `wetland_analysis_[coords]_[timestamp].json`
- **Content**: Complete wetland data, NWI classifications, regulatory implications

### **Generated Maps**
- **Location**: `WetlandsINFO/output/`
- **Format**: High-resolution PDF files
- **Naming**: `[map_type]_[location]_[timestamp].pdf`
- **Resolution**: 250-300 DPI for professional printing

## 🔧 **Integration Examples**

### **LangGraph Agent Integration**

```python
from langgraph.graph import StateGraph
from mcp import Client

# Create MCP client
mcp_client = Client(transport="stdio", 
                   command=["python", "WetlandsINFO/mcp_server.py"])

# Use in LangGraph agent
async def wetland_analysis_node(state):
    coordinates = state["coordinates"]
    
    # Query wetland data
    wetland_data = await mcp_client.call_tool(
        "query_wetland_data", 
        coordinates
    )
    
    # Generate adaptive map if wetlands found
    if wetland_data["key_findings"]["wetlands_found"]:
        map_result = await mcp_client.call_tool(
            "generate_adaptive_wetland_map",
            coordinates
        )
        state["map_generated"] = map_result["success"]
    
    state["wetland_analysis"] = wetland_data
    return state
```

### **Cursor/Claude Integration**

```python
# Example tool call in Cursor/Claude
import subprocess
import json

def analyze_wetlands(longitude, latitude, location_name=None):
    """Analyze wetlands using MCP server"""
    
    # Start MCP server process
    process = subprocess.Popen(
        ["python", "WetlandsINFO/mcp_server.py", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Prepare MCP request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "query_wetland_data",
            "arguments": {
                "longitude": longitude,
                "latitude": latitude,
                "location_name": location_name
            }
        }
    }
    
    # Send request and get response
    stdout, stderr = process.communicate(json.dumps(request))
    return json.loads(stdout)
```

### **HTTP Client Example**

```python
import httpx
import asyncio

async def call_wetland_mcp_http():
    """Call WetlandsINFO MCP server via HTTP"""
    
    async with httpx.AsyncClient() as client:
        # Call query tool
        response = await client.post(
            "http://localhost:8001/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call", 
                "params": {
                    "name": "query_wetland_data",
                    "arguments": {
                        "longitude": -66.199399,
                        "latitude": 18.408303,
                        "location_name": "Puerto Rico Test Site"
                    }
                }
            }
        )
        
        result = response.json()
        print(f"Wetland analysis: {result}")
        
        # Generate adaptive map
        map_response = await client.post(
            "http://localhost:8001/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "generate_adaptive_wetland_map",
                    "arguments": {
                        "longitude": -66.199399,
                        "latitude": 18.408303,
                        "location_name": "Puerto Rico Test Site"
                    }
                }
            }
        )
        
        map_result = map_response.json()
        print(f"Map generation: {map_result}")
```

## 🧪 **Testing**

### **Test Coordinates**

```python
# Puerto Rico (known wetlands)
test_pr = {
    "longitude": -66.199399, 
    "latitude": 18.408303,
    "location_name": "Bayamón, Puerto Rico"
}

# Florida Everglades (extensive wetlands)
test_fl = {
    "longitude": -80.8431,
    "latitude": 25.4663, 
    "location_name": "Everglades National Park"
}

# Urban area (minimal wetlands)
test_urban = {
    "longitude": -74.0060,
    "latitude": 40.7128,
    "location_name": "New York City"
}
```

### **Test Server**

```bash
# Run the example client
python mcp_client_example.py

# Test with curl (HTTP transport)
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "query_wetland_data",
      "arguments": {
        "longitude": -66.199399,
        "latitude": 18.408303,
        "location_name": "Test Location"
      }
    }
  }'
```

## 🔍 **Error Handling**

All tools provide comprehensive error responses:

```json
{
  "success": false,
  "message": "Detailed error description",
  "location": "Location identifier", 
  "coordinates": [longitude, latitude],
  "suggestion": "Helpful suggestion for resolution"
}
```

Common error scenarios:
- Invalid coordinates (out of range)
- Network connectivity issues
- Service unavailability
- Invalid parameter values
- File system permissions

## 📚 **Additional Resources**

- **USFWS Wetlands Mapper**: https://www.fws.gov/wetlands/data/mapper.html
- **EPA Wetlands Information**: https://www.epa.gov/wetlands
- **Clean Water Act Info**: https://www.epa.gov/cwa-404
- **MCP Specification**: https://modelcontextprotocol.io/
- **Wetland Delineation Manual**: https://www.usace.army.mil/

## 📋 **License and Disclaimer**

This tool is for informational and planning purposes. For regulatory determinations, always consult with qualified wetland professionals and obtain official jurisdictional determinations from the U.S. Army Corps of Engineers.

---

**WetlandsINFO MCP Server** - Bringing comprehensive wetland analysis to AI agents and applications through the Model Context Protocol. 