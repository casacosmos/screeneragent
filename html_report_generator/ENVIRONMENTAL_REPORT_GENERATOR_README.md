# Environmental Report Generator

A comprehensive system for generating professional HTML and PDF environmental screening reports from structured JSON data.

## 🌍 **Overview**

The Environmental Report Generator converts structured environmental screening data into professional-quality reports suitable for regulatory submissions, environmental due diligence, and development planning. It supports multiple PDF generation methods and provides flexible template rendering.

## 🚀 **Quick Start**

### **Installation**

```bash
# Install core dependencies
pip install jinja2 weasyprint

# Or install from requirements file
pip install -r requirements_pdf.txt
```

### **Basic Usage**

```bash
# Generate HTML and PDF from JSON data
python generate_environmental_report.py --json template_data_structure.json

# Specify output directory
python generate_environmental_report.py --json data.json --output-dir reports/

# Use specific PDF generation method
python generate_environmental_report.py --json data.json --pdf-method weasyprint
```

### **Programmatic Usage**

```python
from generate_environmental_report import EnvironmentalReportGenerator

# Initialize generator
generator = EnvironmentalReportGenerator()

# Generate report
results = generator.generate_report(
    json_file="template_data_structure.json",
    output_dir="reports",
    pdf_method="auto"
)

print(f"HTML: {results['html_file']}")
print(f"PDF: {results['pdf_file']}")
```

## 📊 **Features**

### **Multiple PDF Generation Methods**
- **WeasyPrint**: Best CSS support, professional layouts
- **pdfkit**: Fast, reliable PDF generation using wkhtmltopdf
- **Playwright**: Browser-based rendering, excellent quality
- **Auto-detection**: Automatically selects best available method

### **Professional Report Features**
- **Executive Summaries**: Risk assessments and key findings
- **Compliance Checklists**: Regulatory requirement matrices with color coding
- **Environmental Maps**: Embedded maps for each domain
- **Data Validation**: JSON schema validation against template requirements
- **Flexible Templates**: Jinja2-based templating system

### **Comprehensive Coverage**
- Cadastral/Property analysis with zoning information
- Flood risk assessment with FEMA data
- Critical habitat analysis with species information
- Air quality compliance with EPA standards
- Karst analysis for Puerto Rico (PRAPEC data)
- Wetland assessment with NWI classifications

## 🔧 **System Requirements**

### **Python Dependencies**
- Python 3.8+
- jinja2 >= 3.1.0
- At least one PDF generation library:
  - weasyprint >= 59.0 (recommended)
  - pdfkit >= 1.0.0 (requires wkhtmltopdf binary)
  - playwright >= 1.40.0

### **System Dependencies**

**For pdfkit method:**
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf

# Windows
# Download from: https://wkhtmltopdf.org/downloads.html
```

**For Playwright method:**
```bash
pip install playwright
playwright install chromium
```

## 📁 **File Structure**

### **Input Files**
- `template_data_structure.json` - Structured environmental data
- `comprehensive_environmental_template_v2.html` - HTML template
- `improved_template_data_schema.json` - Data validation schema

### **Output Files**
- `{project_name}_{timestamp}.html` - Generated HTML report
- `{project_name}_{timestamp}.pdf` - Generated PDF report

### **Project Structure**
```
📁 Environmental Report Generator/
├── 📄 generate_environmental_report.py      # Main generator script
├── 📄 example_report_generation.py          # Usage examples
├── 📄 requirements_pdf.txt                  # Dependencies
├── 📄 comprehensive_environmental_template_v2.html  # HTML template
├── 📄 improved_template_data_schema.json    # Data schema
└── 📁 reports/                              # Generated reports
    ├── 📄 Project_Name_20250129_143000.html
    └── 📄 Project_Name_20250129_143000.pdf
```

## 📋 **Command Line Options**

```bash
python generate_environmental_report.py [OPTIONS]

Required:
  --json FILE           JSON template data file

Optional:
  --output-dir DIR      Output directory (default: reports)
  --pdf-method METHOD   PDF generation method (auto|weasyprint|pdfkit|playwright)
  --template FILE       HTML template file
  --schema FILE         JSON schema file for validation
  --no-html            Skip HTML generation
  --no-pdf             Skip PDF generation
  --verbose, -v        Verbose logging
```

### **Examples**

```bash
# Basic usage
python generate_environmental_report.py --json data.json

# Custom output directory
python generate_environmental_report.py --json data.json --output-dir my_reports/

# Specific PDF method
python generate_environmental_report.py --json data.json --pdf-method weasyprint

# HTML only
python generate_environmental_report.py --json data.json --no-pdf

# PDF only with custom template
python generate_environmental_report.py --json data.json --no-html --template my_template.html
```

## 📊 **JSON Data Format**

The generator expects JSON data matching the `improved_template_data_schema.json` schema:

### **Required Fields**
```json
{
  "project_name": "Environmental Assessment Project",
  "analysis_date": "2025-01-29T15:30:00",
  "location_description": "Property Location Description",
  "coordinates": "18.2294, -65.9266",
  "overall_risk_level": "Low",
  "risk_class": "risk-low"
}
```

### **Environmental Analysis Sections**
```json
{
  "cadastral_analysis": { /* property data */ },
  "karst_analysis": { /* geological data */ },
  "flood_analysis": { /* FEMA flood data */ },
  "critical_habitat_analysis": { /* species data */ },
  "air_quality_analysis": { /* EPA compliance data */ },
  "wetland_analysis": { /* NWI wetland data */ }
}
```

### **Generated Sections**
```json
{
  "executive_summary": {
    "property_overview": "...",
    "risk_assessment": "...",
    "key_environmental_constraints": [...],
    "regulatory_highlights": [...],
    "primary_recommendations": [...]
  },
  "flood_status": "COMPLIANT",
  "flood_risk": "LOW",
  "habitat_status": "REVIEW",
  /* ... other compliance fields */
}
```

## 🎨 **Template Customization**

### **Modifying the HTML Template**

The HTML template uses Jinja2 syntax:

```html
<!-- Basic data rendering -->
<td>{{project_name}}</td>
<td>{{coordinates}}</td>

<!-- Conditional rendering -->
{% if cadastral_analysis %}
<div class="section">
  <h3>Property Analysis</h3>
  <p>Municipality: {{cadastral_analysis.municipality}}</p>
</div>
{% endif %}

<!-- Loop through lists -->
{% for constraint in executive_summary.key_environmental_constraints %}
<li>{{constraint}}</li>
{% endfor %}

<!-- Status-based styling -->
<td class="{{flood_status_class}}">{{flood_status}}</td>
```

### **CSS Styling**

The template includes comprehensive CSS for:
- Professional report formatting
- Status indicators (green/yellow/red)
- Print-optimized layouts
- Responsive design elements
- Map embedding support

## 🔍 **PDF Generation Methods Comparison**

| Method | CSS Support | Speed | Quality | Dependencies |
|--------|-------------|--------|---------|--------------|
| **WeasyPrint** | Excellent | Medium | High | Python only |
| **pdfkit** | Good | Fast | High | wkhtmltopdf binary |
| **Playwright** | Excellent | Slow | Excellent | Chromium browser |

### **Recommendations**
- **WeasyPrint**: Best for complex layouts, no external dependencies
- **pdfkit**: Best for speed and reliability, requires wkhtmltopdf
- **Playwright**: Best quality, but slower and larger footprint

## 🧪 **Testing & Validation**

### **Run Examples**
```bash
# Run all example scenarios
python example_report_generation.py

# Test with existing data
python generate_environmental_report.py --json output/*/data/template_data_structure.json
```

### **Data Validation**
The generator validates JSON data against the schema:
- Required field checking
- Data type validation
- Format compliance
- Missing data handling

### **Error Handling**
- Graceful failure for missing PDF libraries
- Clear error messages for invalid data
- Fallback options for template rendering issues
- Comprehensive logging for debugging

## 🔧 **Integration with Comprehensive Query Tool**

### **Complete Workflow**
```bash
# 1. Run environmental queries
python comprehensive_query_tool.py --location "18.2294,-65.9266" --project "My Project"

# 2. Generate reports from query results
python generate_environmental_report.py --json output/*/data/template_data_structure.json
```

### **Programmatic Integration**
```python
from comprehensive_query_tool import query_environmental_data_for_location
from generate_environmental_report import EnvironmentalReportGenerator

# Run environmental queries
query_result = query_environmental_data_for_location(
    location="18.2294,-65.9266",
    project_name="Comprehensive Assessment"
)

# Generate report from results
if query_result['success']:
    generator = EnvironmentalReportGenerator()
    report_result = generator.generate_report(
        json_file=query_result['template_data_file'],
        output_dir="final_reports"
    )
    
    print(f"Final report: {report_result['pdf_file']}")
```

## 📈 **Advanced Usage**

### **Custom Templates**
```python
# Use custom template
generator = EnvironmentalReportGenerator(
    template_file="my_custom_template.html",
    schema_file="my_schema.json"
)
```

### **Batch Processing**
```python
# Process multiple JSON files
import glob

for json_file in glob.glob("data/*.json"):
    results = generator.generate_report(
        json_file=json_file,
        output_dir=f"reports/{Path(json_file).stem}"
    )
    print(f"Generated: {results['pdf_file']}")
```

### **Custom PDF Settings**
```python
# Custom WeasyPrint settings
html_doc = weasyprint.HTML(string=html_content)
html_doc.write_pdf(
    "custom_report.pdf",
    stylesheets=["custom.css"],
    optimize_images=True
)
```

## 🐛 **Troubleshooting**

### **Common Issues**

**PDF Generation Fails:**
```bash
# Check available methods
python -c "from generate_environmental_report import *; print('WeasyPrint:', WEASYPRINT_AVAILABLE)"

# Install missing dependencies
pip install weasyprint
```

**Template Rendering Errors:**
```bash
# Validate JSON data
python -c "import json; json.load(open('data.json'))"

# Check schema compliance
python generate_environmental_report.py --json data.json --verbose
```

**Missing Data Fields:**
- Check that JSON contains all required fields
- Verify field names match schema exactly
- Ensure nested structures are properly formatted

### **Performance Optimization**
- Use WeasyPrint for better performance than Playwright
- Pre-validate JSON data to avoid rendering failures
- Cache templates for batch processing
- Optimize images in templates for faster PDF generation

## 📞 **Support & Development**

### **Contributing**
- Follow existing code style and patterns
- Add tests for new PDF generation methods
- Update documentation for template changes
- Validate against existing environmental data

### **Extending Functionality**
- Add new PDF generation backends
- Create custom template filters
- Implement additional data validation
- Add new report sections or formatting options

---

## 🎯 **Summary**

The Environmental Report Generator provides a complete solution for converting environmental screening data into professional reports. With multiple PDF generation options, comprehensive template support, and flexible integration capabilities, it serves as the final step in the environmental screening workflow.

**Key Benefits:**
- **Professional Output**: Publication-ready reports
- **Flexible Generation**: Multiple PDF methods
- **Data Validation**: Schema-based validation
- **Easy Integration**: Works with comprehensive query system
- **Customizable**: Template-based design system 