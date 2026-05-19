import folium
import random

def generate_map(latitude=None, longitude=None):
    # If no exact GPS is provided, randomize slightly so it isn't always the exact same spot
    if latitude is None or longitude is None:
        latitude = 33.6844 + random.uniform(-0.05, 0.05)
        longitude = 73.0479 + random.uniform(-0.05, 0.05)
        
    map_obj = folium.Map(
        location=[latitude, longitude],
        zoom_start=13
    )
    folium.Marker(
        [latitude, longitude],
        popup='Animal Herd Detected',
        tooltip='Herd Alert'
    ).add_to(map_obj)
    map_obj.save('templates/map.html')
