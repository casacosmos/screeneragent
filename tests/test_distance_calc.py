#!/usr/bin/env python3
"""
Calculate distances to Guajon and Llanero Coqui habitats
"""

import math

# Web Mercator to WGS84 conversion
def webmercator_to_wgs84(x, y):
    lon = x / 20037508.34 * 180
    lat = y / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lon, lat

# Haversine distance calculation
def haversine_distance(lon1, lat1, lon2, lat2):
    R = 3959  # Earth radius in miles
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# Test location
test_lon, test_lat = -65.925357, 18.228125

print(f'Test location: {test_lon}, {test_lat}')
print()

# Guajon habitat OBJECTID 154 - using first coordinate from the geometry
guajon_x, guajon_y = -7334194.3949, 2052820.0564
guajon_lon, guajon_lat = webmercator_to_wgs84(guajon_x, guajon_y)

print(f'Guajon habitat (OBJECTID 154): {guajon_lon:.6f}, {guajon_lat:.6f}')

distance = haversine_distance(test_lon, test_lat, guajon_lon, guajon_lat)
print(f'Distance to Guajon habitat: {distance:.2f} miles')
print()

# Also check the other Guajon habitat (OBJECTID 196) for comparison
guajon2_x, guajon2_y = -7367118.1366, 2047919.4017
guajon2_lon, guajon2_lat = webmercator_to_wgs84(guajon2_x, guajon2_y)

print(f'Other Guajon habitat (OBJECTID 196): {guajon2_lon:.6f}, {guajon2_lat:.6f}')

distance2 = haversine_distance(test_lon, test_lat, guajon2_lon, guajon2_lat)
print(f'Distance to other Guajon habitat: {distance2:.2f} miles')
print()

# Check Llanero Coqui for comparison
llanero_x, llanero_y = -7369538.8658, 2088928.9779
llanero_lon, llanero_lat = webmercator_to_wgs84(llanero_x, llanero_y)

print(f'Llanero Coqui habitat: {llanero_lon:.6f}, {llanero_lat:.6f}')

distance3 = haversine_distance(test_lon, test_lat, llanero_lon, llanero_lat)
print(f'Distance to Llanero Coqui habitat: {distance3:.2f} miles')
print()

# Find the closest
distances = [
    ("Guajon (OBJECTID 154)", distance),
    ("Guajon (OBJECTID 196)", distance2),
    ("Llanero Coqui", distance3)
]

distances.sort(key=lambda x: x[1])

print("Habitats by distance:")
for i, (name, dist) in enumerate(distances, 1):
    print(f"{i}. {name}: {dist:.2f} miles")

print(f'\nClosest habitat: {distances[0][0]} at {distances[0][1]:.2f} miles') 