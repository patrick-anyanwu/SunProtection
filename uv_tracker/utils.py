import requests
from django.conf import settings
import bleach


# Update this function in utils.py
def get_uv_index(lat, lon, location_name=None):
    """
    Fetches UV index and temperature from WeatherAPI using latitude & longitude.
    Allows passing a location name to use instead of the WeatherAPI one.
    """
    API_KEY = settings.API_KEY  # Ensure this is set in settings.py
    UV_API_URL = "https://api.weatherapi.com/v1/current.json"

    url = f"{UV_API_URL}?key={API_KEY}&q={lat},{lon}"
    
    # Log the API call for debugging
    print(f"Calling WeatherAPI with coordinates: {lat}, {lon}")

    try:
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            error_msg = data.get("error", {}).get("message", "Invalid Location")
            print(f"WeatherAPI error: {error_msg}")
            return (0, 0, "Invalid Location")

        uv_index = data.get("current", {}).get("uv", 0)
        temperature = data.get("current", {}).get("temp_c", 0)
        
        # Debug the location data returned
        location_data = data.get("location", {})
        print(f"WeatherAPI location data: {location_data}")
        
        # Use the provided location name if available
        if location_name:
            city = location_name
        else:
            # Get more detailed location info
            city = location_data.get("name", "Unknown Location")
            region = location_data.get("region", "")
            country = location_data.get("country", "")
            
            # Format the location display
            if region:
                city = f"{city}, {region}"
            # Add country only if it's not Australia (to keep it concise)
            elif country and country != "Australia":
                city = f"{city}, {country}"

        return (uv_index, temperature, city)
    except requests.exceptions.RequestException as e:
        print("Error fetching UV data:", e)
        return (0, 0, "Error fetching data")

def get_uv_index_from_city(city):
    """
    Converts city name to latitude/longitude and fetches UV index.
    """
    GEO_API_URL = "https://api.weatherapi.com/v1/search.json"
    API_KEY = settings.API_KEY

    try:
        geo_url = f"{GEO_API_URL}?key={API_KEY}&q={city}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()

        if geo_data and isinstance(geo_data, list) and len(geo_data) > 0:
            # Use the first match
            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
            return get_uv_index(float(lat), float(lon))
        else:
            return (0, 0, "Location not found")
    except requests.exceptions.RequestException as e:
        print("Error fetching location data:", e)
        return (0, 0, "Error fetching data")

def get_address_suggestions(query):
    """
    Get address suggestions for autocomplete based on user input.
    Uses Mapbox Places API for accurate address suggestions.
    Restricted to Victoria, Australia only.
    """
    if not query or len(query) < 2:
        return []
        
    API_KEY = settings.MAPBOX_API_KEY
    GEOCODING_URL = settings.MAPBOX_GEOCODING_URL
    
    try:
        # Build the Mapbox Geocoding API endpoint
        endpoint = f"{GEOCODING_URL}/{query}.json"
        
        # Define a bounding box for Victoria, Australia
        # Format: [min_longitude, min_latitude, max_longitude, max_latitude]
        # This approximate box covers Victoria:
        vic_bbox = "141.0,-39.2,150.0,-34.0"
        
        params = {
            'access_token': API_KEY,
            'autocomplete': 'true',
            'limit': 10,
            'types': 'address,place,neighborhood,locality,poi',
            'language': 'en',
            'country': 'au',           # Restrict to Australia
            'bbox': vic_bbox,          # Restrict to Victoria's bounding box
            'proximity': '144.9631,-37.8136'  # Center proximity around Melbourne for better sorting
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code != 200:
            print(f"Mapbox API Error: {response.status_code}")
            return []
            
        data = response.json()
        
        if not data or 'features' not in data:
            return []
            
        # Process and format the Mapbox results
        locations = []
        for feature in data['features']:
            # Get the place name and full address
            place_name = feature.get('place_name', '')

            # Filter out results that are not in Victoria
            # This double-checks in case some results are outside the bounding box
            if not "victoria" in place_name.lower():
                continue
                
            # Extract just the parts we need from context
            context = feature.get('context', [])
            suburb = ""
            postcode = ""
            
            for item in context:
                if 'locality' in item.get('id', ''):
                    suburb = item.get('text', '')
                elif 'postcode' in item.get('id', ''):
                    postcode = item.get('text', '')
            
            # If we couldn't find context, extract from place_name
            if not suburb:
                name_parts = place_name.split(',')
                if len(name_parts) > 0:
                    # Use the first part as the suburb for cases like "Northcote, Victoria, Australia"
                    suburb = name_parts[0].strip()
            
            # Create a clean display format
            display_format = place_name  # Default to full name
            if suburb:
                display_format = suburb
                if postcode:
                    display_format += f" {postcode}"
                
            coordinates = feature.get('center', [])
            if len(coordinates) >= 2:
                lon, lat = coordinates  # Mapbox returns [lon, lat]

            # Before returning the location data, sanitize text fields
            locations.append({
                'name': bleach.clean(place_name),
                'suburb': bleach.clean(suburb) if suburb else '',
                'postcode': bleach.clean(postcode) if postcode else '',
                'lat': lat,
                'lon': lon
            })
        
        return locations[:10]  # Return up to 10 results
        
    except Exception as e:
        print(f"Error fetching address suggestions: {e}")
        return []
