
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
from django.shortcuts import render
from uv_tracker.models import CancerData  # Import the model
from django.http import JsonResponse
from django.shortcuts import render
from .utils import get_uv_index, get_uv_index_from_city, get_address_suggestions
from django_ratelimit.decorators import ratelimit

def home(request):
    return render(request, 'home.html')

@ratelimit(key='ip', rate='6/m')
def uv_index(request):
    """
    Fetches UV index based on user's latitude & longitude or city name.
    Restricted to Victoria, Australia only.
    """
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    location = request.GET.get("location")

    # Default location: Melbourne, Victoria, Australia
    default_lat, default_lon = -37.8136, 144.9631

    try:
        if lat and lon:
            # Log the incoming coordinates for debugging
            print(f"Received coordinates: lat={lat}, lon={lon}")
            
            # Check if coordinates are within Victoria's bounding box
            # This is approximate: Victoria is roughly within these coordinates
            vic_min_lat, vic_max_lat = -39.2, -34.0
            vic_min_lon, vic_max_lon = 141.0, 150.0
            
            lat_float, lon_float = float(lat), float(lon)
            
            if (vic_min_lat <= lat_float <= vic_max_lat and 
                vic_min_lon <= lon_float <= vic_max_lon):
                # Within Victoria - use the coordinates
                uv_index, temperature, city = get_uv_index(lat_float, lon_float)
            else:
                # Outside Victoria - notify user but still get data
                uv_index, temperature, city = get_uv_index(lat_float, lon_float)
                city = f"{city} (Note: This location appears to be outside Victoria)"
        elif location:
            uv_index, temperature, city = get_uv_index_from_city(location)
        else:
            uv_index, temperature, city = get_uv_index(default_lat, default_lon)
    except ValueError as e:
        print(f"ValueError in uv_index view: {e}")
        return JsonResponse({"error": "Invalid input."}, status=400)

    # Check if there was a location error
    location_error = "not found" in city.lower() or "invalid" in city.lower() or "error" in city.lower()

    # Return JSON if it's an AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        response_data = {
            "uv_index": uv_index, 
            "temperature": temperature, 
            "city": city
        }
        
        if location_error:
            response_data["error"] = city
            
        return JsonResponse(response_data)

    # For page rendering
    context = {
        "uv_index": uv_index,
        "temperature": temperature,
        "city": city,
        "location_error": location_error,
        "error_message": city if location_error else ""
    }
    
    return render(request, "uv_index.html", context)

@ratelimit(key='ip', rate='60/m')
def address_suggestions(request):
    """
    Returns address suggestions for autocomplete.
    """
    query = request.GET.get("query", "")
    suggestions = get_address_suggestions(query)
    return JsonResponse({"suggestions": suggestions})

def personalization(request):
    skin_types = [
        {
            "type": "Type 1", 
            "color": "#F4E1C1", 
            "title": "Light, Pale White", 
            "desc": "Always burns, never tans. Sensitive to the sun, prone to sunburns even after brief exposure.",
            "sunscreen_advice": {
                "1-2": "SPF 30+, long sleeves, sunglasses. Apply sunscreen 30 minutes before sun exposure.",
                "3-5": "SPF 50+, avoid direct sun from 10 AM - 4 PM. Reapply every 2 hours, especially after swimming.",
                "6-7": "SPF 50+, reapply every 2 hours, seek shade. Consider a wide-brimmed hat and protective clothing.",
                "8-10": "SPF 50+, stay indoors if possible. If outdoors, use full-body sunscreen and wear protective gear.",
                "11+": "SPF 50+, avoid sun exposure, wear full protection, and seek shade at all times. Regular skin check-ups are advised."
            },
            "health_tips": "Avoid tanning beds. Vitamin D intake can be adjusted with supplements or food."
        },
        {
            "type": "Type 2", 
            "color": "#E6D5B8", 
            "title": "White, Fair", 
            "desc": "Usually burns, tans with difficulty. This skin type burns easily and tends to develop redness or peeling.",
            "sunscreen_advice": {
                "1-2": "SPF 30, sunglasses optional. Apply sunscreen every 2 hours when exposed to the sun.",
                "3-5": "SPF 50, wear a hat and sunglasses. Take frequent shade breaks during peak sunlight.",
                "6-7": "SPF 50+, reapply every 2 hours. Be cautious when in direct sunlight, and use wide-brimmed hats.",
                "8-10": "SPF 50+, limit outdoor time. Avoid being outdoors during midday when the sun is strongest.",
                "11+": "SPF 50+, seek shade, wear full protection. Always apply sunscreen when going outside, even on cloudy days."
            },
            "health_tips": "Apply aloe vera or moisturizing lotion if you experience peeling or irritation after sun exposure."
        },
        {
            "type": "Type 3", 
            "color": "#D1B899", 
            "title": "Medium, White to Olive", 
            "desc": "Sometimes mild burn, gradually tans to olive. This type is more resistant to sunburn and tans well.",
            "sunscreen_advice": {
                "1-2": "SPF 15+, light protection needed. Apply sunscreen once before going outside.",
                "3-5": "SPF 30+, wear sunglasses. Sunscreen can be reapplied every 3-4 hours.",
                "6-7": "SPF 50, avoid long exposure. Use lip balm with SPF 15 to protect lips.",
                "8-10": "SPF 50+, stay in shade if possible. A good moisturizer will help keep your skin healthy.",
                "11+": "SPF 50+, avoid sun at all costs. It's recommended to wear hats and protective clothing during prolonged sun exposure."
            },
            "health_tips": "Consider using a lightweight moisturizer post-sun exposure to keep skin hydrated."
        },
        {
            "type": "Type 4", 
            "color": "#B8825A", 
            "title": "Olive, Moderate Brown", 
            "desc": "Rarely burns, tans with ease to moderate brown. This type has natural sun protection and doesn't burn easily.",
            "sunscreen_advice": {
                "1-2": "SPF 15, sunglasses optional. Apply sunscreen in the morning to prevent any damage.",
                "3-5": "SPF 30+, moderate sun protection. A lightweight sunscreen is enough for daily exposure.",
                "6-7": "SPF 50, wear a hat and long sleeves. Reapply sunscreen every 2 hours during outdoor activities.",
                "8-10": "SPF 50+, stay indoors if possible. Wear full protection if exposed to the sun for long periods.",
                "11+": "SPF 50+, full protection recommended. Remember to cover exposed areas, especially the face."
            },
            "health_tips": "Exfoliate gently after sun exposure to prevent skin damage over time."
        },
        {
            "type": "Type 5", 
            "color": "#7D5634", 
            "title": "Brown, Dark Brown", 
            "desc": "Very rarely burns, tans very easily. This type has darker skin that rarely experiences sunburns and tans easily.",
            "sunscreen_advice": {
                "1-2": "SPF 15, minor protection needed. Sunscreen can be applied before sun exposure.",
                "3-5": "SPF 30, sunglasses recommended. Protect sensitive areas like lips and the eyes.",
                "6-7": "SPF 50, apply on sensitive areas. Always wear sunscreen when outdoors for prolonged periods.",
                "8-10": "SPF 50+, wear protective clothing. Reapply sunscreen to maintain protection throughout the day.",
                "11+": "SPF 50+, avoid prolonged sun exposure. Don't skip sunscreen application when engaging in outdoor activities."
            },
            "health_tips": "Consider using a moisturizing sunscreen with natural oils to maintain healthy, glowing skin."
        },
        {
            "type": "Type 6", 
            "color": "#4D3520", 
            "title": "Black, Very Dark", 
            "desc": "Never burns, tans very easily, deeply pigmented. This skin type is highly resistant to sunburn and provides natural protection.",
            "sunscreen_advice": {
                "1-2": "SPF 15, basic protection. Use sunscreen on sensitive areas like the face and neck.",
                "3-5": "SPF 30, especially for face and lips. Apply sunscreen once in the morning, especially if staying outdoors for extended periods.",
                "6-7": "SPF 50, wear protective gear if needed. Even though this type rarely burns, it's still important to protect skin from UV damage.",
                "8-10": "SPF 50+, reapply frequently. Sunscreen should be reapplied after swimming or sweating.",
                "11+": "SPF 50+, stay indoors if possible. Apply sunscreen to areas exposed to the sun regularly."
            },
            "health_tips": "Despite not burning, it's important to apply sunscreen for overall skin health. You may not burn, but UV damage can still occur."
        },
    ]
    
    return render(request, "personalization.html", {"skin_types": skin_types})

def uv_impact(request):
    # ✅ Fetch data from SQLite for years 2007-2020
    data = CancerData.objects.filter(year__gte=2007, cancer_type__in=["Melanoma of the skin", "Non-melanoma skin cancer (rare types)"]).values()
    df = pd.DataFrame(list(data))

    # ✅ Ensure DataFrame is not empty
    if df.empty:
        return render(request, 'uv_impact.html', {'chart1': None, 'chart3': None})

    # ✅ Normalize column names to match expected format
    df.columns = df.columns.str.lower().str.strip()

    # ✅ Convert to correct types
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["count"] = df["count"].replace(',', '', regex=True).astype(float)  # Remove commas and convert to numeric
    df["state"] = df["state"].str.strip()

    


        ###  PLOT 1: Skin Cancer Incidence vs Mortality (Line Chart) (2007-2020)
    skin_cancer_grouped = df.groupby(["year", "data_type"])['count'].sum().reset_index()
    
    plt.figure(figsize=(12, 6))
    sns.set_style("white")
    colors = {"Incidence": "#2E86C1", "Mortality": "#D35400"}

    sns.lineplot(data=skin_cancer_grouped[skin_cancer_grouped["data_type"] == "Incidence"], 
                 x="year", y="count", label="Incidence", color=colors["Incidence"], linewidth=2)

    sns.lineplot(data=skin_cancer_grouped[skin_cancer_grouped["data_type"] == "Mortality"], 
                 x="year", y="count", label="Mortality", color=colors["Mortality"], linewidth=2)

    plt.title("Skin Cancer Incidence vs. Mortality Trends (2007-2020)", fontsize=14, fontweight="bold")
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Cases", fontsize=12)
    plt.legend(title="Type", fontsize=10, loc="upper right")
    plt.grid(False)

    buffer1 = io.BytesIO()
    plt.savefig(buffer1, format="png")
    buffer1.seek(0)
    chart1 = base64.b64encode(buffer1.getvalue()).decode()
    buffer1.close()

    ### 📌 PLOT 2: Gender-Based Skin Cancer Proportion (Pie Chart)
    df_skin_cancer_filtered = df[df["sex"].isin(["Males", "Females"])]
    gender_distribution_filtered = df_skin_cancer_filtered.groupby("sex")["count"].sum()

    plt.figure(figsize=(8, 8))
    colors = ["#3498db", "#e74c3c"]  # Blue for Males, Red for Females
    plt.pie(gender_distribution_filtered, labels=gender_distribution_filtered.index, 
            autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("Proportion of Skin Cancer Cases by Gender (Male vs Female)", fontsize=14, fontweight="bold")

    buffer2 = io.BytesIO()
    plt.savefig(buffer2, format="png")
    buffer2.seek(0)
    chart2 = base64.b64encode(buffer2.getvalue()).decode()
    buffer2.close()
    return render(request, 'uv_impact.html', {'chart1': chart1, 'chart2': chart2})


    


    

def set_reminder(request):
    return render(request, 'set_reminder.html')

def clothing(request):
    return render(request, 'clothing.html')