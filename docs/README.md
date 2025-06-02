# Environmental Screening Chat Application

A modern web-based chat interface for comprehensive environmental screening using LangGraph agents. This application provides an interactive way to perform complete environmental assessments including both FEMA flood analysis and wetland analysis for any location.

## 🌍 Features

### Comprehensive Environmental Screening
- **Dual Analysis Capability**: Both flood and wetland analysis in a single platform
- **Complete FEMA Reports**: Generate FIRMette, Preliminary Comparison, and ABFE maps
- **Wetland Assessment**: NWI analysis with adaptive mapping and regulatory guidance
- **Detailed Environmental Information**: Extract flood zones, wetland classifications, and regulatory requirements
- **Risk Assessment**: Insurance requirements, permit needs, and environmental compliance
- **Real-time Processing**: WebSocket-based chat with live status updates

### Modern Web Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Chat**: WebSocket connection with fallback to HTTP API
- **File Management**: Download and manage generated flood reports
- **Example Queries**: Pre-built examples for common flood analysis requests
- **Connection Status**: Live connection monitoring with auto-reconnect

### Advanced Features
- **Intelligent Tool Selection**: Automatically uses both tools for comprehensive screening
- **Concurrent Report Generation**: Faster processing with parallel report creation
- **Structured Data Extraction**: Organized environmental information with primary identifiers
- **Adaptive Mapping**: Wetland maps with intelligent buffer sizing and base map selection
- **Error Handling**: Graceful error handling with user-friendly messages
- **File Downloads**: Direct access to generated PDF reports and maps

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google API key for Gemini (or other supported LLM provider)

### Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have these files in your directory:
   # - app.py
   # - comprehensive_flood_agent.py
   # - comprehensive_flood_tool.py
   # - requirements.txt
   # - static/index.html
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   ```bash
   export GOOGLE_API_KEY="your-google-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   GOOGLE_API_KEY=your-google-api-key-here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to: http://localhost:8000

## 🎯 Usage Examples

### Complete Environmental Screening
```
Generate a comprehensive environmental screening report for Cataño, Puerto Rico at coordinates -66.150906, 18.434059
```

### Combined Flood and Wetland Assessment
```
I need a complete environmental assessment including flood and wetland analysis for Miami, Florida coordinates -80.1918, 25.7617
```

### Flood Analysis Only
```
Perform flood analysis only for coordinates -80.1918, 25.7617 including FIRM, pFIRM, and ABFE reports
```

### Wetland Analysis Only
```
Analyze wetland conditions and generate wetland map for coordinates -66.199399, 18.408303
```

### Regulatory Screening
```
What are the flood and wetland risks for Bayamón, Puerto Rico at coordinates -66.199399, 18.408303? Include all documents.
```

## 📊 API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message to the flood analysis agent
- `WebSocket /ws` - Real-time chat connection

### File Management
- `GET /files` - List all generated flood analysis files
- `GET /files/{filename}` - Download a specific file
- `DELETE /files/{filename}` - Delete a specific file

### Utility Endpoints
- `GET /health` - Check system health and configuration
- `GET /examples` - Get example queries for the agent
- `GET /` - Serve the main chat interface

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Required for Google Gemini API access
- `OPENAI_API_KEY` - Alternative: Use OpenAI GPT models
- `ANTHROPIC_API_KEY` - Alternative: Use Anthropic Claude models

### Changing the LLM Provider
Edit `comprehensive_flood_agent.py` to use different models:

```python
# For OpenAI
model = "openai:gpt-4o-mini"

# For Anthropic
model = "anthropic:claude-3-5-haiku-latest"

# For Google (default)
model = "google_genai:gemini-2.5-flash-preview-04-17"
```

## 📁 Project Structure

```
screeningagent/
├── app.py                          # FastAPI application
├── comprehensive_flood_agent.py    # LangGraph agent implementation
├── comprehensive_flood_tool.py     # Flood analysis tool
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── static/
│   └── index.html                  # Web interface
├── output/                         # Generated flood reports (auto-created)
└── FloodINFO/                      # Flood data processing modules
    ├── query_coordinates_data.py
    ├── firmette_client.py
    ├── preliminary_comparison_client.py
    └── abfe_client.py
```

## 🌐 Web Interface Features

### Chat Interface
- **Modern Design**: Clean, responsive interface with gradient backgrounds
- **Message Types**: User messages, agent responses, status updates, and errors
- **Auto-resize**: Input field automatically adjusts to content
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new lines

### Sidebar Features
- **Example Queries**: Click to populate input with pre-built examples
- **File Management**: View, download, and delete generated reports
- **Real-time Updates**: File list updates automatically after report generation

### Connection Management
- **WebSocket Connection**: Real-time communication with auto-reconnect
- **Fallback Support**: HTTP API fallback if WebSocket fails
- **Status Indicator**: Visual connection status with pulse animation

## 🔍 Flood Analysis Capabilities

### Report Generation
1. **FIRMette (FIRM)**: Official flood insurance rate maps
2. **Preliminary Comparison**: Shows upcoming flood map changes
3. **ABFE Maps**: Advisory Base Flood Elevation data

### Data Extraction
- **Floodplain Information**: IDs, names, and jurisdictions
- **FIRM Panel Details**: Panel numbers, types, and effective dates
- **Flood Zone Designations**: A, AE, X, VE zones with descriptions
- **Base Flood Elevations**: Elevation requirements for construction
- **Political Jurisdictions**: Community and state information

### Risk Assessment
- **Insurance Requirements**: Mandatory vs. recommended coverage
- **Floodplain Status**: High-risk vs. minimal risk areas
- **Preliminary Changes**: Upcoming map updates and impacts
- **Construction Guidance**: Elevation and building requirements

## 🛠️ Development

### Running in Development Mode
```bash
# With auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Or use the built-in runner
python app.py
```

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

### WebSocket Testing
Use the browser console to test WebSocket connections:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.send(JSON.stringify({message: "Test flood analysis"}));
```

## 🚨 Troubleshooting

### Common Issues

1. **Agent Initialization Failed**
   - Check that your API key is set correctly
   - Verify the API key has the necessary permissions
   - Try using a different LLM provider

2. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify the port 8000 is available
   - Use HTTP API as fallback

3. **Report Generation Errors**
   - Ensure FloodINFO modules are available
   - Check internet connectivity for FEMA services
   - Verify coordinates are valid (longitude, latitude format)

4. **File Download Issues**
   - Check that the `output/` directory exists and is writable
   - Verify file permissions
   - Ensure sufficient disk space

### Debug Mode
Enable debug logging by setting the log level:
```bash
uvicorn app:app --log-level debug
```

## 📝 License

This project is provided as-is for educational and research purposes. Please ensure compliance with FEMA data usage policies and terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the health endpoint at `/health`
4. Examine server logs for detailed error information

---

**Note**: This application requires active internet connectivity to access FEMA flood data services and generate reports. Generated reports are for informational purposes and should be verified with official FEMA sources for regulatory compliance. 