#!/usr/bin/env python3
"""
MIPR Map Generator
Comprehensive map generation with MIPR land use classification data overlays
"""

import sys
import os
from typing import List, Tuple, Optional, Dict, Any

# Add the mapmaker module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mapmaker import MapExporter

class MIPRMapGenerator:
    """
    Generate maps with MIPR land use classification data overlays.
    
    This class provides a high-level interface for creating maps that combine
    base maps (topographic, satellite) with MIPR classification data and
    user-defined polygons.
    """
    
    def __init__(self, base_map_service: str = 'topografico'):
        """
        Initialize the MIPR Map Generator.
        
        Args:
            base_map_service: Base map service to use ('topografico', 'foto_pr_2017', 'mipr_calificacion')
        """
        self.exporter = MapExporter(base_map_service)
        self.base_map_service = base_map_service
    
    def create_basic_mipr_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        title: str = "Site Analysis with MIPR Land Use Classifications",
        save_path: str = "mipr_map.png",
        image_width: int = 1600,
        image_height: int = 1200,
        mipr_opacity: float = 0.7,
        show_buffer: bool = False,
        buffer_radius_miles: float = 0.5
    ) -> bool:
        """
        Create a basic map with MIPR data overlay.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            title: Map title
            save_path: Path to save the output image
            image_width: Width of output image in pixels
            image_height: Height of output image in pixels
            mipr_opacity: Opacity of MIPR layer (0.0 to 1.0)
            show_buffer: Whether to show buffer circle
            buffer_radius_miles: Radius of buffer circle in miles
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, ax = self.exporter.overlay_polygon_with_mipr(
                polygon_coords=polygon_coords,
                image_width_pixels=image_width,
                image_height_pixels=image_height,
                show_mipr_layer=True,
                mipr_layer_opacity=mipr_opacity,
                title=title,
                save_path=save_path,
                show=False,
                show_buffer_circle=show_buffer,
                buffer_circle_radius_miles=buffer_radius_miles
            )
            
            return fig is not None
            
        except Exception as e:
            print(f"❌ Error creating basic MIPR map: {e}")
            return False
    
    def create_filtered_mipr_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        classification_filter: str,
        title: str = "Site Analysis with Filtered MIPR Classifications",
        save_path: str = "mipr_filtered_map.png",
        image_width: int = 1600,
        image_height: int = 1200,
        mipr_opacity: float = 0.8
    ) -> bool:
        """
        Create a map with filtered MIPR data (e.g., only residential classifications).
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            classification_filter: SQL filter expression (e.g., "cali LIKE 'R-%'")
            title: Map title
            save_path: Path to save the output image
            image_width: Width of output image in pixels
            image_height: Height of output image in pixels
            mipr_opacity: Opacity of MIPR layer (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, ax = self.exporter.overlay_polygon_with_mipr(
                polygon_coords=polygon_coords,
                image_width_pixels=image_width,
                image_height_pixels=image_height,
                show_mipr_layer=True,
                mipr_layer_opacity=mipr_opacity,
                mipr_classification_filter=classification_filter,
                title=title,
                save_path=save_path,
                show=False
            )
            
            return fig is not None
            
        except Exception as e:
            print(f"❌ Error creating filtered MIPR map: {e}")
            return False
    
    def create_residential_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        save_path: str = "mipr_residential_map.png"
    ) -> bool:
        """
        Create a map showing only residential classifications.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            save_path: Path to save the output image
            
        Returns:
            True if successful, False otherwise
        """
        return self.create_filtered_mipr_map(
            polygon_coords=polygon_coords,
            classification_filter="cali LIKE 'R-%'",
            title="Site Analysis - Residential Land Use Classifications",
            save_path=save_path
        )
    
    def create_commercial_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        save_path: str = "mipr_commercial_map.png"
    ) -> bool:
        """
        Create a map showing only commercial classifications.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            save_path: Path to save the output image
            
        Returns:
            True if successful, False otherwise
        """
        return self.create_filtered_mipr_map(
            polygon_coords=polygon_coords,
            classification_filter="cali LIKE 'C-%'",
            title="Site Analysis - Commercial Land Use Classifications",
            save_path=save_path
        )
    
    def create_industrial_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        save_path: str = "mipr_industrial_map.png"
    ) -> bool:
        """
        Create a map showing only industrial classifications.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            save_path: Path to save the output image
            
        Returns:
            True if successful, False otherwise
        """
        return self.create_filtered_mipr_map(
            polygon_coords=polygon_coords,
            classification_filter="cali LIKE 'I-%'",
            title="Site Analysis - Industrial Land Use Classifications",
            save_path=save_path
        )
    
    def create_comparison_maps(
        self,
        polygon_coords: List[Tuple[float, float]],
        output_prefix: str = "site_comparison"
    ) -> Dict[str, bool]:
        """
        Create a set of comparison maps with different base maps and MIPR overlays.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            output_prefix: Prefix for output filenames
            
        Returns:
            Dictionary with map names and success status
        """
        results = {}
        
        # 1. Topographic with MIPR
        self.exporter.switch_service('topografico')
        results['topographic_mipr'] = self.create_basic_mipr_map(
            polygon_coords=polygon_coords,
            title="Site Analysis - Topographic Map with MIPR Data",
            save_path=f"{output_prefix}_topographic_mipr.png"
        )
        
        # 2. Satellite with MIPR
        self.exporter.switch_service('foto_pr_2017')
        results['satellite_mipr'] = self.create_basic_mipr_map(
            polygon_coords=polygon_coords,
            title="Site Analysis - Satellite Imagery with MIPR Data",
            save_path=f"{output_prefix}_satellite_mipr.png",
            mipr_opacity=0.6  # Lower opacity to see satellite imagery
        )
        
        # 3. MIPR as base map
        self.exporter.switch_service('mipr_calificacion')
        try:
            fig, ax = self.exporter.overlay_polygon(
                polygon_coords=polygon_coords,
                title="Site Analysis - MIPR Classification Base Map",
                save_path=f"{output_prefix}_mipr_base.png",
                show=False,
                image_width_pixels=1600,
                image_height_pixels=1200
            )
            results['mipr_base'] = fig is not None
        except Exception as e:
            print(f"❌ Error creating MIPR base map: {e}")
            results['mipr_base'] = False
        
        # 4. Regular map for comparison (no MIPR)
        self.exporter.switch_service('topografico')
        try:
            fig, ax = self.exporter.overlay_polygon(
                polygon_coords=polygon_coords,
                title="Site Analysis - Topographic Map (No MIPR Data)",
                save_path=f"{output_prefix}_no_mipr.png",
                show=False,
                image_width_pixels=1600,
                image_height_pixels=1200
            )
            results['no_mipr'] = fig is not None
        except Exception as e:
            print(f"❌ Error creating comparison map: {e}")
            results['no_mipr'] = False
        
        return results
    
    def switch_base_map(self, service_name: str):
        """
        Switch to a different base map service.
        
        Args:
            service_name: Name of the service ('topografico', 'foto_pr_2017', 'mipr_calificacion')
        """
        self.exporter.switch_service(service_name)
        self.base_map_service = service_name
    
    def get_available_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available map services."""
        return MapExporter.list_available_services()
    
    def create_custom_mipr_map(
        self,
        polygon_coords: List[Tuple[float, float]],
        **kwargs
    ) -> bool:
        """
        Create a custom MIPR map with full control over all parameters.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            **kwargs: All parameters supported by overlay_polygon_with_mipr()
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set defaults if not provided
            defaults = {
                'show_mipr_layer': True,
                'mipr_layer_opacity': 0.7,
                'image_width_pixels': 1600,
                'image_height_pixels': 1200,
                'show': False
            }
            
            # Merge defaults with provided kwargs
            params = {**defaults, **kwargs}
            
            fig, ax = self.exporter.overlay_polygon_with_mipr(
                polygon_coords=polygon_coords,
                **params
            )
            
            return fig is not None
            
        except Exception as e:
            print(f"❌ Error creating custom MIPR map: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("MIPR MAP GENERATOR EXAMPLES")
    print("=" * 70)
    
    # Example polygon coordinates
    polygon = [
    (-65.92531668016763, 18.229972284880745),
    (-65.92569637378377, 18.229683903124233),
    (-65.92551131634363, 18.229298606693092),
    (-65.9250381179879, 18.229202305915837),
    (-65.92511720836045, 18.229185448624218),
    (-65.9252262548528, 18.228682675332788),
    (-65.92517802071194, 18.228687688081592),
    (-65.92517429360183, 18.228668794923994),
    (-65.92520548490512, 18.22838245365208),
    (-65.92553638832322, 18.228380366638458),
    (-65.9255223287907, 18.228175282873377),
    (-65.9258077882352, 18.22815207825642),
    (-65.92578523153843, 18.227916415895542),
    (-65.92591981533766, 18.227891835824867),
    (-65.92602066380475, 18.22787420451955),
    (-65.92610576390658, 18.227858627809333),
    (-65.92620885816186, 18.227835897550456),
    (-65.92630156160425, 18.22781619287095),
    (-65.92640284575421, 18.227795076079968),
    (-65.92649073063343, 18.22777767257948),
    (-65.92648764312379, 18.228216913975764),
    (-65.92649427538555, 18.228407938936037),
    (-65.92653608836876, 18.22849775727545),
    (-65.92662990841706, 18.22874927448809),
    (-65.92681091355693, 18.229094434408815),
    (-65.92725367070265, 18.22906559943674),
    (-65.92752799642751, 18.229051154218887),
    (-65.9277663877444, 18.2290348694314),
    (-65.92779940622098, 18.229033485488877),
    (-65.92779978441172, 18.229033477809786),
    (-65.92821711384501, 18.2297660699048),
    (-65.92829070922299, 18.22988642969321),
    (-65.9282903229474, 18.229886415188354),
    (-65.92824748498644, 18.229885025280016),
    (-65.92824105394733, 18.22988481538594),
    (-65.92822174735524, 18.229881447695192),
    (-65.92821245428362, 18.22989766841135),
    (-65.92813887417701, 18.23002614912598),
    (-65.92811369709455, 18.230078132842216),
    (-65.92809879943385, 18.23013578111521),
    (-65.92807050160408, 18.230246863519863),
    (-65.92804355753546, 18.23036073163527),
    (-65.92801691080919, 18.230473254140186),
    (-65.927990358406, 18.230585487329215),
    (-65.92797254571225, 18.2306607647523),
    (-65.92655732454209, 18.230433531389462),
    (-65.92633403929503, 18.23039072933896),
    (-65.92510823419076, 18.230155674095094),
    (-65.92531668016763, 18.229972284880745)
]
    
    # Initialize map generator
    generator = MIPRMapGenerator('topografico')
    
    print("\n1. Creating basic MIPR map...")
    success = generator.create_basic_mipr_map(
        polygon_coords=polygon,
        save_path="mipr/example_basic_mipr.png"
    )
    print(f"   {'✅ Success' if success else '❌ Failed'}")
    
    
    
    print("\n2. Creating comparison maps...")
    results = generator.create_comparison_maps(
        polygon_coords=polygon,
        output_prefix="mipr/example_comparison"
    )
    
    for map_type, success in results.items():
        print(f"   {map_type}: {'✅ Success' if success else '❌ Failed'}")
    
    print(f"\n✅ MIPR Map Generator examples completed!")
    print(f"   Check the 'mipr/' directory for generated maps.") 