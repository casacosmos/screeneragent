#!/usr/bin/env python3
"""
Check Print Templates for Critical Habitat Map Generation
"""

import requests
import json

def check_print_templates():
    """Check available print templates and formats"""
    
    print("🖨️  CHECKING PRINT TEMPLATES FOR CRITICAL HABITAT MAPS")
    print("="*70)
    
    export_url = "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task"
    
    try:
        response = requests.get(f"{export_url}?f=json", timeout=15)
        response.raise_for_status()
        service_info = response.json()
        
        print(f"✅ Export service accessible")
        print(f"Description: {service_info.get('description', 'N/A')}")
        
        # Check parameters
        parameters = service_info.get('parameters', [])
        print(f"\n📋 AVAILABLE PARAMETERS ({len(parameters)} total):")
        
        for param in parameters:
            param_name = param.get('name', 'Unknown')
            param_type = param.get('dataType', 'Unknown')
            param_default = param.get('defaultValue', 'None')
            
            print(f"\n  🔧 {param_name}")
            print(f"     Type: {param_type}")
            print(f"     Default: {param_default}")
            print(f"     Required: {param.get('parameterType') == 'esriGPParameterTypeRequired'}")
            
            # Show choice lists for key parameters
            if param_name in ['Layout_Template', 'Format'] and 'choiceList' in param:
                print(f"     Available Options:")
                for choice in param['choiceList']:
                    print(f"       • {choice}")
            
            # Show description if available
            if 'description' in param and param['description']:
                print(f"     Description: {param['description']}")
        
        return service_info
        
    except Exception as e:
        print(f"❌ Error checking print templates: {e}")
        return None

if __name__ == "__main__":
    check_print_templates() 