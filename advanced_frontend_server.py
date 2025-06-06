"""
Advanced Frontend Server
FastAPI backend that integrates the environmental screening frontend with our agent system
"""

import asyncio
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import time
import logging

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our environmental screening system
try:
    from environmental_screening_templates import (
        ScreeningRequest, 
        ScreeningResponse, 
        EnvironmentalScreeningAPI
    )
except ImportError:
    logger.warning("Environmental screening templates not found - some features may not work")

# Import the comprehensive environmental agent and structured output
try:
    from comprehensive_environmental_agent import create_comprehensive_environmental_agent, StructuredScreeningOutput
    STRUCTURED_OUTPUT_AVAILABLE = True
    logger.info("StructuredScreeningOutput imported successfully")
except ImportError as e:
    logger.warning(f"StructuredScreeningOutput not available: {e} - using legacy approach")
    STRUCTURED_OUTPUT_AVAILABLE = False
    StructuredScreeningOutput = None

# Import the comprehensive screening report tools
try:
    from comprehensive_screening_report_tool import (
        generate_comprehensive_screening_report,
        find_latest_screening_directory
    )
    REPORT_TOOLS_AVAILABLE = True
except ImportError:
    logger.warning("Comprehensive screening report tools not available")
    REPORT_TOOLS_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_existing_data()
    logger.info(f"Loaded {len(projects_db)} existing projects and {len(reports_db)} reports")
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title="Environmental Screening Platform",
    description="Advanced frontend for comprehensive environmental screening analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state management
active_screenings: Dict[str, Dict] = {}
projects_db: List[Dict] = []
reports_db: List[Dict] = []
active_batches: Dict[str, Dict] = {}

# Create a simple wrapper for the agent
class EnvironmentalScreeningAgent:
    def __init__(self):
        try:
            self.graph = create_comprehensive_environmental_agent()
            logger.info("Environmental screening agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize environmental screening agent: {e}")
            self.graph = None

    def is_ready(self) -> bool:
        """Check if the agent is ready to process requests"""
        return self.graph is not None

# Initialize our environmental agent
try:
    agent = EnvironmentalScreeningAgent()
    if not agent.is_ready():
        logger.warning("Environmental agent not ready - some features may not work")
except Exception as e:
    logger.error(f"Critical error initializing agent: {e}")
    agent = None

class ProjectRequest(BaseModel):
    project_name: str
    location_name: Optional[str] = None
    cadastral_number: Optional[str] = None
    coordinates: Optional[List[float]] = None
    analyses_requested: List[str] = []
    include_comprehensive_report: bool = True
    include_pdf: bool = True
    use_llm_enhancement: bool = True

class ScreeningStatus(BaseModel):
    status: str
    progress: float
    current_step: str
    message: str
    log_entries: List[Dict] = []
    error: Optional[str] = None

# Frontend Routes
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the advanced frontend"""
    try:
        with open("static/advanced_index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback to original frontend
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())

@app.get("/help", response_class=HTMLResponse)
async def serve_help():
    """Serve help documentation"""
    help_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Environmental Screening Platform - Help</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }
            h1, h2 { color: #2c5aa0; }
            .section { margin-bottom: 2rem; }
            code { background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Environmental Screening Platform - Help</h1>
        
        <div class="section">
            <h2>Getting Started</h2>
            <p>The Environmental Screening Platform provides comprehensive environmental analysis for development projects.</p>
            
            <h3>Project Types Supported:</h3>
            <ul>
                <li>Industrial Development</li>
                <li>Residential Development</li>
                <li>Commercial Development</li>
                <li>Marina Construction</li>
                <li>Environmental Due Diligence</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Location Specification</h2>
            <h3>Cadastral Numbers (Preferred)</h3>
            <p>Use format: <code>XXX-XXX-XXX-XX</code> (e.g., 060-000-009-58)</p>
            
            <h3>Coordinates</h3>
            <p>Provide latitude and longitude in decimal degrees</p>
            
            <h3>Interactive Map</h3>
            <p>Click on the map to select a location automatically</p>
        </div>
        
        <div class="section">
            <h2>Analysis Types</h2>
            <ul>
                <li><strong>Property & Cadastral:</strong> Land use, zoning, area measurements</li>
                <li><strong>Karst Analysis:</strong> PRAPEC karst areas (Puerto Rico)</li>
                <li><strong>Flood Analysis:</strong> FEMA flood zones, BFE requirements</li>
                <li><strong>Wetland Analysis:</strong> NWI classifications, regulatory significance</li>
                <li><strong>Critical Habitat:</strong> Endangered species, ESA compliance</li>
                <li><strong>Air Quality:</strong> Nonattainment areas, NAAQS compliance</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Reports Generated</h2>
            <ul>
                <li>Comprehensive Environmental Screening Report (11 sections)</li>
                <li>Professional PDF with embedded maps</li>
                <li>JSON data files for each analysis</li>
                <li>Individual maps and supporting documentation</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=help_content)

# API Routes
@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard statistics and recent activity"""
    # Calculate stats from current data
    total_projects = len(projects_db)
    reports_generated = len(reports_db)
    completed_projects = len([p for p in projects_db if p.get('status') == 'completed'])
    risk_areas = len([p for p in projects_db if p.get('risk_level') == 'High'])
    
    # Get recent activity
    recent_activity = []
    
    # Add recent projects
    for project in sorted(projects_db, key=lambda x: x.get('created_date', ''), reverse=True)[:5]:
        recent_activity.append({
            'timestamp': project.get('created_date', datetime.now().isoformat()),
            'description': f"Started environmental screening for {project.get('name', 'Unknown Project')}"
        })
    
    # Add recent reports
    for report in sorted(reports_db, key=lambda x: x.get('created_date', ''), reverse=True)[:3]:
        recent_activity.append({
            'timestamp': report.get('created_date', datetime.now().isoformat()),
            'description': f"Generated report: {report.get('filename', 'Unknown Report')}"
        })
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        'total_projects': total_projects,
        'reports_generated': reports_generated,
        'compliant_projects': completed_projects,
        'risk_areas': risk_areas,
        'recent_activity': recent_activity[:10]
    }

@app.post("/api/environmental-screening")
async def start_environmental_screening(request: ProjectRequest, background_tasks: BackgroundTasks):
    """Start a new environmental screening"""
    try:
        # Check if agent is available
        if not agent or not agent.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Environmental screening agent is not available. Please check server configuration."
            )
        
        # Generate unique screening ID
        screening_id = f"screening_{int(time.time())}_{len(active_screenings)}"
        
        # Initialize screening status
        screening_status = {
            "id": screening_id,
            "status": "running",
            "progress": 0,
            "message": "Initializing environmental screening...",
            "start_time": datetime.now(),
            "request": request.dict(),
            "result": None,
            "error": None,
            "log_entries": []  # Initialize log entries
        }
        
        active_screenings[screening_id] = screening_status
        
        # Start background task
        background_tasks.add_task(run_environmental_screening, screening_id, request)
        
        logger.info(f"Started environmental screening {screening_id}")
        return {"screening_id": screening_id, "status": "started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting screening: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-environmental-screening")
async def start_batch_environmental_screening(batch_request: List[ProjectRequest], background_tasks: BackgroundTasks):
    """Start multiple environmental screenings in batch"""
    try:
        # Check if agent is available
        if not agent or not agent.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Environmental screening agent is not available. Please check server configuration."
            )
        
        # Generate unique batch ID
        batch_id = f"batch_{int(time.time())}_{len(active_batches)}"
        
        # Create individual screening IDs for each item
        screening_ids = []
        batch_items = []
        
        for i, request in enumerate(batch_request):
            screening_id = f"{batch_id}_item_{i}"
            screening_ids.append(screening_id)
            
            # Initialize individual screening status
            screening_status = {
                "id": screening_id,
                "status": "pending",
                "progress": 0,
                "message": "Waiting to start...",
                "start_time": None,
                "request": request.dict(),
                "result": None,
                "error": None,
                "batch_id": batch_id,
                "batch_index": i,
                "log_entries": []
            }
            
            active_screenings[screening_id] = screening_status
            batch_items.append(screening_status)
        
        # Initialize batch status
        batch_status = {
            "id": batch_id,
            "status": "running",
            "total_items": len(batch_request),
            "completed_items": 0,
            "failed_items": 0,
            "start_time": datetime.now(),
            "screening_ids": screening_ids,
            "items": batch_items
        }
        
        active_batches[batch_id] = batch_status
        
        # Start batch processing task
        background_tasks.add_task(run_batch_screening, batch_id, batch_request)
        
        logger.info(f"Started batch screening {batch_id} with {len(batch_request)} items")
        return {
            "batch_id": batch_id, 
            "status": "started",
            "screening_ids": screening_ids,
            "total_items": len(batch_request)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch screening: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/environmental-screening/{screening_id}/status")
async def get_screening_status(screening_id: str):
    """Get the status of a screening process"""
    if screening_id not in active_screenings:
        raise HTTPException(status_code=404, detail="Screening not found")
    
    return active_screenings[screening_id]

@app.get("/api/batch-environmental-screening/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get the status of a batch screening process"""
    if batch_id not in active_batches:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch = active_batches[batch_id]
    
    # Include individual item statuses
    item_statuses = []
    for screening_id in batch["screening_ids"]:
        if screening_id in active_screenings:
            item_statuses.append(active_screenings[screening_id])
    
    return {
        **batch,
        "item_statuses": item_statuses,
        "remaining_items": batch["total_items"] - batch["completed_items"] - batch["failed_items"]
    }

@app.get("/api/projects")
async def get_projects():
    """Get all projects"""
    return {'projects': projects_db}

@app.get("/api/reports")
async def get_reports():
    """Get all reports with enhanced PDF information"""
    # Enhance reports with download URLs and categorization
    enhanced_reports = []
    
    for report in reports_db:
        enhanced_report = report.copy()
        
        # Add download URLs
        enhanced_report['download_url'] = f"/files/{report['filename']}"
        enhanced_report['preview_url'] = f"/preview/{report['filename']}"
        
        # Add specific PDF download URL if it's a PDF
        if enhanced_report.get('is_pdf'):
            enhanced_report['pdf_download_url'] = f"/pdfs/{report['filename']}"
        
        # Add file type icon
        file_ext = Path(report['filename']).suffix.lower()
        enhanced_report['file_type'] = file_ext.lstrip('.')
        enhanced_report['file_icon'] = get_file_icon(file_ext)
        
        enhanced_reports.append(enhanced_report)
    
    # Sort by creation date (newest first)
    enhanced_reports.sort(key=lambda x: x['created_date'], reverse=True)
    
    return {"reports": enhanced_reports}

@app.get("/files/{filename}")
async def download_file(filename: str):
    """Download a generated file"""
    # Look for file in output directories
    output_dir = Path("output")
    
    # Search all project directories
    for project_dir in output_dir.glob("*"):
        if project_dir.is_dir():
            # Check reports/pdfs folder first (for comprehensive PDFs)
            pdf_dir = project_dir / "reports" / "pdfs"
            if pdf_dir.exists():
                file_path = pdf_dir / filename
                if file_path.exists():
                    return FileResponse(file_path, filename=filename)
            
            # Check reports folder
            reports_dir = project_dir / "reports"
            if reports_dir.exists():
                file_path = reports_dir / filename
                if file_path.exists():
                    return FileResponse(file_path, filename=filename)
            
            # Check main project directory
            file_path = project_dir / filename
            if file_path.exists():
                return FileResponse(file_path, filename=filename)
    
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/pdfs/{filename}")
async def download_pdf(filename: str):
    """Download a PDF file specifically from the pdfs directory"""
    output_dir = Path("output")
    
    # Search all project directories for PDFs
    for project_dir in output_dir.glob("*"):
        if project_dir.is_dir():
            # Check reports/pdfs folder
            pdf_dir = project_dir / "reports" / "pdfs"
            if pdf_dir.exists():
                file_path = pdf_dir / filename
                if file_path.exists():
                    return FileResponse(
                        file_path, 
                        filename=filename,
                        media_type="application/pdf"
                    )
            
            # Also check reports folder for other PDFs
            reports_dir = project_dir / "reports"
            if reports_dir.exists():
                file_path = reports_dir / filename
                if file_path.exists() and file_path.suffix.lower() == '.pdf':
                    return FileResponse(
                        file_path, 
                        filename=filename,
                        media_type="application/pdf"
                    )
    
    raise HTTPException(status_code=404, detail="PDF file not found")

@app.get("/preview/{filename}")
async def preview_file(filename: str):
    """Preview a file (for PDFs, images, etc.)"""
    # Similar to download but with inline disposition
    output_dir = Path("output")
    
    for project_dir in output_dir.glob("*"):
        if project_dir.is_dir():
            # Check reports/pdfs folder first
            pdf_dir = project_dir / "reports" / "pdfs"
            if pdf_dir.exists():
                file_path = pdf_dir / filename
                if file_path.exists():
                    return FileResponse(
                        file_path, 
                        filename=filename,
                        headers={"Content-Disposition": "inline"}
                    )
            
            # Check reports folder
            reports_dir = project_dir / "reports"
            if reports_dir.exists():
                file_path = reports_dir / filename
                if file_path.exists():
                    return FileResponse(
                        file_path, 
                        filename=filename,
                        headers={"Content-Disposition": "inline"}
                    )
            
            file_path = project_dir / filename
            if file_path.exists():
                return FileResponse(
                    file_path, 
                    filename=filename,
                    headers={"Content-Disposition": "inline"}
                )
    
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/projects/{project_id}/download")
async def download_project_reports(project_id: str):
    """Download all reports for a project as ZIP"""
    # Find project directory
    output_dir = Path("output")
    project_dirs = list(output_dir.glob(f"*{project_id}*"))
    
    if not project_dirs:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = project_dirs[0]
    
    # Create ZIP file
    import zipfile
    zip_path = f"temp_project_{project_id}.zip"
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    zip_file.write(file_path, file_path.relative_to(project_dir))
        
        return FileResponse(
            zip_path,
            filename=f"project_{project_id}_reports.zip",
            media_type="application/zip"
        )
    finally:
        # Clean up temp file after response
        if os.path.exists(zip_path):
            os.remove(zip_path)

# Background Processing
async def process_environmental_screening(screening_id: str, request: ProjectRequest):
    """Process environmental screening in background - this is now a wrapper"""
    await run_environmental_screening(screening_id, request)

def create_screening_request(request: ProjectRequest) -> ProjectRequest:
    """Convert ProjectRequest to ScreeningRequest (now just returns the same object)"""
    return request

def generate_screening_command(screening_request: ProjectRequest) -> str:
    """Generate command for environmental screening agent"""
    
    # Determine location string
    if screening_request.cadastral_number:
        location_str = f"cadastral number {screening_request.cadastral_number}"
    elif screening_request.coordinates:
        coords = screening_request.coordinates
        location_str = f"coordinates {coords[1]}, {coords[0]}"  # lat, lng format
    else:
        location_str = screening_request.location_name or 'specified location'
    
    # Build command
    command = f"""Generate comprehensive environmental screening report for {screening_request.project_name} at {location_str}."""
    
    # Add analysis specifications
    if screening_request.analyses_requested:
        analyses_list = ', '.join(screening_request.analyses_requested)
        command += f" Include the following analyses: {analyses_list}."
    
    # Add report options
    if screening_request.include_comprehensive_report:
        command += " Generate comprehensive 11-section environmental screening report."
    
    if screening_request.include_pdf:
        command += " Generate professional PDF report with embedded maps."
    
    if screening_request.use_llm_enhancement:
        command += " Use AI-enhanced analysis for intelligent risk assessment and recommendations."
    
    return command

async def run_agent_screening(command: str) -> Dict[str, Any]:
    """Run the environmental screening agent with proper async handling"""
    try:
        # Use our comprehensive environmental agent
        # According to LangGraph docs, use ainvoke for async execution
        # When using checkpointer (MemorySaver), we need to provide config with thread_id
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        result = await agent.graph.ainvoke(
            {"messages": [{"role": "user", "content": command}]},
            config=config
        )
        
        # According to LangGraph docs, agent returns:
        # - 'messages': List of all messages exchanged during execution
        # - 'structured_response': If structured output is configured
        # - Additional state fields if using custom state schema
        
        if result and isinstance(result, dict):
            # Check for structured response first (from response_format configuration)
            if 'structured_response' in result:
                logger.info("Agent returned structured response")
                return result
            
            # If no structured response, try to extract from messages
            elif 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                
                # Check if the last message has content that might be structured JSON
                if hasattr(last_message, 'content') and last_message.content:
                    content = last_message.content
                    if isinstance(content, str) and content.strip().startswith('{'):
                        try:
                            import json
                            structured_data = json.loads(content)
                            return {'structured_response': structured_data, 'messages': result['messages']}
                        except json.JSONDecodeError:
                            logger.warning("Could not parse message content as JSON")
                    
                    # Return the content as is if not JSON
                    return {'response_content': content, 'messages': result['messages']}
                else:
                    # Return the message object as string
                    return {'response_content': str(last_message), 'messages': result['messages']}
            else:
                # Fallback: return the entire result
                return {'response_content': str(result)}
        
        # Final fallback
        return {'response_content': str(result)}
        
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        raise Exception(f"Agent execution failed: {str(e)}")

async def process_screening_response(screening_id: str, response: Dict[str, Any], request: ProjectRequest):
    """Process the agent response and extract generated files"""
    try:
        # Extract structured data from the corrected agent response format
        structured_data = None
        
        # Check for structured_response key (preferred)
        if 'structured_response' in response:
            structured_data = response['structured_response']
            logger.info("Found structured response from agent")
        
        # Fallback: check for response_content
        elif 'response_content' in response:
            response_content = response['response_content']
            # Try to parse as JSON if it's a string
            if isinstance(response_content, str) and response_content.strip().startswith('{'):
                try:
                    import json
                    structured_data = json.loads(response_content)
                    logger.info("Parsed response_content as JSON")
                except json.JSONDecodeError:
                    logger.warning("Could not parse response_content as JSON")
                    # Create a minimal structured response
                    structured_data = {
                        'success': True,
                        'project_name': request.project_name,
                        'agent_raw_response': response_content
                    }
            else:
                # Create a minimal structured response from content
                structured_data = {
                    'success': True,
                    'project_name': request.project_name,
                    'agent_raw_response': str(response_content)
                }
        
        # Final fallback: create minimal structure
        if not structured_data:
            structured_data = {
                'success': True,
                'project_name': request.project_name,
                'agent_raw_response': str(response)
            }
            logger.warning("No structured data found, created minimal response structure")
        
        # Validate the structured data using our Pydantic model if possible
        validated_output = structured_data
        try:
            if isinstance(structured_data, dict) and STRUCTURED_OUTPUT_AVAILABLE:
                validated_output = StructuredScreeningOutput(**structured_data)
                logger.info("Successfully validated structured output with Pydantic model")
            elif not STRUCTURED_OUTPUT_AVAILABLE:
                logger.info("Using legacy structured data approach - StructuredScreeningOutput not available")
        except Exception as e:
            logger.warning(f"Error validating structured output with Pydantic: {e}")
            # Continue with the dict directly
            validated_output = structured_data
        
        # Extract project information from structured output
        project_name_from_agent = getattr(validated_output, 'project_name', None) or structured_data.get('project_name')
        project_directory_from_agent = getattr(validated_output, 'project_directory', None) or structured_data.get('project_directory')
        success_status = getattr(validated_output, 'success', None) or structured_data.get('success', True)
        
        # Find the project directory - prefer agent's report, fallback to filesystem scan
        latest_dir = None
        if project_directory_from_agent:
            latest_dir = Path(project_directory_from_agent)
            if not latest_dir.exists():
                # Try relative to current directory
                latest_dir = Path.cwd() / project_directory_from_agent
        
        # If we don't have a directory from the agent, try to find the latest one
        if not latest_dir or not latest_dir.exists():
            if REPORT_TOOLS_AVAILABLE:
                # Use the find_latest_screening_directory tool
                result = find_latest_screening_directory()
                if result["success"]:
                    latest_dir = Path(result["latest_directory"])
                    logger.info(f"Found latest screening directory: {latest_dir}")
            else:
                # Fallback: scan for most recent directory
                output_dir = Path("output")
                if output_dir.exists():
                    project_dirs = sorted([d for d in output_dir.glob("*") if d.is_dir()], 
                                        key=lambda x: x.stat().st_mtime, reverse=True)
                    if project_dirs:
                        latest_dir = project_dirs[0]
        
        # If we still don't have a directory, there's a problem
        if not latest_dir or not latest_dir.exists():
            logger.error(f"Could not find project directory for screening {screening_id}")
            raise Exception("Project directory not found after agent completion")
        
        logger.info(f"Using project directory: {latest_dir}")
        
        # Check if comprehensive reports were already generated by the agent
        reports_already_generated = False
        if isinstance(structured_data, dict) and 'comprehensive_reports' in structured_data:
            comp_reports = structured_data['comprehensive_reports']
            if comp_reports and isinstance(comp_reports, dict):
                if comp_reports.get('pdf') or comp_reports.get('json_report') or comp_reports.get('markdown'):
                    reports_already_generated = True
                    logger.info("Comprehensive reports already generated by agent")
        
        # If reports weren't generated by the agent, generate them now using the tools
        if not reports_already_generated and REPORT_TOOLS_AVAILABLE:
            logger.info("Generating comprehensive reports using report generation tools...")
            try:
                # Use invoke method instead of deprecated __call__
                report_result = generate_comprehensive_screening_report.invoke({
                    "output_directory": str(latest_dir),
                    "output_format": "both",
                    "include_pdf": True,
                    "use_llm": request.use_llm_enhancement,
                    "use_professional_html_pdf": True
                })
                
                if report_result["success"]:
                    logger.info(f"Successfully generated comprehensive reports: {report_result['output_files']}")
                    # Update the structured data with the generated report paths
                    if not structured_data.get('comprehensive_reports'):
                        structured_data['comprehensive_reports'] = {}
                    
                    for file_path in report_result['output_files']:
                        file_path_obj = Path(file_path)
                        relative_path = file_path_obj.relative_to(latest_dir)
                        if file_path.endswith('.pdf'):
                            structured_data['comprehensive_reports']['pdf'] = str(relative_path)
                        elif file_path.endswith('.json'):
                            structured_data['comprehensive_reports']['json_report'] = str(relative_path)
                        elif file_path.endswith('.md'):
                            structured_data['comprehensive_reports']['markdown'] = str(relative_path)
                else:
                    logger.warning(f"Report generation failed: {report_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Error generating comprehensive reports: {e}")
        
        # Extract and catalog all generated files
        report_files_generated = []
        file_paths_to_add = []
        
        # Add comprehensive reports to the catalog
        if isinstance(structured_data, dict) and 'comprehensive_reports' in structured_data:
            comp_reports = structured_data['comprehensive_reports']
            if comp_reports and isinstance(comp_reports, dict):
                if comp_reports.get('json_report'):
                    file_paths_to_add.append({"path": comp_reports['json_report'], "category": "comprehensive_json"})
                if comp_reports.get('markdown'):
                    file_paths_to_add.append({"path": comp_reports['markdown'], "category": "comprehensive_markdown"})
                if comp_reports.get('pdf'):
                    file_paths_to_add.append({"path": comp_reports['pdf'], "category": "comprehensive_pdf"})
        
        # Extract maps from analysis sections
        analysis_sections = ['flood_analysis', 'wetland_analysis', 'habitat_analysis', 'air_quality_analysis', 'karst_analysis']
        for section_name in analysis_sections:
            # Handle both Pydantic models and dict cases properly
            if hasattr(validated_output, section_name):
                section_data = getattr(validated_output, section_name, None)
            else:
                section_data = structured_data.get(section_name) if isinstance(structured_data, dict) else None
                
            if section_data:
                # Look for map path fields ending with '_map_path'
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if key.endswith('_map_path') and value:
                            file_paths_to_add.append({"path": value, "category": "analysis_map"})
                elif hasattr(section_data, '__dict__'):
                    for key, value in section_data.__dict__.items():
                        if key.endswith('_map_path') and value:
                            file_paths_to_add.append({"path": value, "category": "analysis_map"})
        
        # Extract other maps and reports - handle both Pydantic and dict cases
        def safe_get_attr(obj, attr_name, default=None):
            """Safely get attribute from either Pydantic model or dict"""
            if hasattr(obj, attr_name):
                return getattr(obj, attr_name, default)
            elif isinstance(structured_data, dict):
                return structured_data.get(attr_name, default)
            return default
        
        other_maps = safe_get_attr(validated_output, 'maps_generated_other', [])
        if other_maps:
            for map_path in other_maps:
                file_paths_to_add.append({"path": map_path, "category": "map"})
        
        other_reports = safe_get_attr(validated_output, 'individual_analysis_reports_other', [])
        if other_reports:
            for report_path in other_reports:
                file_paths_to_add.append({"path": report_path, "category": "individual_report"})
        
        data_files = safe_get_attr(validated_output, 'data_files_supporting', [])
        if data_files:
            for data_path in data_files:
                file_paths_to_add.append({"path": data_path, "category": "data"})
        
        # Add files to reports database
        for file_info in file_paths_to_add:
            file_path = latest_dir / file_info["path"]
            
            if file_path.exists() and file_path.is_file():
                file_stat = file_path.stat()
                
                reports_db.append({
                    'filename': file_path.name,
                    'title': file_path.stem.replace('_', ' ').title(),
                    'project_id': screening_id,
                    'size': file_stat.st_size,
                    'created_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'file_path': str(file_path),
                    'category': file_info["category"],
                    'is_pdf': file_path.suffix.lower() == '.pdf',
                    'relative_path': str(file_path.relative_to(latest_dir))
                })
                report_files_generated.append(file_path)
        
        # Update project with file count and risk assessment
        project = next((p for p in projects_db if p['id'] == screening_id), None)
        if project:
            project['reports_count'] = len([r for r in reports_db if r.get('project_id') == screening_id])
            pdf_count = len([r for r in reports_db if r.get('project_id') == screening_id and r.get('is_pdf')])
            project['pdf_count'] = pdf_count
            
            # Extract risk level from structured output - handle both cases
            risk_level = safe_get_attr(validated_output, 'overall_risk_level_assessment', 'Unknown')
            project['risk_level'] = risk_level
            project['project_directory'] = str(latest_dir)
        
        update_screening_log(screening_id, f"Processed structured response. Generated {len(report_files_generated)} reports and documents.")
        logger.info(f"Successfully processed {len(report_files_generated)} files for screening {screening_id}")
        
    except Exception as e:
        logger.error(f"Error processing screening response: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update error status
        active_screenings[screening_id].update({
            'status': 'failed',
            'error': str(e),
            'message': f'Screening failed during response processing: {str(e)}'
        })
        update_project_status(screening_id, 'failed')

def update_screening_status(screening_id: str, status: str, progress: float, step: str, message: str):
    """Update screening status"""
    if screening_id in active_screenings:
        active_screenings[screening_id].update({
            'status': status,
            'progress': progress,
            'current_step': step,
            'message': message
        })
        
        # Add log entry
        active_screenings[screening_id]['log_entries'].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })

def update_screening_log(screening_id: str, message: str):
    """Add log entry to screening"""
    if screening_id in active_screenings:
        active_screenings[screening_id]['log_entries'].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })

def update_project_status(screening_id: str, status: str):
    """Update project status in database"""
    project = next((p for p in projects_db if p['id'] == screening_id), None)
    if project:
        project['status'] = status
        if status == 'completed':
            project['completed_date'] = datetime.now().isoformat()

def get_file_icon(file_extension: str) -> str:
    """Get Font Awesome icon class for file type"""
    icon_map = {
        '.pdf': 'fas fa-file-pdf',
        '.json': 'fas fa-file-code',
        '.md': 'fas fa-file-alt',
        '.png': 'fas fa-file-image',
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.txt': 'fas fa-file-text'
    }
    return icon_map.get(file_extension, 'fas fa-file')

# Load existing data on startup
def load_existing_data():
    """Load existing projects and reports from output directory"""
    output_dir = Path("output")
    if not output_dir.exists():
        return
    
    for project_dir in output_dir.glob("*"):
        if project_dir.is_dir():
            # Try to extract project info from directory name
            dir_name = project_dir.name
            
            # Create project entry
            project_id = str(uuid.uuid4())
            project = {
                'id': project_id,
                'name': dir_name.replace('_', ' ').split(' Environmental')[0],
                'description': 'Imported project',
                'location_name': None,
                'status': 'completed',
                'created_date': datetime.fromtimestamp(project_dir.stat().st_mtime).isoformat(),
                'analyses_count': 6,  # Assume full analysis
                'reports_count': 0,
                'risk_level': 'Low'
            }
            
            # Count reports
            report_count = 0
            reports_dir = project_dir / "reports"
            if reports_dir.exists():
                for file_path in reports_dir.rglob("*"):
                    if file_path.is_file():
                        report_count += 1
                        file_stat = file_path.stat()
                        reports_db.append({
                            'filename': file_path.name,
                            'title': file_path.stem.replace('_', ' ').title(),
                            'project_id': project_id,
                            'size': file_stat.st_size,
                            'created_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'file_path': str(file_path)
                        })
            
            project['reports_count'] = report_count
            projects_db.append(project)

async def run_environmental_screening(screening_id: str, request: ProjectRequest):
    """Background task to run environmental screening using the comprehensive agent"""
    try:
        screening = active_screenings[screening_id]
        screening["status"] = "running"
        screening["message"] = "Starting environmental analysis..."
        screening["progress"] = 10
        
        # Create project entry
        project = {
            'id': screening_id,
            'name': request.project_name,
            'location_name': request.location_name,
            'cadastral_number': request.cadastral_number,
            'coordinates': request.coordinates,
            'status': 'in-progress',
            'created_date': datetime.now().isoformat(),
            'analyses_requested': request.analyses_requested,
            'analyses_count': len(request.analyses_requested),
            'reports_count': 0,
            'risk_level': None
        }
        
        projects_db.append(project)
        
        # Update progress
        screening["progress"] = 20
        screening["message"] = "Preparing environmental screening command..."
        update_screening_log(screening_id, "Generating screening command from request parameters")
        
        # Generate the screening command
        command = generate_screening_command(request)
        logger.info(f"Generated screening command: {command}")
        
        # Update progress
        screening["progress"] = 30
        screening["message"] = "Running comprehensive environmental agent..."
        update_screening_log(screening_id, f"Executing agent with command: {command}")
        
        # Execute the screening using our agent with proper async handling
        response = await run_agent_screening(command)
        logger.info(f"Agent completed for screening {screening_id}")
        
        # Update progress
        screening["progress"] = 80
        screening["message"] = "Processing results and generating reports..."
        update_screening_log(screening_id, "Agent execution completed, processing response")
        
        # Process the response and extract files
        await process_screening_response(screening_id, response, request)
        
        # Update final status
        screening["status"] = "completed"
        screening["progress"] = 100
        screening["message"] = "Environmental screening completed successfully!"
        update_screening_log(screening_id, "Screening process completed successfully")
        
        # Update project status
        project['status'] = 'completed'
        project['completed_date'] = datetime.now().isoformat()
        
        logger.info(f"Screening {screening_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in screening {screening_id}: {e}")
        import traceback
        traceback.print_exc()
        
        screening = active_screenings.get(screening_id, {})
        screening["status"] = "failed"
        screening["error"] = str(e)
        screening["message"] = f"Screening failed: {str(e)}"
        update_screening_log(screening_id, f"Screening failed with error: {str(e)}")
        
        # Update project status
        project = next((p for p in projects_db if p['id'] == screening_id), None)
        if project:
            project['status'] = 'failed'
            project['error'] = str(e)

async def run_batch_screening(batch_id: str, batch_requests: List[ProjectRequest]):
    """Background task to run batch environmental screening"""
    try:
        batch = active_batches[batch_id]
        
        for i, request in enumerate(batch_requests):
            screening_id = f"{batch_id}_item_{i}"
            
            # Update batch status
            batch["status"] = "processing"
            
            # Run individual screening
            await run_environmental_screening(screening_id, request)
            
            # Update batch counters based on result
            screening = active_screenings[screening_id]
            if screening["status"] == "completed":
                batch["completed_items"] += 1
            elif screening["status"] == "failed":
                batch["failed_items"] += 1
        
        # Complete batch
        batch["status"] = "completed"
        batch["end_time"] = datetime.now()
        
        logger.info(f"Batch {batch_id} completed: {batch['completed_items']}/{batch['total_items']} successful")
        
    except Exception as e:
        logger.error(f"Error in batch {batch_id}: {e}")
        batch = active_batches.get(batch_id, {})
        batch["status"] = "failed"
        batch["error"] = str(e)

async def _generate_sophisticated_pdf_from_structured_data(screening_id: str, structured_data: dict, project_directory: Path):
    """Generate sophisticated PDF using structured data from agent response"""
    try:
        # Check if sophisticated PDF generation is available
        try:
            from pdf_report_generator import StructuredPDFGenerator, STRUCTURED_OUTPUT_AVAILABLE
            if not STRUCTURED_OUTPUT_AVAILABLE:
                print(f"⚠️ Structured PDF generation not available for {screening_id}")
                return
        except ImportError:
            print(f"⚠️ PDF generation modules not available for {screening_id}")
            return
        
        # Extract the structured data (either from StructuredScreeningOutput or raw dict)
        if hasattr(structured_data, '__dict__'):
            # Convert Pydantic model to dict
            data_dict = structured_data.dict() if hasattr(structured_data, 'dict') else structured_data.__dict__
        else:
            data_dict = structured_data
        
        print(f"📄 Generating sophisticated PDF for {screening_id} using structured data...")
        
        # Create sophisticated PDF generator
        pdf_generator = StructuredPDFGenerator(
            structured_data=data_dict,
            project_directory=str(project_directory),
            use_llm=True  # Use LLM enhancement if available
        )
        
        # Generate the PDF
        project_name = data_dict.get('project_name', 'Environmental_Screening')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"sophisticated_screening_report_{project_name}_{timestamp}.pdf"
        
        pdf_path = pdf_generator.generate_sophisticated_pdf_report(pdf_filename)
        
        # Add to reports database
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            file_stat = pdf_file.stat()
            reports_db.append({
                'filename': pdf_file.name,
                'title': 'Sophisticated Environmental Screening Report',
                'project_id': screening_id,
                'size': file_stat.st_size,
                'created_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'file_path': str(pdf_file),
                'category': 'sophisticated_pdf',
                'is_pdf': True,
                'relative_path': f"reports/{pdf_file.name}"
            })
            
            update_screening_log(screening_id, f"Generated sophisticated PDF report: {pdf_file.name}")
            print(f"✅ Sophisticated PDF generated for {screening_id}: {pdf_file.name}")
            
            # Update project PDF count
            project = next((p for p in projects_db if p['id'] == screening_id), None)
            if project:
                project['pdf_count'] = project.get('pdf_count', 0) + 1
        
    except Exception as e:
        print(f"⚠️ Failed to generate sophisticated PDF for {screening_id}: {e}")
        update_screening_log(screening_id, f"Sophisticated PDF generation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "advanced_frontend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 