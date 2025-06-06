# Comprehensive Environmental Screening System

A complete solution for environmental due diligence and regulatory compliance screening, featuring automated data retrieval, analysis, and professional report generation.

## 🌍 **System Overview**

This system provides comprehensive environmental screening capabilities by integrating multiple government data sources and generating professional-quality reports. The system is designed for environmental consultants, developers, and regulatory professionals who need efficient, accurate environmental assessments.

### **Key Capabilities**
- **Multi-Domain Analysis**: Cadastral, flood, wetland, habitat, air quality, and karst assessments
- **Government Data Integration**: Direct API access to FEMA, EPA, USFWS, CRIM, and other authoritative sources
- **Automated Report Generation**: Professional HTML and PDF environmental screening reports
- **Schema-Compliant Data**: Structured JSON output matching comprehensive template requirements
- **Regulatory Compliance**: Built-in knowledge of environmental regulations and requirements

## 📊 **Data Sources & Integration**

### **Cadastral/Property Data**
- **Source**: Puerto Rico CRIM (Centro de Recaudación de Ingresos Municipales)
- **Service**: MIPR cadastral data services
- **Coverage**: Property boundaries, ownership, zoning, land use classification
- **API Access**: Direct integration with cadastral databases

### **Flood Risk Assessment**
- **Source**: FEMA National Flood Hazard Layer (NFHL)
- **Data Types**: Current Effective FIRM, Preliminary FIRM, ABFE
- **Coverage**: Flood zones, base flood elevations, FIRM panels, community data
- **Maps**: Automated FIRMette and ABFE map generation

### **Critical Habitat Analysis**
- **Source**: USFWS Critical Habitat designations
- **Service**: USFWS ECOS database and spatial services
- **Coverage**: Designated and proposed critical habitats, species information
- **Compliance**: ESA consultation requirements and recommendations

### **Air Quality Assessment**
- **Source**: EPA Green Book (Nonattainment Areas)
- **Services**: EPA OAR, OAQPS, NAAQS databases
- **Coverage**: Nonattainment areas, air quality standards, emission requirements
- **Compliance**: Clean Air Act requirements and permitting guidance

### **Karst Analysis (Puerto Rico)**
- **Source**: PRAPEC (Programa de Protección del Carso)
- **Authority**: Puerto Rico Planning Board
- **Coverage**: Karst zones, geological hazards, regulatory buffers
- **Regulations**: PRAPEC regulatory requirements and development constraints

### **Wetland Assessment**
- **Source**: USFWS National Wetlands Inventory (NWI)
- **Coverage**: Wetland types, classifications, jurisdictional boundaries
- **Compliance**: Section 404 permit requirements and mitigation guidance

## 🔧 **System Architecture**

### **Core Components**

#### **1. Comprehensive Query Tool** (`comprehensive_query_tool.py`)
- **Function**: Unified environmental data retrieval
- **Features**: Multi-domain queries, batch processing, error handling
- **Output**: Raw JSON data files for each environmental domain
- **Integration**: LangChain tools for agent-based workflows

#### **2. Data Normalization Engine**
- **Function**: Maps raw API responses to standardized schema
- **Features**: Data validation, error correction, metadata preservation
- **Output**: Schema-compliant structured data
- **Schema**: `improved_template_data_schema.json`

#### **3. Template Data Generator**
- **Function**: Creates template-ready structured JSON
- **Features**: Executive summary generation, compliance checklist, risk assessment
- **Output**: `template_data_structure.json`
- **Integration**: Direct compatibility with HTML templates

#### **4. HTML Template Engine**
- **Template**: `comprehensive_environmental_template_v2.html`
- **Features**: Professional layout, responsive design, compliance tables
- **Technology**: Jinja2 templating with CSS styling
- **Output**: Publication-ready HTML reports

#### **5. PDF Generation Tools**
- **Function**: Converts HTML to professional PDF reports
- **Features**: Page formatting, map embedding, print optimization
- **Integration**: HTML to PDF conversion utilities

### **Data Flow Architecture**

```
📍 Input (Coordinates/Cadastral) 
    ↓
🔍 Comprehensive Query Tool
    ↓
📊 Raw Environmental Data (JSON files)
    ↓
🛠️ Data Normalization Engine
    ↓
📋 Structured Template Data (template_data_structure.json)
    ↓
🎨 HTML Template Rendering
    ↓
📄 Professional Environmental Report (HTML/PDF)
```

## 📋 **File Structure**

### **Core System Files**
```
📁 Environmental Screening System/
├── 📄 comprehensive_query_tool.py           # Main query orchestration
├── 📄 improved_template_data_schema.json    # Data structure schema
├── 📄 comprehensive_environmental_template_v2.html  # HTML template
├── 📄 enhanced_template_example_data.json   # Example structured data
├── 📄 DATA_SOURCES_MAPPING.md              # Data source documentation
└── 📄 test_comprehensive_template_workflow.py  # System testing
```

### **Individual Analysis Tools**
```
📁 Domain-Specific Tools/
├── 📄 cadastral/cadastral_data_tool.py      # Property data analysis
├── 📄 flood_helpers.py                      # FEMA flood analysis
├── 📄 simple_karst_analysis_tool.py         # Karst assessment
├── 📄 wetland_analysis_tool.py              # NWI wetland analysis
├── 📄 nonattainment_analysis_tool.py        # EPA air quality
└── 📄 HabitatINFO/tools.py                  # Critical habitat analysis
```

### **Output Structure** (Per Project)
```
📁 Project_Name_YYYYMMDD_HHMMSS/
├── 📁 data/
│   ├── 📄 cadastral_analysis.json
│   ├── 📄 flood_analysis_comprehensive.json
│   ├── 📄 karst_analysis_comprehensive.json
│   ├── 📄 critical_habitat_analysis_comprehensive.json
│   ├── 📄 air_quality_analysis_comprehensive.json
│   ├── 📄 comprehensive_query_results.json
│   └── 📄 template_data_structure.json      # 🎯 Template-ready data
├── 📁 maps/
│   ├── 📄 flood_maps_*.pdf
│   ├── 📄 karst_maps_*.pdf
│   └── 📄 habitat_maps_*.pdf
├── 📁 reports/
│   └── 📄 environmental_screening_report.pdf
└── 📁 logs/
    └── 📄 analysis_logs.txt
```

## 🚀 **Usage Workflows**

### **1. Single Location Analysis**
```python
from comprehensive_query_tool import query_environmental_data_for_location

# Run comprehensive environmental queries
result = query_environmental_data_for_location(
    location="18.2294, -65.9266",
    project_name="My Environmental Assessment",
    cadastral_number="227-052-007-20",  # Optional
    include_maps=True,
    buffer_distance=1.0
)

# Access structured template data
template_data = result['template_data']
template_file = result['template_data_file']
```

### **2. Batch Location Processing**
```python
from comprehensive_query_tool import batch_query_environmental_data

locations = [
    {"location": "18.2294, -65.9266", "cadastral_number": "227-052-007-20"},
    {"location": "18.4058, -66.7135", "cadastral_number": "115-053-432-02"}
]

batch_result = batch_query_environmental_data(
    locations=locations,
    project_base_name="Batch Environmental Assessment",
    parallel_processing=True
)
```

### **3. Template Data Generation**
```python
from comprehensive_query_tool import generate_structured_template_data

# Generate template data from existing query results
template_result = generate_structured_template_data(
    project_directory="/path/to/project",
    comprehensive_results_file=None  # Auto-locate results
)

template_data_file = template_result['template_data_file']
```

### **4. HTML Report Generation**
```python
from jinja2 import Template
import json

# Load template data
with open('template_data_structure.json', 'r') as f:
    data = json.load(f)

# Load HTML template
with open('comprehensive_environmental_template_v2.html', 'r') as f:
    template = Template(f.read())

# Generate HTML report
html_report = template.render(**data)

# Save HTML report
with open('environmental_report.html', 'w') as f:
    f.write(html_report)
```

## 🎯 **Key Features**

### **Comprehensive Coverage**
- **6 Environmental Domains**: Complete regulatory compliance coverage
- **Multiple Data Sources**: Government-authoritative data integration
- **Real-Time Queries**: Live API access to current data
- **Buffer Analysis**: Proximity-based environmental assessments

### **Professional Output**
- **Executive Summaries**: Risk assessments and key findings
- **Compliance Checklists**: Regulatory requirement matrices
- **Visual Maps**: Embedded environmental constraint maps
- **PDF Reports**: Publication-ready professional formatting

### **Regulatory Intelligence**
- **Built-in Expertise**: Environmental regulation knowledge
- **Compliance Guidance**: Permit and consultation requirements
- **Risk Assessment**: Automated environmental risk categorization
- **Recommendations**: Action items and next steps

### **Quality Assurance**
- **Schema Validation**: Structured data validation
- **Error Handling**: Graceful failure management
- **Source Attribution**: Data source tracking and metadata
- **Audit Trails**: Complete analysis documentation

## 📊 **Template Data Schema**

The system generates structured JSON data matching `improved_template_data_schema.json`:

### **Required Fields**
- `project_name`: Project identification
- `analysis_date`: Timestamp of analysis
- `location_description`: Human-readable location
- `coordinates`: Latitude/longitude coordinates
- `overall_risk_level`: Calculated risk assessment
- `risk_class`: CSS styling class for risk level

### **Environmental Analysis Sections**
- `cadastral_analysis`: Property and zoning information
- `karst_analysis`: Geological hazard assessment (Puerto Rico)
- `flood_analysis`: FEMA flood risk data
- `critical_habitat_analysis`: ESA compliance assessment
- `air_quality_analysis`: EPA air quality compliance
- `wetland_analysis`: NWI wetland assessment (optional)

### **Generated Sections**
- `executive_summary`: Automated summary and risk assessment
- `compliance_checklist`: Regulatory compliance status fields
- `recommendations`: Synthesized action items

## 🔍 **Testing & Validation**

### **System Testing**
```bash
# Run comprehensive workflow test
python test_comprehensive_template_workflow.py

# Test individual tools
python comprehensive_query_tool.py --location "18.2294, -65.9266" --project "Test Project"
```

### **Schema Validation**
- JSON schema compliance checking
- Required field validation
- Data type verification
- Template compatibility testing

### **Quality Checks**
- Data completeness analysis
- Source attribution verification
- Error handling validation
- Output format compliance

## 🛠️ **Technical Requirements**

### **Dependencies**
- Python 3.8+
- LangChain framework
- Jinja2 templating
- JSON schema validation
- HTTP request libraries
- Spatial analysis libraries

### **External Services**
- FEMA flood data APIs
- EPA air quality databases
- USFWS habitat services
- Puerto Rico CRIM cadastral data
- PRAPEC karst databases

### **System Requirements**
- Internet connectivity for API access
- Sufficient storage for map files and reports
- PDF generation capabilities
- File system write permissions

## 📞 **Support & Maintenance**

### **Error Handling**
- Comprehensive logging throughout system
- Graceful degradation for missing data
- Clear error messages and suggestions
- Retry mechanisms for API failures

### **Updates & Maintenance**
- Regular data source compatibility checks
- Schema updates for new requirements
- Template enhancements and improvements
- API endpoint monitoring and updates

---

## 🎯 **Summary**

This Comprehensive Environmental Screening System provides a complete solution for environmental due diligence, from initial data queries through final report generation. The system integrates authoritative government data sources, applies environmental regulatory expertise, and generates professional screening reports suitable for regulatory submissions and development planning.

**Key Advantages:**
- **Efficiency**: Automated data retrieval and analysis
- **Accuracy**: Government-authoritative data sources
- **Completeness**: Multi-domain environmental coverage
- **Professional**: Publication-ready report output
- **Compliance**: Built-in regulatory knowledge
- **Scalable**: Batch processing and template-driven architecture 