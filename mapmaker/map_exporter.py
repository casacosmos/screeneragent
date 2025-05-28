# mapmaker/map_exporter.py

# Configure matplotlib backend for web compatibility
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import warnings
import math
import json
from typing import List, Dict, Any, Tuple, Sequence, Optional, Union

from mapmaker.common import MapServerClient, DEFAULT_DPI
from mapmaker.map_overlays import (
    PrintServiceClient, convert_color_to_rgba_list, fetch_image_from_url,
    generate_circle_points, add_buffer_to_polygon, geodesic_point_at_distance_and_bearing,
    create_polygon_layer_json, create_circle_layer_json, draw_matplotlib_overlays,
    create_web_map_json, calculate_map_extent, lonlat_to_pixel
)
from matplotlib.patches import Rectangle, Polygon as MatplotlibPolygon
from matplotlib.lines import Line2D

class MapExporter(MapServerClient):
    """
    Map exporter that can work with different map backgrounds (topographic, satellite, etc.).
    Provides a consistent API while allowing easy switching between different map services.
    """
    
    # Print profile information from the JP_print template
    PRINT_PROFILES = {
        'JP_print': {
            'page_size_inches': (24.0, 18.0),
            'data_frame_size_inches': (22.0, 13.446799999999712),
            'aspect_ratio': 22.0 / 13.446799999999712,  # ≈ 1.636
            'has_title': True,
            'has_legend': True,
            'has_author': False,
            'has_copyright': False,
            'description': 'Full layout with title and legend support'
        },
        'MAP_ONLY': {
            'page_size_inches': None,  # Variable based on request
            'data_frame_size_inches': None,  # Same as page size
            'aspect_ratio': None,  # User-defined
            'has_title': False,
            'has_legend': False,
            'has_author': False,
            'has_copyright': False,
            'description': 'Map only without layout elements'
        }
    }
    
    # Predefined map services
    MAP_SERVICES = {
        'topografico': {
            'url': 'https://sige.pr.gov/server/rest/services/topografico/MapServer',
            'description': 'Puerto Rico Topographic Map',
            'type': 'topographic',
            'layer_info': {
                'primary_layer_id': 1,
                'primary_layer_name': 'topografico',
                'supports_legend': False,  # Cached service
                'is_cached': True
            },
            'defaults': {
                'polygon_color': 'red',
                'polygon_alpha': 0.4,
                'outline_color': 'black',
                'outline_width': 3.0,
                'buffer_circle_radius_miles': 0.5,
                'buffer_circle_color': 'yellow',
                'buffer_circle_width': 6.0,
                'buffer_circle_dashed': True,
                'buffer_circle_fill': False,
                'buffer_circle_fill_alpha': 0.15,
                'output_dpi': 180,
                'buffer_miles': 0.5,
                'title_template': "Polygon on {description}",
                'preferred_template': 'JP_print',
                'scale_bar_style': 'classic',
                'show_scale_bar': True,
                'show_legend': True
            }
        },
        'foto_pr_2017': {
            'url': 'https://sige.pr.gov/server/rest/services/foto_pr_2017/MapServer',
            'description': 'Fotos PR 2017 antes huracan Maria',
            'type': 'satellite',
            'year': 2017,
            'layer_info': {
                'primary_layer_id': 0,
                'primary_layer_name': 'fotos2017',
                'supports_legend': False,  # Cached service
                'is_cached': False
            },
            'defaults': {
                'polygon_color': 'red',
                'polygon_alpha': 0.4,
                'outline_color': 'black',
                'outline_width': 3.0,
                'buffer_circle_radius_miles': 0.5,
                'buffer_circle_color': 'yellow',
                'buffer_circle_width': 6.0,
                'buffer_circle_dashed': True,
                'buffer_circle_fill': False,
                'buffer_circle_fill_alpha': 0.15,
                'output_dpi': 180,
                'buffer_miles': 0.5,
                'title_template': "Polygon on {description}",
                'preferred_template': 'JP_print',
                'scale_bar_style': 'classic',
                'show_scale_bar': True,
                'show_legend': True
            }
        }
        # Add more services here as they become available
    }
    
    # Predefined style presets
    STYLE_PRESETS = {
        'default': {
            # This matches the new unified defaults (red fill, black outline)
            'polygon_color': 'red',
            'polygon_alpha': 0.4,
            'outline_color': 'black',
            'outline_width': 3.0,
            'buffer_circle_color': 'yellow',
            'buffer_circle_width': 6.0,
            'buffer_circle_dashed': True,
            'buffer_circle_fill': False
        },
        'yellow_circle_filled': {
            'polygon_color': 'red',
            'polygon_alpha': 0.4,
            'outline_color': 'black',
            'outline_width': 3.0,
            'buffer_circle_color': 'black',
            'buffer_circle_width': 3.0,
            'buffer_circle_dashed': False,
            'buffer_circle_fill': True,
            'buffer_circle_fill_color': 'yellow',
            'buffer_circle_fill_alpha': 0.15
        },
        'blue_circle_classic': {
            # Classic topographic style with blue circle
            'polygon_color': 'red',
            'polygon_alpha': 0.4,
            'outline_color': 'black',
            'outline_width': 3.0,
            'buffer_circle_color': 'blue',
            'buffer_circle_width': 2.0,
            'buffer_circle_dashed': True,
            'buffer_circle_fill': False
        }
    }
    
    def __init__(self, service_name: str = 'topografico', dpi: int = DEFAULT_DPI, fetch_metadata: bool = True):
        """
        Initialize the MapExporter.
        
        Args:
            service_name: Name of the map service to use (from MAP_SERVICES)
            dpi: Dots per inch for image resolution
            fetch_metadata: Whether to fetch metadata on initialization
        """
        if service_name not in self.MAP_SERVICES:
            available_services = ', '.join(self.MAP_SERVICES.keys())
            raise ValueError(f"Unknown service '{service_name}'. Available services: {available_services}")
        
        self.service_info = self.MAP_SERVICES[service_name]
        self.service_name = service_name
        self.service_defaults = self.service_info['defaults']
        
        super().__init__(
            self.service_info['url'],
            dpi
        )
        
        if fetch_metadata:
            self.fetch_metadata()
    
    @classmethod
    def list_available_services(cls) -> Dict[str, Dict[str, Any]]:
        """List all available map services."""
        return cls.MAP_SERVICES.copy()
    
    @classmethod
    def list_style_presets(cls) -> Dict[str, Dict[str, Any]]:
        """List all available style presets."""
        return cls.STYLE_PRESETS.copy()
    
    @classmethod
    def list_print_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """List all available print profiles with their specifications."""
        return cls.PRINT_PROFILES.copy()
    
    def get_service_description(self) -> str:
        """Get a human-readable description of the current service."""
        return self.service_info['description']
    
    def get_service_type(self) -> str:
        """Get the type of the current service (topographic, satellite, etc.)."""
        return self.service_info['type']
    
    def get_service_layer_info(self) -> Dict[str, Any]:
        """Get layer information for the current service."""
        return self.service_info['layer_info']
    
    def get_optimal_dimensions_for_template(self, template_name: str = 'JP_print') -> Tuple[int, int]:
        """
        Get optimal image dimensions based on print template specifications.
        
        Args:
            template_name: Name of the print template
            
        Returns:
            Tuple of (width_pixels, height_pixels) optimized for the template
        """
        if template_name not in self.PRINT_PROFILES:
            template_name = 'JP_print'  # Fallback to default
        
        profile = self.PRINT_PROFILES[template_name]
        
        if template_name == 'MAP_ONLY':
            # For map-only, use the same aspect ratio as JP_print but smaller dimensions
            jp_profile = self.PRINT_PROFILES['JP_print']
            aspect_ratio = jp_profile['aspect_ratio']
            
            # Use a reasonable base width and calculate height to maintain aspect ratio
            base_width = 1600  # Higher resolution than before
            height = int(base_width / aspect_ratio)
            return (base_width, height)
        
        # For JP_print, use the data frame aspect ratio
        aspect_ratio = profile['aspect_ratio']
        
        # Calculate dimensions that work well with the template
        # Using 180 DPI as base (our default)
        base_dpi = 180
        
        # Target the data frame size in pixels
        data_frame_width_inches = profile['data_frame_size_inches'][0]
        data_frame_height_inches = profile['data_frame_size_inches'][1]
        
        width_pixels = int(data_frame_width_inches * base_dpi)
        height_pixels = int(data_frame_height_inches * base_dpi)
        
        return (width_pixels, height_pixels)
    
    def switch_service(self, service_name: str, fetch_metadata: bool = True):
        """
        Switch to a different map service.
        
        Args:
            service_name: Name of the new service to use
            fetch_metadata: Whether to fetch metadata for the new service
        """
        if service_name not in self.MAP_SERVICES:
            available_services = ', '.join(self.MAP_SERVICES.keys())
            raise ValueError(f"Unknown service '{service_name}'. Available services: {available_services}")
        
        self.service_info = self.MAP_SERVICES[service_name]
        self.service_name = service_name
        self.service_defaults = self.service_info['defaults']
        self.service_url = self.service_info['url']
        
        if fetch_metadata:
            self.fetch_metadata()
    
    def apply_style_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Get style settings from a predefined preset.
        
        Args:
            preset_name: Name of the style preset
            
        Returns:
            Dictionary of style settings
        """
        if preset_name not in self.STYLE_PRESETS:
            available_presets = ', '.join(self.STYLE_PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available_presets}")
        
        return self.STYLE_PRESETS[preset_name].copy()
    
    def _apply_defaults(self, **kwargs) -> Dict[str, Any]:
        """
        Apply service defaults to parameters, with style preset support.
        
        Args:
            **kwargs: All the parameters passed to overlay_polygon
            
        Returns:
            Dictionary with all parameters resolved to actual values
        """
        # Apply style preset if specified
        if kwargs.get('style_preset'):
            preset_settings = self.apply_style_preset(kwargs['style_preset'])
            # Only apply preset values if the parameter wasn't explicitly provided
            for key, value in preset_settings.items():
                if kwargs.get(key) is None:
                    kwargs[key] = value
        
        # Apply service defaults for any remaining None values
        defaults_mapping = {
            'polygon_color': 'polygon_color',
            'polygon_alpha': 'polygon_alpha', 
            'outline_color': 'outline_color',
            'outline_width': 'outline_width',
            'buffer_circle_radius_miles': 'buffer_circle_radius_miles',
            'buffer_circle_color': 'buffer_circle_color',
            'buffer_circle_width': 'buffer_circle_width',
            'buffer_circle_dashed': 'buffer_circle_dashed',
            'buffer_circle_fill': 'buffer_circle_fill',
            'buffer_circle_fill_alpha': 'buffer_circle_fill_alpha',
            'output_dpi': 'output_dpi',
            'buffer_miles': 'buffer_miles',
            'scale_bar_style': 'scale_bar_style',
            'show_scale_bar': 'show_scale_bar',
            'show_legend': 'show_legend'
        }
        
        for param_name, default_key in defaults_mapping.items():
            if kwargs.get(param_name) is None:
                kwargs[param_name] = self.service_defaults[default_key]
        
        # Auto-generate title if not provided
        if kwargs.get('title') is None:
            title_template = self.service_defaults['title_template']
            if '{description}' in title_template:
                kwargs['title'] = title_template.format(description=self.get_service_description())
            else:
                kwargs['title'] = title_template
                
        return kwargs
    
    def _create_basemap_layer(self) -> Dict[str, Any]:
        """Create the basemap layer definition for operational layers."""
        layer_info = self.get_service_layer_info()
        
        return {
            "id": f"basemap_layer_{self.service_name}",
            "title": f"{self.get_service_type().title()} Basemap - {self.get_service_description()}",
            "opacity": 1,
            "minScale": 0,
            "maxScale": 0,
            "url": self.service_url,
            "type": "ArcGISTiledMapServiceLayer" if layer_info['is_cached'] else "ArcGISDynamicMapServiceLayer"
        }
    
    def overlay_polygon(
        self,
        polygon_coords: Sequence[Tuple[float, float]], 
        image_width_pixels: int = 800,
        image_height_pixels: int = 600,
        save_path: Optional[str] = None, 
        show: bool = True, 
        title: Optional[str] = None,  # Will use service default or auto-generate if None
        style_preset: Optional[str] = None,  # Apply a predefined style preset
        polygon_color: Optional[str] = None,  # Will use service default if None
        polygon_alpha: Optional[float] = None,  # Will use service default if None
        outline_color: Optional[str] = None,  # Will use service default if None
        outline_width: Optional[float] = None,  # Will use service default if None
        no_fill: bool = False,
        show_buffer_circle: bool = False,
        buffer_circle_radius_miles: Optional[float] = None,  # Will use service default if None
        buffer_circle_color: Optional[str] = None,  # Will use service default if None
        buffer_circle_width: Optional[float] = None,  # Will use service default if None
        buffer_circle_dashed: Optional[bool] = None,  # Will use service default if None
        buffer_circle_fill: Optional[bool] = None,  # Will use service default if None
        buffer_circle_fill_color: Optional[str] = None,
        buffer_circle_fill_alpha: Optional[float] = None,  # Will use service default if None
        output_dpi: Optional[int] = None,  # Will use service default if None
        verify_ssl: bool = False,
        print_service_url: str = "https://sige.pr.gov/server/rest/services/printjp/JPTemplate/GPServer",
        use_template: bool = True,
        layout_template_name: str = "JP_print",
        target_map_scale: Optional[float] = None,
        buffer_miles: Optional[float] = None,  # Will use service default if None
        auto_adjust_extent: bool = True,
        show_scale_bar: Optional[bool] = None,  # Show distance scale bar (uses service default if None)
        scale_bar_position: str = 'bottom-left',  # Position of scale bar
        scale_bar_style: str = 'classic',  # Style of scale bar
        scale_bar_distance_miles: Optional[float] = None  # Distance for scale bar
    ) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
        """
        Generates a map with an overlay of the given polygon using the ArcGIS Print Service.
        
        This method automatically uses appropriate defaults based on the selected map service,
        but allows all parameters to be overridden.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            image_width_pixels: Width of the output image in pixels
            image_height_pixels: Height of the output image in pixels
            save_path: Path to save the output image
            show: Whether to display the image
            title: Title for the map (auto-generated based on service if None)
            style_preset: Name of a predefined style preset to apply
            polygon_color: Color for the polygon fill (uses service default if None)
            polygon_alpha: Opacity for the polygon fill (uses service default if None)
            outline_color: Color for the polygon outline (uses service default if None)
            outline_width: Width of the polygon outline (uses service default if None)
            no_fill: If True, the polygon will have no fill (transparent)
            show_buffer_circle: Whether to show a circle with exact radius around the polygon center
            buffer_circle_radius_miles: Radius of the buffer circle in miles (uses service default if None)
            buffer_circle_color: Color for the buffer circle outline (uses service default if None)
            buffer_circle_width: Width of the buffer circle line (uses service default if None)
            buffer_circle_dashed: If True, use dashed line for circle (uses service default if None)
            buffer_circle_fill: If True, fill the buffer circle with color (uses service default if None)
            buffer_circle_fill_color: Fill color for buffer circle (defaults to buffer_circle_color if None)
            buffer_circle_fill_alpha: Opacity for the buffer circle fill (uses service default if None)
            output_dpi: Resolution of the output image in dots per inch (uses service default if None)
            verify_ssl: Whether to verify SSL certificates
            print_service_url: URL of the ArcGIS Print Service
            use_template: If True, use the layout template; if False, export map only with no template
            layout_template_name: Name of the layout template to use (ignored if use_template=False)
            target_map_scale: Desired map scale (e.g., 4513 for LOD 17)
            buffer_miles: Optional buffer distance around polygon in miles (uses service default if None)
            auto_adjust_extent: If True, automatically adjust the map extent to fit the buffer circle
            
        Returns:
            Tuple of (figure, axes) for the plot, or (None, None) if an error occurred
        """
        if not polygon_coords:
            print("Error: Polygon coordinates are empty.")
            return None, None
        
        # Apply defaults and style presets using helper method
        params = self._apply_defaults(
            style_preset=style_preset,
            polygon_color=polygon_color,
            polygon_alpha=polygon_alpha,
            outline_color=outline_color,
            outline_width=outline_width,
            buffer_circle_radius_miles=buffer_circle_radius_miles,
            buffer_circle_color=buffer_circle_color,
            buffer_circle_width=buffer_circle_width,
            buffer_circle_dashed=buffer_circle_dashed,
            buffer_circle_fill=buffer_circle_fill,
            buffer_circle_fill_alpha=buffer_circle_fill_alpha,
            output_dpi=output_dpi,
            buffer_miles=buffer_miles,
            title=title,
            show_scale_bar=show_scale_bar,
            scale_bar_position=scale_bar_position,
            scale_bar_style=scale_bar_style,
            scale_bar_distance_miles=scale_bar_distance_miles
        )
        
        # Calculate polygon center for buffer circle reference
        lons, lats = zip(*polygon_coords)
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
            
        # Auto-adjust extent for buffer circle if needed
        if show_buffer_circle and auto_adjust_extent:
            # Use the circle radius (plus a 20% margin) for the buffer to ensure the circle is visible
            display_buffer_miles = params['buffer_circle_radius_miles'] * 1.2
            if params['buffer_miles'] < display_buffer_miles:
                params['buffer_miles'] = display_buffer_miles
                print(f"Auto-adjusting map extent to fit {params['buffer_circle_radius_miles']} mile radius circle")
        
        # Calculate extent using the imported function
        extent = calculate_map_extent(polygon_coords, params['buffer_miles'])

        # For non-template mode, use matplotlib rendering
        if not use_template:
            return self._render_matplotlib_map(
                polygon_coords, extent, center_lon, center_lat,
                image_width_pixels, image_height_pixels, 
                show_buffer_circle, no_fill, verify_ssl,
                save_path, show, buffer_circle_fill_color, params
            )
        
        # For template mode, use ArcGIS Print Service
        return self._render_template_map(
            polygon_coords, extent, center_lon, center_lat,
            image_width_pixels, image_height_pixels,
            show_buffer_circle, no_fill, verify_ssl,
            print_service_url, layout_template_name, target_map_scale,
            save_path, show, buffer_circle_fill_color, params
        )
    
    def _get_scale_denominator_for_extent(
        self, extent: dict, image_width_pixels: int
    ) -> Optional[float]:
        """
        Get the appropriate scale denominator based on map extent and available LODs.
        For services without LODs, calculates a synthetic scale denominator.
        
        Args:
            extent: Map extent dictionary with xmin, xmax, ymin, ymax
            image_width_pixels: Width of the image in pixels
            
        Returns:
            Scale denominator (either from LODs or calculated)
        """
        # If we have LODs, use the standard method
        if self.scales:
            try:
                # Create extent corners as polygon for LOD calculation
                extent_polygon = [
                    (extent['xmin'], extent['ymin']),
                    (extent['xmax'], extent['ymin']),
                    (extent['xmax'], extent['ymax']),
                    (extent['xmin'], extent['ymax'])
                ]
                
                # Use the pick_best_lod method to get the appropriate LOD level
                best_lod_level = self.pick_best_lod(extent_polygon, image_width_pixels)
                
                # Get the scale denominator for this LOD
                if best_lod_level in self.scales:
                    return self.scales[best_lod_level].scale_denominator
                else:
                    # Fallback to a middle-range LOD if available
                    middle_lod = sorted(self.scales.keys())[len(self.scales) // 2]
                    return self.scales[middle_lod].scale_denominator
            except Exception as e:
                print(f"Warning: Could not determine LOD scale: {e}")
        
        # For services without LODs (like satellite), calculate synthetic scale denominator
        try:
            return self._calculate_synthetic_scale_denominator_from_extent(extent, image_width_pixels)
        except Exception as e:
            print(f"Warning: Could not calculate synthetic scale: {e}")
            return None
    
    def _calculate_synthetic_scale_denominator_from_extent(
        self, extent: dict, image_width_pixels: int
    ) -> float:
        """
        Calculate a synthetic scale denominator for services without LOD information.
        This mimics the LOD-based calculation to ensure consistent scale bar sizing.
        
        Args:
            extent: Map extent dictionary with xmin, xmax, ymin, ymax
            image_width_pixels: Width of the image in pixels
            
        Returns:
            Calculated scale denominator
        """
        # Calculate center latitude for accurate distance calculation
        center_lat = (extent['ymin'] + extent['ymax']) / 2
        
        # Calculate real-world width in meters
        # Use geodesic distance for accuracy
        real_world_width_meters = self.geodesic_distance(
            extent['xmin'], center_lat, extent['xmax'], center_lat
        )
        
        # Calculate meters per pixel
        meters_per_pixel = real_world_width_meters / image_width_pixels
        
        # Calculate scale denominator using standard cartographic formula
        # Scale denominator = (meters per pixel) / (meters per inch) * DPI
        meters_per_inch = 0.0254
        scale_denominator = (meters_per_pixel * self.dpi) / meters_per_inch
        
        return scale_denominator
    
    def _render_matplotlib_map(
        self, polygon_coords, extent, center_lon, center_lat,
        image_width_pixels, image_height_pixels, 
        show_buffer_circle, no_fill, verify_ssl,
        save_path, show, buffer_circle_fill_color, params
    ) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
        """Render map using matplotlib (non-template mode)."""
        try:
            # Get the basemap image
            extent_str = f"{extent['xmin']},{extent['ymin']},{extent['xmax']},{extent['ymax']}"
            basemap_url = f"{self.service_url}/export?bbox={extent_str}&bboxSR=4326&size={image_width_pixels},{image_height_pixels}&format=png32&transparent=true&f=image"
            basemap_image = fetch_image_from_url(basemap_url, verify_ssl)
            
            # Create the figure and plot the basemap
            basemap_array = np.array(basemap_image)
            fig, ax = plt.subplots(
                figsize=(image_width_pixels / params['output_dpi'], image_height_pixels / params['output_dpi']), 
                dpi=params['output_dpi']
            )
            ax.imshow(basemap_array)
            
            # Get the appropriate scale denominator from LOD
            scale_denominator = self._get_scale_denominator_for_extent(extent, image_width_pixels)
            
            # Draw overlays using the imported function
            draw_matplotlib_overlays(
                ax=ax,
                polygon_coords=polygon_coords,
                extent=extent,
                image_width_pixels=image_width_pixels,
                image_height_pixels=image_height_pixels,
                polygon_color=params['polygon_color'],
                polygon_alpha=params['polygon_alpha'],
                outline_color=params['outline_color'],
                outline_width=params['outline_width'],
                no_fill=no_fill,
                show_buffer_circle=show_buffer_circle,
                buffer_circle_center=(center_lon, center_lat) if show_buffer_circle else None,
                buffer_circle_radius_miles=params['buffer_circle_radius_miles'],
                buffer_circle_color=params['buffer_circle_color'],
                buffer_circle_width=params['buffer_circle_width'],
                buffer_circle_dashed=params['buffer_circle_dashed'],
                buffer_circle_fill=params['buffer_circle_fill'],
                buffer_circle_fill_color=buffer_circle_fill_color,
                buffer_circle_fill_alpha=params['buffer_circle_fill_alpha'],
                show_scale_bar=params.get('show_scale_bar', False),
                scale_bar_position=params.get('scale_bar_position', 'bottom-left'),
                scale_bar_style=params.get('scale_bar_style', 'classic'),
                scale_bar_distance_miles=params.get('scale_bar_distance_miles', None),
                scale_bar_scale_denominator=scale_denominator,
                scale_bar_dpi=params['output_dpi']
            )
            
            # Set title and formatting
            if params['title']:
                plt.title(params['title'])
            plt.axis('off')
            plt.tight_layout()
            
            # Save and show
            if save_path:
                plt.savefig(save_path, dpi=params['output_dpi'], bbox_inches='tight')
            if show:
                plt.show()
                
            return fig, ax
            
        except Exception as e:
            print(f"Error generating map without template: {e}")
            return None, None
    
    def _render_template_map(
        self, polygon_coords, extent, center_lon, center_lat,
        image_width_pixels, image_height_pixels,
        show_buffer_circle, no_fill, verify_ssl,
        print_service_url, layout_template_name, target_map_scale,
        save_path, show, buffer_circle_fill_color, params
    ) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
        """Render map using ArcGIS Print Service (template mode)."""
        try:
            # Create Print Service Client
            pcs = PrintServiceClient(gp_root_url=print_service_url)

            # Create operational layers
            operational_layers = [self._create_basemap_layer()]
            
            # Add polygon layer using imported function
            polygon_layer = create_polygon_layer_json(
                polygon_coords=polygon_coords,
                polygon_color=params['polygon_color'],
                polygon_alpha=params['polygon_alpha'],
                outline_color=params['outline_color'],
                outline_width=params['outline_width'],
                no_fill=no_fill
            )
            operational_layers.append(polygon_layer)
            
            # Add buffer circle if requested using imported function
            if show_buffer_circle:
                circle_layer = create_circle_layer_json(
                    center_lon=center_lon,
                    center_lat=center_lat,
                    radius_miles=params['buffer_circle_radius_miles'],
                    circle_color=params['buffer_circle_color'],
                    circle_width=params['buffer_circle_width'],
                    circle_dashed=params['buffer_circle_dashed'],
                    circle_fill=params['buffer_circle_fill'],
                    circle_fill_color=buffer_circle_fill_color,
                    circle_fill_alpha=params['buffer_circle_fill_alpha']
                )
                operational_layers.append(circle_layer)

            # Create enhanced Web_Map_as_JSON with proper legend support
            web_map_json = self._create_enhanced_web_map_json(
                extent=extent,
                operational_layers=operational_layers,
                output_dpi=params['output_dpi'],
                image_width_pixels=image_width_pixels,
                image_height_pixels=image_height_pixels,
                title=params['title'],
                use_template=True,
                layout_template_name=layout_template_name,
                target_map_scale=target_map_scale
            )
            
            # Call the Print Service
            export_result = pcs.export_web_map(
                web_map_json=web_map_json,
                layout_template=layout_template_name,
                fmt="PNG32",
                dpi=params['output_dpi']
            )
            
            # Extract the output URL
            output_url = self._extract_output_url(export_result)
            if not output_url:
                return None, None

            # Fetch and display the final map image
            final_map_image = fetch_image_from_url(output_url, verify_ssl)
            
            # Add custom legend and scale bar if using JP_print template
            if layout_template_name == 'JP_print':
                # Always show legend and scale bar for JP_print template (override user setting)
                params_with_legend = params.copy()
                params_with_legend['show_scale_bar'] = True
                params_with_legend['show_legend'] = True
                
                final_map_image = self._add_custom_legend_to_image(
                    final_map_image, 
                    show_buffer_circle, 
                    params['buffer_circle_radius_miles'],
                    params_with_legend,
                    extent=extent,
                    polygon_coords=polygon_coords,
                    image_width_pixels=image_width_pixels
                )
            
            fig, ax = plt.subplots(
                figsize=(final_map_image.width / params['output_dpi'], final_map_image.height / params['output_dpi']), 
                dpi=params['output_dpi']
            )
            ax.imshow(final_map_image)
            
            # Only add matplotlib title if showing
            if show and params['title']:
                plt.title(params['title'])
            plt.axis('off')
            
            # Save and show
            if save_path:
                plt.savefig(save_path, dpi=params['output_dpi'], bbox_inches='tight')
            if show:
                plt.show()
            
            return fig, ax
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error from print service: {e.response.status_code}")
            try:
                print(f"Server response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Server response (text): {e.response.text}")
            return None, None
        except Exception as e:
            print(f"Error calling print service: {e}")
            return None, None
    
    def _create_enhanced_web_map_json(
        self,
        extent: dict,
        operational_layers: List[dict],
        output_dpi: int,
        image_width_pixels: int,
        image_height_pixels: int,
        title: str,
        use_template: bool,
        layout_template_name: str,
        target_map_scale: Optional[float] = None
    ) -> dict:
        """
        Create enhanced Web_Map_as_JSON with proper legend and layout support.
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
        
        # Add layout options based on template profile
        if use_template and layout_template_name in self.PRINT_PROFILES:
            profile = self.PRINT_PROFILES[layout_template_name]
            
            layout_options = {}
            
            if profile['has_title']:
                layout_options["titleText"] = title
            
            if profile['has_legend']:
                # Enhanced legend options for operational layers
                legend_options = {
                    "operationalLayers": True,
                    "baseMapLayers": False,  # Don't include basemap in legend (cached services don't have meaningful legends)
                }
                
                # Only include layers that have meaningful legend information
                legend_layers = []
                for layer in operational_layers:
                    if layer.get('id', '').startswith('user_') or layer.get('id', '').startswith('buffer_'):
                        legend_layers.append({
                            "layerId": layer.get('id'),
                            "subLayerIds": None
                        })
                
                if legend_layers:
                    legend_options["legendLayers"] = legend_layers
                
                layout_options["legendOptions"] = legend_options
            
            if layout_options:
                web_map_json["layoutOptions"] = layout_options
        
        # Add target scale to mapOptions if provided
        if target_map_scale is not None and target_map_scale > 0:
            web_map_json["mapOptions"]["scale"] = target_map_scale
        
        return web_map_json
    
    def _add_custom_legend_to_image(
        self, 
        image: Image.Image, 
        show_buffer_circle: bool,
        buffer_circle_radius_miles: float,
        params: Dict[str, Any],
        extent: Optional[dict] = None,
        polygon_coords: Optional[Sequence[Tuple[float, float]]] = None,
        image_width_pixels: Optional[int] = None
    ) -> Image.Image:
        """
        Add a custom legend overlay to the map image since ArcGIS Print Service
        doesn't automatically generate legends for feature collections.
        Also adds scale bar if requested.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Polygon as MatplotlibPolygon
        from matplotlib.lines import Line2D
        import numpy as np
        from io import BytesIO
        
        # Ensure matplotlib uses non-interactive backend
        import matplotlib
        current_backend = matplotlib.get_backend()
        if current_backend != 'Agg':
            matplotlib.use('Agg')
        
        # Create a figure for the legend (increased size)
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=180)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Legend items
        legend_items = []
        y_pos = 8.5
        
        # Polygon legend item
        polygon_patch = Rectangle((0.5, y_pos-0.3), 1, 0.6, 
                                facecolor=params['polygon_color'], 
                                alpha=params['polygon_alpha'],
                                edgecolor=params['outline_color'],
                                linewidth=2)
        ax.add_patch(polygon_patch)
        ax.text(2, y_pos, 'Site', fontsize=12, va='center')
        y_pos -= 1.5
        
        # Buffer circle legend item (only if circle is actually shown)
        if show_buffer_circle:
            # Create a small circle representation
            circle_x, circle_y = 1, y_pos
            circle = plt.Circle((circle_x, circle_y), 0.3, 
                              fill=params['buffer_circle_fill'],
                              facecolor=params.get('buffer_circle_fill_color', params['buffer_circle_color']) if params['buffer_circle_fill'] else 'none',
                              alpha=params['buffer_circle_fill_alpha'] if params['buffer_circle_fill'] else 1,
                              edgecolor=params['buffer_circle_color'],
                              linewidth=2,
                              linestyle='--' if params['buffer_circle_dashed'] else '-')
            ax.add_patch(circle)
            ax.text(2, y_pos, f'{buffer_circle_radius_miles} Mile Radius', fontsize=12, va='center')
        
        # Add legend border with increased spacing
        legend_border = Rectangle((0.2, 6.2 if show_buffer_circle else 7.2), 
                                9.6, 3.1 if show_buffer_circle else 2.1,
                                fill=False, edgecolor='black', linewidth=1)
        ax.add_patch(legend_border)
        
        # Add legend title with increased spacing and font size
        ax.text(5, 9.5, 'Legend', fontsize=14, weight='bold', ha='center')
        
        # Save legend to bytes
        legend_buffer = BytesIO()
        plt.savefig(legend_buffer, format='PNG', bbox_inches='tight', 
                   facecolor='white', edgecolor='none', dpi=180)
        plt.close(fig)
        legend_buffer.seek(0)
        
        # Load legend as PIL image
        legend_img = Image.open(legend_buffer)
        
        # Start with the main image
        main_img = image.copy()
        margin = 20
        
        # Calculate positions for bottom-left layout (scale bar above legend)
        legend_width, legend_height = legend_img.size
        
        # First, create scale bar if requested
        scale_bar_img = None
        scale_bar_height = 0
        if (params.get('show_scale_bar', True) and extent is not None and 
            polygon_coords is not None and image_width_pixels is not None):
            
            scale_bar_img = self._create_scale_bar_image(
                extent, polygon_coords, image_width_pixels, params
            )
            
            if scale_bar_img:
                scale_bar_height = scale_bar_img.size[1]
        
        # Position legend in bottom-left corner
        legend_x_pos = margin
        legend_y_pos = main_img.height - legend_height - margin
        
        # Position scale bar above the legend (if it exists)
        if scale_bar_img:
            scale_bar_width, scale_bar_height = scale_bar_img.size
            scale_bar_x_pos = margin
            # Place scale bar above legend with some spacing
            scale_bar_y_pos = legend_y_pos - scale_bar_height - 15  # 15px gap between scale and legend
            
            # Add scale bar first (so it appears above legend)
            scale_bar_bg = Image.new('RGBA', (scale_bar_width + 10, scale_bar_height + 10), (255, 255, 255, 240))
            main_img.paste(scale_bar_bg, (scale_bar_x_pos - 5, scale_bar_y_pos - 5), scale_bar_bg)
            main_img.paste(scale_bar_img, (scale_bar_x_pos, scale_bar_y_pos), scale_bar_img)
        
        # Add legend below scale bar
        legend_bg = Image.new('RGBA', (legend_width + 10, legend_height + 10), (255, 255, 255, 240))
        main_img.paste(legend_bg, (legend_x_pos - 5, legend_y_pos - 5), legend_bg)
        main_img.paste(legend_img, (legend_x_pos, legend_y_pos), legend_img)
        
        return main_img
    
    def _create_scale_bar_image(
        self,
        extent: dict,
        polygon_coords: Sequence[Tuple[float, float]],
        image_width_pixels: int,
        params: Dict[str, Any]
    ) -> Optional[Image.Image]:
        """
        Create a scale bar image for template maps.
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Rectangle
            from io import BytesIO
            from mapmaker.map_overlays import calculate_scale_bar_length, calculate_scale_bar_length_from_lod
            
            # Try to get scale denominator from LOD first
            scale_denominator = self._get_scale_denominator_for_extent(extent, image_width_pixels)
            
            # Calculate scale bar dimensions
            if scale_denominator is not None:
                distance_miles, label_text, bar_width_pixels = calculate_scale_bar_length_from_lod(
                    scale_denominator, image_width_pixels, params['output_dpi'], 
                    params.get('scale_bar_distance_miles', None)
                )
            else:
                distance_miles, label_text, bar_width_pixels = calculate_scale_bar_length(
                    extent, image_width_pixels, params.get('scale_bar_distance_miles', None)
                )
                
                # For services without LODs, ensure minimum scale bar width for visibility
                min_bar_width_pixels = image_width_pixels * 0.15  # At least 15% of image width
                if bar_width_pixels < min_bar_width_pixels:
                    # Recalculate with a more appropriate distance
                    if distance_miles < 0.5:
                        target_distance = 0.5
                    elif distance_miles < 1.0:
                        target_distance = 1.0
                    else:
                        target_distance = round(distance_miles * 2)  # Double the distance
                    
                    distance_miles, label_text, bar_width_pixels = calculate_scale_bar_length(
                        extent, image_width_pixels, target_distance
                    )
            
            # Ensure matplotlib uses non-interactive backend
            import matplotlib
            current_backend = matplotlib.get_backend()
            if current_backend != 'Agg':
                matplotlib.use('Agg')
            
            # Create scale bar figure (increased size)
            fig, ax = plt.subplots(figsize=(5, 1.2), dpi=180)
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 20)
            ax.axis('off')
            
            # Scale bar dimensions (as percentage of figure width)
            bar_width_percent = min(bar_width_pixels / image_width_pixels * 100, 80)  # Cap at 80% of figure
            bar_height = 6  # Make scale bar taller (6 instead of 3)
            bar_x = 10
            bar_y = 8
            
            style = params.get('scale_bar_style', 'classic')
            
            if style == 'classic':
                # Classic alternating black and white segments
                num_segments = 4
                segment_width = bar_width_percent / num_segments
                
                for i in range(num_segments):
                    segment_color = 'black' if i % 2 == 0 else 'white'
                    segment_x = bar_x + i * segment_width
                    
                    segment = Rectangle(
                        (segment_x, bar_y), segment_width, bar_height,
                        facecolor=segment_color,
                        edgecolor='black',
                        linewidth=0.5
                    )
                    ax.add_patch(segment)
                    
            elif style == 'simple':
                # Simple single line
                bar = Rectangle(
                    (bar_x, bar_y), bar_width_percent, bar_height,
                    facecolor='none',
                    edgecolor='black',
                    linewidth=2
                )
                ax.add_patch(bar)
                
            elif style == 'modern':
                # Modern filled style
                bar = Rectangle(
                    (bar_x, bar_y), bar_width_percent, bar_height,
                    facecolor='black',
                    edgecolor='black',
                    linewidth=1,
                    alpha=0.8
                )
                ax.add_patch(bar)
            
            # Add scale labels (increased font size)
            ax.text(bar_x, bar_y + bar_height + 1, '0', fontsize=11, ha='left', va='bottom', weight='bold')
            ax.text(bar_x + bar_width_percent, bar_y + bar_height + 1, label_text, fontsize=11, ha='right', va='bottom', weight='bold')
            
            # Save scale bar to bytes
            scale_bar_buffer = BytesIO()
            plt.savefig(scale_bar_buffer, format='PNG', bbox_inches='tight', 
                       facecolor='white', edgecolor='none', dpi=180, pad_inches=0.1)
            plt.close(fig)
            scale_bar_buffer.seek(0)
            
            # Load as PIL image
            scale_bar_img = Image.open(scale_bar_buffer)
            return scale_bar_img
            
        except Exception as e:
            print(f"Warning: Could not create scale bar image: {e}")
            return None
    
    def _extract_output_url(self, export_result: dict) -> Optional[str]:
        """Extract the output URL from the print service response."""
        output_url = None
        if export_result.get("results"):
            for result_item in export_result["results"]:
                if result_item.get("paramName") == "Output_File" and result_item.get("value", {}).get("url"):
                    output_url = result_item["value"]["url"]
                    break
        elif export_result.get("url"):
            output_url = export_result.get("url")
            
        if not output_url:
            print("Error: Could not find output URL in print service response.")
            print("Full response:", json.dumps(export_result, indent=2))
            
        return output_url

 