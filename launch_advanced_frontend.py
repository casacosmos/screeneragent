#!/usr/bin/env python3
"""
Launch script for the Advanced Environmental Screening Platform
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install fastapi uvicorn pydantic")
        return False
    
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'static/advanced_index.html',
        'static/advanced_styles.css',
        'static/environmental_screening_app.js',
        'environmental_screening_templates.py',
        'comprehensive_environmental_agent.py',
        'advanced_frontend_server.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    return True

def main():
    """Main launch function"""
    print("🌱 Environmental Screening Platform")
    print("=" * 50)
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check files
    print("Checking files...")
    if not check_files():
        sys.exit(1)
    
    print("✅ All checks passed!")
    print()
    
    # Launch the server
    print("🚀 Starting Advanced Environmental Screening Platform...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 Help documentation at: http://localhost:8000/help")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        # Run the FastAPI server
        subprocess.run([
            sys.executable, 
            'advanced_frontend_server.py'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Python not found in PATH")
        sys.exit(1)

if __name__ == "__main__":
    main() 