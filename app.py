#!/usr/bin/env python3
"""
FastAPI Frontend for Comprehensive FEMA Flood Analysis Agent

This application provides a web-based chat interface for interacting with
the comprehensive flood analysis agent that generates FEMA reports and
extracts detailed flood information.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
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
    title="Environmental Screening Chat",
    description="Interactive chat interface for comprehensive environmental screening (flood and wetland analysis)",
    version="1.0.0"
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

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    analysis_data: Optional[Dict[str, Any]] = None
    generated_files: Optional[List[str]] = None

if WEBSOCKET_AVAILABLE:
    class ConnectionManager:
        """Manages WebSocket connections for real-time chat"""
        
        def __init__(self):
            self.active_connections: List[WebSocket] = []
        
        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
        
        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)
        
        async def send_personal_message(self, message: str, websocket: WebSocket):
            await websocket.send_text(message)
        
        async def broadcast(self, message: str):
            for connection in self.active_connections:
                await connection.send_text(message)

    manager = ConnectionManager()
else:
    manager = None

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

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    try:
        initialize_agent()
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize agent on startup: {e}")
        print("Agent will be initialized on first request")

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the main chat interface"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Return a basic HTML page if static file doesn't exist
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FEMA Flood Analysis Chat</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>FEMA Flood Analysis Chat</h1>
            <p>Static files not found. Please create the static/index.html file.</p>
            <p>Use the API endpoints:</p>
            <ul>
                <li>POST /chat - Send a message</li>
                <li>GET /health - Check system health</li>
                <li>GET /files - List generated files</li>
            </ul>
        </body>
        </html>
        """)

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
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

if WEBSOCKET_AVAILABLE:
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time chat"""
        await manager.connect(websocket)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process the message
                try:
                    message = ChatMessage(**message_data)
                    
                    # Send processing status
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "status",
                            "message": "Processing your environmental screening request...",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                    
                    # Process with agent
                    if agent is None:
                        initialize_agent()
                    
                    response = agent.invoke(
                        {"messages": [HumanMessage(content=message.message)]},
                        config={"configurable": {"thread_id": "default"}}
                    )
                    
                    last_message = response["messages"][-1]
                    
                    # Get generated files
                    generated_files = []
                    if output_dir.exists():
                        generated_files = [f.name for f in output_dir.glob("*") if f.is_file()]
                        generated_files.sort(key=lambda x: (output_dir / x).stat().st_mtime, reverse=True)
                    
                    # Send response
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "response",
                            "response": last_message.content,
                            "timestamp": datetime.now().isoformat(),
                            "generated_files": generated_files
                        }),
                        websocket
                    )
                    
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Error processing request: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket)
else:
    # WebSocket not available - provide a fallback endpoint
    @app.get("/ws")
    async def websocket_fallback():
        return {"message": "WebSocket not available - using HTTP API only"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global agent
    
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": agent is not None,
        "google_api_key_set": bool(os.getenv("GOOGLE_API_KEY")),
        "output_directory_exists": output_dir.exists(),
        "websocket_available": WEBSOCKET_AVAILABLE
    }
    
    return status

@app.get("/files")
async def list_files():
    """List generated environmental screening files"""
    if not output_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": file_path.suffix.lower()
            })
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"files": files}

@app.get("/files/{filename}")
async def download_file(filename: str):
    """Download a generated environmental screening file"""
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a generated environmental screening file"""
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
    """Get example queries for the environmental screening agent"""
    examples = [
        {
            "title": "Complete Environmental Screening - Puerto Rico",
            "query": "Generate a comprehensive environmental screening report for Cataño, Puerto Rico at coordinates -66.150906, 18.434059",
            "description": "Complete flood and wetland analysis with all reports and maps for a Puerto Rico location"
        },
        {
            "title": "Miami Environmental Assessment",
            "query": "I need a complete environmental assessment including flood and wetland analysis for Miami, Florida coordinates -80.1918, 25.7617",
            "description": "Comprehensive environmental screening for a Florida coastal location"
        },
        {
            "title": "Bayamón Wetland and Flood Screening",
            "query": "What are the flood and wetland risks for Bayamón, Puerto Rico at coordinates -66.199399, 18.408303? Include all documents.",
            "description": "Combined flood and wetland assessment with regulatory guidance"
        },
        {
            "title": "Houston Environmental Screening",
            "query": "Generate screening report with flood analysis and wetland assessment for Houston, Texas coordinates -95.3698, 29.7604",
            "description": "Complete environmental screening including regulatory requirements"
        },
        {
            "title": "New York Comprehensive Analysis",
            "query": "Perform environmental screening with all reports and maps for New York City coordinates -74.0060, 40.7128",
            "description": "Full environmental assessment with flood and wetland analysis"
        },
        {
            "title": "Flood Analysis Only",
            "query": "Perform flood analysis only for coordinates -80.1918, 25.7617 including FIRM, pFIRM, and ABFE reports",
            "description": "Flood-specific analysis when wetland assessment is not needed"
        },
        {
            "title": "Wetland Analysis Only", 
            "query": "Analyze wetland conditions and generate wetland map for coordinates -66.199399, 18.408303",
            "description": "Wetland-specific analysis when flood assessment is not needed"
        }
    ]
    
    return {"examples": examples}

if __name__ == "__main__":
    import uvicorn
    
    print("🌍 Starting Environmental Screening Chat Server")
    print("=" * 50)
    print("🚀 Server will be available at: http://localhost:8000")
    print("📊 API documentation at: http://localhost:8000/docs")
    if WEBSOCKET_AVAILABLE:
        print("🔗 WebSocket endpoint: ws://localhost:8000/ws")
    else:
        print("⚠️ WebSocket not available - using HTTP API only")
    print("📁 Generated files at: http://localhost:8000/files")
    print("🌊 Flood Analysis: FEMA reports (FIRMette, Preliminary, ABFE)")
    print("🌿 Wetland Analysis: NWI assessment with adaptive mapping")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 