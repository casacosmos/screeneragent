# WetlandsINFO Tools for LangGraph Agents

This module provides LangGraph-compatible tools for comprehensive wetland data analysis and map generation. The tools are designed to work seamlessly with LangGraph agents and provide structured, actionable wetland information.

## 🌿 **Available Tools**

### **1. `query_wetland_data`**
Query comprehensive wetland data for specific coordinates.

**Purpose**: Retrieve detailed wetland information from multiple authoritative sources
**Data Sources**: 
- USFWS National Wetlands Inventory (NWI)
- EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)
- EPA National Hydrography Dataset (NHD)
- USFWS Riparian Mapping

**Search Strategy**:
- Checks for wetlands at exact coordinates
- If none found, searches within 0.5 mile radius
- If still none found, expands to 1.0 mile radius

**Returns**:
```python
{
    "location": "Location identifier",
    "coordinates": (longitude, latitude),
    "is_in_wetland": bool,
    "search_summary": {
        "total_wetlands_analyzed": int,
        "search_radius_used": float
    },
    "key_findings": {
        "wetlands_found": bool,
        "wetland_types": ["list", "of", "types"],
        "environmental_significance": "string",
        "regulatory_status": "string"
    },
    "data_sources": ["list", "of", "sources"]
}
```

### **2. `generate_detailed_wetland_map`**
Generate high-resolution detailed wetland map with 0.3 mile buffer.

**Purpose**: Create detailed site-specific wetland maps for analysis and regulatory submissions
**Features**:
- High-resolution imagery background
- 0.3 mile buffer radius
- 300 DPI resolution
- Professional legend with wetland symbols
- Scale bar in miles and kilometers

**Use Cases**: Site analysis, regulatory submissions, environmental assessments

**Returns**:
```python
{
    "success": bool,
    "message": "Status message",
    "filename": "path/to/generated/map.pdf",
    "map_settings": {
        "buffer_miles": 0.3,
        "base_map": "World_Imagery",
        "resolution_dpi": 300,
        "wetland_transparency": 0.75
    },
    "document_type": "High-Resolution Wetland Analysis Map"
}
```

### **3. `generate_overview_wetland_map`**
Generate regional overview wetland map with 1.0 mile buffer.

**Purpose**: Provide regional wetland context for planning and preliminary assessments
**Features**:
- Topographic background
- 1.0 mile buffer radius
- 250 DPI resolution
- Regional wetland context
- Professional legend and scale bar

**Use Cases**: Regional planning, context analysis, preliminary assessments

**Returns**:
```python
{
    "success": bool,
    "message": "Status message",
    "filename": "path/to/generated/map.pdf",
    "map_settings": {
        "buffer_miles": 1.0,
        "base_map": "World_Topo_Map",
        "resolution_dpi": 250,
        "wetland_transparency": 0.8
    },
    "coverage_area": "3.14 square miles"
}
```

### **4. `generate_adaptive_wetland_map`**
Generate intelligent adaptive wetland map with automatic buffer sizing.

**Purpose**: Automatically determine optimal map settings based on wetland analysis
**Intelligence**:
- Analyzes wetland presence at location
- Calculates optimal buffer based on nearest wetland distance
- Selects appropriate base map and transparency
- Ensures wetlands are visible with good context

**Buffer Logic**:
- Wetlands at exact location: 0.5 mile buffer
- Wetlands found at 0.5 miles: Nearest distance + 1.5 miles buffer
- No wetlands found: 2.0 mile regional view

**Use Cases**: Optimal wetland visualization, context-aware mapping, automated analysis

**Returns**:
```python
{
    "success": bool,
    "message": "Status message",
    "filename": "path/to/generated/map.pdf",
    "adaptive_settings": {
        "buffer_miles": float,
        "base_map": "string",
        "reasoning": "Explanation of settings chosen"
    },
    "wetland_analysis": {
        "is_in_wetland": bool,
        "total_wetlands_found": int,
        "nearest_distance": float
    }
}
```

### **5. `generate_custom_wetland_map`**
Generate custom wetland map with user-specified parameters.

**Purpose**: Create maps with specific requirements and custom settings
**Customizable Parameters**:
- Buffer radius (0.1 to 5.0 miles)
- Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
- Wetland layer transparency (0.0 to 1.0)
- High-resolution output (300 DPI)

**Parameter Validation**: Automatically validates and adjusts parameters to valid ranges

**Use Cases**: Specific requirements, custom analysis, tailored presentations

**Returns**:
```python
{
    "success": bool,
    "message": "Status message",
    "filename": "path/to/generated/map.pdf",
    "custom_settings": {
        "buffer_miles": float,
        "base_map": "string",
        "wetland_transparency": float,
        "coverage_area": "X.XX square miles"
    },
    "validation_notes": ["list", "of", "adjustments"]
}
```

## 🚀 **Usage Examples**

### **Basic Import and Setup**
```python
from WetlandsINFO.tools import WETLAND_TOOLS, query_wetland_data

# Use with LangGraph
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(WETLAND_TOOLS)

# Or use individual tools
result = query_wetland_data.invoke({
    "longitude": -66.199399,
    "latitude": 18.408303,
    "location_name": "Bayamón, Puerto Rico"
})
```

### **LangGraph Agent Integration**
```python
from langgraph.graph import StateGraph
from WetlandsINFO.tools import WETLAND_TOOLS

# Create agent with wetland tools
def create_wetland_agent():
    graph = StateGraph(AgentState)
    
    # Add tool node with wetland tools
    graph.add_node("tools", ToolNode(WETLAND_TOOLS))
    
    # Add agent logic
    graph.add_node("agent", agent_node)
    
    # Define edges
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", "agent")
    
    return graph.compile()
```

### **Coordinate Input Formats**
```python
# Puerto Rico coordinates
puerto_rico = {
    "longitude": -66.199399,
    "latitude": 18.408303,
    "location_name": "Bayamón, Puerto Rico"
}

# Florida Everglades coordinates
everglades = {
    "longitude": -80.8431,
    "latitude": 25.4663,
    "location_name": "Everglades National Park"
}

# Custom map with specific settings
custom_map = {
    "longitude": -66.199399,
    "latitude": 18.408303,
    "location_name": "Custom Analysis Site",
    "buffer_miles": 1.5,
    "base_map": "World_Topo_Map",
    "wetland_transparency": 0.6
}
```

## 📊 **Tool Input Schemas**

### **CoordinateInput** (Used by most tools)
```python
class CoordinateInput(BaseModel):
    longitude: float  # Required: -180 to 180
    latitude: float   # Required: -90 to 90
    location_name: Optional[str] = None  # Optional descriptive name
```

### **CustomMapInput** (Used by generate_custom_wetland_map)
```python
class CustomMapInput(BaseModel):
    longitude: float  # Required: -180 to 180
    latitude: float   # Required: -90 to 90
    location_name: Optional[str] = None
    buffer_miles: float = 0.5  # 0.1 to 5.0 miles
    base_map: str = "World_Imagery"  # World_Imagery, World_Topo_Map, World_Street_Map
    wetland_transparency: float = 0.8  # 0.0 to 1.0
```

## 🔍 **Error Handling**

All tools include comprehensive error handling:

```python
{
    "success": False,
    "message": "Detailed error description",
    "location": "Location identifier",
    "coordinates": (longitude, latitude),
    "suggestion": "Helpful suggestion for resolution"
}
```

Common error scenarios:
- Invalid coordinates (out of range)
- Network connectivity issues
- Service unavailability
- Invalid parameter values
- File system permissions

## 📁 **Output Files**

### **Data Query Results**
- **Location**: `WetlandsINFO/logs/`
- **Format**: JSON files with detailed analysis
- **Naming**: `wetland_analysis_[coords]_[timestamp].json`
- **Summary**: `wetland_analysis_[coords]_[timestamp]_summary.json`

### **Generated Maps**
- **Location**: `WetlandsINFO/output/`
- **Format**: High-resolution PDF files
- **Naming**: `[map_type]_[location]_[timestamp].pdf`
- **Resolution**: 250-300 DPI for professional printing

## 🌍 **Supported Regions**

The tools work globally but are optimized for:
- **United States**: Complete NWI coverage
- **Puerto Rico**: Full wetland inventory
- **US Territories**: Comprehensive data available
- **International**: Limited to available datasets

## 📋 **Data Sources and Accuracy**

### **Primary Sources**
1. **USFWS National Wetlands Inventory (NWI)**
   - Most comprehensive wetland mapping
   - Updated regularly
   - Standardized classification system

2. **EPA RIBITS**
   - Regulatory tracking system
   - Mitigation bank information
   - In-lieu fee programs

3. **EPA National Hydrography Dataset (NHD)**
   - Surface water features
   - Watershed boundaries
   - Stream networks

4. **USFWS Riparian Mapping**
   - Riparian corridor identification
   - Buffer zone analysis
   - Habitat connectivity

### **Data Limitations**
- Mapping scale varies by region
- Some seasonal wetlands may not be captured
- Field verification recommended for regulatory purposes
- Data currency varies by location

## 🔧 **Advanced Configuration**

### **Environment Variables**
```bash
# Optional: Configure output directories
export WETLANDS_OUTPUT_DIR="/custom/output/path"
export WETLANDS_LOGS_DIR="/custom/logs/path"

# Optional: Configure service timeouts
export WETLANDS_TIMEOUT=60
export WETLANDS_RETRY_COUNT=3
```

### **Custom Tool Configuration**
```python
# Modify tool behavior
from WetlandsINFO.tools import query_wetland_data

# Access tool configuration
tool_config = query_wetland_data.args_schema
print(tool_config.schema())

# Get tool descriptions
from WetlandsINFO.tools import get_tool_descriptions
descriptions = get_tool_descriptions()
```

## 🧪 **Testing and Validation**

### **Test Coordinates**
```python
# Puerto Rico test site (known wetlands)
test_pr = {"longitude": -66.199399, "latitude": 18.408303}

# Florida Everglades (extensive wetlands)
test_fl = {"longitude": -80.8431, "latitude": 25.4663}

# Urban area (minimal wetlands)
test_urban = {"longitude": -74.0060, "latitude": 40.7128}
```

### **Validation Checklist**
- ✅ Coordinates within valid ranges
- ✅ Network connectivity to data sources
- ✅ Output directory permissions
- ✅ Required dependencies installed
- ✅ Tool schema validation

## 📚 **Additional Resources**

- **USFWS Wetlands Mapper**: https://www.fws.gov/wetlands/data/mapper.html
- **EPA Wetlands Information**: https://www.epa.gov/wetlands
- **Clean Water Act Info**: https://www.epa.gov/cwa-404
- **Wetland Delineation Manual**: https://www.usace.army.mil/Missions/Civil-Works/Regulatory-Program-and-Permits/reg_supp/

---

**Note**: These tools are designed for informational and planning purposes. For regulatory determinations, always consult with qualified wetland professionals and obtain official jurisdictional determinations from the U.S. Army Corps of Engineers. 