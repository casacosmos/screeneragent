# Mapmaker package 

# Main classes
from .map_exporter import MapExporter
from .common import MapServerClient

# Map overlay utilities
from .map_overlays import (
    # Classes
    PrintServiceClient,
    
    # Utility Functions
    convert_color_to_rgba_list,
    fetch_image_from_url,
    
    # Geographic/Geodesic Functions
    geodesic_point_at_distance_and_bearing,
    generate_circle_points,
    add_buffer_to_polygon,
    
    # Coordinate Conversion Functions
    lonlat_to_pixel,
    
    # ArcGIS Layer Creation Functions
    create_polygon_layer_json,
    create_circle_layer_json,
    
    # Rendering Functions
    draw_matplotlib_overlays,
    
    # Map Configuration Functions
    create_web_map_json,
    calculate_map_extent,
    
    # Scale Bar Functions
    add_scale_bar,
    calculate_scale_bar_length,
    calculate_scale_bar_length_from_lod,
)

# Package exports
__all__ = [
    # Main classes
    'MapExporter',
    'MapServerClient',
    
    # Map overlay classes
    'PrintServiceClient',
    
    # Utility Functions
    'convert_color_to_rgba_list',
    'fetch_image_from_url',
    
    # Geographic/Geodesic Functions
    'geodesic_point_at_distance_and_bearing',
    'generate_circle_points',
    'add_buffer_to_polygon',
    
    # Coordinate Conversion Functions
    'lonlat_to_pixel',
    
    # ArcGIS Layer Creation Functions
    'create_polygon_layer_json',
    'create_circle_layer_json',
    
    # Rendering Functions
    'draw_matplotlib_overlays',
    
    # Map Configuration Functions
    'create_web_map_json',
    'calculate_map_extent',
    
    # Scale Bar Functions
    'add_scale_bar',
    'calculate_scale_bar_length',
    'calculate_scale_bar_length_from_lod',
] 