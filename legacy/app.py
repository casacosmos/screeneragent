#!/usr/bin/env python3
"""
FastAPI Backend for Comprehensive Environmental Screening Platform

This application provides a web-based interface for comprehensive environmental
screening including batch processing, individual screenings, and report generation.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Disable WebSocket support to avoid compatibility issues
WEBSOCKET_AVAILABLE = False
print("⚠️ WebSocket disabled - using HTTP API only for better compatibility")

from langchain_core.messages import HumanMessage
from comprehensive_environmental_agent import create_comprehensive_environmental_agent

# Initialize FastAPI app
app = FastAPI(
    title="Environmental Screening Platform",
    description="Comprehensive environmental screening platform with batch processing capabilities",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create output directory for reports
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Global agent instance
agent = None

# In-memory storage for screening jobs (in production, use a database)
screening_jobs = {}
screening_lock = threading.Lock()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    analysis_data: Optional[Dict[str, Any]] = None
    generated_files: Optional[List[str]] = None

class ScreeningRequest(BaseModel):
    projectName: str
    projectDescription: Optional[str] = None
    locationName: Optional[str] = None
    cadastralNumber: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    analyses: Optional[List[str]] = None
    includeComprehensiveReport: bool = True
    includePdf: bool = True
    useLlmEnhancement: bool = True

class ScreeningResponse(BaseModel):
    screening_id: str
    status: str
    message: str

class ScreeningStatus(BaseModel):
    screening_id: str
    status: str
    progress: int
    message: str
    start_time: str
    end_time: Optional[str] = None
    output_directory: Optional[str] = None
    generated_files: Optional[List[str]] = None
    error: Optional[str] = None

class DashboardData(BaseModel):
    total_projects: int
    reports_generated: int
    risk_areas: int
    compliant_projects: int
    recent_activity: List[Dict[str, Any]]

class ProjectData(BaseModel):
    id: str
    name: str
    location: str
    status: str
    created_date: str
    risk_level: str
    reports_count: int

class ReportData(BaseModel):
    id: str
    filename: str
    project_name: str
    created_date: str
    file_size: int
    category: str
    download_url: str

def initialize_agent():
    """Initialize the comprehensive environmental screening agent"""
    global agent
    
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    try:
        agent = create_comprehensive_environmental_agent()
        print("✅ Environmental screening agent initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        raise

def create_screening_job(screening_id: str, request_data: ScreeningRequest):
    """Create a new screening job"""
    with screening_lock:
        screening_jobs[screening_id] = {
            "id": screening_id,
            "status": "pending",
            "progress": 0,
            "message": "Screening queued",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "request_data": request_data.dict(),
            "output_directory": None,
            "generated_files": [],
            "error": None
        }

def update_screening_status(screening_id: str, status: str, progress: int = None, message: str = None, error: str = None):
    """Update screening job status"""
    with screening_lock:
        if screening_id in screening_jobs:
            job = screening_jobs[screening_id]
            job["status"] = status
            if progress is not None:
                job["progress"] = progress
            if message is not None:
                job["message"] = message
            if error is not None:
                job["error"] = error
            if status in ["completed", "failed"]:
                job["end_time"] = datetime.now().isoformat()

async def process_screening(screening_id: str, request_data: ScreeningRequest):
    """Process a single environmental screening"""
    global agent
    
    try:
        # Initialize agent if needed
        if agent is None:
            initialize_agent()
        
        # Update status to processing
        update_screening_status(screening_id, "processing", 10, "Starting environmental screening...")
        
        # Build a comprehensive screening query that triggers the full workflow
        query_parts = []
        
        # Start with comprehensive screening request
        if request_data.projectName:
            query_parts.append(f"Generate a comprehensive environmental screening report for {request_data.projectName}")
        else:
            query_parts.append("Generate a comprehensive environmental screening report")
        
        if request_data.projectDescription:
            query_parts.append(f"Project description: {request_data.projectDescription}")
        
        # Location information - prioritize cadastral number
        if request_data.cadastralNumber:
            query_parts.append(f"Cadastral number: {request_data.cadastralNumber}")
        elif request_data.coordinates:
            lat = request_data.coordinates.get("latitude")
            lng = request_data.coordinates.get("longitude")
            if lat and lng:
                query_parts.append(f"Coordinates: {lng}, {lat}")
        
        if request_data.locationName:
            query_parts.append(f"Location: {request_data.locationName}")
        
        # Specify required analyses - default to all if none specified
        if request_data.analyses and len(request_data.analyses) > 0:
            # Map frontend analysis names to agent tool names
            analysis_mapping = {
                'property': 'property',
                'cadastral': 'property', 
                'karst': 'karst',
                'flood': 'flood',
                'wetland': 'wetland',
                'habitat': 'habitat',
                'critical_habitat': 'habitat',
                'air_quality': 'air_quality',
                'nonattainment': 'air_quality'
            }
            
            mapped_analyses = []
            for analysis in request_data.analyses:
                mapped = analysis_mapping.get(analysis.lower(), analysis)
                if mapped not in mapped_analyses:
                    mapped_analyses.append(mapped)
            
            query_parts.append(f"Required analyses: {', '.join(mapped_analyses)}")
        else:
            # Default to comprehensive analysis
            query_parts.append("Required analyses: property, karst, flood, wetland, habitat, air_quality")
        
        # Always request comprehensive reports
        report_requirements = []
        if request_data.includeComprehensiveReport:
            report_requirements.append("comprehensive report")
        if request_data.includePdf:
            report_requirements.append("PDF report")
        if request_data.useLlmEnhancement:
            report_requirements.append("LLM-enhanced analysis")
        
        if report_requirements:
            query_parts.append(f"Generate {', '.join(report_requirements)}")
        
        # Add explicit instruction for complete workflow
        query_parts.append("I need complete property information, environmental analysis with all reports, maps, and regulatory assessments")
        
        # Combine into final query
        screening_query = ". ".join(query_parts) + "."
        
        print(f"🔄 Processing screening {screening_id}: {screening_query}")
        
        # Update progress
        update_screening_status(screening_id, "processing", 25, "Running environmental analysis...")
        
        # Run the agent
        response = agent.invoke(
            {"messages": [HumanMessage(content=screening_query)]},
            config={"configurable": {"thread_id": screening_id}}
        )
        
        # Update progress
        update_screening_status(screening_id, "processing", 75, "Generating reports...")
        
        # Extract response
        last_message = response["messages"][-1]
        agent_response = last_message.content
        
        # Find the output directory for this screening
        output_directory = None
        generated_files = []
        
        # Look for the most recent directory in output/
        if output_dir.exists():
            # Get all directories sorted by creation time
            dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            if dirs:
                # Sort by modification time, newest first
                dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                output_directory = str(dirs[0])
                
                # Get all files in the directory
                for file_path in dirs[0].rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(dirs[0])
                        generated_files.append(str(relative_path))
        
        # Update final status
        with screening_lock:
            if screening_id in screening_jobs:
                screening_jobs[screening_id]["output_directory"] = output_directory
                screening_jobs[screening_id]["generated_files"] = generated_files
        
        update_screening_status(screening_id, "completed", 100, "Environmental screening completed successfully")
        
        print(f"✅ Screening {screening_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Screening {screening_id} failed: {error_msg}")
        update_screening_status(screening_id, "failed", 0, "Screening failed", error_msg)

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    try:
        initialize_agent()
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize agent on startup: {e}")
        print("Agent will be initialized on first request")

# Main interface routes
@app.get("/", response_class=HTMLResponse)
async def get_main_interface():
    """Serve the main environmental screening interface"""
    html_file = static_dir / "advanced_index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Fallback to basic index.html
        basic_html = static_dir / "index.html"
        if basic_html.exists():
            return FileResponse(basic_html)
        else:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Environmental Screening Platform</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>Environmental Screening Platform</h1>
                <p>Static files not found. Please create the static files.</p>
                <p>Available API endpoints:</p>
                <ul>
                    <li>POST /api/environmental-screening - Submit screening request</li>
                    <li>GET /api/environmental-screening/{screening_id}/status - Check status</li>
                    <li>GET /api/dashboard - Dashboard data</li>
                    <li>GET /api/projects - List projects</li>
                    <li>GET /api/reports - List reports</li>
                </ul>
            </body>
            </html>
            """)

# API Routes for Environmental Screening
@app.post("/api/environmental-screening", response_model=ScreeningResponse)
async def submit_screening(request: ScreeningRequest, background_tasks: BackgroundTasks):
    """Submit a new environmental screening request"""
    
    # Generate unique screening ID
    screening_id = str(uuid.uuid4())
    
    # Create screening job
    create_screening_job(screening_id, request)
    
    # Start processing in background
    background_tasks.add_task(process_screening, screening_id, request)
    
    return ScreeningResponse(
        screening_id=screening_id,
        status="pending",
        message="Environmental screening request submitted successfully"
    )

@app.get("/api/environmental-screening/{screening_id}/status", response_model=ScreeningStatus)
async def get_screening_status(screening_id: str):
    """Get the status of a screening request"""
    
    with screening_lock:
        if screening_id not in screening_jobs:
            raise HTTPException(status_code=404, detail="Screening not found")
        
        job = screening_jobs[screening_id]
        
        # Create proper ScreeningStatus response
        return ScreeningStatus(
            screening_id=job["id"],
            status=job["status"],
            progress=job["progress"],
            message=job["message"],
            start_time=job["start_time"],
            end_time=job.get("end_time"),
            output_directory=job.get("output_directory"),
            generated_files=job.get("generated_files"),
            error=job.get("error")
        )

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get dashboard statistics and recent activity"""
    
    # Count completed screenings
    with screening_lock:
        total_projects = len([job for job in screening_jobs.values() if job["status"] == "completed"])
        reports_generated = sum(len(job.get("generated_files", [])) for job in screening_jobs.values())
    
    # Count output directories
    project_dirs = len([d for d in output_dir.iterdir() if d.is_dir()]) if output_dir.exists() else 0
    
    # Generate recent activity
    recent_activity = []
    with screening_lock:
        # Get recent completed jobs
        completed_jobs = [job for job in screening_jobs.values() if job["status"] == "completed"]
        completed_jobs.sort(key=lambda x: x["start_time"], reverse=True)
        
        for job in completed_jobs[:5]:  # Last 5 activities
            recent_activity.append({
                "timestamp": job["end_time"] or job["start_time"],
                "description": f"Completed screening for {job['request_data'].get('projectName', 'Unknown Project')}"
            })
    
    return DashboardData(
        total_projects=max(total_projects, project_dirs),
        reports_generated=reports_generated,
        risk_areas=0,  # This would need to be calculated from actual analysis results
        compliant_projects=total_projects,  # Simplified for now
        recent_activity=recent_activity
    )

@app.get("/api/projects")
async def get_projects():
    """Get list of projects"""
    
    projects = []
    
    # Get projects from screening jobs
    with screening_lock:
        for job in screening_jobs.values():
            if job["status"] == "completed":
                request_data = job["request_data"]
                projects.append(ProjectData(
                    id=job["id"],
                    name=request_data.get("projectName", "Unknown Project"),
                    location=request_data.get("locationName") or request_data.get("cadastralNumber", "Unknown Location"),
                    status="completed",
                    created_date=job["start_time"],
                    risk_level="low",  # This would need to be extracted from analysis results
                    reports_count=len(job.get("generated_files", []))
                ))
    
    # Also check output directories
    if output_dir.exists():
        for project_dir in output_dir.iterdir():
            if project_dir.is_dir():
                # Check if we already have this project from screening jobs
                existing_ids = [p.id for p in projects]
                if project_dir.name not in existing_ids:
                    projects.append(ProjectData(
                        id=project_dir.name,
                        name=project_dir.name.replace("_", " "),
                        location="Unknown",
                        status="completed",
                        created_date=datetime.fromtimestamp(project_dir.stat().st_mtime).isoformat(),
                        risk_level="unknown",
                        reports_count=len(list(project_dir.rglob("*.pdf"))) + len(list(project_dir.rglob("*.json")))
                    ))
    
    return {"projects": [p.dict() for p in projects]}

@app.get("/api/reports")
async def get_reports():
    """Get list of generated reports"""
    
    reports = []
    
    if output_dir.exists():
        for project_dir in output_dir.iterdir():
            if project_dir.is_dir():
                # Look for reports in the reports subdirectory
                reports_dir = project_dir / "reports"
                if reports_dir.exists():
                    for report_file in reports_dir.iterdir():
                        if report_file.is_file() and report_file.suffix in ['.pdf', '.json', '.md']:
                            reports.append(ReportData(
                                id=f"{project_dir.name}_{report_file.name}",
                                filename=report_file.name,
                                project_name=project_dir.name.replace("_", " "),
                                created_date=datetime.fromtimestamp(report_file.stat().st_mtime).isoformat(),
                                file_size=report_file.stat().st_size,
                                category=report_file.suffix[1:].upper(),
                                download_url=f"/api/files/{project_dir.name}/{report_file.name}"
                            ))
    
    return {"reports": [r.dict() for r in reports]}

# Legacy chat endpoint for backward compatibility
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Process chat messages and return environmental screening results"""
    global agent
    
    if agent is None:
        try:
            initialize_agent()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")
    
    try:
        # Add timestamp if not provided
        if not message.timestamp:
            message.timestamp = datetime.now().isoformat()
        
        print(f"🤔 Processing message: {message.message}")
        
        # Run the agent with thread configuration for memory
        response = agent.invoke(
            {"messages": [HumanMessage(content=message.message)]},
            config={"configurable": {"thread_id": "default"}}
        )
        
        # Extract the response
        last_message = response["messages"][-1]
        agent_response = last_message.content
        
        # Ensure agent_response is a string
        if isinstance(agent_response, list):
            agent_response = "\n".join(map(str, agent_response))
        elif not isinstance(agent_response, str):
            agent_response = str(agent_response)
        
        # Try to extract analysis data if it's a tool response
        analysis_data = None
        generated_files = []
        
        # Look for generated files in the output directory
        if output_dir.exists():
            generated_files = [f.name for f in output_dir.glob("*") if f.is_file()]
            # Sort by modification time, newest first
            generated_files.sort(key=lambda x: (output_dir / x).stat().st_mtime, reverse=True)
        
        return ChatResponse(
            response=agent_response,
            timestamp=datetime.now().isoformat(),
            analysis_data=analysis_data,
            generated_files=generated_files
        )
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": agent is not None,
        "active_screenings": len(screening_jobs),
        "output_directory": str(output_dir),
        "output_directory_exists": output_dir.exists()
    }

@app.get("/api/files/{project_name}/{filename}")
async def download_project_file(project_name: str, filename: str):
    """Download a specific file from a project"""
    
    project_path = output_dir / project_name
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Look for the file in various subdirectories
    possible_paths = [
        project_path / filename,
        project_path / "reports" / filename,
        project_path / "maps" / filename,
        project_path / "data" / filename,
        project_path / "logs" / filename
    ]
    
    for file_path in possible_paths:
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path, filename=filename)
    
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/files")
async def list_files():
    """List all generated files"""
    files = []
    
    if output_dir.exists():
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(output_dir)
                files.append({
                    "name": file_path.name,
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": file_path.suffix[1:] if file_path.suffix else "unknown"
                })
    
    return {"files": files}

@app.get("/files/{filename}")
async def download_file(filename: str):
    """Download a file from the output directory"""
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=filename)

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a file from the output directory"""
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.get("/examples")
async def get_examples():
    """Get example queries for the chat interface"""
    return {
        "examples": [
            "Environmental screening for cadastral 227-052-007-20 in Puerto Rico",
            "Comprehensive flood and wetland analysis for coordinates -66.150906, 18.434059",
            "Generate FEMA flood reports for property at cadastral 389-077-300-08",
            "Wetland assessment with map for coordinates -80.1918, 25.7617 in Miami",
            "Complete environmental screening including karst analysis for cadastral 156-023-045-12"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🌍 Starting Environmental Screening Platform")
    print("=" * 60)
    print("🔧 Features:")
    print("   • Individual environmental screenings")
    print("   • Batch processing capabilities") 
    print("   • Real-time status monitoring")
    print("   • Comprehensive report generation")
    print("   • Dashboard with project management")
    print("   • File download and management")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 