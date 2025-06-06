# Environmental Screening Data Sources Mapping

This document outlines the data sources for each section of the comprehensive environmental screening report template and how they map to the structured JSON output.

## 📊 **Data Source Overview**

### **1. Cadastral/Property Analysis**
- **Primary Source**: Puerto Rico CRIM (Centro de Recaudación de Ingresos Municipales)
- **Service**: MIPR cadastral data services
- **Fields Retrieved**:
  - `cadastral_number` → from cadastral search API
  - `municipality`, `neighborhood`, `region` → from cadastral features
  - `total_area_m2`, `total_area_hectares` → calculated from geometry
  - `classification_code`, `classification_description` → land use classification
  - `sub_classification`, `sub_classification_description` → detailed zoning
  - `status`, `resolution` → regulatory status
  - `geometry` → property boundaries (coordinate rings)

**JSON Path**: `cadastral_analysis.*`
**Tool Function**: `get_cadastral_data_from_coordinates()`

### **2. Karst Analysis (Puerto Rico)**
- **Primary Source**: PRAPEC (Programa de Protección del Carso)
- **Service**: MIPR Reglamentario_va2 MapServer
- **Layer**: "PRAPEC (Carso) - Layer 15"
- **Authority**: Puerto Rico Planning Board (Junta de Planificación)
- **Fields Retrieved**:
  - `karst_status` → presence within karst zones
  - `karst_proximity` → proximity classification
  - `distance_miles` → distance to nearest karst feature
  - `regulatory_impact` → impact level assessment
  - `buffer_miles` → search buffer used
  - `query_time` → analysis timestamp

**JSON Path**: `karst_analysis.*`
**Tool Function**: `check_coordinates_karst()`

### **3. Flood Analysis**
- **Primary Source**: FEMA National Flood Hazard Layer (NFHL)
- **Services**: 
  - Current Effective FIRM data
  - Preliminary FIRM data
  - Advisory Base Flood Elevation (ABFE)
- **Fields Retrieved**:
  - `flood_zone` → FEMA flood zone designation
  - `base_flood_elevation` → elevation data
  - `firm_panel` → FIRM panel identification
  - `effective_date` → panel effective date
  - `political_jurisdictions` → community information
  - `dfirm_id` → Digital FIRM identifier

**JSON Path**: `flood_analysis.*`
**Tool Function**: `get_flood_data()`, `generate_flood_maps()`

### **4. Critical Habitat Analysis**
- **Primary Source**: USFWS Critical Habitat designations
- **Service**: USFWS ECOS database
- **Fields Retrieved**:
  - `status` → habitat proximity status
  - `distance_to_nearest_habitat_miles` → distance calculation
  - `species_common_name`, `species_scientific_name` → species information
  - `unit_name` → habitat unit designation
  - `layer_type` → designation type (Final/Proposed)
  - `esa_consultation_required` → regulatory requirement
  - `recommendations` → analysis recommendations

**JSON Path**: `critical_habitat_analysis.*`
**Tool Function**: `generate_adaptive_critical_habitat_map()`

### **5. Air Quality Analysis**
- **Primary Source**: EPA Green Book (Nonattainment Areas)
- **Services**:
  - EPA Office of Air and Radiation (OAR)
  - Office of Air Quality Planning and Standards (OAQPS)
  - National Ambient Air Quality Standards (NAAQS)
- **Fields Retrieved**:
  - `has_violations` → nonattainment status
  - `total_violations` → violation count
  - `compliance_status` → overall compliance
  - `air_quality_status` → NAAQS compliance
  - `regulatory_requirements` → applicable requirements
  - `epa_data_sources` → data source attribution

**JSON Path**: `air_quality_analysis.*`
**Tool Function**: `NonattainmentAnalysisTool.analyze_nonattainment()`

### **6. Wetland Analysis**
- **Primary Source**: USFWS National Wetlands Inventory (NWI)
- **Service**: NWI web services
- **Fields Retrieved**:
  - `directly_on_property` → direct wetland presence
  - `within_search_radius` → proximity analysis
  - `distance_to_nearest` → distance calculation
  - `wetland_classifications` → NWI codes
  - `regulatory_significance` → jurisdictional assessment

**JSON Path**: `wetland_analysis.*` (if present)
**Tool Function**: `WetlandAnalysisTool.analyze_wetland_location()`

## 🔄 **Data Flow Process**

1. **Input Coordinates/Cadastral** → `comprehensive_query_tool.py`
2. **Individual Tool Queries** → Each domain-specific tool
3. **Raw Results Aggregation** → Collect all JSON responses
4. **Data Normalization** → Map to template schema
5. **Executive Summary Generation** → Analyze results for summary
6. **Compliance Checklist Generation** → Evaluate against standards
7. **Structured JSON Output** → Final template-ready data

## 📋 **Template Field Mapping**

### **Executive Summary Fields**
- `property_overview` → Generated from cadastral + location data
- `risk_assessment` → Aggregated from all analysis results
- `key_environmental_constraints` → Identified constraints list
- `regulatory_highlights` → Key regulatory findings
- `primary_recommendations` → Synthesized recommendations

### **Compliance Checklist Fields**
- `flood_status/risk/action` → From flood analysis results
- `habitat_status/risk/action` → From critical habitat analysis
- `zoning_status/risk/action` → From cadastral classification
- `air_status/risk/action` → From air quality analysis
- `karst_status/risk/action` → From karst analysis

## 🛠️ **Tool Configuration**

Each analysis tool is configured with:
- **Buffer distances** for proximity analysis
- **Data source endpoints** for API calls
- **Error handling** for missing data
- **Metadata collection** for audit trails
- **Map generation parameters** for visualization

## 📊 **Output Schema Compliance**

The comprehensive query tool outputs JSON that matches:
- `improved_template_data_schema.json` → Full schema specification
- `enhanced_template_example_data.json` → Example data structure
- `comprehensive_environmental_template_v2.html` → Template requirements

## 🔍 **Quality Assurance**

- **Data validation** against schema
- **Source attribution** for each data point
- **Timestamp tracking** for analysis timing
- **Error logging** for failed queries
- **Completeness checking** for required fields 