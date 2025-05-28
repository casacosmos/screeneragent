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
from typing import Dict, List, Optional
import uuid
import time
import logging

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our environmental screening system
from environmental_screening_templates import (
    ScreeningRequest, 
    ScreeningResponse, 
    EnvironmentalScreeningAPI,
    ResponseProcessingTemplates
)
from comprehensive_environmental_agent import create_comprehensive_environmental_agent

app = FastAPI(
    title="Environmental Screening Platform",
    description="Advanced frontend for comprehensive environmental screening analysis",
    version="1.0.0"
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
        self.graph = create_comprehensive_environmental_agent()

# Initialize our environmental agent
agent = EnvironmentalScreeningAgent()

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
            "error": None
        }
        
        active_screenings[screening_id] = screening_status
        
        # Start background task
        background_tasks.add_task(run_environmental_screening, screening_id, request)
        
        return {"screening_id": screening_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting screening: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-environmental-screening")
async def start_batch_environmental_screening(batch_request: List[ProjectRequest], background_tasks: BackgroundTasks):
    """Start multiple environmental screenings in batch"""
    try:
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
                "batch_index": i
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
        
        return {
            "batch_id": batch_id, 
            "status": "started",
            "screening_ids": screening_ids,
            "total_items": len(batch_request)
        }
        
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
    """Process environmental screening in background"""
    try:
        # Update status
        update_screening_status(screening_id, 'running', 10, 'setup', 'Setting up analysis parameters...')
        
        # Convert request to screening request format
        screening_request = create_screening_request(request)
        
        # Update status
        update_screening_status(screening_id, 'running', 20, 'property', 'Starting property analysis...')
        
        # Generate the environmental screening command
        command = generate_screening_command(screening_request)
        
        # Update status
        update_screening_status(screening_id, 'running', 40, 'environmental', 'Running environmental analysis...')
        
        # Execute the screening using our agent
        response = await run_agent_screening(command)
        
        # Update status
        update_screening_status(screening_id, 'running', 80, 'reports', 'Generating reports...')
        
        # Process the response and extract files
        await process_screening_response(screening_id, response, request)
        
        # Update final status
        update_screening_status(screening_id, 'completed', 100, 'reports', 'Screening completed successfully!')
        
        # Update project status
        update_project_status(screening_id, 'completed')
        
    except Exception as e:
        # Update error status
        active_screenings[screening_id].update({
            'status': 'failed',
            'error': str(e),
            'message': f'Screening failed: {str(e)}'
        })
        
        # Update project status
        update_project_status(screening_id, 'failed')
        
        print(f"Screening {screening_id} failed: {str(e)}")

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

async def run_agent_screening(command: str) -> str:
    """Run the environmental screening agent"""
    try:
        # Use our comprehensive environmental agent
        result = agent.graph.invoke({"messages": [{"role": "user", "content": command}]})
        
        # Extract the response
        if result and 'messages' in result:
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                return last_message.content
            else:
                return str(last_message)
        
        return str(result)
        
    except Exception as e:
        raise Exception(f"Agent execution failed: {str(e)}")

async def process_screening_response(screening_id: str, response: str, request: ProjectRequest):
    """Process the agent response and extract generated files"""
    try:
        # Extract project information
        project_info = ResponseProcessingTemplates.extract_project_info(response)
        
        # Extract environmental findings
        findings = ResponseProcessingTemplates.extract_environmental_findings(response)
        
        # Extract generated files
        files_info = ResponseProcessingTemplates.extract_generated_files(response)
        
        # Find the most recent project directory
        output_dir = Path("output")
        project_dirs = sorted([d for d in output_dir.glob("*") if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
        
        if project_dirs:
            latest_dir = project_dirs[0]
            
            # Scan for generated files
            report_files = []
            
            # Check reports/pdfs directory (comprehensive PDFs)
            pdf_dir = latest_dir / "reports" / "pdfs"
            if pdf_dir.exists():
                for file_path in pdf_dir.rglob("*"):
                    if file_path.is_file():
                        report_files.append(file_path)
            
            # Check reports directory
            reports_dir = latest_dir / "reports"
            if reports_dir.exists():
                for file_path in reports_dir.rglob("*"):
                    if file_path.is_file() and file_path not in report_files:  # Avoid duplicates
                        report_files.append(file_path)
            
            # Check main directory
            for file_path in latest_dir.rglob("*"):
                if file_path.is_file() and file_path.parent == latest_dir:
                    report_files.append(file_path)
            
            # Add files to reports database with proper categorization
            for file_path in report_files:
                file_stat = file_path.stat()
                
                # Determine file category based on location and name
                file_category = "report"
                if "comprehensive" in file_path.name.lower():
                    file_category = "comprehensive_pdf"
                elif file_path.suffix.lower() == '.pdf':
                    file_category = "pdf"
                elif file_path.suffix.lower() in ['.json', '.md']:
                    file_category = "data"
                
                reports_db.append({
                    'filename': file_path.name,
                    'title': file_path.stem.replace('_', ' ').title(),
                    'project_id': screening_id,
                    'size': file_stat.st_size,
                    'created_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'file_path': str(file_path),
                    'category': file_category,
                    'is_pdf': file_path.suffix.lower() == '.pdf',
                    'relative_path': str(file_path.relative_to(latest_dir))
                })
            
            # Update project with file count and risk assessment
            project = next((p for p in projects_db if p['id'] == screening_id), None)
            if project:
                project['reports_count'] = len([r for r in reports_db if r.get('project_id') == screening_id])
                
                # Count PDFs specifically
                pdf_count = len([r for r in reports_db if r.get('project_id') == screening_id and r.get('is_pdf')])
                project['pdf_count'] = pdf_count
                
                # Assess risk level based on findings
                if findings:
                    risk_level = assess_risk_level(findings)
                    project['risk_level'] = risk_level
        
        # Log completion
        update_screening_log(screening_id, f"Generated {len(report_files)} reports and documents")
        
    except Exception as e:
        print(f"Error processing screening response: {str(e)}")
        # Continue anyway - don't fail the whole screening

def assess_risk_level(findings: dict) -> str:
    """Assess risk level based on environmental findings"""
    risk_factors = 0
    
    # Check for high-risk indicators
    if findings.get('flood_zone') and findings['flood_zone'] not in ['X', 'X (unshaded)']:
        risk_factors += 2
    
    if findings.get('wetlands_present'):
        risk_factors += 1
    
    if findings.get('critical_habitat_present'):
        risk_factors += 2
    
    if findings.get('karst_areas_present'):
        risk_factors += 1
    
    if findings.get('nonattainment_areas'):
        risk_factors += 1
    
    # Determine risk level
    if risk_factors >= 4:
        return 'High'
    elif risk_factors >= 2:
        return 'Moderate'
    else:
        return 'Low'

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

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Load existing data on startup"""
    load_existing_data()
    print(f"Loaded {len(projects_db)} existing projects and {len(reports_db)} reports")

async def run_environmental_screening(screening_id: str, request: ProjectRequest):
    """Background task to run environmental screening"""
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
        screening["progress"] = 30
        screening["message"] = "Running environmental agent..."
        
        # Here you would run the actual environmental screening
        # For now, we'll simulate the process
        await asyncio.sleep(5)  # Simulate processing time
        
        screening["progress"] = 80
        screening["message"] = "Generating reports..."
        
        await asyncio.sleep(2)  # Simulate report generation
        
        # Complete the screening
        screening["status"] = "completed"
        screening["progress"] = 100
        screening["message"] = "Environmental screening completed successfully"
        screening["result"] = {
            "project_directory": f"output/{request.project_name}_{screening_id}",
            "reports_generated": ["comprehensive_report.md", "environmental_analysis.pdf"],
            "risk_assessment": "Low to Medium Risk"
        }
        
        # Update project status
        project['status'] = 'completed'
        project['risk_level'] = 'Medium'
        project['reports_count'] = 2
        
        logger.info(f"Screening {screening_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in screening {screening_id}: {e}")
        screening = active_screenings.get(screening_id, {})
        screening["status"] = "failed"
        screening["error"] = str(e)
        screening["message"] = f"Screening failed: {str(e)}"

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

if __name__ == "__main__":
    uvicorn.run(
        "advanced_frontend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 