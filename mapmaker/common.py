# mapmaker/common.py

import math
import json
import warnings
from dataclasses import dataclass
from typing import Any, Dict, Sequence, Tuple, Union

import requests
from pyproj import Geod

# Suppress insecure HTTPS warnings for self-signed certs
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Constants
DEFAULT_DPI = 180
METERS_PER_INCH = 0.0254
METERS_PER_DEGREE_LAT = 110_750.0
METERS_PER_MILE = 1609.34
GEOD = Geod(ellps="WGS84")

# Corrected GeometryServer URL (path is /Utilities/Geometry/GeometryServer)
GEOMETRY_SERVER_URL = (
    "https://sige.pr.gov/server/rest/services/Utilities/"
    "Geometry/GeometryServer"
)


@dataclass(frozen=True)
class Scale:
    level: int
    resolution: float
    scale_denominator: float
    name: str

    @classmethod
    def from_lod(cls, lod: Dict[str, Any]) -> "Scale":
        lvl = int(lod["level"])
        res = float(lod["resolution"])
        sc = float(lod.get("scale", res * DEFAULT_DPI / METERS_PER_INCH))
        return cls(
            level=lvl,
            resolution=res,
            scale_denominator=sc,
            name=f"LOD {lvl}"
        )


class MapServerClient:
    """
    Generic ArcGIS MapServer client supporting:
      - Metadata fetch & inspection (fetch_metadata(), describe(), describe_layers())
      - Layer-level details (get_layer_definition())
      - Distance calculations (geodesic_distance())
      - Reprojection helpers (lonlat_to_webmercator(), reproject_bbox_via_geometry_server())
      - Polygon clamping, auto-LOD selection, format picking
      - Export URL generation (export_url())
    """
    def __init__(self, service_url: str, dpi: int = DEFAULT_DPI) -> None:
        self.service_url = service_url.rstrip("/")
        self.dpi = dpi

        # Service-level metadata
        self.service_description: str = ""
        self.capabilities: str = ""
        self.supported_image_format_types: str = ""
        self.units: Union[str, None] = None
        self.max_record_count: Union[int, None] = None
        self.min_scale: Union[float, None] = None
        self.max_scale: Union[float, None] = None

        # Layers and tables
        self.layers: list[Dict[str, Any]] = []
        self.tables: list[Dict[str, Any]] = []

        # Spatial & tiling
        self.spatial_reference: Dict[str, Any] = {}
        self.initial_extent: Dict[str, Any] = {}
        self.full_extent: Dict[str, Any] = {}
        self.tile_info: Dict[str, Any] = {}
        self.scales: Dict[int, Scale] = {}

    def fetch_metadata(self) -> None:
        """Populate all service, spatial, and tiling metadata from ?f=pjson."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        # Increased timeout from 5 to 15 seconds for potentially slow server
        resp = requests.get(f"{self.service_url}?f=pjson", verify=False, timeout=15, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        # Service info
        self.service_description = data.get("serviceDescription", "")
        self.capabilities = data.get("capabilities", "")
        self.supported_image_format_types = data.get("supportedImageFormatTypes", "")
        self.units = data.get("units")
        self.max_record_count = data.get("maxRecordCount")
        self.min_scale = data.get("minScale")
        self.max_scale = data.get("maxScale")

        # Layers & tables
        self.layers = data.get("layers", [])
        self.tables = data.get("tables", [])

        # Spatial & tiling
        self.spatial_reference = data.get("spatialReference", {})
        self.initial_extent = data.get("initialExtent", {})
        self.full_extent = data.get("fullExtent", {})
        self.tile_info = data.get("tileInfo", {})

        # Parse LODs into Scale objects
        for lod in self.tile_info.get("lods", []):
            s = Scale.from_lod(lod)
            self.scales[s.level] = s

    def describe(self) -> None:
        """Prints a summary of the MapServer's key metadata."""
        print(f"Service URL         : {self.service_url}")
        print(f"Description         : {self.service_description}")
        print(f"Capabilities        : {self.capabilities}")
        print(f"Supported formats   : {self.supported_image_format_types}")
        print(f"Units               : {self.units}")
        print(f"Scale range         : 1:{self.max_scale} down to 1:{self.min_scale}")
        print(f"Max record count    : {self.max_record_count}\n")
        print(f"Layers ({len(self.layers)}):")
        for lyr in self.layers:
            print(f"  [{lyr['id']}] {lyr['name']} ({lyr['type']})")
        print(f"\nTables ({len(self.tables)}):")
        for tbl in self.tables:
            print(f"  [{tbl['id']}] {tbl['name']}")

    def get_layer_definition(self, layer_id: int) -> Dict[str, Any]:
        """Fetch detailed metadata for a specific layer via /<layer_id>?f=pjson."""
        resp = requests.get(f"{self.service_url}/{layer_id}?f=pjson",
                            verify=False, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def describe_layers(self) -> None:
        """Prints detailed metadata for each layer: fields, geometryType, renderer."""
        if not self.layers:
            self.fetch_metadata()
        for lyr in self.layers:
            defn = self.get_layer_definition(lyr["id"])
            print(f"\nLayer {defn.get('id')} — {defn.get('name')}")
            print(f"  GeometryType : {defn.get('geometryType')}")
            print(f"  DefinitionExpression: {defn.get('definitionExpression')}")
            print("  Fields:")
            for fld in defn.get("fields", []):
                print(f"    • {fld['name']} ({fld['type']}) alias='{fld['alias']}'")
            renderer = defn.get("drawingInfo", {}).get("renderer", {})
            if renderer:
                print(f"  Renderer type: {renderer.get('type')}")

    @staticmethod
    def geodesic_distance(
        lon1: float, lat1: float, lon2: float, lat2: float
    ) -> float:
        """True ellipsoidal distance (metres) on WGS84."""
        _, _, dist = GEOD.inv(lon1, lat1, lon2, lat2)
        return dist

    @staticmethod
    def lonlat_to_webmercator(lon: float, lat: float) -> Tuple[float, float]:
        """Local spherical Mercator formulas for EPSG:3857."""
        R = 6378137.0
        x = R * math.radians(lon)
        lat = max(min(lat, 85.05112878), -85.05112878)
        y = R * math.log(math.tan(math.pi/4 + math.radians(lat)/2))
        return x, y

    def add_buffer_to_polygon(
        self, polygon: Sequence[Tuple[float, float]], buffer_miles: float = 0.5
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
        buffer_meters = buffer_miles * METERS_PER_MILE
        
        lons, lats = zip(*polygon)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Calculate center
        center_lat = (min_lat + max_lat) / 2
        
        # Convert buffer distance from meters to degrees
        # For latitude, use the constant conversion factor
        lat_buffer_deg = buffer_meters / METERS_PER_DEGREE_LAT
        
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

    def clamp_polygon_to_full_extent(
        self, polygon: Sequence[Tuple[float, float]]
    ) -> Sequence[Tuple[float, float]]:
        """
        Clamps each point of a WGS84 polygon to the MapServer's fullExtent,
        reprojecting the extent to WGS84 if necessary.
        Assumes the input polygon is in WGS84 (EPSG:4326).
        """
        if not self.full_extent or not self.spatial_reference or not self.full_extent.get("spatialReference"):
            # Not enough metadata to perform clamping or determine extent's SR
            print("Warning: Insufficient metadata for fullExtent or its spatial reference. Polygon will not be clamped.")
            return polygon

        # Get the service's native full extent coordinates
        service_fe_xmin = float(self.full_extent["xmin"])
        service_fe_ymin = float(self.full_extent["ymin"])
        service_fe_xmax = float(self.full_extent["xmax"])
        service_fe_ymax = float(self.full_extent["ymax"])
        
        service_sr_info = self.full_extent["spatialReference"]
        service_sr_wkid = int(service_sr_info.get("latestWkid", service_sr_info.get("wkid", 0)))

        # Define the target extent for clamping (will be in WGS84 degrees)
        clamp_extent_wgs84_coords = {}

        if service_sr_wkid == 4326:
            # Service's full extent is already in WGS84 degrees
            clamp_extent_wgs84_coords["xmin"] = service_fe_xmin
            clamp_extent_wgs84_coords["ymin"] = service_fe_ymin
            clamp_extent_wgs84_coords["xmax"] = service_fe_xmax
            clamp_extent_wgs84_coords["ymax"] = service_fe_ymax
        elif service_sr_wkid != 0:
            # Service's full extent is in a different SR, reproject it to WGS84
            try:
                (
                    clamp_extent_wgs84_coords["xmin"],
                    clamp_extent_wgs84_coords["ymin"],
                    clamp_extent_wgs84_coords["xmax"],
                    clamp_extent_wgs84_coords["ymax"],
                ) = self.reproject_bbox_via_geometry_server(
                    service_fe_xmin, service_fe_ymin, service_fe_xmax, service_fe_ymax,
                    in_sr=service_sr_wkid, 
                    out_sr=4326 
                )
            except Exception as e:
                # If reprojection fails, log an error and don't clamp
                print(f"Warning: Failed to reproject fullExtent for clamping: {e}. Polygon will not be clamped.")
                return polygon
        else:
            # service_sr_wkid is 0 or missing from fullExtent's SR info (shouldn't happen if SR object exists)
            print("Warning: Cannot determine spatial reference Wkid of fullExtent. Polygon will not be clamped.")
            return polygon

        # Now clamp_extent_wgs84_coords holds the clamping boundaries in WGS84 degrees
        clamped_polygon = []
        # Ensure keys exist before trying to access them, in case reprojection failed silently before exception
        if not all(k in clamp_extent_wgs84_coords for k in ["xmin", "ymin", "xmax", "ymax"]):
             print("Warning: Clamping extent coordinates are incomplete. Polygon will not be clamped.")
             return polygon

        for lon, lat in polygon:
            clamped_lon = min(max(lon, clamp_extent_wgs84_coords["xmin"]), clamp_extent_wgs84_coords["xmax"])
            clamped_lat = min(max(lat, clamp_extent_wgs84_coords["ymin"]), clamp_extent_wgs84_coords["ymax"])
            clamped_polygon.append((clamped_lon, clamped_lat))
            
        return clamped_polygon

    def pick_best_lod(
        self, polygon: Sequence[Tuple[float, float]], width_px: int
    ) -> int:
        """
        Picks the LOD whose metres/pixel is closest to ground_width_m/width_px.
        """
        lons, lats = zip(*polygon)
        lon_min, lon_max = min(lons), max(lons)
        lat_min, lat_max = min(lats), max(lats)

        out_sr = int(self.spatial_reference.get("latestWkid",
                    self.spatial_reference.get("wkid", 4326)))
        x1, y1, x2, y2 = self.reproject_bbox_via_geometry_server(
            lon_min, lat_min, lon_max, lat_max,
            in_sr=4326, out_sr=out_sr
        )
        ground_width_m = abs(x2 - x1)
        desired_res = ground_width_m / width_px

        best = min(
            self.scales.values(),
            key=lambda s: abs(s.resolution - desired_res)
        )
        return best.level

    def choose_format(self, preferred: Sequence[str] = ("PNG32", "PNG", "JPEG")) -> str:
        """Returns the first supported image format from preferred list."""
        supported = [
            fmt.strip().lower()
            for fmt in self.supported_image_format_types.split(",")
        ]
        for fmt in preferred:
            if fmt.lower() in supported:
                return fmt
        return self.supported_image_format_types.split(",")[0].strip()

    def reproject_bbox_via_geometry_server(
        self,
        xmin: float, ymin: float, xmax: float, ymax: float,
        in_sr: int = 4326, out_sr: Union[int, None] = None
    ) -> Tuple[float, float, float, float]:
        """Reprojects an envelope via the ArcGIS GeometryServer."""
        if out_sr is None:
            out_sr = self.spatial_reference.get("latestWkid") or self.spatial_reference.get("wkid")
        params = {
            "f": "json",
            "inSR": in_sr,
            "outSR": out_sr,
            "geometries": json.dumps({
                "geometryType": "esriGeometryEnvelope",
                "geometries": [{
                    "xmin": xmin, "ymin": ymin,
                    "xmax": xmax, "ymax": ymax
                }]
            }, separators=(',', ':'))
        }
        request_url = f"{GEOMETRY_SERVER_URL}/project"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        resp = requests.get(
            request_url,
            params=params, verify=False, timeout=5,
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        env = data["geometries"][0]
        return (
            float(env["xmin"]),
            float(env["ymin"]),
            float(env["xmax"]),
            float(env["ymax"])
        )

    def export_url(
        self,
        polygon: Sequence[Tuple[float, float]],
        level_or_scale: Union[int, float],
        *, width_px: int = 800, height_px: int = 600,
        output_format: str = "png", transparent: bool = True,
        use_geometry_reprojection: bool = False
    ) -> str:
        """
        Builds an ExportMap URL. Optionally reprojects WGS84 bbox to native CRS.
        """
        # Determine scale denominator
        if isinstance(level_or_scale, int) and level_or_scale in self.scales:
            denom = self.scales[level_or_scale].scale_denominator
        else:
            denom = float(level_or_scale)

        lons, lats = zip(*polygon)
        center_lon = (min(lons) + max(lons)) / 2
        center_lat = (min(lats) + max(lats)) / 2

        map_w_m = (width_px / self.dpi) * METERS_PER_INCH
        map_h_m = (height_px / self.dpi) * METERS_PER_INCH
        real_w = map_w_m * denom
        real_h = map_h_m * denom

        metres_per_deg_lon = 111320.0 * math.cos(math.radians(center_lat))
        span_lon = real_w / metres_per_deg_lon
        span_lat = real_h / METERS_PER_DEGREE_LAT

        xmin = center_lon - span_lon / 2
        ymin = center_lat - span_lat / 2
        xmax = center_lon + span_lon / 2
        ymax = center_lat + span_lat / 2

        bbox_sr = 4326
        if use_geometry_reprojection:
            xmin, ymin, xmax, ymax = self.reproject_bbox_via_geometry_server(
                xmin, ymin, xmax, ymax
            )
            bbox_sr = int(self.spatial_reference.get("latestWkid",
                        self.spatial_reference.get("wkid", 4326)))

        bbox = f"{xmin},{ymin},{xmax},{ymax}"
        return (
            f"{self.service_url}/export?"
            f"bbox={bbox}&bboxSR={bbox_sr}"
            f"&size={width_px},{height_px}"
            f"&format={output_format}"
            f"&transparent={'true' if transparent else 'false'}"
            f"&f=image"
        )

