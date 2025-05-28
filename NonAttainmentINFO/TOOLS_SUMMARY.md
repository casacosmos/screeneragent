# NonAttainmentINFO Tools Summary

## 🌫️ Available Tools for EPA Nonattainment Areas Analysis

The NonAttainmentINFO module provides a comprehensive suite of LangChain-compatible tools for analyzing EPA nonattainment areas and assessing Clean Air Act compliance. These tools can be used individually or integrated into larger environmental screening workflows.

## 📋 Tool Categories

### 1. **Module-Specific Tools** (`NonAttainmentINFO/tools.py`)

#### `analyze_nonattainment_areas`
**Purpose**: Core analysis tool for EPA nonattainment area intersections
**Functionality**:
- Queries EPA OAR_OAQPS nonattainment data
- Determines if location violates National Ambient Air Quality Standards (NAAQS)
- Provides detailed pollutant and regulatory information
- Supports buffer analysis and pollutant filtering
- Returns structured JSON with compliance status

**Use Cases**:
- Environmental due diligence
- Regulatory compliance assessment
- Site selection analysis
- Clean Air Act requirement determination

**Parameters**:
- `longitude`, `latitude`: Location coordinates
- `include_revoked`: Include revoked air quality standards
- `buffer_meters`: Buffer distance for area analysis
- `pollutants`: Specific pollutants to check

---

#### `generate_nonattainment_map`
**Purpose**: Professional PDF map generation for nonattainment areas
**Functionality**:
- Creates high-quality maps with EPA nonattainment layers
- Color-coded pollutant visualization with proper symbology
- Customizable base maps, legends, and styling
- Professional layout for regulatory submissions
- Automatic fallback to HTML if PDF services unavailable

**Use Cases**:
- Regulatory submission documentation
- Environmental impact assessment visuals
- Site analysis presentations
- Compliance reporting

**Parameters**:
- `longitude`, `latitude`: Map center coordinates
- `location_name`: Map title
- `buffer_miles`: Map extent radius
- `base_map`: Background map style
- `include_legend`: Legend inclusion
- `pollutants`: Specific pollutants to display

---

#### `generate_adaptive_nonattainment_map`
**Purpose**: Intelligent map generation with automatic optimization
**Functionality**:
- Analyzes location first to determine optimal map settings
- Automatically adjusts buffer size based on findings
- Selects appropriate base map and styling
- Provides reasoning for adaptive choices
- Combines analysis and visualization in one step

**Use Cases**:
- Automated environmental screening
- Quick assessment with optimal visualization
- Standardized reporting workflows
- AI-driven environmental analysis

**Parameters**:
- `longitude`, `latitude`: Location coordinates
- `location_name`: Optional location identifier

---

#### `search_pollutant_areas`
**Purpose**: Nationwide pollutant-specific nonattainment area search
**Functionality**:
- Searches all EPA nonattainment areas for specific pollutants
- Provides geographic distribution analysis
- State-by-state breakdown of violations
- Classification and severity analysis
- Trend and pattern identification

**Use Cases**:
- National air quality research
- Regional compliance comparisons
- Policy analysis and planning
- Environmental trend studies

**Parameters**:
- `pollutant`: Specific pollutant name
- `include_revoked`: Include historical standards

---

#### `analyze_location_with_map`
**Purpose**: Comprehensive analysis combining data retrieval and map generation
**Functionality**:
- Complete air quality assessment workflow
- Detailed violation analysis with regulatory implications
- Professional map generation
- Actionable recommendations
- Integrated documentation package

**Use Cases**:
- Complete environmental screening
- Regulatory compliance packages
- Development feasibility studies
- Environmental consulting reports

**Parameters**:
- `longitude`, `latitude`: Location coordinates
- `location_name`: Location identifier
- `buffer_miles`: Map extent
- `include_revoked`: Historical standards inclusion

---

### 2. **Project Integration Tool** (`nonattainment_analysis_tool.py`)

#### `analyze_nonattainment_with_map`
**Purpose**: Comprehensive project-integrated tool with output directory management
**Functionality**:
- Complete EPA nonattainment analysis workflow
- Adaptive map generation with optimal settings
- Organized file output with project directory structure
- Detailed regulatory compliance assessment
- Comprehensive recommendations and next steps
- Integration with project's output directory management system

**Advanced Features**:
- **Output Organization**: Creates dedicated project directories with subdirectories for data, reports, maps, and logs
- **Regulatory Assessment**: Detailed Clean Air Act compliance analysis with severity classification
- **Adaptive Intelligence**: Automatically determines optimal map settings based on violation findings
- **Comprehensive Documentation**: Saves detailed JSON reports for all analysis components
- **Error Handling**: Robust error management with detailed logging

**Use Cases**:
- Complete environmental screening projects
- Regulatory compliance documentation packages
- Development feasibility assessments
- Environmental consulting deliverables
- Automated environmental analysis workflows

**Integration Benefits**:
- Seamless integration with other environmental modules (wetlands, critical habitat, flood, karst)
- Consistent output directory structure across all environmental analyses
- Professional documentation suitable for regulatory submission
- Standardized reporting format for multi-module environmental screening

---

## 🎯 Tool Selection Guide

### **For Simple Queries**
- Use `analyze_nonattainment_areas` for basic compliance checking
- Use `search_pollutant_areas` for research and trend analysis

### **For Visualization Needs**
- Use `generate_nonattainment_map` for custom map requirements
- Use `generate_adaptive_nonattainment_map` for automated optimal maps

### **For Comprehensive Analysis**
- Use `analyze_location_with_map` (module tool) for complete assessment
- Use `analyze_nonattainment_with_map` (project tool) for integrated environmental screening

### **For Project Integration**
- Use `analyze_nonattainment_with_map` when integrating with other environmental modules
- Provides consistent output structure with wetlands, critical habitat, flood, and karst tools

---

## 📊 Data Coverage

### **EPA Data Sources**
- EPA Office of Air and Radiation (OAR)
- Office of Air Quality Planning and Standards (OAQPS)
- National Ambient Air Quality Standards (NAAQS) database

### **Pollutants Covered**
- **Ozone (O₃)**: 8-hour standards (2008, 2015) + revoked standards (1997, 1979)
- **Particulate Matter**: PM2.5 (multiple standards), PM10
- **Carbon Monoxide (CO)**: 1971 standard
- **Sulfur Dioxide (SO₂)**: 1-hour 2010 standard
- **Nitrogen Dioxide (NO₂)**: 1971 standard
- **Lead (Pb)**: 2008 standard

### **Geographic Coverage**
- All 50 United States
- District of Columbia
- U.S. Territories
- Tribal lands

---

## 🔧 Technical Features

### **Analysis Capabilities**
- Point-in-polygon intersection analysis
- Buffer-based proximity analysis
- Multi-pollutant assessment
- Historical standards inclusion
- Regulatory status classification

### **Map Generation**
- Professional PDF output with fallback HTML
- Multiple base map options (topographic, street, imagery)
- Color-coded pollutant layers with proper EPA symbology
- Customizable legends and scale bars
- Adaptive buffer sizing based on analysis results

### **Output Management**
- Structured JSON data files
- Professional map files (PDF/HTML)
- Comprehensive summary reports
- Error logging and debugging information
- Organized project directory structure

---

## 🚀 Integration Examples

### **LangGraph Agent Integration**
```python
from NonAttainmentINFO.tools import NONATTAINMENT_TOOLS
from nonattainment_analysis_tool import COMPREHENSIVE_NONATTAINMENT_TOOL

# Add to agent tools
agent_tools = NONATTAINMENT_TOOLS + [COMPREHENSIVE_NONATTAINMENT_TOOL]
```

### **Comprehensive Environmental Screening**
```python
# Use with other environmental modules
from comprehensive_environmental_agent import create_comprehensive_environmental_agent

# Includes nonattainment analysis alongside:
# - Property/Cadastral analysis
# - FEMA flood analysis  
# - Wetland analysis
# - Critical habitat analysis
# - Karst analysis
```

---

## 📈 Performance Characteristics

### **Response Times**
- Analysis queries: 2-10 seconds
- Map generation: 30-120 seconds
- Comprehensive analysis: 1-3 minutes

### **Reliability Features**
- Multiple EPA service endpoints with fallback
- Retry logic for network issues
- Graceful degradation (HTML maps if PDF fails)
- Comprehensive error handling and logging

### **Scalability**
- Supports batch analysis workflows
- Efficient caching for repeated queries
- Optimized for high-volume environmental screening

---

## 💡 Best Practices

### **Tool Selection**
1. **Single Location Analysis**: Use module-specific tools for focused analysis
2. **Project Integration**: Use comprehensive project tool for multi-module screening
3. **Research Applications**: Use pollutant search tools for trend analysis
4. **Regulatory Submissions**: Use comprehensive tools with full documentation

### **Parameter Optimization**
1. **Buffer Sizing**: 0m for exact point, 1000-5000m for proximity analysis
2. **Map Extent**: 10-15 miles for detailed view, 25-50 miles for regional context
3. **Pollutant Filtering**: Specify pollutants for focused analysis
4. **Historical Standards**: Include revoked standards for comprehensive historical analysis

### **Output Management**
1. Use project integration tool for organized file structure
2. Save analysis results for regulatory documentation
3. Maintain consistent naming conventions across projects
4. Archive comprehensive analysis packages for future reference

---

**Summary**: The NonAttainmentINFO module provides a complete toolkit for EPA air quality analysis, from simple compliance checking to comprehensive environmental screening with professional documentation. The tools are designed for flexibility, reliability, and integration with larger environmental assessment workflows. 