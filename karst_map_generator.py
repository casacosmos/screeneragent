#!/usr/bin/env python3
"""
Karst Map Generator

This module generates a map image showing PRAPEC karst areas (Layer 15)
and specific zones (APE-ZC, ZA from Layer 0) around a given location.
"""

import folium
import requests
import json
import os
import math
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Helper to convert Web Mercator to WGS84 for Folium (simplified)
# For high accuracy, a proper library like pyproj should be used.
def web_mercator_to_wgs84_simple(x_merc: float, y_merc: float) -> Tuple[float, float]:
    lon = (x_merc / 20037508.34) * 180
    lat = (y_merc / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lat, lon

class KarstMapGenerator:
    """Generates maps for karst analysis."""

    def __init__(self, longitude: float, latitude: float, output_directory: str = "maps", 
                 map_buffer_miles: float = 1.0):
        self.longitude = longitude
        self.latitude = latitude
        self.output_directory = output_directory
        self.map_buffer_miles = map_buffer_miles
        self.base_service_url = "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer"
        self.prapec_layer_id = 15
        self.zones_layer_id = 0
        self.session = requests.Session()
        self.session.verify = False # Matches other tools

        os.makedirs(self.output_directory, exist_ok=True)

    def _get_layer_geojson(self, layer_id: int, color: str, weight: int, fill_opacity: float, layer_name: str,
                             where_clause: str = "1=1") -> Optional[Dict[str, Any]]:
        """Queries a layer and returns its GeoJSON representation with styling info."""
        try:
            # Calculate extent for the query based on buffer
            # Simple bounding box for query extent
            deg_per_mile_lat = 1 / 69.0
            deg_per_mile_lon = 1 / (69.0 * abs(math.cos(math.radians(self.latitude)))) # Varies with latitude
            
            lat_buffer = self.map_buffer_miles * deg_per_mile_lat
            lon_buffer = self.map_buffer_miles * deg_per_mile_lon

            extent = {
                "xmin": self.longitude - lon_buffer,
                "ymin": self.latitude - lat_buffer,
                "xmax": self.longitude + lon_buffer,
                "ymax": self.latitude + lat_buffer,
                "spatialReference": {"wkid": 4326} # WGS84 for extent
            }

            params = {
                'where': where_clause,
                'geometry': json.dumps(extent),
                'geometryType': 'esriGeometryEnvelope',
                'inSR': 4326, # Extent SR
                'outSR': 4326, # Output GeoJSON in WGS84 for Folium
                'outFields': '*', # Get all fields for potential popups
                'returnGeometry': 'true',
                'f': 'geojson'
            }
            
            query_url = f"{self.base_service_url}/{layer_id}/query"
            response = self.session.get(query_url, params=params, timeout=30)
            response.raise_for_status()
            geojson_data = response.json()
            
            if geojson_data and geojson_data.get('features'):
                # Add styling information for folium
                for feature in geojson_data['features']:
                    feature['properties'] = feature.get('properties', {})
                    feature['properties']['_style'] = {
                        'color': color,
                        'weight': weight,
                        'fillColor': color,
                        'fillOpacity': fill_opacity
                    }
                    feature['properties']['_popup'] = f"<strong>{layer_name}</strong><br>" + "<br>".join([f"{k}: {v}" for k,v in feature['properties'].items() if k not in ['_style', '_popup']])
                return geojson_data
            return None
        except Exception as e:
            print(f"Error fetching GeoJSON for layer {layer_id} ({layer_name}): {e}")
            return None

    def generate_karst_map(self, filename_prefix: str = "karst_map") -> Optional[str]:
        """Generates and saves the karst map."""
        
        # Create map centered on the location
        # Using a generic tile provider that doesn't require API keys for simplicity
        # Stamen Terrain, Stamen Toner, OpenStreetMap are good options
        m = folium.Map(location=[self.latitude, self.longitude], zoom_start=14, tiles="OpenStreetMap") # Was Stamen Terrain

        # 1. PRAPEC Overall Area (Layer 15)
        prapec_geojson = self._get_layer_geojson(
            layer_id=self.prapec_layer_id, 
            color='#FFD700', # Gold-ish
            weight=1,
            fill_opacity=0.3,
            layer_name="PRAPEC Karst Area (L15)"
        )
        if prapec_geojson:
            folium.GeoJson(
                prapec_geojson, 
                name="PRAPEC Karst Area (L15)",
                style_function=lambda x: x['properties']['_style'],
                tooltip=folium.GeoJsonTooltip(fields=['_popup'], aliases=["Details:"], localize=True, sticky=False)
            ).add_to(m)

        # 2. APE-ZC Zones (Layer 0, CALI_SOBRE = 'APE-ZC')
        ape_zc_geojson = self._get_layer_geojson(
            layer_id=self.zones_layer_id, 
            color='#FF0000', # Red
            weight=2,
            fill_opacity=0.4,
            layer_name="APE-ZC (Special Karst Zone - L0)",
            where_clause="UPPER(CALI_SOBRE) LIKE '%APE-ZC%'"
        )
        if ape_zc_geojson:
            folium.GeoJson(
                ape_zc_geojson, 
                name="APE-ZC Zones (L0)",
                style_function=lambda x: x['properties']['_style'],
                tooltip=folium.GeoJsonTooltip(fields=['_popup'], aliases=["APE-ZC Details:"], localize=True, sticky=False)
            ).add_to(m)

        # 3. ZA - Buffer Zones (Layer 0, CALI_SOBRE = 'ZA')
        za_geojson = self._get_layer_geojson(
            layer_id=self.zones_layer_id, 
            color='#0000FF', # Blue
            weight=2,
            fill_opacity=0.3,
            layer_name="ZA (Buffer Zone - L0)",
            where_clause="UPPER(CALI_SOBRE) LIKE '%ZA%'"
        )
        if za_geojson:
            folium.GeoJson(
                za_geojson, 
                name="ZA - Buffer Zones (L0)",
                style_function=lambda x: x['properties']['_style'],
                tooltip=folium.GeoJsonTooltip(fields=['_popup'], aliases=["ZA Details:"], localize=True, sticky=False)
            ).add_to(m)

        # Add a marker for the query location
        folium.Marker(
            [self.latitude, self.longitude],
            popup=f"Query Location\n({self.latitude:.6f}, {self.longitude:.6f})",
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        
        # Add Layer Control
        folium.LayerControl().add_to(m)

        # Save map to HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"{filename_prefix}_{timestamp}.html"
        html_filepath = os.path.join(self.output_directory, html_filename)
        m.save(html_filepath)
        print(f"🗺️ Karst map saved to: {html_filepath}")
        
        # Placeholder for PDF conversion: 
        # In a real scenario, you'd use a library like imgkit (with wkhtmltoimage) or Selenium to render HTML to image/PDF.
        # For now, we will return the HTML path. The comprehensive report tool can decide how to embed/reference this.
        pdf_filepath = html_filepath.replace(".html", ".pdf") # Ideal path
        print(f"💡 To convert to PDF (manual step for now): Open {html_filename} in a browser and print to PDF, or use a conversion tool.")
        print(f"   (Or integrate a library like WeasyPrint/imgkit if available in environment)")

        # For now, let's focus on generating the HTML. PDF conversion is a separate step.
        return html_filepath # Return HTML path, PDF path is aspirational for now

# Example Usage:
if __name__ == "__main__":
    import math # Required for _get_layer_geojson helper's extent calculation
    # Test coordinates (e.g., Arecibo area, known for karst)
    test_longitude = -66.7
    test_latitude = 18.4
    output_dir = "karst_maps_output"
    
    print(f"Generating karst map for location: ({test_latitude}, {test_longitude})")
    generator = KarstMapGenerator(longitude=test_longitude, latitude=test_latitude, output_directory=output_dir, map_buffer_miles=1.5)
    map_file = generator.generate_karst_map()
    
    if map_file:
        print(f"Map HTML successfully generated: {map_file}")
        # Try to open the map in the default web browser (platform dependent)
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.realpath(map_file)}")
        except Exception as e:
            print(f"Could not open map in browser: {e}")
    else:
        print("Map generation failed.")

    # Test coordinates likely outside direct karst but near buffer zones
    test_longitude_2 = -66.15 # Near San Juan / Catano
    test_latitude_2 = 18.45
    print(f"\nGenerating karst map for location: ({test_latitude_2}, {test_longitude_2})")
    generator2 = KarstMapGenerator(longitude=test_longitude_2, latitude=test_latitude_2, output_directory=output_dir, map_buffer_miles=2.0)
    map_file2 = generator2.generate_karst_map(filename_prefix="karst_map_san_juan_nearby")
    if map_file2:
        print(f"Map HTML successfully generated: {map_file2}") 