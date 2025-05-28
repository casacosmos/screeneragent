# Comprehensive Environmental Screening Report Generator

## Overview

The Comprehensive Environmental Screening Report Generator is a powerful tool that takes multiple JSON files from environmental analysis processes and combines them into a structured, comprehensive environmental screening report. The tool follows the specified comprehensive environmental screening report schema and generates both JSON and Markdown format outputs.

## Features

### 📊 Data Integration
- **Multi-source JSON parsing**: Automatically categorizes and processes different types of environmental data
- **Intelligent data extraction**: Extracts relevant information from cadastral, flood, wetland, critical habitat, and air quality analyses
- **Cross-referencing**: Links related data points across different environmental domains

### 📋 Comprehensive Analysis Sections
1. **Project Information**: Location, cadastral data, timestamps
2. **Executive Summary**: Property overview, constraints, regulatory highlights, risk assessment
3. **Property & Cadastral Analysis**: Land use, zoning, area measurements, regulatory status
4. **Karst Analysis**: PRAPEC compliance (extensible for Puerto Rico projects)
5. **Flood Analysis**: FEMA zones, BFE, FIRM data, regulatory requirements
6. **Wetland Analysis**: NWI classifications, regulatory significance, development guidance
7. **Critical Habitat Analysis**: ESA compliance, species impacts, consultation requirements
8. **Air Quality Analysis**: Nonattainment status, NAAQS compliance, permitting implications
9. **Cumulative Risk Assessment**: Integrated environmental risk profiling
10. **Recommendations**: Actionable compliance guidance
11. **File Inventory**: Complete listing of generated maps, reports, and data files

### 🎯 Risk Assessment & Scoring
- **Complexity Scoring**: Numerical assessment of environmental compliance complexity (0-12 scale)
- **Risk Categorization**: Low/Moderate/High risk profiles based on multiple factors
- **Development Feasibility**: Assessment of project viability and regulatory requirements
- **Integrated Analysis**: Synthesis of multiple environmental constraints

### 📤 Multiple Output Formats
- **JSON**: Structured data format for programmatic access and integration
- **Markdown**: Human-readable format for documentation and reporting
- **Comprehensive Coverage**: Both formats include all schema sections

## Installation & Setup

### Prerequisites
```bash
# Required Python packages
pip install json os glob datetime typing dataclasses argparse
```

### Files Required
1. `comprehensive_report_generator.py` - Main tool
2. `example_usage.py` - Usage examples and demonstrations

## Usage

### Command Line Interface

#### Basic Usage
```bash
python comprehensive_report_generator.py <data_directory>
```

#### With Output Format Selection
```bash
# Generate both JSON and Markdown (default)
python comprehensive_report_generator.py data_directory --format both

# Generate only JSON
python comprehensive_report_generator.py data_directory --format json

# Generate only Markdown
python comprehensive_report_generator.py data_directory --format markdown
```

#### With Custom Output Filename
```bash
python comprehensive_report_generator.py data_directory --output "my_custom_report"
```

### Programmatic Usage

#### Basic Implementation
```python
from comprehensive_report_generator import ComprehensiveReportGenerator

# Initialize with data directory
generator = ComprehensiveReportGenerator("path/to/data/directory")

# Generate comprehensive report object
report = generator.generate_comprehensive_report()

# Export to files
json_file = generator.export_to_json("output_report.json")
md_file = generator.export_to_markdown("output_report.md")
```

#### Accessing Specific Analysis Sections
```python
# Extract individual analysis components
project_info = generator.extract_project_info()
cadastral = generator.extract_cadastral_analysis()
flood = generator.extract_flood_analysis()
wetland = generator.extract_wetland_analysis()
habitat = generator.extract_critical_habitat_analysis()
air_quality = generator.extract_air_quality_analysis()
```

## Input Data Requirements

### Expected JSON Files
The tool expects the following JSON file types in the input directory:

| File Pattern | Content Type | Required Fields |
|--------------|--------------|-----------------|
| `cadastral_search_*.json` | Property/cadastral data | `search_cadastral`, `results`, `total_area_*` |
| `panel_info_*.json` | Flood analysis data | `current_effective_data`, `preliminary_data` |
| `wetland_summary_*.json` | Wetland analysis | `location_analysis`, `wetlands_in_radius` |
| `critical_habitat_*.json` | Critical habitat data | `critical_habitat_analysis` |
| `nonattainment_summary_*.json` | Air quality data | `location_analysis`, `regulatory_assessment` |

### File Structure Example
```
data_directory/
├── cadastral_search_115_053_432_02_20250528_030323.json
├── panel_info_neg66p0449908567397_18p356280214827173_20250528_030355.json
├── wetland_summary_neg66p0449908567397_18p356280214827173_20250528_030451.json
├── critical_habitat_analysis_20250528_030539.json
├── nonattainment_summary_20250528_030558.json
└── nonattainment_analysis_20250528_030558.json
```

## Output Structure

### JSON Format
```json
{
  "project_info": {
    "project_name": "Environmental Screening - Cadastral 115-053-432-02",
    "analysis_date_time": "2025-05-28 03:48:43",
    "longitude": -66.0449908567397,
    "latitude": 18.356280214827173,
    "cadastral_numbers": ["115-053-432-02"],
    "location_name": "Dynamic Payments Project",
    "project_directory": "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17"
  },
  "executive_summary": {
    "property_overview": "...",
    "key_environmental_constraints": ["..."],
    "regulatory_highlights": ["..."],
    "risk_assessment": "...",
    "primary_recommendations": ["..."]
  },
  // ... additional sections
}
```

### Markdown Format
- Structured sections with clear headings
- Bulleted lists for easy reading
- Table format for area measurements
- Cross-references to generated maps and reports

## Risk Assessment Methodology

### Complexity Scoring System
The tool uses a 12-point complexity scoring system:

| Environmental Factor | Score Range | Criteria |
|---------------------|-------------|----------|
| **Flood Risk** | 0-3 | Zone X (0), AH/AO (2), AE/VE/A (3) |
| **Wetland Impact** | 0-4 | None (0), Nearby (1), Direct (4) |
| **Critical Habitat** | 0-4 | Distant (0), Close (2), Proposed (3), Designated (4) |
| **Air Quality** | 0-2 | Compliant (0), Nonattainment (2) |

### Risk Categories
- **Low (0-3)**: Minimal environmental constraints
- **Moderate (4-7)**: Some environmental considerations required
- **High (8-12)**: Multiple significant environmental constraints

### Development Feasibility Assessment
- **Straightforward**: Routine environmental compliance expected
- **Moderate**: Standard environmental compliance measures needed
- **Complex**: Extensive environmental studies and permitting likely required

## Integration with Environmental Screening Tools

### Workflow Integration
1. **Run Environmental Analyses**: Use cadastral, flood, wetland, habitat, and air quality tools
2. **Generate JSON Data**: Tools save structured data to project directories
3. **Process with Report Generator**: Use this tool to create comprehensive reports
4. **Review & Export**: Generate final reports in preferred formats

### File Location Patterns
The tool automatically searches for and catalogs:
- **Maps**: `maps/*.pdf`, `maps/*.png`, `maps/*.jpg`
- **Reports**: `reports/*.pdf`
- **Logs**: `logs/*.json`

## Example Output

### Sample Executive Summary
```markdown
## Executive Summary

**Property Overview:** Environmental screening analysis for cadastral 115-053-432-02 
located in Cupey, San Juan, Este. The property is classified as Residencial de Baja 
Densidad Poblacional with a total area of 2.56 acres (1.04 hectares).

**Key Environmental Constraints:**
- Wetlands present within search radius

**Risk Assessment:** Low environmental risk profile identified.

**Primary Recommendations:**
- Conduct detailed environmental due diligence prior to development
- Consult with relevant regulatory agencies early in planning process
- Consider environmental constraints in site design and engineering
```

### Sample Risk Assessment
```json
{
  "risk_factors": ["Nearby wetland considerations"],
  "complexity_score": 1,
  "overall_risk_profile": "Low - Minimal environmental constraints identified",
  "development_feasibility": "Straightforward - Routine environmental compliance expected"
}
```

## Advanced Features

### Extensibility
- **Karst Analysis**: Ready for Puerto Rico PRAPEC data integration
- **Custom Assessments**: Easily add new environmental analysis types
- **Regulatory Updates**: Configurable regulatory requirement mappings

### Data Validation
- **Error Handling**: Graceful handling of missing or malformed JSON files
- **Data Completeness**: Identifies and reports missing analysis components
- **Coordinate Validation**: Cross-validates location data across multiple sources

### Reporting Enhancements
- **File Referencing**: Automatic detection and cataloging of generated files
- **Map Integration**: References to generated environmental maps
- **Regulatory Citations**: Specific regulatory requirement identification

## Troubleshooting

### Common Issues

#### No JSON Files Found
```bash
Error: No valid JSON files found in directory
```
**Solution**: Ensure the directory contains properly formatted environmental analysis JSON files.

#### Missing Required Fields
```bash
Error loading filename.json: KeyError: 'required_field'
```
**Solution**: Verify that input JSON files contain all required data fields for their analysis type.

#### Coordinate Mismatch
**Issue**: Different coordinates across JSON files
**Solution**: The tool uses the first available coordinate set and reports the source.

### Debugging Tips
1. **Check File Patterns**: Ensure JSON files follow expected naming conventions
2. **Validate JSON Format**: Use a JSON validator to check file structure
3. **Review Logs**: Check console output for specific loading errors
4. **Test with Example**: Use the provided example data for initial testing

## Performance Considerations

### File Size Limits
- **Recommended**: < 100MB total JSON data per analysis
- **Large Files**: Flood data files can be substantial (80MB+)
- **Memory Usage**: Tool loads all JSON files into memory simultaneously

### Processing Time
- **Typical Analysis**: 1-5 seconds for standard dataset
- **Large Datasets**: May require 10-30 seconds
- **Optimization**: Consider splitting very large datasets

## Future Enhancements

### Planned Features
- **PDF Generation**: Direct PDF report output
- **GIS Integration**: Spatial analysis and mapping integration
- **Regulatory Database**: Automated regulatory requirement updates
- **Multi-language Support**: Spanish language environmental reports
- **API Integration**: RESTful API for web service integration

### Extensibility Points
- **Custom Analysis Types**: Framework for adding new environmental analyses
- **Report Templates**: Customizable output formatting
- **Regulatory Frameworks**: Support for different jurisdictional requirements

## License & Support

### Usage License
This tool is designed for environmental compliance and due diligence purposes. 
Users are responsible for ensuring compliance with applicable environmental regulations.

### Support Resources
- **Example Files**: Use `example_usage.py` for implementation guidance
- **Documentation**: Comprehensive schema documentation included
- **Testing**: Test with provided sample data before production use

### Contributing
Contributions welcome for:
- Additional environmental analysis types
- Enhanced risk assessment methodologies
- Improved reporting formats
- Regulatory requirement updates

---

**Note**: This tool processes existing environmental analysis data and does not perform 
primary environmental assessments. Always consult qualified environmental professionals 
for site-specific analysis and regulatory compliance guidance. 