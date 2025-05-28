# Advanced Environmental Screening Platform Frontend

A comprehensive, modern web interface for environmental screening analysis with full integration to our LangGraph agent system.

![Environmental Screening Platform](https://img.shields.io/badge/Status-Production%20Ready-green)
![Platform](https://img.shields.io/badge/Platform-Web-blue)
![Technology](https://img.shields.io/badge/Tech-FastAPI%20%2B%20Vanilla%20JS-orange)

## 🌟 Features

### **Modern Dashboard Interface**
- Real-time project statistics and metrics
- Recent activity tracking
- Interactive navigation and status indicators
- Responsive design for all device sizes

### **Comprehensive Project Management**
- **Multi-input Location Specification**:
  - Cadastral numbers (preferred format: XXX-XXX-XXX-XX)
  - Latitude/longitude coordinates
  - Interactive Leaflet map with click-to-select
- **Project Type Templates**:
  - Industrial Development Environmental Assessment
  - Residential Development Environmental Assessment
  - Commercial Development Environmental Assessment
  - Marina Construction Environmental Screening
  - Environmental Due Diligence Assessment
  - Custom Environmental Screening

### **Advanced Analysis Configuration**
- **Configurable Analysis Types**:
  - ✅ Property & Cadastral Analysis
  - ✅ PRAPEC Karst Analysis (Puerto Rico)
  - ✅ FEMA Flood Analysis
  - ✅ National Wetland Inventory Analysis
  - ✅ Critical Habitat Analysis
  - ✅ Air Quality Nonattainment Analysis
- **Report Generation Options**:
  - Comprehensive 11-section environmental reports
  - Professional PDF generation with embedded maps
  - AI-enhanced risk assessment and recommendations

### **Real-time Progress Monitoring**
- Live progress tracking with percentage completion
- Step-by-step process visualization
- Real-time log streaming during analysis
- Background processing with status updates

### **Comprehensive Report Management**
- File browser with preview capabilities
- Download individual reports or complete project packages
- Support for multiple file formats (PDF, JSON, PNG, Markdown)
- Automatic file organization and metadata tracking

## 🏗️ Architecture

### **Frontend Components**
```
static/
├── advanced_index.html          # Main application interface
├── advanced_styles.css          # Comprehensive styling system
└── environmental_screening_app.js # Full-featured JavaScript application
```

### **Backend Integration**
```
advanced_frontend_server.py     # FastAPI server with full API
environmental_screening_templates.py # Integration templates
comprehensive_environmental_agent.py # LangGraph agent system
```

### **Key Technologies**
- **Frontend**: Vanilla JavaScript ES6+, CSS Grid/Flexbox, Leaflet Maps
- **Backend**: FastAPI, Pydantic, asyncio background processing
- **Maps**: Leaflet with OpenStreetMap tiles
- **Charts**: Chart.js for data visualization
- **Icons**: Font Awesome 6.5.0

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
pip install fastapi uvicorn pydantic
```

### **2. Launch the Platform**
```bash
python launch_advanced_frontend.py
```

### **3. Access the Interface**
- **Main Application**: http://localhost:8000
- **Help Documentation**: http://localhost:8000/help
- **API Documentation**: http://localhost:8000/docs

## 📊 Dashboard Overview

The main dashboard provides:
- Project statistics and completion metrics
- Recent activity feed with timestamps
- Quick action buttons for common tasks
- System status indicators

## 🔄 Batch Screening Guide

### Creating a Batch Queue

1. **Navigate to Batch Screening**: Click the "Batch Screening" tab in the navigation
2. **Configure Global Settings**: Set default project types, analysis options, and report preferences
3. **Add Items**: Use one of the following methods:

#### Manual Entry
- Click "Add Item" to create individual screening requests
- Fill in project details, location information, and specific settings
- Each item can override global settings if needed

#### CSV Import
Create a CSV file with the following supported columns:
```csv
project_name,cadastral_number,location_name,project_type,longitude,latitude
Industrial Site Alpha,060-000-009-58,Toa Baja,Industrial Development Environmental Assessment,,
Residential Complex Beta,060-000-010-25,Toa Alta,Residential Development Environmental Assessment,,
Marina Project,060-000-012-45,Dorado,Marina Construction Environmental Screening,,
Coordinates Project,,San Juan,Commercial Development Environmental Assessment,-66.1057,18.4655
```

#### Text File Import
Simple text file with one cadastral number per line:
```
060-000-009-58
060-000-010-25
060-000-011-33
```

#### JSON Batch Configuration
```json
[
  {
    "projectName": "Industrial Site Alpha",
    "cadastralNumber": "060-000-009-58",
    "locationName": "Toa Baja",
    "projectDescription": "Industrial Development Environmental Assessment",
    "analyses": ["property", "karst", "flood", "wetland"],
    "reportOptions": {
      "comprehensive": true,
      "pdf": true,
      "llmEnhancement": true
    }
  }
]
```

### Processing Configuration

#### Processing Modes
- **Sequential**: Items processed one at a time (recommended for resource management)
- **Parallel**: Multiple items processed simultaneously (faster but resource-intensive)
- **Timed**: Sequential with configurable delays (useful for API rate limiting)

#### Notification Settings
- **Each Completion**: Notified when each individual item completes
- **Batch Completion**: Single notification when entire batch finishes
- **Errors Only**: Notifications only for failed items

### Monitoring Batch Progress

The batch progress modal shows:
- **Overall Statistics**: Total, completed, failed, and remaining items
- **Progress Bar**: Visual completion percentage
- **Individual Item Status**: Real-time status for each item in the queue
- **Live Log**: Detailed progress messages and error information
- **Control Options**: Pause, resume, or cancel batch processing

### Best Practices

1. **Start Small**: Test with 2-3 items before running large batches
2. **Use Sequential Mode**: For most cases to avoid overwhelming the system
3. **Monitor Progress**: Keep the progress modal open to track issues
4. **Backup Data**: Export your batch configuration before starting
5. **Network Stability**: Ensure stable internet connection for long batches

## 🗺️ Location Specification

### **Step 1: Project Information**
- Project name and description
- Location specification
- Project type selection from templates

### **Step 2: Location Specification**
Choose from three methods:
1. **Cadastral Number** (most accurate)
2. **Coordinate Entry** (decimal degrees)
3. **Interactive Map** (click to select)

### **Step 3: Analysis Configuration**
Select required environmental analyses:
- Property & cadastral information
- Karst geological features
- Flood zone assessments
- Wetland classifications
- Critical habitat evaluations
- Air quality compliance

### **Step 4: Report Options**
Configure output preferences:
- Comprehensive screening report
- Professional PDF generation
- AI-enhanced analysis

### **Step 5: Real-time Processing**
Monitor progress through:
- Visual progress indicators
- Step-by-step status updates
- Live log streaming
- Completion notifications

## 📱 User Interface Features

### **Responsive Design**
- Mobile-friendly interface
- Tablet optimization
- Desktop full-feature experience
- Consistent user experience across devices

### **Interactive Elements**
- **Form Validation**: Real-time field validation with error messaging
- **Auto-formatting**: Cadastral number format assistance
- **Map Integration**: Interactive location selection
- **Progress Modals**: Beautiful progress tracking overlays
- **Toast Notifications**: Non-intrusive status updates

### **Accessibility Features**
- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- High contrast color schemes
- Screen reader compatibility

## 🔌 API Integration

### **Core Endpoints**

#### **Dashboard Data**
```http
GET /api/dashboard
```
Returns comprehensive dashboard statistics and recent activity.

#### **Start Environmental Screening**
```http
POST /api/environmental-screening
Content-Type: application/json

{
  "project_name": "Cytoimmune Toa BAJA",
  "project_description": "Industrial Development Environmental Assessment",
  "cadastral_number": "060-000-009-58",
  "analyses_requested": ["property", "karst", "flood", "wetland", "habitat", "air_quality"],
  "include_comprehensive_report": true,
  "include_pdf": true,
  "use_llm_enhancement": true
}
```

#### **Monitor Progress**
```http
GET /api/environmental-screening/{screening_id}/status
```
Returns real-time progress updates and log entries.

#### **Project Management**
```http
GET /api/projects          # List all projects
GET /api/reports           # List all reports
GET /files/{filename}      # Download specific file
GET /preview/{filename}    # Preview file in browser
```

## 🎨 Customization

### **Styling System**
The CSS uses a comprehensive design system with CSS custom properties:

```css
:root {
    --primary-color: #2c5aa0;
    --secondary-color: #4a90e2;
    --accent-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
    --success-color: #27ae60;
    /* ... */
}
```

### **Component Architecture**
- Modular JavaScript classes
- Event-driven architecture
- Separation of concerns
- Easy extensibility

## 🔍 Example Usage

### **Industrial Development Project**
```javascript
const projectData = {
    project_name: "Industrial Facility Expansion",
    project_description: "Industrial Development Environmental Assessment",
    location_name: "Toa Baja, Puerto Rico",
    cadastral_number: "060-000-009-58",
    analyses_requested: [
        "property", "karst", "flood", 
        "wetland", "habitat", "air_quality"
    ],
    include_comprehensive_report: true,
    include_pdf: true,
    use_llm_enhancement: true
};
```

### **Marina Construction Project**
```javascript
const marinaProject = {
    project_name: "Waterfront Marina Development",
    project_description: "Marina Construction Environmental Screening",
    location_name: "Cataño, Puerto Rico",
    coordinates: [-66.150906, 18.434059],
    analyses_requested: ["flood", "wetland", "habitat"],
    include_comprehensive_report: true,
    include_pdf: true
};
```

## 🛡️ Error Handling

### **Frontend Error Management**
- Comprehensive form validation
- Network error recovery
- Graceful degradation
- User-friendly error messages
- Automatic retry mechanisms

### **Backend Error Handling**
- Structured error responses
- Background task error tracking
- File system error management
- Agent execution error recovery

## 📈 Performance Features

### **Optimization Strategies**
- Lazy loading of map components
- Efficient file scanning algorithms
- Background processing for heavy operations
- Minimal JavaScript bundle size
- CSS optimization and minification

### **Real-time Updates**
- WebSocket-style progress monitoring
- Periodic data refresh
- Efficient DOM manipulation
- Memory leak prevention

## 🔐 Security Considerations

### **Input Validation**
- Server-side validation for all inputs
- XSS prevention measures
- CSRF protection
- File upload validation

### **API Security**
- CORS configuration
- Request rate limiting
- Input sanitization
- Secure file serving

## 📚 Integration with Existing System

### **Template Integration**
The frontend seamlessly integrates with our existing template system:
- `ScreeningRequest` and `ScreeningResponse` dataclasses
- `EnvironmentalScreeningAPI` templates
- Response parsing and extraction functions

### **Agent Integration**
Direct integration with the LangGraph agent:
- `EnvironmentalScreeningAgent` execution
- Command generation from form data
- Response processing and file extraction

## 🎯 Future Enhancements

### **Planned Features**
- [ ] User authentication and project ownership
- [ ] Advanced data visualization and charts
- [ ] Export capabilities to multiple formats
- [ ] Integration with external GIS systems
- [ ] Mobile app companion
- [ ] Advanced search and filtering
- [ ] Project templates and saved configurations
- [ ] Collaboration features and sharing
- [ ] API key management for external services
- [ ] Automated report scheduling

### **Technical Improvements**
- [ ] Progressive Web App (PWA) capabilities
- [ ] Offline mode support
- [ ] Advanced caching strategies
- [ ] Database integration for persistence
- [ ] Microservices architecture
- [ ] Container deployment support

## 🤝 Contributing

This advanced frontend system is designed to be easily extensible and maintainable. Key areas for contribution:

1. **UI/UX Improvements**: Enhanced user experience features
2. **New Analysis Types**: Additional environmental screening modules
3. **Report Templates**: New output formats and styling
4. **Integration Modules**: External service connections
5. **Performance Optimizations**: Speed and efficiency improvements

## 📄 License

This software is part of the Environmental Screening Platform and follows the same licensing terms as the main project.

## 🎯 Key Features

### Multi-Input Location Specification
- **Cadastral Numbers**: Standard Puerto Rico format (XXX-XXX-XXX-XX)
- **Geographic Coordinates**: Latitude/Longitude decimal degrees
- **Interactive Map**: Click-to-select with Leaflet integration

### Batch Screening Capabilities
- **Multiple Property Processing**: Queue multiple screenings for efficient processing
- **Flexible Input Methods**: 
  - Manual item-by-item entry
  - CSV file import with customizable columns
  - Text file import (one cadastral per line)
  - JSON batch configuration files
- **Processing Modes**:
  - Sequential: Process one item at a time
  - Parallel: Process multiple items simultaneously
  - Timed: Add delays between items for rate limiting
- **Real-time Monitoring**: Track progress of entire batch with individual item status
- **Global Configuration**: Set default analysis types and report options for all items
- **Notification Options**: Configure when to receive completion notifications

### Project Templates

---

**🌱 Environmental Screening Platform** - *Comprehensive environmental analysis made simple* 

## PDF Report Organization & Downloads

### Enhanced PDF Structure
The system now organizes PDF reports in a dedicated folder structure for better management:

```
output/
├── [Project_Name]/
│   ├── reports/
│   │   ├── pdfs/                           # 📁 Dedicated PDF folder
│   │   │   ├── comprehensive_report.pdf    # 🎯 Main comprehensive report
│   │   │   └── other_comprehensive.pdf     # Additional comprehensive PDFs
│   │   ├── supporting_report.pdf           # Supporting documents
│   │   ├── data_file.json                  # Data files
│   │   └── report.md                       # Markdown reports
│   └── maps/
│       └── various_maps.pdf
```

### Download Features

#### Frontend Downloads
- **Direct Download**: Click "Download PDF" button on comprehensive reports
- **Preview**: View PDFs in browser before downloading
- **Copy Link**: Share direct download links with others
- **Enhanced Sharing**: Use native share API when available

#### API Endpoints
- `/files/{filename}` - Download any generated file
- `/pdfs/{filename}` - Specific PDF download with proper MIME type
- `/preview/{filename}` - Preview files in browser

#### Report Categories
The frontend now categorizes reports for better organization:
- **Comprehensive PDFs**: Complete 11-section environmental reports
- **Supporting Documents**: Maps, analysis files, and supplementary reports
- **Data Files**: JSON and Markdown exports

### Visual Enhancements
- Comprehensive PDFs are visually highlighted with special styling
- Badge indicators show report types
- File size and format information displayed
- Animated highlighting for important comprehensive reports

### Usage Examples
1. **Download Comprehensive Report**: Automatically opens in new tab
2. **Share Report**: Uses native sharing or copies download link
3. **Preview**: View PDF content without downloading
4. **Copy Link**: Share direct access with team members 