#!/usr/bin/env python3
"""
Simple validation script for structured output fixes
"""

import json
from comprehensive_environmental_agent import StructuredScreeningOutput

def test_structured_model():
    """Test that the StructuredScreeningOutput model works correctly"""
    
    print("🧪 Testing StructuredScreeningOutput Model")
    print("=" * 50)
    
    # Test with minimal required fields
    minimal_data = {
        "success": True,
        "project_name": "Test Project",
        "project_directory": "output/test_project"
    }
    
    try:
        result = StructuredScreeningOutput(**minimal_data)
        print("✅ Minimal validation: PASSED")
        print(f"   Project Name: {result.project_name}")
        print(f"   Success: {result.success}")
    except Exception as e:
        print(f"❌ Minimal validation: FAILED - {e}")
        return False
    
    # Test with error scenario
    error_data = {
        "success": False,
        "project_name": "Failed Project",
        "project_directory": "output/failed_project",
        "error_message": "Test error message",
        "error_details": "This is a string error detail"  # Testing string type
    }
    
    try:
        result = StructuredScreeningOutput(**error_data)
        print("✅ Error scenario validation: PASSED")
        print(f"   Error Message: {result.error_message}")
        print(f"   Error Details: {result.error_details}")
    except Exception as e:
        print(f"❌ Error scenario validation: FAILED - {e}")
        return False
    
    # Test with comprehensive data
    comprehensive_data = {
        "success": True,
        "project_name": "Comprehensive Test",
        "project_directory": "output/comprehensive_test",
        "project_input_location_description": "Cadastral 060-000-009-58",
        "project_input_coordinates_lng_lat": [-66.2097, 18.4154],
        "screening_datetime_utc": "2025-05-28T16:00:00Z",
        "property_analysis": {
            "cadastral_number": "060-000-009-58",
            "area_acres": 4.99,
            "land_use": "Industrial Liviano",
            "zoning": "I-L",
            "development_potential": "High"
        },
        "flood_analysis": {
            "flood_zone_code": "X",
            "flood_risk_category": "Minimal",
            "insurance_requirements": "Not Required"
        },
        "comprehensive_reports": {
            "json_report": "reports/comprehensive_report.json",
            "markdown": "reports/comprehensive_report.md",
            "pdf": "reports/comprehensive_report.pdf"
        },
        "environmental_constraints_summary": [
            "Property in minimal flood zone",
            "Nearby wetlands identified"
        ],
        "overall_risk_level_assessment": "Low",
        "key_regulatory_requirements_identified": [
            "Standard development permits required"
        ],
        "agent_recommendations": [
            "Proceed with standard development process"
        ],
        "narrative_summary_of_findings": "The property shows low environmental risk with minimal constraints identified."
    }
    
    try:
        result = StructuredScreeningOutput(**comprehensive_data)
        print("✅ Comprehensive validation: PASSED")
        print(f"   Property Analysis: {bool(result.property_analysis)}")
        print(f"   Flood Analysis: {bool(result.flood_analysis)}")
        print(f"   Comprehensive Reports: {bool(result.comprehensive_reports)}")
        print(f"   Constraints: {len(result.environmental_constraints_summary or [])}")
        print(f"   Risk Level: {result.overall_risk_level_assessment}")
    except Exception as e:
        print(f"❌ Comprehensive validation: FAILED - {e}")
        return False
    
    # Test JSON serialization
    try:
        json_str = json.dumps(comprehensive_data, indent=2)
        print("✅ JSON serialization: PASSED")
    except Exception as e:
        print(f"❌ JSON serialization: FAILED - {e}")
        return False
    
    print("\n🎉 All validation tests passed!")
    return True

if __name__ == "__main__":
    success = test_structured_model()
    if success:
        print("\n✅ Structured output model is working correctly!")
    else:
        print("\n❌ Structured output model has issues!") 