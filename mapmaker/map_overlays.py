# mapmaker/map_overlays.py

import matplotlib.pyplot as plt
import numpy as np
import requests
from matplotlib.patches import Polygon as MatplotlibPolygon, Rectangle
from matplotlib.patches import FancyBboxPatch
from io import BytesIO
from PIL import Image
import warnings
import math
import json
from typing import List, Dict, Any, Tuple, Sequence, Optional, Union

# Export all public functions and classes
__all__ = [
    # Classes
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

class PrintServiceClient:
    """
    Client for ArcGIS Print JPTemplate GPServer:
      - export_web_map(): generate a printable map (image or PDF)
    """
    def __init__(self, gp_root_url: str = "https://sige.pr.gov/server/rest/services/printjp/JPTemplate/GPServer") -> None:
        self.gp_root = gp_root_url.rstrip('/')

    def export_web_map(
        self,
        web_map_json: dict,
        layout_template: str,
        fmt: str = "PNG32",
        dpi: int = 96,
        extra_params: dict = None
    ) -> dict:
        """
        Executes the Export Web Map task.
        """
        url = f"{self.gp_root}/Export%20Web%20Map/execute"
        
        # Ensure Web_Map_as_JSON is a JSON string
        web_map_as_json_string = json.dumps(web_map_json)

        payload = {
            "Web_Map_as_JSON": web_map_as_json_string,
            "Format": fmt,
            "Layout_Template": layout_template,
            "f": "json"
        }
        if dpi:
            payload["dpi"] = dpi 
        if extra_params:
            payload.update(extra_params)
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": "Mozilla/5.0 (Python MapMaker Client)"
        }

        resp = requests.post(url, data=payload, verify=False, timeout=60, headers=headers)
        resp.raise_for_status()
        return resp.json()

def convert_color_to_rgba_list(color_name_or_hex, alpha_float):
    """Converts matplotlib color and alpha to RGBA list for ArcGIS JSON."""
    from matplotlib import colors
    if isinstance(color_name_or_hex, str):
        rgb_float = colors.to_rgb(color_name_or_hex)
    elif isinstance(color_name_or_hex, (list, tuple)) and len(color_name_or_hex) == 3:
        rgb_float = color_name_or_hex
    else: # Fallback
        rgb_float = colors.to_rgb('red')

    return [int(c * 255) for c in rgb_float] + [int(alpha_float * 255)]

def fetch_image_from_url(url, verify_ssl=False):
    """Fetch an image from a URL."""
    if not verify_ssl:
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        warnings.simplefilter('ignore', InsecureRequestWarning)
    
    response = requests.get(url, verify=verify_ssl, timeout=60)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch image: HTTP {response.status_code} from {url}")
    
    return Image.open(BytesIO(response.content))

def geodesic_point_at_distance_and_bearing(lon: float, lat: float, distance_meters: float, bearing_degrees: float) -> Tuple[float, float, float]:
    """
    Calculate the destination point given a starting point, distance and bearing.
    Uses the pyproj Geod object for accurate geodesic calculations.
    
    Args:
        lon: Starting longitude in degrees
        lat: Starting latitude in degrees
        distance_meters: Distance to travel in meters
        bearing_degrees: Direction to travel in degrees (0=North, 90=East, etc.)
        
    Returns:
        Tuple of (destination_lon, destination_lat, reverse_bearing)
    """
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    
    # Forward geodesic calculation
    lon2, lat2, back_bearing = geod.fwd(lon, lat, bearing_degrees, distance_meters)
    return lon2, lat2, back_bearing

def generate_circle_points(center_lon: float, center_lat: float, radius_miles: float, num_points: int = 64) -> List[Tuple[float, float]]:
    """
    Generate points for a circle of specified radius (in miles) around a center point.
    Uses the geodesic distance calculation to ensure the circle is accurate regardless of latitude.
    
    Args:
        center_lon: Longitude of circle center in degrees
        center_lat: Latitude of circle center in degrees
        radius_miles: Radius of the circle in miles
        num_points: Number of points to generate for the circle (more = smoother)
        
    Returns:
        List of (lon, lat) coordinates forming the circle
    """
    # Convert miles to meters
    radius_meters = radius_miles * 1609.34
    
    # Generate points around the circle
    circle_points = []
    for i in range(num_points + 1):  # +1 to close the circle
        angle = (i * 2 * math.pi) / num_points
        # Calculate the destination point using the geodesic formula
        lon, lat, _ = geodesic_point_at_distance_and_bearing(
            center_lon, center_lat, radius_meters, angle * 180 / math.pi
        )
        circle_points.append((lon, lat))
        
    return circle_points

def add_buffer_to_polygon(
    polygon: Sequence[Tuple[float, float]], buffer_miles: float = 0.5
) -> Sequence[Tuple[float, float]]:
    """
    Add a buffer around polygon in miles.
    Uses proper geographic calculations for accurate distance.
    
    Args:
        polygon: Sequence of (lon, lat) coordinates in WGS84 (EPSG:4326)
        buffer_miles: Buffer distance in miles around the polygon
        
    Returns:
        A new polygon (bounding box) with the buffer applied
    """
    # Convert miles to meters
    buffer_meters = buffer_miles * 1609.34
    
    lons, lats = zip(*polygon)
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    
    # Calculate center
    center_lat = (min_lat + max_lat) / 2
    
    # Convert buffer distance from meters to degrees
    # For latitude, use the constant conversion factor
    meters_per_degree_lat = 110750.0
    lat_buffer_deg = buffer_meters / meters_per_degree_lat
    
    # For longitude, account for the cosine of latitude (degrees get wider near equator, narrower near poles)
    meters_per_degree_lon = 111320.0 * math.cos(math.radians(center_lat))
    lon_buffer_deg = buffer_meters / meters_per_degree_lon
    
    # Create buffered bounding box
    buffered_poly = [
        (min_lon - lon_buffer_deg, min_lat - lat_buffer_deg),
        (max_lon + lon_buffer_deg, min_lat - lat_buffer_deg),
        (max_lon + lon_buffer_deg, max_lat + lat_buffer_deg),
        (min_lon - lon_buffer_deg, max_lat + lat_buffer_deg),
        (min_lon - lon_buffer_deg, min_lat - lat_buffer_deg)
    ]
    return buffered_poly

def lonlat_to_pixel(lon, lat, extent, image_width_pixels, image_height_pixels):
    """Convert longitude/latitude coordinates to pixel coordinates."""
    # Map longitude to x-pixel
    x_range = extent['xmax'] - extent['xmin']
    x_pixel = ((lon - extent['xmin']) / x_range) * image_width_pixels
    
    # Map latitude to y-pixel
    y_range = extent['ymax'] - extent['ymin']
    y_pixel = ((extent['ymax'] - lat) / y_range) * image_height_pixels
    
    return x_pixel, y_pixel

def create_polygon_layer_json(
    polygon_coords: Sequence[Tuple[float, float]],
    polygon_color: str = 'red',
    polygon_alpha: float = 0.4,
    outline_color: Optional[str] = None,
    outline_width: float = 1.5,
    no_fill: bool = False
) -> dict:
    """
    Create ArcGIS JSON layer definition for a polygon.
    
    Args:
        polygon_coords: List of (longitude, latitude) coordinate pairs
        polygon_color: Color for the polygon fill
        polygon_alpha: Opacity for the polygon fill (0-1)
        outline_color: Color for the polygon outline (defaults to polygon_color if None)
        outline_width: Width of the polygon outline
        no_fill: If True, the polygon will have no fill (transparent)
        
    Returns:
        Dictionary containing the ArcGIS layer definition
    """
    # Ensure the polygon is closed
    display_polygon = list(polygon_coords)
    if display_polygon[0] != display_polygon[-1]:
        display_polygon = display_polygon + [display_polygon[0]]
    
    # Prepare polygon for Web_Map_as_JSON (rings format)
    arcgis_rings = [[list(coord) for coord in display_polygon]]
    
    # Convert polygon style for ArcGIS JSON
    fill_alpha = 0 if no_fill else polygon_alpha
    polygon_fill_rgba = convert_color_to_rgba_list(polygon_color, fill_alpha)
    
    # Use outline_color if provided, otherwise use polygon_color
    final_outline_color = outline_color if outline_color is not None else polygon_color
    outline_rgba = convert_color_to_rgba_list(final_outline_color, 1.0)
    
    return {
        "id": "user_polygon_overlay",
        "title": "Site",
        "opacity": 1,
        "minScale": 0,
        "maxScale": 0,
        "featureCollection": {
            "layers": [{
                "layerDefinition": {
                    "name": "drawnPolygon",
                    "geometryType": "esriGeometryPolygon",
                    "drawingInfo": {
                        "renderer": {
                            "type": "simple",
                            "symbol": {
                                "type": "esriSFS",
                                "style": "esriSFSSolid",
                                "color": polygon_fill_rgba,
                                "outline": {
                                    "type": "esriSLS",
                                    "style": "esriSLSSolid",
                                    "color": outline_rgba,
                                    "width": outline_width
                                }
                            }
                        }
                    }
                },
                "featureSet": {
                    "geometryType": "esriGeometryPolygon",
                    "features": [{
                        "geometry": {
                            "rings": arcgis_rings, 
                            "spatialReference": {"wkid": 4326}
                        },
                        "attributes": {"id": 1, "name": "Site"}
                    }]
                }
            }]
        }
    }

def create_circle_layer_json(
    center_lon: float,
    center_lat: float,
    radius_miles: float,
    circle_color: str = 'blue',
    circle_width: float = 1.0,
    circle_dashed: bool = True,
    circle_fill: bool = False,
    circle_fill_color: Optional[str] = None,
    circle_fill_alpha: float = 0.1
) -> dict:
    """
    Create ArcGIS JSON layer definition for a buffer circle.
    
    Args:
        center_lon: Longitude of circle center
        center_lat: Latitude of circle center
        radius_miles: Radius of the circle in miles
        circle_color: Color for the circle outline
        circle_width: Width of the circle line
        circle_dashed: If True, use dashed line; if False, use solid line
        circle_fill: If True, fill the circle with color
        circle_fill_color: Fill color for circle (defaults to circle_color if None)
        circle_fill_alpha: Opacity for the circle fill (0-1)
        
    Returns:
        Dictionary containing the ArcGIS layer definition
    """
    # Generate circle points
    circle_points = generate_circle_points(
        center_lon, center_lat, 
        radius_miles, 
        num_points=64
    )
    
    # Convert to ArcGIS ring format
    circle_ring = [[list(coord) for coord in circle_points]]
    
    # Circle outline style
    circle_outline_rgba = convert_color_to_rgba_list(circle_color, 1.0)
    
    # Determine fill style
    circle_fill_style = "esriSFSSolid" if circle_fill else "esriSFSNull"
    
    # Determine fill color and alpha
    if circle_fill:
        fill_color = circle_fill_color if circle_fill_color else circle_color
        circle_fill_rgba = convert_color_to_rgba_list(fill_color, circle_fill_alpha)
    else:
        circle_fill_rgba = [0, 0, 0, 0]  # Transparent
        
    # Determine line style
    line_style = "esriSLSDash" if circle_dashed else "esriSLSSolid"
    
    return {
        "id": "buffer_circle_overlay",
        "title": f"{radius_miles} Mile Radius",
        "opacity": 1,
        "minScale": 0,
        "maxScale": 0,
        "featureCollection": {
            "layers": [{
                "layerDefinition": {
                    "name": "bufferCircle",
                    "geometryType": "esriGeometryPolygon",
                    "drawingInfo": {
                        "renderer": {
                            "type": "simple",
                            "symbol": {
                                "type": "esriSFS",
                                "style": circle_fill_style,
                                "color": circle_fill_rgba,
                                "outline": {
                                    "type": "esriSLS",
                                    "style": line_style,
                                    "color": circle_outline_rgba,
                                    "width": circle_width
                                }
                            }
                        }
                    }
                },
                "featureSet": {
                    "geometryType": "esriGeometryPolygon",
                    "features": [{
                        "geometry": {
                            "rings": circle_ring,
                            "spatialReference": {"wkid": 4326}
                        },
                        "attributes": {"id": 2, "name": f"{radius_miles} Mile Radius"}
                    }]
                }
            }]
        }
    }

def draw_matplotlib_overlays(
    ax,
    polygon_coords: Sequence[Tuple[float, float]],
    extent: dict,
    image_width_pixels: int,
    image_height_pixels: int,
    polygon_color: str = 'red',
    polygon_alpha: float = 0.4,
    outline_color: Optional[str] = None,
    outline_width: float = 1.5,
    no_fill: bool = False,
    show_buffer_circle: bool = False,
    buffer_circle_center: Optional[Tuple[float, float]] = None,
    buffer_circle_radius_miles: float = 1.0,
    buffer_circle_color: str = 'blue',
    buffer_circle_width: float = 1.0,
    buffer_circle_dashed: bool = True,
    buffer_circle_fill: bool = False,
    buffer_circle_fill_color: Optional[str] = None,
    buffer_circle_fill_alpha: float = 0.1,
    show_scale_bar: bool = False,
    scale_bar_position: str = 'bottom-left',
    scale_bar_style: str = 'classic',
    scale_bar_distance_miles: Optional[float] = None,
    scale_bar_scale_denominator: Optional[float] = None,
    scale_bar_dpi: int = 180
):
    """
    Draw polygon and circle overlays on a matplotlib axes using pixel coordinates.
    
    Args:
        ax: Matplotlib axes object
        polygon_coords: List of (longitude, latitude) coordinate pairs
        extent: Map extent dictionary with xmin, xmax, ymin, ymax
        image_width_pixels: Width of the image in pixels
        image_height_pixels: Height of the image in pixels
        polygon_color: Color for the polygon fill
        polygon_alpha: Opacity for the polygon fill (0-1)
        outline_color: Color for the polygon outline
        outline_width: Width of the polygon outline
        no_fill: If True, the polygon will have no fill
        show_buffer_circle: Whether to show a buffer circle
        buffer_circle_center: Center of the buffer circle (lon, lat)
        buffer_circle_radius_miles: Radius of the buffer circle in miles
        buffer_circle_color: Color for the buffer circle outline
        buffer_circle_width: Width of the buffer circle line
        buffer_circle_dashed: If True, use dashed line for circle
        buffer_circle_fill: If True, fill the buffer circle
        buffer_circle_fill_color: Fill color for buffer circle
        buffer_circle_fill_alpha: Opacity for the buffer circle fill
        show_scale_bar: Whether to show a scale bar
        scale_bar_position: Position of scale bar ('bottom-left', 'bottom-right', 'top-left', 'top-right')
        scale_bar_style: Style of scale bar ('classic', 'simple', 'modern')
        scale_bar_distance_miles: Distance for scale bar in miles (auto-calculated if None)
        scale_bar_scale_denominator: Scale denominator from LOD (preferred for accuracy)
        scale_bar_dpi: DPI of the image for scale calculations
    """
    # Ensure the polygon is closed
    display_polygon = list(polygon_coords)
    if display_polygon[0] != display_polygon[-1]:
        display_polygon = display_polygon + [display_polygon[0]]
    
    # Convert polygon to pixel coordinates
    polygon_pixels = [lonlat_to_pixel(lon, lat, extent, image_width_pixels, image_height_pixels) 
                     for lon, lat in display_polygon]
    
    # Draw the polygon
    polygon_patch = MatplotlibPolygon(
        polygon_pixels, 
        closed=True, 
        fill=not no_fill,
        alpha=polygon_alpha if not no_fill else 0,
        edgecolor=outline_color if outline_color else polygon_color,
        linewidth=outline_width,
        facecolor=polygon_color
    )
    ax.add_patch(polygon_patch)
    
    # Add buffer circle if requested
    if show_buffer_circle and buffer_circle_center:
        center_lon, center_lat = buffer_circle_center
        
        # Generate circle points
        circle_points = generate_circle_points(
            center_lon, center_lat, 
            buffer_circle_radius_miles, 
            num_points=64
        )
        
        # Convert to pixel coordinates
        circle_pixels = [lonlat_to_pixel(lon, lat, extent, image_width_pixels, image_height_pixels) 
                        for lon, lat in circle_points]
        
        # Determine the linestyle
        linestyle = 'dashed' if buffer_circle_dashed else 'solid'
        
        # Draw the circle
        circle_patch = MatplotlibPolygon(
            circle_pixels,
            closed=True,
            fill=buffer_circle_fill,
            alpha=buffer_circle_fill_alpha if buffer_circle_fill else 0,
            edgecolor=buffer_circle_color,
            linewidth=buffer_circle_width,
            linestyle=linestyle,
            facecolor=buffer_circle_fill_color if buffer_circle_fill_color else buffer_circle_color
        )
        ax.add_patch(circle_patch)
    
    # Add scale bar if requested
    if show_scale_bar:
        add_scale_bar(
            ax=ax,
            extent=extent,
            image_width_pixels=image_width_pixels,
            image_height_pixels=image_height_pixels,
            position=scale_bar_position,
            target_distance_miles=scale_bar_distance_miles,
            style=scale_bar_style,
            scale_denominator=scale_bar_scale_denominator,
            dpi=scale_bar_dpi
        )

def create_web_map_json(
    extent: dict,
    operational_layers: List[dict],
    output_dpi: int = 150,
    image_width_pixels: int = 800,
    image_height_pixels: int = 600,
    title: str = "Map",
    use_template: bool = True,
    target_map_scale: Optional[float] = None
) -> dict:
    """
    Create the Web_Map_as_JSON structure for ArcGIS Print Service.
    
    Args:
        extent: Map extent dictionary
        operational_layers: List of operational layer definitions
        output_dpi: Resolution of the output image
        image_width_pixels: Width of the output image
        image_height_pixels: Height of the output image
        title: Title for the map
        use_template: Whether to use a layout template
        target_map_scale: Desired map scale
        
    Returns:
        Dictionary containing the Web_Map_as_JSON structure
    """
    web_map_json = {
        "mapOptions": {
            "extent": extent,
            "spatialReference": {"wkid": 4326},
            "showAttribution": False
        },
        "operationalLayers": operational_layers,
        "exportOptions": {
            "dpi": output_dpi,
            "outputSize": [image_width_pixels, image_height_pixels]
        }
    }
    
    # Add layout options if using template
    if use_template:
        web_map_json["layoutOptions"] = {
            "titleText": title,
            "legendOptions": {"operationalLayers": True}
        }
    
    # Add target scale to mapOptions if provided
    if target_map_scale is not None and target_map_scale > 0:
        web_map_json["mapOptions"]["scale"] = target_map_scale
    
    return web_map_json

def calculate_map_extent(
    polygon_coords: Sequence[Tuple[float, float]],
    buffer_miles: float = 0.0,
    extent_buffer_percent: float = 0.10
) -> dict:
    """
    Calculate the map extent from polygon coordinates with optional buffer.
    
    Args:
        polygon_coords: List of (longitude, latitude) coordinate pairs
        buffer_miles: Buffer distance in miles around the polygon
        extent_buffer_percent: Additional buffer as percentage of width/height for display
        
    Returns:
        Dictionary containing the map extent
    """
    # Apply buffer if requested
    if buffer_miles > 0:
        extent_coords = add_buffer_to_polygon(polygon_coords, buffer_miles)
    else:
        extent_coords = polygon_coords

    min_lon = min(p[0] for p in extent_coords)
    max_lon = max(p[0] for p in extent_coords)
    min_lat = min(p[1] for p in extent_coords)
    max_lat = max(p[1] for p in extent_coords)
    
    # Add a small buffer to the extent for display purposes
    width_deg = max_lon - min_lon
    height_deg = max_lat - min_lat
    buffer_lon = width_deg * extent_buffer_percent
    buffer_lat = height_deg * extent_buffer_percent

    return {
        "xmin": min_lon - buffer_lon, "ymin": min_lat - buffer_lat,
        "xmax": max_lon + buffer_lon, "ymax": max_lat + buffer_lat,
        "spatialReference": {"wkid": 4326}
    }


def calculate_scale_bar_length_from_lod(
    scale_denominator: float,
    image_width_pixels: int,
    dpi: int = 180,
    target_distance_miles: Optional[float] = None
) -> Tuple[float, str, float]:
    """
    Calculate appropriate scale bar length based on LOD scale denominator.
    
    Args:
        scale_denominator: Scale denominator from LOD (e.g., 4513 for 1:4513 scale)
        image_width_pixels: Width of the image in pixels
        dpi: Dots per inch for the image
        target_distance_miles: Desired distance in miles (auto-calculated if None)
        
    Returns:
        Tuple of (distance_miles, label_text, width_pixels)
    """
    # Calculate the real-world width of the map in miles using scale denominator
    # Formula: real_world_distance = (pixel_distance / dpi) * scale_denominator * meters_per_inch
    meters_per_inch = 0.0254
    map_width_meters = (image_width_pixels / dpi) * scale_denominator * meters_per_inch
    map_width_miles = map_width_meters / 1609.34
    
    # If no target distance specified, calculate based on scale denominator like ArcGIS
    if target_distance_miles is None:
        # Calculate appropriate scale bar distance based on scale denominator
        # This mimics ArcGIS behavior where scale bar adapts to the map scale
        
        # Standard scale bar distances in miles (ArcGIS-like progression)
        standard_distances = [
            0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 
            1.0, 1.5, 2.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 50.0, 75.0, 
            100.0, 150.0, 200.0, 250.0, 500.0, 750.0, 1000.0
        ]
        
        # Target scale bar to be about 1.5 inches on the final map
        target_inches = 1.5
        
        # Calculate what distance 1.5 inches represents at this scale
        # Formula: real_distance = (inches_on_map * scale_denominator) / (inches_per_mile)
        inches_per_mile = 63360  # 5280 feet * 12 inches/foot
        real_world_target_miles = (target_inches * scale_denominator) / inches_per_mile
        
        # Find the closest standard distance
        target_distance_miles = min(standard_distances, 
                                  key=lambda x: abs(x - real_world_target_miles))
        
        # Verify the resulting scale bar size is reasonable (0.5 to 3 inches)
        resulting_inches = (target_distance_miles * inches_per_mile) / scale_denominator
        
        # If resulting scale bar would be too small (< 0.5 inch) or too large (> 3 inches), adjust
        if resulting_inches < 0.5:
            # Scale bar too small, find next larger standard distance
            larger_distances = [d for d in standard_distances if d > target_distance_miles]
            if larger_distances:
                target_distance_miles = larger_distances[0]
        elif resulting_inches > 3.0:
            # Scale bar too large, find next smaller standard distance
            smaller_distances = [d for d in standard_distances if d < target_distance_miles]
            if smaller_distances:
                target_distance_miles = smaller_distances[-1]
    
    # Calculate pixel width for this distance based on the scale denominator
    # Use the scale denominator directly to ensure accurate representation
    inches_per_mile = 63360  # 5280 feet * 12 inches/foot
    scale_bar_inches = (target_distance_miles * inches_per_mile) / scale_denominator
    width_pixels = scale_bar_inches * dpi
    
    # Ensure minimum visibility - scale bar should be at least 25% of image width
    # This accounts for the fact that the scale bar appears on the final composed image
    min_width_pixels = max(800, image_width_pixels * 0.25)  # At least 800px or 25% of image width
    max_width_pixels = image_width_pixels * 0.45  # No more than 45% of image width
    
    if width_pixels < min_width_pixels:
        # Find a larger standard distance that gives us adequate width
        standard_distances = [
            0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 
            1.0, 1.5, 2.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 50.0, 75.0, 
            100.0, 150.0, 200.0, 250.0, 500.0, 750.0, 1000.0
        ]
        
        for distance in standard_distances:
            if distance > target_distance_miles:
                test_inches = (distance * inches_per_mile) / scale_denominator
                test_pixels = test_inches * dpi
                if test_pixels >= min_width_pixels:
                    target_distance_miles = distance
                    width_pixels = test_pixels
                    break
    
    # Cap the width if it's too large
    if width_pixels > max_width_pixels:
        width_pixels = max_width_pixels
    
    # Create label text with both miles and feet
    feet = target_distance_miles * 5280
    
    if target_distance_miles >= 1:
        if target_distance_miles == int(target_distance_miles):
            miles_text = f"{int(target_distance_miles)} mi"
        else:
            miles_text = f"{target_distance_miles:.1f} mi"
        
        # Add feet equivalent for reference
        if feet >= 1000:
            feet_text = f"({feet/1000:.1f}k ft)"
        else:
            feet_text = f"({int(feet)} ft)"
        label_text = f"{miles_text} {feet_text}"
    else:
        # For distances less than 1 mile, show as 0.x mi with feet
        miles_text = f"{target_distance_miles:.1f} mi"
        if feet >= 1000:
            feet_text = f"({feet/1000:.1f}k ft)"
        else:
            feet_text = f"({int(feet)} ft)"
        label_text = f"{miles_text} {feet_text}"
    
    return target_distance_miles, label_text, width_pixels


def calculate_scale_bar_length(
    extent: dict,
    image_width_pixels: int,
    target_distance_miles: Optional[float] = None
) -> Tuple[float, str, float]:
    """
    Calculate appropriate scale bar length based on map extent (fallback method).
    
    Args:
        extent: Map extent dictionary with xmin, xmax, ymin, ymax
        image_width_pixels: Width of the image in pixels
        target_distance_miles: Desired distance in miles (auto-calculated if None)
        
    Returns:
        Tuple of (distance_miles, label_text, width_pixels)
    """
    # Calculate the real-world width of the map in miles
    map_width_degrees = extent['xmax'] - extent['xmin']
    center_lat = (extent['ymax'] + extent['ymin']) / 2
    
    # Convert degrees to miles at the center latitude
    meters_per_degree_lon = 111320.0 * math.cos(math.radians(center_lat))
    map_width_miles = (map_width_degrees * meters_per_degree_lon) / 1609.34
    
    # If no target distance specified, calculate based on estimated scale like ArcGIS
    if target_distance_miles is None:
        # Calculate appropriate scale bar distance based on estimated scale
        # This mimics ArcGIS behavior where scale bar adapts to the map scale
        
        # Standard scale bar distances in miles (ArcGIS-like progression)
        standard_distances = [
            0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 
            1.0, 1.5, 2.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 50.0, 75.0, 
            100.0, 150.0, 200.0, 250.0, 500.0, 750.0, 1000.0
        ]
        
        # Estimate scale denominator from map width
        # Assume 180 DPI and calculate scale denominator
        default_dpi = 180
        meters_per_inch = 0.0254
        map_width_meters = map_width_miles * 1609.34
        estimated_scale_denominator = (map_width_meters * default_dpi) / (image_width_pixels * meters_per_inch)
        
        # Target scale bar to be about 1.5 inches on the final map
        target_inches = 1.5
        
        # Calculate what distance 1.5 inches represents at this estimated scale
        inches_per_mile = 63360  # 5280 feet * 12 inches/foot
        real_world_target_miles = (target_inches * estimated_scale_denominator) / inches_per_mile
        
        # Find the closest standard distance
        target_distance_miles = min(standard_distances, 
                                  key=lambda x: abs(x - real_world_target_miles))
        
        # Verify the resulting scale bar size is reasonable (0.5 to 3 inches)
        resulting_inches = (target_distance_miles * inches_per_mile) / estimated_scale_denominator
        
        # If resulting scale bar would be too small (< 0.5 inch) or too large (> 3 inches), adjust
        if resulting_inches < 0.5:
            # Scale bar too small, find next larger standard distance
            larger_distances = [d for d in standard_distances if d > target_distance_miles]
            if larger_distances:
                target_distance_miles = larger_distances[0]
        elif resulting_inches > 3.0:
            # Scale bar too large, find next smaller standard distance
            smaller_distances = [d for d in standard_distances if d < target_distance_miles]
            if smaller_distances:
                target_distance_miles = smaller_distances[-1]
    
    # Calculate pixel width for this distance
    pixels_per_mile = image_width_pixels / map_width_miles
    width_pixels = target_distance_miles * pixels_per_mile
    
    # Create label text with both miles and feet
    feet = target_distance_miles * 5280
    
    if target_distance_miles >= 1:
        if target_distance_miles == int(target_distance_miles):
            miles_text = f"{int(target_distance_miles)} mi"
        else:
            miles_text = f"{target_distance_miles:.1f} mi"
        
        # Add feet equivalent for reference
        if feet >= 1000:
            feet_text = f"({feet/1000:.1f}k ft)"
        else:
            feet_text = f"({int(feet)} ft)"
        label_text = f"{miles_text} {feet_text}"
    else:
        # For distances less than 1 mile, show as 0.x mi with feet
        miles_text = f"{target_distance_miles:.1f} mi"
        if feet >= 1000:
            feet_text = f"({feet/1000:.1f}k ft)"
        else:
            feet_text = f"({int(feet)} ft)"
        label_text = f"{miles_text} {feet_text}"
    
    return target_distance_miles, label_text, width_pixels


def add_scale_bar(
    ax,
    extent: dict,
    image_width_pixels: int,
    image_height_pixels: int,
    position: str = 'bottom-left',
    target_distance_miles: Optional[float] = None,
    style: str = 'classic',
    color: str = 'black',
    background_color: str = 'white',
    background_alpha: float = 0.8,
    font_size: int = 10,
    margin_pixels: int = 20,
    scale_denominator: Optional[float] = None,
    dpi: int = 180
) -> None:
    """
    Add a scale bar to the map.
    
    Args:
        ax: Matplotlib axes object
        extent: Map extent dictionary
        image_width_pixels: Width of the image in pixels
        image_height_pixels: Height of the image in pixels
        position: 'bottom-left', 'bottom-right', 'top-left', 'top-right'
        target_distance_miles: Desired distance in miles (auto-calculated if None)
        style: 'classic' (alternating black/white), 'simple' (single line), or 'modern'
        color: Color for the scale bar
        background_color: Background color for the scale bar area
        background_alpha: Transparency of the background (0-1)
        font_size: Font size for the label
        margin_pixels: Margin from edge in pixels
        scale_denominator: Scale denominator from LOD (preferred method)
        dpi: Dots per inch for the image
    """
    # Calculate scale bar dimensions using LOD if available, otherwise use extent
    if scale_denominator is not None:
        distance_miles, label_text, bar_width_pixels = calculate_scale_bar_length_from_lod(
            scale_denominator, image_width_pixels, dpi, target_distance_miles
        )
    else:
        distance_miles, label_text, bar_width_pixels = calculate_scale_bar_length(
            extent, image_width_pixels, target_distance_miles
        )
    
    # Convert to axes coordinates (0-1)
    bar_width_norm = bar_width_pixels / image_width_pixels
    bar_height_pixels = max(40, int(image_height_pixels * 0.025))  # Scale bar height proportional to image (2.5% of height, min 40px)
    bar_height_norm = bar_height_pixels / image_height_pixels
    # Make margins proportional to image size
    margin_pixels_x = max(margin_pixels, int(image_width_pixels * 0.02))  # At least 2% of width
    margin_pixels_y = max(margin_pixels, int(image_height_pixels * 0.02))  # At least 2% of height
    margin_x_norm = margin_pixels_x / image_width_pixels
    margin_y_norm = margin_pixels_y / image_height_pixels
    
    # Determine position
    if position == 'bottom-left':
        x_pos = margin_x_norm
        y_pos = margin_y_norm
    elif position == 'bottom-right':
        x_pos = 1 - margin_x_norm - bar_width_norm
        y_pos = margin_y_norm
    elif position == 'top-left':
        x_pos = margin_x_norm
        y_pos = 1 - margin_y_norm - bar_height_norm * 3  # Extra space for text
    elif position == 'top-right':
        x_pos = 1 - margin_x_norm - bar_width_norm
        y_pos = 1 - margin_y_norm - bar_height_norm * 3
    else:
        raise ValueError("Position must be 'bottom-left', 'bottom-right', 'top-left', or 'top-right'")
    
    # Add background
    bg_width = bar_width_norm + 0.02
    bg_height = bar_height_norm * 3
    bg_x = x_pos - 0.01
    bg_y = y_pos - 0.005
    
    background = FancyBboxPatch(
        (bg_x, bg_y), bg_width, bg_height,
        boxstyle="round,pad=0.005",
        facecolor=background_color,
        edgecolor='none',
        alpha=background_alpha,
        transform=ax.transAxes,
        zorder=1000
    )
    ax.add_patch(background)
    
    if style == 'classic':
        # Classic alternating black and white segments
        num_segments = 4
        segment_width = bar_width_norm / num_segments
        
        for i in range(num_segments):
            segment_color = 'black' if i % 2 == 0 else 'white'
            segment_x = x_pos + i * segment_width
            
            segment = Rectangle(
                (segment_x, y_pos), segment_width, bar_height_norm,
                facecolor=segment_color,
                edgecolor='black',
                linewidth=0.5,
                transform=ax.transAxes,
                zorder=1001
            )
            ax.add_patch(segment)
            
    elif style == 'simple':
        # Simple single line
        bar = Rectangle(
            (x_pos, y_pos), bar_width_norm, bar_height_norm,
            facecolor='none',
            edgecolor=color,
            linewidth=2,
            transform=ax.transAxes,
            zorder=1001
        )
        ax.add_patch(bar)
        
    elif style == 'modern':
        # Modern gradient style
        bar = Rectangle(
            (x_pos, y_pos), bar_width_norm, bar_height_norm,
            facecolor=color,
            edgecolor='none',
            alpha=0.8,
            transform=ax.transAxes,
            zorder=1001
        )
        ax.add_patch(bar)
        
        # Add border
        border = Rectangle(
            (x_pos, y_pos), bar_width_norm, bar_height_norm,
            facecolor='none',
            edgecolor=color,
            linewidth=1,
            transform=ax.transAxes,
            zorder=1002
        )
        ax.add_patch(border)
    
    # Add scale labels
    # Start label (0)
    ax.text(
        x_pos, y_pos + bar_height_norm + 0.01,
        '0',
        transform=ax.transAxes,
        fontsize=max(font_size + 4, int(image_width_pixels * 0.004)),  # Font size proportional to image width
        ha='left',
        va='bottom',
        color=color,
        weight='bold',
        zorder=1003
    )
    
    # End label (distance)
    ax.text(
        x_pos + bar_width_norm, y_pos + bar_height_norm + 0.01,
        label_text,
        transform=ax.transAxes,
        fontsize=max(font_size + 4, int(image_width_pixels * 0.004)),  # Font size proportional to image width
        ha='right',
        va='bottom',
        color=color,
        weight='bold',
        zorder=1003
    )