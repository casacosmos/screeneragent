#!/usr/bin/env python3
"""
Simple Karst Analysis Tool

This module provides simple functions for karst analysis that can be used by
the comprehensive query tool and other environmental screening tools.

It serves as a bridge to the more comprehensive karst tools in the karst/ directory.

Updated to include BOTH:
1. PRAPEC (Carso) areas - primary karst regulation zones
2. Zona de Amortiguamiento Reglamentada - regulated buffer zones around karst areas
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

# Import the karst tools
from karst.prapec_karst_checker import (
    PrapecKarstChecker,
    check_cadastral_for_karst,
    check_coordinates_for_karst
)

# Import the comprehensive karst analyzer
from karst.comprehensive_karst_analysis import ComprehensiveKarstAnalyzer

def check_cadastral_karst(
    cadastral_number: str,
    buffer_miles: float = 0.5,
    include_buffer_search: bool = True,
    include_regulatory_buffers: bool = True,
    max_search_radius_for_nearest_miles: float = 5.0,
    map_base_map_name: str = "World_Topo_Map",
    map_layout_template: str = "Letter ANSI A Landscape"
) -> Dict[str, Any]:
    """
    Simple function to check if a cadastral falls within PRAPEC karst areas or regulated buffer zones.
    
    Args:
        cadastral_number: Puerto Rico cadastral number (e.g., '227-052-007-20')
        buffer_miles: Buffer distance in miles for proximity search
        include_buffer_search: Whether to search within buffer if not directly in karst
        include_regulatory_buffers: Whether to include analysis of regulated buffer zones
        max_search_radius_for_nearest_miles: Maximum search distance in miles for finding nearest karst
        map_base_map_name: Base map name for map generation
        map_layout_template: Layout template for map generation
        
    Returns:
        Dict containing comprehensive karst analysis including buffer zones
    """
    print(f"🗿 Comprehensive karst analysis for cadastral {cadastral_number}")
    
    try:
        # First get coordinates for this cadastral
        from cadastral.cadastral_search import MIPRCadastralSearch
        search = MIPRCadastralSearch()
        
        result = search.search_by_cadastral(cadastral_number, exact_match=True)
        
        if not result['success'] or result['feature_count'] == 0:
            return {
                'success': False,
                'error': f'Cadastral {cadastral_number} not found',
                'cadastral_number': cadastral_number,
                'karst_status': 'error',
                'query_time': datetime.now().isoformat()
            }
        
        # Get the first result and extract coordinates
        feature = result['results'][0]
        
        # Try to get center point from geometry or use a fallback method
        if 'geometry' in feature and feature['geometry']:
            # Calculate centroid from polygon rings
            rings = feature['geometry'].get('rings', [])
            if rings and rings[0]:
                # Simple centroid calculation
                coords = rings[0]
                total_x = sum(coord[0] for coord in coords)
                total_y = sum(coord[1] for coord in coords)
                center_x = total_x / len(coords)
                center_y = total_y / len(coords)
                
                # Convert from Web Mercator to WGS84 approximately
                # This is a rough conversion - for precise work, use proper projection
                longitude = center_x / 111319.5  # Approximate conversion
                latitude = center_y / 111000.0   # Approximate conversion
            else:
                # Fallback: use Puerto Rico center
                longitude = feature.get('attributes', {}).get('CENTROID_X', -66.5)
                latitude = feature.get('attributes', {}).get('CENTROID_Y', 18.2)
                if longitude == -66.5 : print("Warning: Using fallback coordinates for cadastral karst check.")
        else:
            # Fallback: use Puerto Rico center
            longitude = feature.get('attributes', {}).get('CENTROID_X', -66.5)
            latitude = feature.get('attributes', {}).get('CENTROID_Y', 18.2)
            if longitude == -66.5 : print("Warning: Using fallback coordinates for cadastral karst check.")
        
        # Use comprehensive karst analyzer
        if include_regulatory_buffers:
            analyzer = ComprehensiveKarstAnalyzer()
            analysis = analyzer.analyze_comprehensive_karst(
                longitude=longitude,
                latitude=latitude,
                search_radius_miles=buffer_miles
            )
            
            # Convert to simplified format
            result = _process_comprehensive_analysis(analysis, cadastral_number, buffer_miles)
        else:
            # Use traditional PRAPEC-only analysis
            checker = PrapecKarstChecker()
            prapec_result = checker.check_cadastral(
                cadastral_number=cadastral_number,
                buffer_miles=buffer_miles,
                include_buffer_search=include_buffer_search
            )
            result = _process_prapec_only_analysis(prapec_result, cadastral_number, buffer_miles)
        
        return result
        
    except Exception as e:
        # Initialize map_gen_params for error case if not already available through a coord_based_results call
        map_gen_params_error = {
            "center_longitude": None, "center_latitude": None, # Unknown if cadastral -> coord failed
            "analysis_buffer_miles": buffer_miles, 
            "map_view_buffer_miles": max(buffer_miles * 1.5, 1.0),
            "error_note": "Parameters reflect intended map for this cadastral, coords might be missing."
        }
        err_res = {
            'success': False, 'error': str(e), 'identifier': cadastral_number,
            'karst_status_general': 'error', 'query_time': datetime.now().isoformat(),
            'map_generation_parameters': map_gen_params_error
        }
        return _add_interpretive_guidance(err_res)

def check_coordinates_karst(
    longitude: float,
    latitude: float,
    buffer_miles: float = 0.5,
    include_regulatory_buffers: bool = True,
    max_search_radius_for_nearest_miles: float = 5.0,
    map_base_map_name: str = "World_Topo_Map",
    map_layout_template: str = "Letter ANSI A Landscape"
) -> Dict[str, Any]:
    """
    Simple function to check if coordinates fall within PRAPEC karst areas or regulated buffer zones.
    If not found within initial buffer_miles, searches for the nearest karst feature up to max_search_radius_for_nearest_miles.
    Includes interpretive guidance and map generation parameters in the results.
    """
    print(f"🗿 Comprehensive karst analysis for coordinates ({longitude:.6f}, {latitude:.6f})")
    
    # Store intended map parameters early
    # Map view buffer is often larger than analysis buffer for context
    map_view_buffer_miles = max(buffer_miles * 1.5, 1.0) 

    map_gen_params = {
        "center_longitude": longitude,
        "center_latitude": latitude,
        "analysis_buffer_miles": buffer_miles, # The buffer used for this specific analysis call
        "map_view_buffer_miles": map_view_buffer_miles, # Buffer typically used for map generation extent
        "base_map_name": map_base_map_name,
        "layout_template": map_layout_template,
        "output_format_planned": "PDF", # Default, can be changed by map generator call
        "karst_data_service_url": "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer",
        "prapec_layer_id": 15,
        "zones_layer_id": 0,
        "layer_styles": {
            "prapec_overall_l15": {"color": "[255, 215, 0, 102] (Gold, 40% opacity)", "outline": "[204, 172, 0, 255]"},
            "ape_zc_l0": {"color": "[255, 0, 0, 153] (Red, 60% opacity)", "outline": "[200, 0, 0, 255]"},
            "za_l0": {"color": "[0, 0, 255, 128] (Blue, 50% opacity)", "outline": "[0, 0, 200, 255]"}
        }
    }

    try:
        analyzer = ComprehensiveKarstAnalyzer()
        # Initial check for direct intersection or within the primary buffer_miles
        initial_analysis_results = analyzer.analyze_comprehensive_karst(
            longitude=longitude,
            latitude=latitude,
            search_radius_miles=buffer_miles 
        )
        
        # Process these initial results first
        processed_results = _process_comprehensive_analysis(initial_analysis_results, f"coords_{longitude}_{latitude}", buffer_miles)
        processed_results['map_generation_parameters'] = map_gen_params # Add map params

        # If no karst feature was found directly or within the initial buffer, search for the nearest one
        if processed_results.get('karst_status_general') == 'none':
            print(f"   No karst found within initial {buffer_miles} miles. Searching for nearest up to {max_search_radius_for_nearest_miles} miles...")
            nearest_features_data = analyzer.find_nearest_karst_features(
                longitude=longitude,
                latitude=latitude,
                max_search_radius_miles=max_search_radius_for_nearest_miles
            )
            processed_results['nearest_karst_search_results'] = nearest_features_data
            map_gen_params["extended_search_performed_radius_miles"] = max_search_radius_for_nearest_miles # Document extended search
            
            # Update message and status if nearest is found
            nearest_prapec = nearest_features_data.get('nearest_prapec_l15')
            nearest_zone0 = nearest_features_data.get('nearest_zone_l0')

            if (nearest_prapec and nearest_prapec.get('found_within_radius')) or \
               (nearest_zone0 and nearest_zone0.get('found_within_radius')):
                processed_results['karst_status_general'] = 'nearby_extended_search'
                message_parts = ["No direct karst intersection or buffer zone found at the immediate location."]
                if nearest_prapec and nearest_prapec.get('found_within_radius'):
                    message_parts.append(f"Nearest PRAPEC (L15) feature '{nearest_prapec.get('Nombre', 'Unknown')}' found within {max_search_radius_for_nearest_miles} miles.")
                if nearest_zone0 and nearest_zone0.get('found_within_radius'):
                    message_parts.append(f"Nearest Zone (L0) feature (Type: {nearest_zone0.get('CALI_SOBRE', 'Unknown')}, Project: {nearest_zone0.get('Proyecto', 'Unknown')}) found within {max_search_radius_for_nearest_miles} miles.")
                processed_results['message'] = " ".join(message_parts)
                if processed_results.get('regulatory_impact_level', 'none') == 'none': 
                    processed_results['regulatory_impact_level'] = 'low' 
            else:
                processed_results['message'] = f"No karst features (PRAPEC L15 or specific Zones L0) found within the extended search radius of {max_search_radius_for_nearest_miles} miles."

        return _add_interpretive_guidance(processed_results)
        
    except Exception as e:
        error_result = {
            'success': False, 'error': str(e), 'location': {'longitude': longitude, 'latitude': latitude},
            'karst_status_general': 'error', 'query_time': datetime.now().isoformat(),
            'map_generation_parameters': map_gen_params # Include map params even in error if defined early
        }
        return _add_interpretive_guidance(error_result)

def find_nearest_karst(
    cadastral_number: str,
    max_search_miles: float = 5.0,
    include_regulatory_buffers: bool = True
) -> Dict[str, Any]:
    """
    Find nearest karst area (PRAPEC or buffer zones) to a cadastral.
    
    Args:
        cadastral_number: Puerto Rico cadastral number
        max_search_miles: Maximum search distance in miles
        include_regulatory_buffers: Whether to include buffer zone analysis
        
    Returns:
        Dict containing nearest karst analysis
    """
    print(f"🔍 Finding nearest karst areas to cadastral {cadastral_number}")
    
    try:
        # Progressive search at increasing distances
        search_distances = [0.5, 1.0, 2.0, 3.0, max_search_miles]
        
        for distance in search_distances:
            result = check_cadastral_karst(
                cadastral_number=cadastral_number,
                buffer_miles=distance,
                include_buffer_search=True,
                include_regulatory_buffers=include_regulatory_buffers
            )
            
            if result['success'] and result['karst_status'] in ['direct', 'nearby', 'buffer']:
                result['nearest_karst_distance'] = distance
                result['search_method'] = 'progressive_distance'
                return result
        
        # No karst found within search radius
        return {
            'success': True,
            'cadastral_number': cadastral_number,
            'karst_status': 'none',
            'nearest_karst_distance': f'> {max_search_miles}',
            'message': f'No karst areas found within {max_search_miles} miles',
            'query_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'cadastral_number': cadastral_number,
            'karst_status': 'error',
            'query_time': datetime.now().isoformat()
        }

def _process_comprehensive_analysis(analysis: Dict[str, Any], identifier: str, buffer_miles: float) -> Dict[str, Any]:
    """Process comprehensive analysis into simplified format, extracting detailed karst zone types."""
    
    if not analysis.get('success'):
        return {
            'success': False,
            'error': analysis.get('error', 'Unknown error'),
            'identifier': identifier,
            'karst_status_general': 'error',
            'query_time': datetime.now().isoformat()
        }
    
    prapec_l15_result = analysis.get('prapec_analysis', {})
    buffer_l0_result = analysis.get('buffer_zone_analysis', {})
    
    # Initialize default values
    karst_status_general = 'none'
    karst_type_detailed = 'None'
    specific_zone_description = 'N/A'
    primary_regulation_l15 = 'None'
    primary_regulation_l0 = 'None'
    final_primary_regulation = 'None'
    regulatory_impact_level = 'none'
    message_l15 = ""
    message_l0 = ""

    # --- Step 1: Analyze PRAPEC Layer 15 results ---
    if prapec_l15_result.get('karst_found'):
        karst_status_general = 'direct' # Directly in the overall PRAPEC area
        karst_type_detailed = 'PRAPEC Karst Area (Layer 15)'
        specific_zone_description = 'PRAPEC Overall Area (Layer 15)'
        prapec_info = prapec_l15_result.get('karst_info', {})
        primary_regulation_l15 = f"Regulation {prapec_info.get('regla', 'Unknown')} (PRAPEC Layer 15)"
        regulatory_impact_level = 'high'
        message_l15 = f"Property is within the PRAPEC Karst Area (Layer 15, Regulation {prapec_info.get('regla', 'Unknown')})."

    # --- Step 2: Analyze Buffer Zone Layer 0 results ---
    if buffer_l0_result.get('buffer_zones_found'):
        # A Layer 0 zone is present. This could be an APE-ZC or ZA.
        primary_l0_zone_info = buffer_l0_result.get('buffer_zones', [{}])[0]
        cali_sobre = primary_l0_zone_info.get('classification', 'Unknown').upper()
        zone_project = primary_l0_zone_info.get('project', 'N/A')
        zone_desc = primary_l0_zone_info.get('description', 'N/A')
        buff_dist_miles = primary_l0_zone_info.get('buffer_distance_miles')
        layer0_rule = primary_l0_zone_info.get('regulation_rule')
        
        l0_message_part = ""
        l0_impact_level = 'none'
        l0_karst_type = 'None'
        l0_specific_desc = 'N/A'
        
        if 'APE-ZC' in cali_sobre:
            l0_karst_type = 'APE-ZC (Special Planning Karst Zone - Layer 0)'
            l0_specific_desc = f'APE-ZC: {zone_desc} (Project: {zone_project}) - Layer 0'
            l0_impact_level = 'high'
            l0_message_part = f"Additionally, it falls within an APE-ZC zone ({zone_desc}, Project: {zone_project}) from Layer 0."
            if layer0_rule: primary_regulation_l0 = f"Rule {layer0_rule} (APE-ZC Layer 0)"
        elif 'ZA' in cali_sobre:
            l0_karst_type = 'ZA (Regulated Buffer Zone - Layer 0)'
            buffer_desc_text = f", Buffer: {buff_dist_miles:.2f} miles" if buff_dist_miles is not None else ""
            l0_specific_desc = f'ZA: {zone_desc}{buffer_desc_text} (Project: {zone_project}) - Layer 0'
            l0_impact_level = 'moderate'
            l0_message_part = f"Additionally, it falls within a Regulated Buffer Zone (ZA: {zone_desc}{buffer_desc_text}, Project: {zone_project}) from Layer 0."
            if layer0_rule: primary_regulation_l0 = f"Rule {layer0_rule} (ZA Layer 0)"
        else: # Other type in Layer 0
            l0_karst_type = f'Other Regulated Zone ({cali_sobre} - Layer 0)'
            l0_specific_desc = f'Other Zone ({cali_sobre}): {zone_desc} (Project: {zone_project}) - Layer 0'
            l0_impact_level = 'moderate' # Assume moderate for other Layer 0 zones
            l0_message_part = f"Additionally, it falls within an 'Other' regulated zone ({cali_sobre}: {zone_desc}, Project: {zone_project}) from Layer 0."
            if layer0_rule: primary_regulation_l0 = f"Rule {layer0_rule} ({cali_sobre} Layer 0)"

        # Combine Layer 0 findings with existing status
        if karst_status_general == 'none': # Only in Layer 0, not in general PRAPEC L15
            karst_status_general = 'buffer' # Indicates presence in a Layer 0 specific zone
            karst_type_detailed = l0_karst_type
            specific_zone_description = l0_specific_desc
            regulatory_impact_level = l0_impact_level
            message_l0 = l0_message_part.replace("Additionally, it falls within", "Property falls within") # Main finding
            final_primary_regulation = primary_regulation_l0 if primary_regulation_l0 != 'None' else "Rule for Layer 0 zone not specified."
        else: # Already in PRAPEC L15, Layer 0 provides more detail
            # Update detailed type and description if Layer 0 is more specific
            specific_zone_description += f" AND {l0_specific_desc}"
            # Combine impact level - take the higher one
            if l0_impact_level == 'high': 
                regulatory_impact_level = 'high'
            elif l0_impact_level == 'moderate' and regulatory_impact_level == 'none':
                regulatory_impact_level = 'moderate'
            message_l0 = l0_message_part
            # Regulation: L15 is primary, L0 adds detail if present
            final_primary_regulation = primary_regulation_l15
            if primary_regulation_l0 != 'None':
                final_primary_regulation += f"; also subject to {primary_regulation_l0}"

    # --- Step 3: Finalize message and regulation --- 
    final_message = message_l15
    if message_l0:
        if final_message: final_message += " " + message_l0
        else: final_message = message_l0.replace("Additionally, it falls within", "Property falls within")
    
    if not final_message: # If still no message (e.g. not in L15 and no L0 zones found)
        final_message = f'No PRAPEC karst areas (Layer 15) or specific Karst/Buffer zones (Layer 0) found within {buffer_miles} miles'

    if final_primary_regulation == 'None' and primary_regulation_l15 != 'None':
        final_primary_regulation = primary_regulation_l15
    elif final_primary_regulation == 'None' and primary_regulation_l0 != 'None': # Should be covered by logic in Step 2
        final_primary_regulation = primary_regulation_l0
    elif final_primary_regulation == 'None':
        final_primary_regulation = "No specific regulation identified based on available data."

    return {
        'success': True,
        'identifier': identifier,
        'karst_status_general': karst_status_general, 
        'karst_type_detailed': karst_type_detailed if karst_type_detailed != 'None' else specific_zone_description, # Use specific if general is just 'None' 
        'specific_zone_description': specific_zone_description, 
        'primary_regulation': final_primary_regulation,
        'regulatory_impact_level': regulatory_impact_level,
        'buffer_miles_queried': buffer_miles,
        'query_time': datetime.now().isoformat(),
        'message': final_message.strip(),
        'prapec_layer15_analysis': prapec_l15_result, 
        'buffer_zone_layer0_analysis': buffer_l0_result, 
        'combined_assessment_details': analysis.get('combined_assessment', {}),
        'regulatory_implications_details': analysis.get('regulatory_implications', [])
    }

def _process_prapec_only_analysis(prapec_result: Dict[str, Any], identifier: str, buffer_miles: float) -> Dict[str, Any]:
    """Process PRAPEC-only analysis into simplified format."""
    
    if not prapec_result['success']:
        return {
            'success': False,
            'error': prapec_result.get('error', 'Unknown error'),
            'identifier': identifier,
            'karst_status': 'error',
            'query_time': datetime.now().isoformat()
        }
    
    # Map PRAPEC results to standardized format
    if prapec_result['in_karst']:
        karst_status = 'direct'
        message = 'Property directly intersects PRAPEC karst area'
    elif prapec_result['karst_proximity'] == 'nearby':
        karst_status = 'nearby'
        message = f'PRAPEC karst area found within {buffer_miles} miles'
    else:
        karst_status = 'none'
        message = f'No PRAPEC karst area found within {buffer_miles} miles'
    
    return {
        'success': True,
        'identifier': identifier,
        'karst_status': karst_status,
        'karst_type': 'PRAPEC' if karst_status in ['direct', 'nearby'] else 'None',
        'primary_regulation': f"Regulation {prapec_result.get('karst_info', {}).get('regla', 'Unknown')}" if karst_status in ['direct', 'nearby'] else 'None',
        'buffer_miles': buffer_miles,
        'distance_miles': prapec_result.get('distance_miles', 0),
        'message': message,
        'prapec_only_analysis': prapec_result,
        'query_time': datetime.now().isoformat()
    }

def _add_interpretive_guidance(results: Dict[str, Any]) -> Dict[str, Any]:
    """Adds a field with interpretive guidance to the karst results."""
    guidance = []
    status = results.get('karst_status_general')
    detailed_type = results.get('karst_type_detailed', '')
    impact = results.get('regulatory_impact_level')
    regulation = results.get('primary_regulation')
    initial_buffer_miles = results.get('buffer_miles_queried') # Get the initial buffer used
    nearest_search_data = results.get('nearest_karst_search_results')
    extended_search_radius = None
    if nearest_search_data:
        extended_search_radius = nearest_search_data.get('max_search_radius_miles')

    guidance.append("**Interpreting Karst Analysis Results:**")
    if status == 'direct':
        guidance.append(f"- **Direct Intersection**: The location is directly within a mapped karst-related zone ({detailed_type}). This was determined within an initial search radius of {initial_buffer_miles} miles. Regulatory impact is typically '{impact}'. Specific regulation(s) identified: {regulation}.")
    elif status == 'buffer':
        guidance.append(f"- **Buffer Zone Intersection**: The location is within a specific mapped zone from Layer 0 ({detailed_type}), likely an APE-ZC or a ZA buffer. This was determined within an initial search radius of {initial_buffer_miles} miles. Regulatory impact is typically '{impact}'. Specific regulation(s) identified: {regulation}.")
    elif status == 'nearby_extended_search':
        guidance.append(f"- **Nearby (Extended Search)**: No karst features were found at the immediate location or its initial buffer of {initial_buffer_miles} miles. However, karst features were identified within an extended search radius of {extended_search_radius} miles. Review details in 'nearest_karst_search_results'. Impact is generally considered '{impact}' but requires careful review of proximity and feature types.")
    elif status == 'none':
        no_find_message = f"- **None Found**: No PRAPEC karst areas (Layer 15) or specific Karst/Buffer zones (Layer 0) were identified directly at the location or within its initial buffer of {initial_buffer_miles} miles."
        if extended_search_radius is not None: # Implies extended search was done
            no_find_message += f" An extended search up to {extended_search_radius} miles also yielded no results."
        else: # Implies extended search was not performed or not applicable in this result context
            no_find_message += " An extended search for nearest features may not have been triggered or yielded no results within its defined maximum radius."
        no_find_message += " Standard development regulations regarding karst may still apply based on broader regional context not covered by these specific layers."
        guidance.append(no_find_message)
    elif status == 'error':
        guidance.append("- **Error**: The karst analysis could not be completed. See error messages.")

    guidance.append("- **PRAPEC (Layer 15)** refers to the overall 'Plan y Reglamento del Área de Planificación Especial del Carso'.")
    guidance.append("- **APE-ZC (Layer 0)** refers to an 'Área de Planificación Especial-Zona Cársica' (Special Planning Karst Zone), typically high sensitivity.")
    guidance.append("- **ZA (Layer 0)** refers to a 'Zona de Amortiguamiento' (Regulated 50m Buffer Zone)." )
    guidance.append("- **Note on APE-RC**: Executive Order OE-2014-022 also adopted the 'Área de Planificación Especial Restringida del Carso (APE-RC)'. While not explicitly queryable as a distinct attribute in these GIS services, APE-ZC areas are key restricted zones. For definitive APE-RC boundaries, consult official PRAPEC maps and documents from the PR Planning Board.")
    guidance.append("- **Always consult** the full PRAPEC regulations and the Puerto Rico Planning Board for authoritative interpretations and project-specific requirements.")
    
    results['interpretation_guidance'] = "\n".join(guidance)
    return results

# Example usage and testing
if __name__ == "__main__":
    print("🗿 Simple Karst Analysis Tool - Testing")
    print("=" * 50)
    
    # Test coordinates in known karst area
    print("\n1. Testing coordinates in Arecibo (known karst area):")
    coords_result = check_coordinates_karst(-66.209931, 18.414997, buffer_miles=1.0)
    print(f"   Status: {coords_result.get('karst_status_general', 'Unknown')}")
    print(f"   Type: {coords_result.get('karst_type_detailed', 'Unknown')}")
    print(f"   Message: {coords_result.get('message', 'No message')}")
    
    # Test cadastral analysis
    print("\n2. Testing cadastral analysis:")
    test_cadastral = "227-052-007-20"
    cadastral_result = check_cadastral_karst(test_cadastral, buffer_miles=1.0)
    print(f"   Cadastral: {test_cadastral}")
    print(f"   Status: {cadastral_result.get('karst_status_general', 'Unknown')}")
    print(f"   Type: {cadastral_result.get('karst_type_detailed', 'Unknown')}")
    print(f"   Message: {cadastral_result.get('message', 'No message')}")
    
    # Test nearest karst search
    print("\n3. Testing nearest karst search:")
    nearest_result = find_nearest_karst(test_cadastral, max_search_miles=3.0)
    print(f"   Nearest distance: {nearest_result.get('nearest_karst_distance', 'Unknown')}")
    print(f"   Status: {nearest_result.get('karst_status_general', 'Unknown')}")
    
    print("\n✅ Testing complete!")
    print("💡 Note: This tool now checks BOTH PRAPEC karst areas AND regulated buffer zones") 