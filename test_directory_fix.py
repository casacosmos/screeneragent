#!/usr/bin/env python3
"""
Test script to verify that the nonattainment analysis tool uses existing project directories
"""

from output_directory_manager import get_output_manager
from nonattainment_analysis_tool import analyze_nonattainment_with_map

def test_directory_usage():
    """Test that nonattainment tool uses existing project directory"""
    
    print("🧪 Testing Project Directory Usage Fix")
    print("=" * 50)
    
    # Step 1: Create a project directory (simulating comprehensive screening)
    print("📁 Step 1: Creating initial project directory...")
    output_manager = get_output_manager()
    project_dir = output_manager.create_project_directory(
        custom_name='Test_Comprehensive_Screening_20250528'
    )
    print(f"✅ Created project directory: {project_dir}")
    
    # Step 2: Run nonattainment analysis - should use existing directory
    print("\n🌫️ Step 2: Running nonattainment analysis...")
    print("   This should use the existing project directory, not create a new one")
    
    try:
        result = analyze_nonattainment_with_map.invoke({
            "longitude": -118.2437,  # Los Angeles (known nonattainment area)
            "latitude": 34.0522,
            "location_name": "Los Angeles Test Location"
        })
        
        # Check if it used the same directory
        result_project_dir = result["project_directory"]["project_directory"]
        
        print(f"\n📊 Results:")
        print(f"   Original project directory: {project_dir}")
        print(f"   Nonattainment result directory: {result_project_dir}")
        
        if project_dir == result_project_dir:
            print("✅ SUCCESS: Nonattainment tool used existing project directory!")
        else:
            print("❌ FAILURE: Nonattainment tool created a new directory")
            
        print(f"\n📄 Files generated:")
        for file_type, filename in result.get("files_generated", {}).items():
            if filename:
                print(f"   {file_type}: {filename}")
                
        return project_dir == result_project_dir
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_directory_usage()
    if success:
        print("\n🎉 Test PASSED: Directory usage fix is working correctly!")
    else:
        print("\n💥 Test FAILED: Directory usage fix needs more work") 