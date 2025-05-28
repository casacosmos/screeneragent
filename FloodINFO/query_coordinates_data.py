#!/usr/bin/env python3
"""
Coordinate Data Query Tool - Core Library

Query specific coordinates and provide all available FEMA flood data
in a clear, organized format.

This module provides the core data querying functionality used by main.py.
For interactive usage, use the main.py module in the parent directory.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fema_flood_client import FEMAFloodClient
import requests
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

def query_coordinate_data(longitude: float, latitude: float, location_name: str = None) -> Dict[str, Any]:
    """
    Query all available data for specific coordinates
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Optional name for the location
        
    Returns:
        Dictionary with all available data organized by service and layer
    """
    
    if location_name is None:
        location_name = f"({longitude}, {latitude})"
    
    print(f"=== QUERYING DATA FOR {location_name.upper()} ===")
    print(f"Coordinates: {longitude}, {latitude}")
    print(f"Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    client = FEMAFloodClient()
    
    # Services and their key layers to query
    services_config = {
        'NFHL (Current Effective)': {
            'service_key': 'nfhl',
            'layers': {
                0: 'NFHL Availability',
                1: 'FIRM Panels', 
                4: 'Political Jurisdictions',
                20: 'Flood Hazard Zones',
                22: 'Base Index'
            }
        },
        'Preliminary FIRM': {
            'service_key': 'preliminary',
            'layers': {
                0: 'Preliminary Data Availability',
                1: 'Preliminary FIRM Panel Index',
                3: 'Preliminary FIRM Panels',
                22: 'Preliminary Political Jurisdictions'
            }
        },
        'MapSearch (Reports)': {
            'service_key': 'mapsearch',
            'layers': {
                0: 'GeoIndex',
                1: 'Communities'
            }
        }
    }
    
    results = {
        'location': location_name,
        'coordinates': (longitude, latitude),
        'query_time': datetime.now().isoformat(),
        'services': {},
        'summary': {
            'total_services_queried': len(services_config),
            'services_with_data': 0,
            'total_features_found': 0,
            'puerto_rico_data_confirmed': False
        }
    }
    
    # Query each service
    for service_name, config in services_config.items():
        print(f"\n{'-'*60}")
        print(f"QUERYING: {service_name}")
        print(f"{'-'*60}")
        
        service_key = config['service_key']
        service_url = client.services.get(service_key)
        
        if not service_url:
            print(f"❌ Service {service_key} not configured")
            continue
        
        service_results = {
            'service_name': service_name,
            'service_url': service_url,
            'layers': {},
            'has_data': False,
            'total_features': 0,
            'puerto_rico_identifiers': {}
        }
        
        # Query each layer in the service
        for layer_id, layer_name in config['layers'].items():
            print(f"\n  Layer {layer_id}: {layer_name}")
            
            layer_data = query_layer_at_coordinate(service_url, layer_id, longitude, latitude)
            service_results['layers'][layer_id] = layer_data
            
            if layer_data['has_data']:
                service_results['has_data'] = True
                service_results['total_features'] += layer_data['feature_count']
                
                print(f"    ✅ {layer_data['feature_count']} feature(s) found")
                
                # Show key attributes
                for i, feature in enumerate(layer_data['features'][:2]):  # Show first 2 features
                    attrs = feature.get('attributes', {})
                    print(f"    📋 Feature {i+1} data:")
                    
                    # Key fields to display
                    key_fields = [
                        'DFIRM_ID', 'FIRM_PAN', 'POL_AR_ID', 'POL_NAME1', 'POL_NAME2',
                        'FLD_ZONE', 'STATIC_BFE', 'EFF_DATE', 'ST_FIPS', 'CID',
                        'PANEL', 'SUFFIX', 'PANEL_TYP'
                    ]
                    
                    displayed_fields = []
                    for field in key_fields:
                        if field in attrs and attrs[field] is not None and str(attrs[field]).strip():
                            value = attrs[field]
                            print(f"      {field}: {value}")
                            displayed_fields.append(field)
                            
                            # Track Puerto Rico identifiers
                            if field == 'DFIRM_ID' and value == '72000C':
                                service_results['puerto_rico_identifiers']['dfirm_id'] = value
                                results['summary']['puerto_rico_data_confirmed'] = True
                            elif field == 'ST_FIPS' and value == '72':
                                service_results['puerto_rico_identifiers']['st_fips'] = value
                                results['summary']['puerto_rico_data_confirmed'] = True
                    
                    # Show geometry info if available
                    geometry = feature.get('geometry', {})
                    if geometry:
                        geom_type = geometry.get('type', 'Unknown')
                        print(f"      GEOMETRY_TYPE: {geom_type}")
                        
                        if 'rings' in geometry and geometry['rings']:
                            coords = geometry['rings'][0]
                            if coords and len(coords) > 0:
                                x_coords = [pt[0] for pt in coords]
                                y_coords = [pt[1] for pt in coords]
                                print(f"      BOUNDS: ({min(x_coords):.6f}, {min(y_coords):.6f}) to ({max(x_coords):.6f}, {max(y_coords):.6f})")
                    
                    if not displayed_fields:
                        print(f"      (No key fields with data)")
                    
                    print()  # Empty line between features
            else:
                print(f"    ❌ No data found")
        
        # Service summary
        if service_results['has_data']:
            results['summary']['services_with_data'] += 1
            results['summary']['total_features_found'] += service_results['total_features']
            
            print(f"\n  📊 {service_name} Summary:")
            print(f"    Total features: {service_results['total_features']}")
            print(f"    Layers with data: {sum(1 for layer in service_results['layers'].values() if layer['has_data'])}")
            
            if service_results['puerto_rico_identifiers']:
                print(f"    🏝️  Puerto Rico data confirmed:")
                for key, value in service_results['puerto_rico_identifiers'].items():
                    print(f"      {key.upper()}: {value}")
        else:
            print(f"\n  📊 {service_name} Summary: No data found")
        
        results['services'][service_name] = service_results
    
    return results

def query_layer_at_coordinate(service_url: str, layer_id: int, longitude: float, latitude: float) -> Dict[str, Any]:
    """Query a specific layer at given coordinates"""
    
    try:
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        query_params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'json',
            'returnGeometry': 'true'
        }
        
        response = requests.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('features', [])
        
        return {
            'layer_id': layer_id,
            'has_data': len(features) > 0,
            'feature_count': len(features),
            'features': features,
            'query_successful': True
        }
        
    except Exception as e:
        return {
            'layer_id': layer_id,
            'has_data': False,
            'feature_count': 0,
            'features': [],
            'query_successful': False,
            'error': str(e)
        }

def generate_summary_report(results: Dict[str, Any]):
    """Generate a summary report of all findings"""
    
    print(f"\n{'='*80}")
    print(f"COORDINATE DATA SUMMARY REPORT")
    print(f"{'='*80}")
    
    print(f"\n📍 LOCATION: {results['location']}")
    print(f"📍 COORDINATES: {results['coordinates'][0]}, {results['coordinates'][1]}")
    print(f"🕒 QUERY TIME: {results['query_time']}")
    
    summary = results['summary']
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"   Services queried: {summary['total_services_queried']}")
    print(f"   Services with data: {summary['services_with_data']}")
    print(f"   Total features found: {summary['total_features_found']}")
    print(f"   Puerto Rico data: {'✅ Confirmed' if summary['puerto_rico_data_confirmed'] else '❌ Not found'}")
    
    if summary['services_with_data'] > 0:
        print(f"\n🗂️  SERVICES WITH DATA:")
        
        for service_name, service_data in results['services'].items():
            if service_data['has_data']:
                print(f"\n   📁 {service_name}:")
                print(f"      Total features: {service_data['total_features']}")
                
                # List layers with data
                layers_with_data = []
                for layer_id, layer_data in service_data['layers'].items():
                    if layer_data['has_data']:
                        layers_with_data.append(f"Layer {layer_id} ({layer_data['feature_count']} features)")
                
                if layers_with_data:
                    print(f"      Layers with data:")
                    for layer_info in layers_with_data:
                        print(f"        • {layer_info}")
                
                # Show Puerto Rico identifiers if found
                if service_data['puerto_rico_identifiers']:
                    print(f"      🏝️  Puerto Rico identifiers:")
                    for key, value in service_data['puerto_rico_identifiers'].items():
                        print(f"        • {key.upper()}: {value}")
    
    # Data interpretation guide
    print(f"\n📖 DATA FIELD GUIDE:")
    print(f"   DFIRM_ID: Digital FIRM identifier (72000C = Puerto Rico)")
    print(f"   FIRM_PAN: FIRM panel identifier")
    print(f"   FLD_ZONE: Flood zone designation (A, AE, X, VE, etc.)")
    print(f"   STATIC_BFE: Base Flood Elevation in feet")
    print(f"   POL_AR_ID: Political area identifier")
    print(f"   ST_FIPS: State FIPS code (72 = Puerto Rico)")
    print(f"   EFF_DATE: Effective date of the data")
    print(f"   CID: Community identifier")
    
    print(f"\n📋 STRUCTURED DATA:")
    print(f"   A separate panel information file is generated with:")
    print(f"   • Panel information (FIRM panels, numbers, types)")
    print(f"   • Effective dates in MM/DD/YYYY format")
    print(f"   • Regional identification and FIPS codes")
    print(f"   • Flood zone designations and elevations")
    print(f"   • Political jurisdictions and floodplain numbers")
    print(f"   • Complete data interpretation guide")

def save_results_to_file(results: Dict[str, Any], filename: str = None):
    """Save results to a JSON file"""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{results['coordinates'][0]}_{results['coordinates'][1]}".replace('-', 'neg').replace('.', 'p')
        filename = f"coordinate_query_{coords}_{timestamp}.json"
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    filepath = os.path.join('logs', filename)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filepath}")
    
    # Generate additional structured panel information file
    panel_info_filepath = generate_panel_info_file(results)
    
    return filepath

def generate_panel_info_file(results: Dict[str, Any]) -> str:
    """Generate a structured JSON file with panel information and key identifiable data"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    coords = f"{results['coordinates'][0]}_{results['coordinates'][1]}".replace('-', 'neg').replace('.', 'p')
    filename = f"panel_info_{coords}_{timestamp}.json"
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    filepath = os.path.join('logs', filename)
    
    # Extract structured panel information
    panel_info = extract_panel_information(results)
    
    with open(filepath, 'w') as f:
        json.dump(panel_info, f, indent=2, default=str)
    
    print(f"📋 Panel information saved to: {filepath}")
    return filepath

def extract_panel_information(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and structure panel information from query results"""
    
    from datetime import datetime
    
    def format_date(date_str):
        """Convert date string to MM/DD/YYYY format"""
        if not date_str or date_str in ['null', 'None', '']:
            return None
        
        try:
            # Handle various date formats
            if isinstance(date_str, (int, float)):
                # Unix timestamp (milliseconds)
                if date_str > 1000000000000:  # Milliseconds
                    date_obj = datetime.fromtimestamp(date_str / 1000)
                else:  # Seconds
                    date_obj = datetime.fromtimestamp(date_str)
                return date_obj.strftime("%m/%d/%Y")
            
            # String date formats
            date_str = str(date_str).strip()
            
            # Try common formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d', '%m-%d-%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%m/%d/%Y")
                except ValueError:
                    continue
            
            # If no format matches, return original
            return date_str
            
        except Exception:
            return date_str
    
    def determine_region(st_fips, dfirm_id, pol_name):
        """Determine region based on available data"""
        if st_fips == '72' or dfirm_id == '72000C':
            return "Puerto Rico"
        elif pol_name:
            # Extract state from political name if available
            pol_name_str = str(pol_name).upper()
            if 'PUERTO RICO' in pol_name_str or 'PR' in pol_name_str:
                return "Puerto Rico"
            # Add more state mappings as needed
        
        # Map common FIPS codes to regions
        fips_to_region = {
            '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
            '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
            '11': 'District of Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
            '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa',
            '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
            '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
            '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
            '32': 'Nevada', '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico',
            '36': 'New York', '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio',
            '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
            '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas',
            '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
            '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming', '72': 'Puerto Rico'
        }
        
        return fips_to_region.get(str(st_fips), f"FIPS {st_fips}" if st_fips else "Unknown")
    
    # Initialize structured data
    structured_info = {
        "query_metadata": {
            "location": results.get('location'),
            "coordinates": {
                "longitude": results.get('coordinates', [None, None])[0],
                "latitude": results.get('coordinates', [None, None])[1]
            },
            "query_time": results.get('query_time'),
            "generation_time": datetime.now().isoformat()
        },
        "current_effective_data": {
            "panel_information": [],
            "flood_zones": [],
            "political_jurisdictions": []
        },
        "preliminary_data": {
            "panel_information": [],
            "flood_zones": [],
            "political_jurisdictions": [],
            "has_preliminary_data": False
        },
        "summary": {
            "current_panels_found": 0,
            "preliminary_panels_found": 0,
            "current_flood_zones_found": 0,
            "preliminary_flood_zones_found": 0,
            "current_jurisdictions_found": 0,
            "preliminary_jurisdictions_found": 0,
            "regions_identified": set(),
            "effective_dates_found": set(),
            "dfirm_ids_found": set(),
            "has_preliminary_changes": False
        }
    }
    
    # Track unique entries to avoid duplicates
    seen_panels = set()
    seen_zones = set()
    seen_jurisdictions = set()
    
    # Process each service's data
    for service_name, service_data in results.get('services', {}).items():
        if not service_data.get('has_data'):
            continue
        
        for layer_id, layer_data in service_data.get('layers', {}).items():
            if not layer_data.get('has_data'):
                continue
            
            for feature in layer_data.get('features', []):
                attrs = feature.get('attributes', {})
                
                # Extract common fields
                dfirm_id = attrs.get('DFIRM_ID')
                firm_pan = attrs.get('FIRM_PAN')
                panel = attrs.get('PANEL')
                suffix = attrs.get('SUFFIX')
                panel_typ = attrs.get('PANEL_TYP')
                eff_date = attrs.get('EFF_DATE')
                st_fips = attrs.get('ST_FIPS')
                cid = attrs.get('CID')
                pol_ar_id = attrs.get('POL_AR_ID')
                pol_name1 = attrs.get('POL_NAME1')
                pol_name2 = attrs.get('POL_NAME2')
                fld_zone = attrs.get('FLD_ZONE')
                static_bfe = attrs.get('STATIC_BFE')
                
                # Determine region
                region = determine_region(st_fips, dfirm_id, pol_name1 or pol_name2)
                
                # Format effective date
                formatted_date = format_date(eff_date)
                
                # Update summary tracking
                if region != "Unknown":
                    structured_info["summary"]["regions_identified"].add(region)
                if formatted_date:
                    structured_info["summary"]["effective_dates_found"].add(formatted_date)
                if dfirm_id:
                    structured_info["summary"]["dfirm_ids_found"].add(str(dfirm_id))
                
                # Determine if this is current effective or preliminary data
                is_preliminary = "Preliminary" in service_name
                
                # Panel Information
                if firm_pan or panel or dfirm_id:
                    # Create unique identifier to avoid duplicates
                    panel_key = f"{dfirm_id}_{firm_pan}_{panel}_{suffix}_{service_name}_{layer_id}"
                    
                    if panel_key not in seen_panels:
                        seen_panels.add(panel_key)
                        
                        panel_info = {
                            "dfirm_id": dfirm_id,
                            "firm_panel": firm_pan,
                            "panel_number": panel,
                            "panel_suffix": suffix,
                            "panel_type": panel_typ,
                            "effective_date": formatted_date,
                            "region": region,
                            "state_fips": st_fips,
                            "community_id": cid,
                            "floodplain_number": pol_ar_id,
                            "source_layer": f"{service_name} - Layer {layer_id}",
                            "additional_identifiers": {
                                "political_area_id": pol_ar_id,
                                "political_name_1": pol_name1,
                                "political_name_2": pol_name2
                            }
                        }
                        
                        if is_preliminary:
                            structured_info["preliminary_data"]["panel_information"].append(panel_info)
                            structured_info["preliminary_data"]["has_preliminary_data"] = True
                            structured_info["summary"]["preliminary_panels_found"] += 1
                        else:
                            structured_info["current_effective_data"]["panel_information"].append(panel_info)
                            structured_info["summary"]["current_panels_found"] += 1
                
                # Flood Zone Information
                if fld_zone:
                    # Create unique identifier for flood zones
                    zone_key = f"{dfirm_id}_{fld_zone}_{static_bfe}_{service_name}_{layer_id}"
                    
                    if zone_key not in seen_zones:
                        seen_zones.add(zone_key)
                        
                        flood_zone_info = {
                            "flood_zone": fld_zone,
                            "base_flood_elevation": static_bfe,
                            "effective_date": formatted_date,
                            "region": region,
                            "dfirm_id": dfirm_id,
                            "firm_panel": firm_pan,
                            "community_id": cid,
                            "source_layer": f"{service_name} - Layer {layer_id}"
                        }
                        
                        if is_preliminary:
                            structured_info["preliminary_data"]["flood_zones"].append(flood_zone_info)
                            structured_info["preliminary_data"]["has_preliminary_data"] = True
                            structured_info["summary"]["preliminary_flood_zones_found"] += 1
                        else:
                            structured_info["current_effective_data"]["flood_zones"].append(flood_zone_info)
                            structured_info["summary"]["current_flood_zones_found"] += 1
                
                # Political Jurisdiction Information
                if pol_name1 or pol_name2 or pol_ar_id:
                    # Create unique identifier for jurisdictions
                    jurisdiction_key = f"{pol_ar_id}_{pol_name1}_{pol_name2}_{service_name}_{layer_id}"
                    
                    if jurisdiction_key not in seen_jurisdictions:
                        seen_jurisdictions.add(jurisdiction_key)
                        
                        jurisdiction_info = {
                            "political_area_id": pol_ar_id,
                            "jurisdiction_name_1": pol_name1,
                            "jurisdiction_name_2": pol_name2,
                            "region": region,
                            "state_fips": st_fips,
                            "community_id": cid,
                            "effective_date": formatted_date,
                            "dfirm_id": dfirm_id,
                            "source_layer": f"{service_name} - Layer {layer_id}"
                        }
                        
                        if is_preliminary:
                            structured_info["preliminary_data"]["political_jurisdictions"].append(jurisdiction_info)
                            structured_info["preliminary_data"]["has_preliminary_data"] = True
                            structured_info["summary"]["preliminary_jurisdictions_found"] += 1
                        else:
                            structured_info["current_effective_data"]["political_jurisdictions"].append(jurisdiction_info)
                            structured_info["summary"]["current_jurisdictions_found"] += 1
    
    # Check if there are preliminary changes
    if (structured_info["summary"]["preliminary_panels_found"] > 0 or 
        structured_info["summary"]["preliminary_flood_zones_found"] > 0):
        structured_info["summary"]["has_preliminary_changes"] = True
    
    # Convert sets to lists for JSON serialization
    structured_info["summary"]["regions_identified"] = list(structured_info["summary"]["regions_identified"])
    structured_info["summary"]["effective_dates_found"] = list(structured_info["summary"]["effective_dates_found"])
    structured_info["summary"]["dfirm_ids_found"] = list(structured_info["summary"]["dfirm_ids_found"])
    
    # Add data interpretation guide
    structured_info["data_guide"] = {
        "data_structure_explanation": {
            "current_effective_data": "Official flood data currently in effect - legally binding for insurance and regulations",
            "preliminary_data": "Upcoming flood map changes - not yet effective but shows future flood risk modifications",
            "has_preliminary_changes": "Indicates if there are upcoming changes to flood maps for this location"
        },
        "field_descriptions": {
            "dfirm_id": "Digital FIRM identifier (72000C = Puerto Rico)",
            "firm_panel": "FIRM panel identifier",
            "panel_number": "Specific panel number within FIRM",
            "panel_suffix": "Panel suffix (if applicable)",
            "panel_type": "Type of panel (Printed, Digital, etc.)",
            "effective_date": "Date when flood data became effective (MM/DD/YYYY)",
            "flood_zone": "Flood zone designation (A, AE, X, VE, etc.)",
            "base_flood_elevation": "Base Flood Elevation in feet above sea level",
            "region": "Geographic region/state",
            "state_fips": "Federal Information Processing Standard state code",
            "community_id": "NFIP Community identifier",
            "floodplain_number": "Political area/floodplain identifier",
            "source_layer": "Which FEMA service and layer provided this data"
        },
        "flood_zone_meanings": {
            "X": "Minimal flood hazard (outside 0.2% annual chance floodplain)",
            "AE": "1% annual chance flood zone with base flood elevations",
            "A": "1% annual chance flood zone without base flood elevations",
            "VE": "1% annual chance coastal flood zone with wave action",
            "V": "1% annual chance coastal flood zone without base flood elevations"
        },
        "important_notes": {
            "current_vs_preliminary": "Current effective data is what's legally binding today. Preliminary data shows upcoming changes.",
            "duplicates_removed": "Duplicate entries from multiple FEMA services have been filtered out",
            "preliminary_importance": "If preliminary data exists, it indicates upcoming flood map changes that may affect insurance rates and building requirements"
        }
    }
    
    return structured_info

# This module is now used as a library by main.py
# For interactive usage, use: python ../main.py

if __name__ == "__main__":
    print("🌊 FEMA Flood Data Query Tool")
    print("=" * 50)
    print("This module is now used as a library.")
    print("For interactive usage, please use:")
    print("  python ../main.py")
    print("\nOr import this module:")
    print("  from query_coordinates_data import query_coordinate_data")
    print("  results = query_coordinate_data(longitude, latitude, location_name)")
    print("=" * 50) 