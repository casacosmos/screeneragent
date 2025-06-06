#!/usr/bin/env python3
"""
Quick diagnostic test for our fixes
"""

import os
from pathlib import Path
from simplified_html_pdf_generator import SimplifiedHTMLPDFGenerator, configure_global_directories

def test_directory_fixes():
    """Test directory management fixes"""
    print("🧪 Testing Directory Management Fixes")
    print("=" * 50)
    
    # Create test project directory
    test_project = Path("test_fixes_output")
    test_project.mkdir(exist_ok=True)
    
    # Test global directory configuration
    configure_global_directories(str(test_project))
    
    # Check environment variables
    print(f"ENV_PROJECT_DIR: {os.environ.get('ENV_PROJECT_DIR', 'NOT SET')}")
    print(f"ENV_MAPS_DIR: {os.environ.get('ENV_MAPS_DIR', 'NOT SET')}")
    
    # Create test data
    test_data = {
        'project_info': {
            'project_name': 'Test Fixes',
            'latitude': 18.4058,
            'longitude': -66.7135
        },
        'query_results': {
            'flood_analysis': {'success': True},
            'wetland_analysis': {'success': True}
        }
    }
    
    # Create data directory and file
    data_dir = test_project / "data"
    data_dir.mkdir(exist_ok=True)
    
    import json
    data_file = data_dir / "test_report.json"
    with open(data_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Create test maps with different formats
    maps_dir = test_project / "maps"
    maps_dir.mkdir(exist_ok=True)
    
    # Create dummy map files
    (maps_dir / "firmette_test.pdf").write_text("dummy pdf content")
    (maps_dir / "karst_test.png32").write_text("dummy png32 content")
    (maps_dir / "wetland_test.png").write_text("dummy png content")
    
    print(f"\n📁 Test files created:")
    print(f"   Data: {data_file}")
    print(f"   Maps: {list(maps_dir.iterdir())}")
    
    # Test simplified generator
    try:
        generator = SimplifiedHTMLPDFGenerator(
            json_report_path=str(data_file),
            project_directory=str(test_project)
        )
        
        print(f"\n🗺️ Testing map finding:")
        maps = generator.find_maps()
        print(f"   Found maps: {list(maps.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Generator test failed: {e}")
        return False

def main():
    """Run diagnostic tests"""
    print("🚀 Running Diagnostic Tests for Fixes")
    
    success = test_directory_fixes()
    
    if success:
        print("\n✅ Basic fixes working correctly!")
    else:
        print("\n❌ Issues remain - check output above")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 