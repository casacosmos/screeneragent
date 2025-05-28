#!/usr/bin/env python3
"""
FEMA Flood Data Client

Client for accessing FEMA flood data services including NFHL, Preliminary FIRM,
and MapSearch services.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class FloodZone:
    """Data class for flood zone information"""
    zone: str
    description: str
    bfe: Optional[float] = None  # Base Flood Elevation


@dataclass
class FIRMPanel:
    """Data class for FIRM panel information"""
    panel_id: str
    effective_date: str
    panel_type: str

    
@dataclass
class FloodHazardInfo:
    """Data class for comprehensive flood hazard information"""
    location: str
    coordinates: tuple
    flood_zones: List[FloodZone]
    firm_panels: List[FIRMPanel]
    political_jurisdiction: str
    dfirm_id: str


class FEMAFloodClient:
    """
    Client for accessing FEMA flood data services
    """
    
    def __init__(self):
        self.base_url = "https://hazards.fema.gov/arcgis/rest/services"
        
        # Service endpoints - using current best practices
        self.services = {
            'nfhl': f"{self.base_url}/FIRMette/NFHLREST_FIRMette/MapServer",
            'preliminary': f"{self.base_url}/PrelimPending/Prelim_NFHL/MapServer", 
            'mapsearch': f"{self.base_url}/MapSearch/MapSearch_v5/MapServer",
            'cslf_preliminary': f"{self.base_url}/CSLF/Prelim_CSLF/MapServer"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FEMA-Flood-Client/1.0'
        })
        
    def query_flood_hazard_at_point(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """
        Query flood hazard information at a specific point
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            
        Returns:
            Dictionary with flood hazard information
        """
        
        results = {
            'coordinates': (longitude, latitude),
            'services': {},
            'summary': {
                'has_flood_data': False,
                'flood_zones': [],
                'firm_panels': []
            }
        }
        
        # Query each service
        for service_name, service_url in self.services.items():
            service_data = self._query_service_at_point(service_url, longitude, latitude)
            results['services'][service_name] = service_data
            
            if service_data.get('has_data'):
                results['summary']['has_flood_data'] = True
        
        return results
    
    def _query_service_at_point(self, service_url: str, longitude: float, latitude: float) -> Dict[str, Any]:
        """Query a specific service at given coordinates"""
        
        try:
            # Create point geometry
            geometry = {
                'x': longitude,
                'y': latitude,
                'spatialReference': {'wkid': 4326}
            }
            
            # Query parameters
            params = {
                'geometry': json.dumps(geometry),
                'geometryType': 'esriGeometryPoint',
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            # Query layer 0 (typically the main data layer)
            response = self.session.get(f"{service_url}/0/query", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            return {
                'service_url': service_url,
                'has_data': len(features) > 0,
                'feature_count': len(features),
                'features': features
            }
                
        except Exception as e:
            return {
                'service_url': service_url,
                'has_data': False,
                'feature_count': 0,
                'features': [],
                'error': str(e)
            }


def main():
    """Example usage of the FEMA flood client"""
    
    client = FEMAFloodClient()
    
    # Example coordinates (Cataño, Puerto Rico)
    longitude = -66.1689712
    latitude = 18.4282314
    
    print("=== FEMA Flood Data Query Example ===")
    print(f"Coordinates: {latitude}, {longitude}")
    
    # Query flood hazard data
    results = client.query_flood_hazard_at_point(longitude, latitude)
    
    print(f"\nFlood data found: {results['summary']['has_flood_data']}")
    
    for service_name, service_data in results['services'].items():
        print(f"\n{service_name}: {service_data['feature_count']} features")


if __name__ == "__main__":
    main() 