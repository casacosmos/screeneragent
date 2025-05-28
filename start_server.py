#!/usr/bin/env python3
"""
Startup script for FEMA Flood Analysis Chat Application

This script checks dependencies and environment setup before starting the server.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'websockets',
        'pydantic',
        'langchain_core',
        'langgraph'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("   Please run: pip install -r requirements.txt")
            return False
    
    return True

def check_api_key():
    """Check if API key is configured"""
    api_keys = {
        'GOOGLE_API_KEY': 'Google Gemini',
        'OPENAI_API_KEY': 'OpenAI GPT',
        'ANTHROPIC_API_KEY': 'Anthropic Claude'
    }
    
    configured_keys = []
    for key, provider in api_keys.items():
        if os.getenv(key):
            configured_keys.append(provider)
            print(f"✅ {provider} API key is configured")
    
    if not configured_keys:
        print("⚠️  No API keys found. Please set one of:")
        for key, provider in api_keys.items():
            print(f"   export {key}='your-key-here'  # for {provider}")
        print("\n   Or create a .env file with your API key")
        return False
    
    return True

def check_file_structure():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'comprehensive_environmental_agent.py',
        'comprehensive_flood_tool.py',
        'wetland_analysis_tool.py',
        'static/index.html',
        'WetlandsINFO/query_wetland_location.py',
        'WetlandsINFO/generate_wetland_map_pdf_v3.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing file: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing required files. Please ensure all files are present.")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['static', 'output']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory ready: {directory}/")

def main():
    """Main startup function"""
    print("🌍 Environmental Screening Chat - Startup Check")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("API Configuration", check_api_key)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print(f"\n📁 Creating directories...")
    create_directories()
    
    if not all_passed:
        print(f"\n❌ Some checks failed. Please fix the issues above before starting.")
        sys.exit(1)
    
    print(f"\n✅ All checks passed! Starting the server...")
    print(f"🚀 Server will be available at: http://localhost:8000")
    print(f"📊 API documentation at: http://localhost:8000/docs")
    print(f"🔗 WebSocket endpoint: ws://localhost:8000/ws")
    print(f"\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 