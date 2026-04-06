import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import numpy as np                     # <--- NEW
from scipy.interpolate import griddata # <--- NEW
import matplotlib.pyplot as plt        # <--- NEW
import geopandas as gpd
import scipy.ndimage as ndimage        # <--- NEW: For meteorological smoothing

st.set_page_config(page_title="🇲🇲 Regional Climate & Seismic Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR MOBILE-FRIENDLY FONTS ---
st.markdown("""
<style>
    /* Reduce the size of the main title */
    h1 {
        font-size: 2.2rem !important;
        padding-bottom: 0.5rem !important;
    }
    /* Reduce the size of subheaders */
    h2 {
        font-size: 1.5rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
    }
    /* Shrink the large metric numbers */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
    /* Make metric labels slightly smaller and allow them to wrap instead of cutting off */
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        white-space: normal !important; 
    }
    
    /* Media query to make things EVEN SMALLER on actual mobile screens (< 600px wide) */
    @media (max-width: 600px) {
        h1 {
            font-size: 1.8rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🇲🇲 Climate & Seismic Dashboard")
    st.markdown("Live tracking and 7-day forecasting across Myanmar and Southeast Asia.")
with col_toggle:
    st.write("")
    st.write("")
    use_fahrenheit = st.toggle("Switch to Fahrenheit (°F)")

# --- MASTER DATABASE: REGIONAL CITIES ---
CITIES = {
    # --- MYANMAR (Core Hubs & States) ---
    "Yangon": {"lat": 16.8409, "lon": 96.1735, "country": "Myanmar"},
    "Mandalay": {"lat": 21.9588, "lon": 96.0891, "country": "Myanmar"},
    "Naypyidaw": {"lat": 19.7450, "lon": 96.1297, "country": "Myanmar"},
    "Taunggyi": {"lat": 20.7814, "lon": 97.0333, "country": "Myanmar"},
    "Bago": {"lat": 17.3333, "lon": 96.4833, "country": "Myanmar"},
    "Mawlamyine": {"lat": 16.4833, "lon": 97.6333, "country": "Myanmar"},
    "Myitkyina": {"lat": 25.3833, "lon": 97.4000, "country": "Myanmar"},
    "Monywa": {"lat": 22.1167, "lon": 95.1333, "country": "Myanmar"},
    "Pathein": {"lat": 16.7833, "lon": 94.7333, "country": "Myanmar"},
    "Sittwe": {"lat": 20.1444, "lon": 92.8986, "country": "Myanmar"},
    "Pyay": {"lat": 18.8239, "lon": 95.2247, "country": "Myanmar"},
    "Pakokku": {"lat": 21.3333, "lon": 95.0833, "country": "Myanmar"},
    "Myeik": {"lat": 12.4333, "lon": 98.6000, "country": "Myanmar"},
    "Lashio": {"lat": 22.9333, "lon": 97.7500, "country": "Myanmar"},
    "Meiktila": {"lat": 20.8833, "lon": 95.8667, "country": "Myanmar"},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333, "country": "Myanmar"},
    "Magway": {"lat": 20.1458, "lon": 94.9153, "country": "Myanmar"},
    "Chauk": {"lat": 20.8906, "lon": 94.8236, "country": "Myanmar"},
    "Minbu": {"lat": 20.1775, "lon": 94.8781, "country": "Myanmar"},
    "Sagaing": {"lat": 21.8787, "lon": 95.9797, "country": "Myanmar"},
    "Bagan": {"lat": 21.1717, "lon": 94.8585, "country": "Myanmar"},
    "Hinthada": {"lat": 17.6475, "lon": 95.4586, "country": "Myanmar"},
    "Hpa-An": {"lat": 16.8906, "lon": 97.6333, "country": "Myanmar"},
    "Putao": {"lat": 27.3333, "lon": 97.4333, "country": "Myanmar"},
    "Kawthaung": {"lat": 10.0167, "lon": 98.5500, "country": "Myanmar"},
    "Hakha": {"lat": 22.6444, "lon": 93.6053, "country": "Myanmar"},
    "Falam": {"lat": 22.9133, "lon": 93.6833, "country": "Myanmar"},
    "Gangaw": {"lat": 22.1764, "lon": 94.1406, "country": "Myanmar"},
    "Matupi": {"lat": 21.6000, "lon": 93.4333, "country": "Myanmar"},
    "Mindat": {"lat": 21.3750, "lon": 93.9750, "country": "Myanmar"},
    "Maungdaw": {"lat": 20.8167, "lon": 92.3667, "country": "Myanmar"},
    "Rathedaung": {"lat": 20.4833, "lon": 92.7500, "country": "Myanmar"},
    "Pauk": {"lat": 21.4500, "lon": 94.4833, "country": "Myanmar"},
    "Myaing": {"lat": 21.6167, "lon": 94.8667, "country": "Myanmar"},
    "Taungdwingyi": {"lat": 20.0000, "lon": 95.5500, "country": "Myanmar"},
    "Aunglan": {"lat": 19.3667, "lon": 95.3167, "country": "Myanmar"},
    "Mindon": {"lat": 19.3667, "lon": 94.7667, "country": "Myanmar"},
    "Kanbalu": {"lat": 23.2000, "lon": 95.5167, "country": "Myanmar"},
    "Kawlin": {"lat": 23.7833, "lon": 95.6833, "country": "Myanmar"},
    "Banmauk": {"lat": 24.3833, "lon": 95.8500, "country": "Myanmar"},
    "Maw Luu": {"lat": 24.1333, "lon": 96.1667, "country": "Myanmar"},
    "Bhamo": {"lat": 24.2667, "lon": 97.2333, "country": "Myanmar"},
    "Shwegu": {"lat": 24.2167, "lon": 96.7833, "country": "Myanmar"},
    "Indaw": {"lat": 24.2167, "lon": 96.1333, "country": "Myanmar"},
    "Muse": {"lat": 23.9833, "lon": 97.8964, "country": "Myanmar"},
    "Namhkam": {"lat": 23.8333, "lon": 97.6833, "country": "Myanmar"},
    "Homalin": {"lat": 24.8667, "lon": 94.9000, "country": "Myanmar"},
    "Danai": {"lat": 26.1167, "lon": 96.6667, "country": "Myanmar"},
    "Mohnyin": {"lat": 24.7833, "lon": 96.3667, "country": "Myanmar"},
    "Coco Island": {"lat": 14.1167, "lon": 93.3500, "country": "Myanmar"},
    "Mongla": {"lat": 21.6833, "lon": 100.0167, "country": "Myanmar"},
    "Tangyan": {"lat": 22.4833, "lon": 98.4000, "country": "Myanmar"},
    "Laukkaing": {"lat": 23.6833, "lon": 98.7667, "country": "Myanmar"},
    "Ye": {"lat": 15.2500, "lon": 97.9667, "country": "Myanmar"},
    "Myawaddy": {"lat": 16.6833, "lon": 98.5167, "country": "Myanmar"},
    "Dawei": {"lat": 14.0833, "lon": 98.2000, "country": "Myanmar"},
    "Palaw": {"lat": 12.9667, "lon": 98.6500, "country": "Myanmar"},
    "Bokpyin": {"lat": 11.2333, "lon": 98.7667, "country": "Myanmar"},

    # --- SOUTHEAST ASIA ---
    "Bangkok": {"lat": 13.7563, "lon": 100.5018, "country": "Thailand"},
    "Chiang Mai": {"lat": 18.7953, "lon": 98.9620, "country": "Thailand"},
    "Mae Sot": {"lat": 16.7167, "lon": 98.5667, "country": "Thailand"},
    "Vientiane": {"lat": 17.9757, "lon": 102.6331, "country": "Laos"},
    "Luang Prabang": {"lat": 19.8833, "lon": 102.1333, "country": "Laos"},
    "Phnom Penh": {"lat": 11.5564, "lon": 104.9282, "country": "Cambodia"},
    "Siem Reap": {"lat": 13.3611, "lon": 103.8590, "country": "Cambodia"},
    "Kuala Lumpur": {"lat": 3.1390, "lon": 101.6869, "country": "Malaysia"},
    "Johor Bahru": {"lat": 1.4927, "lon": 103.7414, "country": "Malaysia"},
    "Kota Bharu": {"lat": 6.1254, "lon": 102.2381, "country": "Malaysia"},
    "Penang": {"lat": 5.4141, "lon": 100.3288, "country": "Malaysia"},
    "Ipoh": {"lat": 4.5975, "lon": 101.0901, "country": "Malaysia"},
    "Malacca": {"lat": 2.1896, "lon": 102.2501, "country": "Malaysia"},
    "Kuantan": {"lat": 3.8077, "lon": 103.3260, "country": "Malaysia"},
    "Kuching": {"lat": 1.5533, "lon": 110.3440, "country": "Malaysia"},
    "Ranau": {"lat": 5.9538, "lon": 116.6667, "country": "Malaysia"},
    "Jakarta": {"lat": -6.2088, "lon": 106.8456, "country": "Indonesia"},
    "Banda Aceh": {"lat": 5.5483, "lon": 95.3238, "country": "Indonesia"},
    "Surabaya": {"lat": -7.2504, "lon": 112.7688, "country": "Indonesia"},
    "Bandung": {"lat": -6.9175, "lon": 107.6191, "country": "Indonesia"},
    "Medan": {"lat": 3.5952, "lon": 98.6722, "country": "Indonesia"},
    "Denpasar (Bali)": {"lat": -8.6500, "lon": 115.2167, "country": "Indonesia"},
    "Balikpapan": {"lat": -1.2379, "lon": 116.8529, "country": "Indonesia"},
    "Manokwari (Papua)": {"lat": -0.8614, "lon": 134.0620, "country": "Indonesia"},
    "Hanoi": {"lat": 21.0285, "lon": 105.8542, "country": "Vietnam"},
    "Ho Chi Minh City": {"lat": 10.8231, "lon": 106.6297, "country": "Vietnam"},
    "Singapore": {"lat": 1.3521, "lon": 103.8198, "country": "Singapore"},
    "Bandar Seri Begawan": {"lat": 4.9031, "lon": 114.9398, "country": "Brunei"},
    "Dili": {"lat": -8.5586, "lon": 125.5736, "country": "Timor-Leste"},
    "Manila": {"lat": 14.5995, "lon": 120.9842, "country": "Philippines"},
    "Cebu": {"lat": 10.3157, "lon": 123.8854, "country": "Philippines"},

    # --- EAST ASIA ---
    "Beijing": {"lat": 39.9042, "lon": 116.4074, "country": "China"},
    "Shanghai": {"lat": 31.2304, "lon": 121.4737, "country": "China"},
    "Guangzhou": {"lat": 23.1291, "lon": 113.2644, "country": "China"},
    "Shenzhen": {"lat": 22.5431, "lon": 114.0579, "country": "China"},
    "Chengdu": {"lat": 30.6500, "lon": 104.0667, "country": "China"},
    "Chongqing": {"lat": 29.5332, "lon": 106.5050, "country": "China"},
    "Tianjin": {"lat": 39.0842, "lon": 117.2009, "country": "China"},
    "Wuhan": {"lat": 30.5928, "lon": 114.3055, "country": "China"},
    "Xi'an": {"lat": 34.3416, "lon": 108.9398, "country": "China"},
    "Lhasa": {"lat": 29.6500, "lon": 91.1000, "country": "China"},
    "Kunming": {"lat": 25.0453, "lon": 102.7100, "country": "China"},
    "Dali": {"lat": 25.5928, "lon": 100.2177, "country": "China"},
    "Lijiang": {"lat": 26.8701, "lon": 100.2277, "country": "China"},
    "Yuxi": {"lat": 24.3533, "lon": 102.5408, "country": "China"},
    "Honghe": {"lat": 23.3667, "lon": 102.4167, "country": "China"},
    "Baoshan": {"lat": 25.1167, "lon": 99.1667, "country": "China"},
    "Wenshan": {"lat": 23.3667, "lon": 104.2500, "country": "China"},
    "Baotou": {"lat": 40.6522, "lon": 109.8222, "country": "China"},
    "Nanning": {"lat": 22.8149, "lon": 108.3131, "country": "China"},
    "Hong Kong": {"lat": 22.3193, "lon": 114.1694, "country": "Hong Kong"},
    "Taipei": {"lat": 25.0330, "lon": 121.5654, "country": "Taiwan"},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},

    # --- SOUTH ASIA ---
    "New Delhi": {"lat": 28.6139, "lon": 77.2090, "country": "India"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "country": "India"},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "country": "India"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "country": "India"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "country": "India"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "country": "India"},
    "Imphal": {"lat": 24.8170, "lon": 93.9368, "country": "India"},
    "Kohima": {"lat": 25.6586, "lon": 94.1053, "country": "India"},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362, "country": "India"},
    "Gangtok": {"lat": 27.3389, "lon": 88.6065, "country": "India"},
    "Patna": {"lat": 25.5941, "lon": 85.1376, "country": "India"},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739, "country": "India"},
    "Hazaribagh": {"lat": 23.9925, "lon": 85.3637, "country": "India"},
    "Gaya": {"lat": 24.7914, "lon": 85.0002, "country": "India"},
    "Aurangabad": {"lat": 19.8762, "lon": 75.3433, "country": "India"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "country": "India"},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714, "country": "India"},
    "Indore": {"lat": 22.7196, "lon": 75.8577, "country": "India"},
    "Surat": {"lat": 21.1702, "lon": 72.8311, "country": "India"},
    "Kochi": {"lat": 9.9312, "lon": 76.2673, "country": "India"},
    "Vijayapura": {"lat": 16.8302, "lon": 75.7100, "country": "India"},
    "Port Blair": {"lat": 11.6234, "lon": 92.7265, "country": "India"},
    "Dhaka": {"lat": 23.8103, "lon": 90.4125, "country": "Bangladesh"},
    "Chittagong": {"lat": 22.3569, "lon": 91.7832, "country": "Bangladesh"},
    "Islamabad": {"lat": 33.6844, "lon": 73.0479, "country": "Pakistan"},
    "Karachi": {"lat": 24.8607, "lon": 67.0011, "country": "Pakistan"},
    "Lahore": {"lat": 31.5204, "lon": 74.3587, "country": "Pakistan"},
    "Multan": {"lat": 30.1575, "lon": 71.5249, "country": "Pakistan"},
    "Kathmandu": {"lat": 27.7172, "lon": 85.3240, "country": "Nepal"},
    "Thimphu": {"lat": 27.4728, "lon": 89.6393, "country": "Bhutan"},
    "Paro": {"lat": 27.4305, "lon": 89.4133, "country": "Bhutan"},
    "Colombo": {"lat": 6.9271, "lon": 79.8612, "country": "Sri Lanka"},
    "Male": {"lat": 4.1755, "lon": 73.5093, "country": "Maldives"}
}

# --- UI: DYNAMIC COUNTRY & CITY FILTERS ---
st.markdown("### 🔍 Select Location")
filter_col1, filter_col2 = st.columns(2)

# 1. Extract and sort unique countries, adding "All Countries" at the top
all_countries = sorted(list(set(info["country"] for info in CITIES.values())))
all_countries.insert(0, "All Countries")

with filter_col1:
    selected_country = st.selectbox("🌍 Filter by Country:", all_countries)

# 2. Filter the city list based on the selected country
if selected_country == "All Countries":
    available_cities = sorted(list(CITIES.keys()))
else:
    available_cities = sorted([city for city, info in CITIES.items() if info["country"] == selected_country])

with filter_col2:
    # Ensure this variable replaces any old active_city variable you had
    active_city = st.selectbox("📍 Select City:", available_cities)

st.divider()
    
# --- NEW: CACHED WORLD MAP LOADER ---
@st.cache_data(ttl=86400, show_spinner=False)
def load_world_map():
    """Downloads country boundaries once per day to bypass the GeoPandas 1.0 deprecation."""
    url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    return gpd.read_file(url)

# --- 1. CLOUD-READY DATA LOADER (Upgraded with BCDR Metrics) ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    all_data = []
    city_names = list(CITIES.keys())
    
    # We fetch data in batches of 30 to bypass slow loops
    BATCH_SIZE = 30 
    
    for i in range(0, len(city_names), BATCH_SIZE):
        batch_names = city_names[i : i + BATCH_SIZE]
        
        # Pull lat/lon from the new dictionary structure
        lats = ",".join([str(CITIES[name]["lat"]) for name in batch_names])
        lons = ",".join([str(CITIES[name]["lon"]) for name in batch_names])
        
        # A single API call asks for all 30 cities at once
        W_URL = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&past_days=7&forecast_days=7&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_gusts_10m,uv_index,shortwave_radiation,cloud_cover,surface_pressure,soil_moisture_0_to_1cm,runoff,visibility&timezone=Asia%2FYangon"
        AQ_URL = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lats}&longitude={lons}&past_days=7&forecast_days=7&hourly=pm2_5,us_aqi,carbon_monoxide,dust&timezone=Asia%2FYangon"
        
        try:
            w_resp = requests.get(W_URL).json()
            aq_resp = requests.get(AQ_URL).json()
            
            # Catch Open-Meteo rate limit or parameter errors
            if isinstance(w_resp, dict) and 'error' in w_resp:
                st.warning(f"Batch API Error: {w_resp.get('reason')}")
                continue
                
            # If only 1 city is in the batch, Open-Meteo returns a dictionary. 
            # If multiple cities, it returns a list of dictionaries. We unify them:
            if isinstance(w_resp, dict): w_resp = [w_resp]
            if isinstance(aq_resp, dict): aq_resp = [aq_resp]
            
            # Process the returned batch list
            for j, city in enumerate(batch_names):
                city_w_data = w_resp[j]
                city_aq_data = aq_resp[j]
                
                w_df = pd.DataFrame(city_w_data.get('hourly', {}))
                aq_df = pd.DataFrame(city_aq_data.get('hourly', {}))
                
                if not w_df.empty and not aq_df.empty:
                    city_merged = pd.merge(w_df, aq_df, on='time', how='left')
                    city_merged['City'] = city
                    city_merged['Lat'] = CITIES[city]['lat']
                    city_merged['Lon'] = CITIES[city]['lon']
                    all_data.append(city_merged)
                    
        except Exception as e:
            st.error(f"Failed to load batch starting with {batch_names[0]}")
            
        # A tiny pause between large batches to respect free-tier servers
        time.sleep(0.5) 
        
    # Crash-proof safety net
    if not all_data:
        st.error("Critical API Error: Weather data requests failed. Please check API parameters.")
        return pd.DataFrame() 

    df = pd.concat(all_data, ignore_index=True)
    
    # Rename all columns to clean, readable titles
    df.rename(columns={
        'time': 'Timestamp',
        'temperature_2m': 'Temperature',
        'relative_humidity_2m': 'Humidity',
        'apparent_temperature': 'Heat Index',
        'precipitation': 'Precipitation',
        'wind_gusts_10m': 'Wind Gusts',
        'uv_index': 'UV Index',
        'shortwave_radiation': 'Solar Radiation',
        'cloud_cover': 'Cloud Cover',
        'surface_pressure': 'Surface Pressure',
        'soil_moisture_0_to_1cm': 'Soil Moisture',
        'runoff': 'Runoff',
        'visibility': 'Visibility',
        'pm2_5': 'PM2.5',
        'us_aqi': 'US AQI',
        'carbon_monoxide': 'Carbon Monoxide',
        'dust': 'Dust'
    }, inplace=True)
    
    df['Timestamp'] = df['Timestamp'].str.replace('T', ' ') + ':00'
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Visibility'] = df['Visibility'] / 1000.0
    
    df.ffill(inplace=True)
    df.bfill(inplace=True)

    # --- ADDED: LIVE USGS SEISMIC DATA ---
    eq_url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-03-01&minmagnitude=3.5&minlatitude=9.0&maxlatitude=29.0&minlongitude=92.0&maxlongitude=102.0"
    try:
        eq_resp = requests.get(eq_url).json()
        eq_data = []
        for feature in eq_resp.get('features', []):
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            eq_data.append({
                "Place": props['place'],
                "Magnitude": props['mag'],
                "Time": pd.to_datetime(props['time'], unit='ms').tz_localize('UTC').tz_convert('Asia/Yangon').strftime('%Y-%m-%d %H:%M'),
                "Lat": coords[1],
                "Lon": coords[0],
                "Depth": coords[2]
            })
        st.session_state.eq_df = pd.DataFrame(eq_data)
    except Exception as e:
        st.error("Failed to load live seismic data.")
        st.session_state.eq_df = pd.DataFrame() 
    
    return df

with st.spinner("Fetching latest regional weather & forecast data..."):
    df = load_data()

display_df = df.copy()
temp_unit = "°C"

if use_fahrenheit:
    display_df['Temperature'] = (display_df['Temperature'] * 9/5) + 32
    display_df['Heat Index'] = (display_df['Heat Index'] * 9/5) + 32
    temp_unit = "°F"

# --- TIME LOGIC ---
current_mm_time = pd.Timestamp.utcnow() + pd.Timedelta(hours=6.5)
current_mm_time = current_mm_time.tz_localize(None)
past_df = display_df[display_df['Timestamp'] <= current_mm_time]
latest_actual_time = past_df['Timestamp'].max()

# --- 2. SESSION STATE & SIDEBAR ---
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Mandalay"

st.sidebar.header("Filter Options")
city_list = display_df['City'].unique()

sidebar_city = st.sidebar.selectbox("Select a City to View Trends:", city_list, index=list(city_list).index(st.session_state.selected_city))

if sidebar_city != st.session_state.selected_city:
    st.session_state.selected_city = sidebar_city
    st.rerun()

active_city = st.session_state.selected_city
city_df = display_df[display_df['City'] == active_city].copy()
city_df['Daily Trend'] = city_df['Temperature'].rolling(window=24, min_periods=1, center=True).mean()
city_df['Est Solar Yield (kW)'] = (city_df['Solar Radiation'] / 1000) * 4.72 * 0.75

st.sidebar.divider()
st.sidebar.subheader("Data Export")
csv_data = display_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(label="📥 Download Full Dataset (CSV)", data=csv_data, file_name=f"regional_weather_{current_mm_time.strftime('%Y%m%d')}.csv", mime="text/csv")

# --- THE SIDEBAR MAP ---
st.sidebar.divider()
st.sidebar.subheader("Regional Map")

map_df = past_df[past_df['Timestamp'] == latest_actual_time]
fig_map = px.scatter_mapbox(
    map_df, lat="Lat", lon="Lon", hover_name="City", custom_data=["City"],
    # Added US AQI to the hover data so you can see air quality on the map
    hover_data={"Temperature": True, "Heat Index": True, "US AQI": True, "Lat": False, "Lon": False, "City": False},
    color="Temperature", color_continuous_scale=px.colors.sequential.YlOrRd, 
    size_max=12, zoom=3.5, center={"lat": 19.0, "lon": 96.0}, height=600 
)

fig_map.update_layout(
    mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0},
    coloraxis_colorbar=dict(
        orientation="h", 
        yanchor="top", 
        y=-0.1, 
        xanchor="center", 
        x=0.5, 
        thickness=10,
        len=0.9  # <--- This is the new setting that makes it wider
    )
)
map_event = st.sidebar.plotly_chart(fig_map, use_container_width=True, on_select="rerun")

if map_event and len(map_event.selection.get("points", [])) > 0:
    clicked_city = map_event.selection["points"][0]["customdata"][0]
    if clicked_city != st.session_state.selected_city:
        st.session_state.selected_city = clicked_city
        st.rerun()

# --- 3. CURRENT METRICS ---
st.subheader(f"Current Conditions in {active_city}")
past_city_df = city_df[city_df['Timestamp'] <= current_mm_time]
latest_city_data = past_city_df.iloc[-1]
st.caption(f"Data valid as of: {latest_city_data['Timestamp'].strftime('%Y-%m-%d %H:%M')} (MMT)")

# Primary Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperature", f"{latest_city_data['Temperature']:.1f} {temp_unit}")
col2.metric("Feels Like (Heat Index)", f"{latest_city_data['Heat Index']:.1f} {temp_unit}")
col3.metric("Humidity", f"{latest_city_data['Humidity']:.0f} %")
col4.metric("Air Quality (US AQI)", f"{latest_city_data['US AQI']:.0f}")

# Disaster & Storm Metrics
st.markdown("###### Disaster & Storm Threats (Current Hour)")
col5, col6, col7, col8 = st.columns(4)
col5.metric("Precipitation", f"{latest_city_data['Precipitation']:.1f} mm")
col6.metric("Wind Gusts", f"{latest_city_data['Wind Gusts']:.1f} km/h")
col7.metric("Surface Pressure", f"{latest_city_data['Surface Pressure']:.1f} hPa")
col8.metric("UV Index", f"{latest_city_data['UV Index']:.1f}")

# Energy & Infrastructure Metrics
st.markdown("###### Energy Infrastructure (Current Hour)")
col9, col10, col11, col12 = st.columns(4)
col9.metric("Cloud Cover", f"{latest_city_data['Cloud Cover']:.0f} %")
col10.metric("Solar Radiation", f"{latest_city_data['Solar Radiation']:.0f} W/m²")
col11.metric("Est. Solar Yield (8x 590W)", f"{latest_city_data['Est Solar Yield (kW)']:.2f} kW")

st.divider()

# --- THREAT ALERTS ---
alert_col1, alert_col2 = st.columns(2)

with alert_col1:
    # Heat Alerts
    dangerous_temp_c = 40.0
    threshold = (dangerous_temp_c * 9/5) + 32 if use_fahrenheit else dangerous_temp_c
    if latest_city_data['Heat Index'] >= threshold:
        st.error(f"⚠️ **EXTREME HEAT WARNING:** The Heat Index is currently {latest_city_data['Heat Index']:.1f} {temp_unit}. Please take precautions.")
    elif latest_city_data['Heat Index'] >= threshold - 5:
        st.warning(f"⚠️ **HEAT ADVISORY:** The Heat Index is elevating ({latest_city_data['Heat Index']:.1f} {temp_unit}).")

with alert_col2:
    # Air Quality Alerts
    if latest_city_data['US AQI'] >= 151:
        st.error(f"😷 **UNHEALTHY AIR WARNING:** The AQI is {latest_city_data['US AQI']:.0f}. Masking and reduced outdoor exertion strongly advised.")
    elif latest_city_data['US AQI'] >= 101:
        st.warning(f"😷 **AIR QUALITY ADVISORY:** The AQI is elevating ({latest_city_data['US AQI']:.0f}). Sensitive groups should take precautions.")

st.divider()

# --- 4. MAIN LAYOUT (Interactive Forecasting Tabs) ---
st.subheader(f"14-Day Trend & Forecast for {active_city}")

# --- NEW: DYNAMIC PERIOD SUMMARY ---
st.markdown("**📊 Period Summary Statistics**")
sum_col1, sum_col2 = st.columns([1, 3])
with sum_col1:
    # Let the user choose the period!
    summary_period = st.selectbox("Select Timeframe:", ["Today", "Next 3 Days", "Next 7 Days", "Past 7 Days"], label_visibility="collapsed")

today_date = current_mm_time.date()
if summary_period == "Today":
    period_df = city_df[city_df['Timestamp'].dt.date == today_date]
elif summary_period == "Next 3 Days":
    period_df = city_df[(city_df['Timestamp'].dt.date >= today_date) & (city_df['Timestamp'].dt.date <= today_date + pd.Timedelta(days=2))]
elif summary_period == "Next 7 Days":
    period_df = city_df[city_df['Timestamp'].dt.date >= today_date]
else: # Past 7 Days
    period_df = city_df[city_df['Timestamp'].dt.date < today_date]

if not period_df.empty:
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("🌡️ Temp (Max | Min | Avg)", f"{period_df['Temperature'].max():.1f} | {period_df['Temperature'].min():.1f} | {period_df['Temperature'].mean():.1f} {temp_unit}")
    sc2.metric("🥵 Heat Index (Max | Min | Avg)", f"{period_df['Heat Index'].max():.1f} | {period_df['Heat Index'].min():.1f} | {period_df['Heat Index'].mean():.1f} {temp_unit}")
    sc3.metric("🌪️ Wind Gust (Max | Avg)", f"{period_df['Wind Gusts'].max():.1f} | {period_df['Wind Gusts'].mean():.1f} km/h")
    sc4.metric("☔ Precip (Total Accumulation)", f"{period_df['Precipitation'].sum():.1f} mm")

st.write("") # Adds a tiny bit of spacing before the tabs

# Tabs definition (Updated to 7 tabs)
tab_heat, tab_storm, tab_health, tab_energy, tab_seismic, tab_logistics, tab_contour = st.tabs([
    "🌡️ Thermal Dynamics", "🌪️ Storm Warning", "😷 Health & Safety", "⚡ Energy & Solar", "🌍 Seismic Activity", "🚛 Logistics & Env", "🗺️ Meteorological Model"
])

with tab_heat:
    fig_temp = px.line(city_df, x='Timestamp', y=['Temperature', 'Heat Index', 'Daily Trend'], color_discrete_map={"Temperature": "#ff9999", "Heat Index": "#800080", "Daily Trend": "#cc0000"})
    fig_temp.update_traces(line=dict(width=4), selector=dict(name="Daily Trend"))
    fig_temp.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, title=None), margin=dict(b=80))
    fig_temp.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    fig_temp.add_annotation(x=latest_actual_time, y=1, yref="paper", text=" Forecast Begins ➔", showarrow=False, xanchor="left", font=dict(color="gray", size=12))
    st.plotly_chart(fig_temp, use_container_width=True)

with tab_storm:
    st.markdown("**Storm Indicators: Wind Gusts, Precipitation & Barometric Pressure**")
    
    # 1. Wind Gusts
    fig_wind = px.area(city_df, x='Timestamp', y='Wind Gusts', color_discrete_sequence=['#008080'])
    fig_wind.update_layout(yaxis_title="Wind Gusts (km/h)", showlegend=False, height=250)
    fig_wind.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    # 2. RESTORED: Precipitation
    fig_precip = px.bar(city_df, x='Timestamp', y='Precipitation', color_discrete_sequence=['#1f77b4'])
    fig_precip.update_layout(yaxis_title="Precipitation (mm)", showlegend=False, height=250)
    fig_precip.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    # 3. Surface Pressure
    fig_pres = px.line(city_df, x='Timestamp', y='Surface Pressure', color_discrete_sequence=['#8A2BE2'])
    fig_pres.update_layout(yaxis_title="Surface Pressure (hPa)", showlegend=False, height=250)
    fig_pres.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    # Render all three charts
    st.plotly_chart(fig_wind, use_container_width=True)
    st.plotly_chart(fig_precip, use_container_width=True)
    st.plotly_chart(fig_pres, use_container_width=True)

with tab_health:
    st.markdown("**Health Risks: Air Quality Index (AQI) & UV Exposure**")
    fig_aqi = px.area(city_df, x='Timestamp', y='US AQI', color_discrete_sequence=['#8B4513'])
    fig_aqi.update_layout(yaxis_title="US Air Quality Index", showlegend=False, height=300)
    fig_aqi.add_hline(y=100, line_dash="dot", line_color="orange", annotation_text="Unhealthy for Sensitive Groups")
    fig_aqi.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    fig_uv = px.line(city_df, x='Timestamp', y='UV Index', color_discrete_sequence=['#ff7f0e'])
    fig_uv.update_traces(line=dict(width=3))
    fig_uv.update_layout(yaxis_title="UV Index", showlegend=False, height=300)
    fig_uv.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_aqi, use_container_width=True)
    st.plotly_chart(fig_uv, use_container_width=True)

with tab_energy:
    st.markdown("**Estimated System Generation Profile (4.72 kW Setup)**")
    fig_solar = px.area(city_df, x='Timestamp', y='Est Solar Yield (kW)', color_discrete_sequence=['#FFD700'])
    fig_solar.update_layout(yaxis_title="Power Output (kW)", showlegend=False)
    fig_solar.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    fig_solar.add_annotation(x=latest_actual_time, y=1, yref="paper", text=" Forecast Begins ➔", showarrow=False, xanchor="left", font=dict(color="gray", size=12))
    st.plotly_chart(fig_solar, use_container_width=True)


# --- NEW TAB 6: Logistics & Environment ---
with tab_logistics:
    st.markdown("**1. Flood & Landslide Risk (Monsoon Season)**")
    # Soil Moisture & Runoff
    fig_soil = px.line(city_df, x='Timestamp', y='Soil Moisture', color_discrete_sequence=['#8B4513'])
    fig_soil.update_layout(yaxis_title="Soil Moisture (m³/m³)", showlegend=False, height=200, margin=dict(b=0, t=30))
    fig_soil.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    fig_runoff = px.bar(city_df, x='Timestamp', y='Runoff', color_discrete_sequence=['#4682B4'])
    fig_runoff.update_layout(yaxis_title="Surface Runoff (mm)", showlegend=False, height=200, margin=dict(t=10))
    fig_runoff.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_soil, use_container_width=True)
    st.plotly_chart(fig_runoff, use_container_width=True)
    
    st.divider()
    
    st.markdown("**2. Supply Chain & Transport Safety**")
    # Visibility
    fig_vis = px.area(city_df, x='Timestamp', y='Visibility', color_discrete_sequence=['#A9A9A9'])
    fig_vis.update_layout(yaxis_title="Visibility (km)", showlegend=False, height=250)
    fig_vis.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_vis, use_container_width=True)
    
    st.divider()

    st.markdown("**3. Industrial & Burning Season Threats**")
    # Carbon Monoxide & Dust
    fig_co = px.line(city_df, x='Timestamp', y=['Carbon Monoxide', 'Dust'], color_discrete_map={"Carbon Monoxide": "#DC143C", "Dust": "#D2B48C"})
    fig_co.update_layout(yaxis_title="Concentration (μg/m³)", height=300, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
    fig_co.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_co, use_container_width=True)

# --- TAB 5: Seismic Activity ---
with tab_seismic:
    st.markdown("**Live Regional Seismic Activity (USGS Data)**")
    
    if "eq_df" in st.session_state and not st.session_state.eq_df.empty:
        eq_df = st.session_state.eq_df
        
        # Convert the string timestamps into actual date objects for the filter logic
        eq_df['DateObj'] = pd.to_datetime(eq_df['Time']).dt.date
        min_date = eq_df['DateObj'].min()
        max_date = eq_df['DateObj'].max()
        
        # Create side-by-side columns to keep the UI clean
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            mag_range = st.slider(
                "Filter by Magnitude Range:", 
                min_value=3.5, max_value=9.0, value=(3.5, 9.0), step=0.1
            )
            
        with col_filter2:
            # Add the date range picker
            selected_dates = st.date_input(
                "Filter by Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
        # Safely handle the date input (it returns a tuple of either 1 or 2 dates depending on user clicks)
        if len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = selected_dates[0]
            end_date = selected_dates[0]
        
        # Apply BOTH the magnitude and the date filters
        filtered_eq_df = eq_df[
            (eq_df['Magnitude'] >= mag_range[0]) & 
            (eq_df['Magnitude'] <= mag_range[1]) &
            (eq_df['DateObj'] >= start_date) &
            (eq_df['DateObj'] <= end_date)
        ]
        
        if not filtered_eq_df.empty:
            # --- NEW: Seismic Period Stats ---
            st.markdown(f"**Period Stats:** Max: **M{filtered_eq_df['Magnitude'].max():.1f}** | Min: **M{filtered_eq_df['Magnitude'].min():.1f}** | Avg: **M{filtered_eq_df['Magnitude'].mean():.1f}** | Total Events: **{len(filtered_eq_df)}**")
            
            # Plot filtered earthquakes
            fig_eq = px.scatter_mapbox(
                filtered_eq_df, lat="Lat", lon="Lon", hover_name="Place",
                hover_data={"Magnitude": True, "Time": True, "Depth": True, "Lat": False, "Lon": False, "DateObj": False},
                color="Magnitude", color_continuous_scale=px.colors.sequential.YlOrRd,
                size="Magnitude", size_max=15,
                zoom=4.5, center={"lat": 19.0, "lon": 96.0}, height=500
            )
            fig_eq.update_layout(
                mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0},
                coloraxis_colorbar=dict(title="Mag", thickness=10)
            )
            st.plotly_chart(fig_eq, use_container_width=True)
            
            # Show a dynamically updating summary table
            st.markdown(f"**Recent Events ({start_date.strftime('%b %d')} to {end_date.strftime('%b %d')} | M{mag_range[0]} - M{mag_range[1]}):**")
            st.dataframe(filtered_eq_df[['Time', 'Place', 'Magnitude', 'Depth']].head(5), use_container_width=True)
        else:
            st.info("No earthquakes match the selected magnitude and date filters.")
            
    else:
        st.info("No recent significant seismic activity found in the region, or data is still loading.")

# --- NEW TAB 7: True Meteorological Contour Model ---
with tab_contour:
    st.markdown("**Regional Thermal Interpolation Model (SciPy & Matplotlib)**")
    st.markdown("This model uses cubic interpolation to mathematically simulate a continuous weather grid based on live data from regional mega-cities.")
    
    # 1. Grab the current temperature data for all cities
    map_df = past_df[past_df['Timestamp'] == latest_actual_time].copy()
    
    if not map_df.empty:
        # 2. Extract Coordinates and Temperatures
        points = map_df[['Lon', 'Lat']].values
        values = map_df['Temperature'].values
        
        # 3. DYNAMIC GRID: Calculate boundaries based on the actual data limits + a 3-degree buffer
        min_lon, max_lon = map_df['Lon'].min() - 3, map_df['Lon'].max() + 3
        min_lat, max_lat = map_df['Lat'].min() - 3, map_df['Lat'].max() + 3
        
        # Create a high-resolution 400x400 grid spanning the new dynamic area
        grid_lon = np.linspace(min_lon, max_lon, 400) 
        grid_lat = np.linspace(min_lat, max_lat, 400)
        grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
        
    try:
        # 4. Interpolate the gaps using SciPy
        # First pass: Cubic for smooth internal gradients
        grid_temp_cubic = griddata(points, values, (grid_lon, grid_lat), method='cubic')
        
        # Second pass: Nearest to fill the blank edges (like oceans) where cubic fails
        grid_temp_nearest = griddata(points, values, (grid_lon, grid_lat), method='nearest')
        
        # Combine them: If cubic is blank (NaN), use nearest
        grid_temp = np.where(np.isnan(grid_temp_cubic), grid_temp_nearest, grid_temp_cubic)
        
        # --- NEW: METEOROLOGICAL SMOOTHING ---
        # Apply a Gaussian blur to the grid to create a perfectly liquid, homogeneous heat map
        # A sigma of 2.0 or 3.0 provides the perfect blend!
        grid_temp_smoothed = ndimage.gaussian_filter(grid_temp, sigma=2.5)
        
        # 5. Render the Meteorological Contour Map
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_facecolor('#e8e9eb') 
        
        # Draw the continuous heat bands using our SMOOTHED grid
        contour = ax.contourf(grid_lon, grid_lat, grid_temp_smoothed, levels=40, cmap='turbo', alpha=0.85, zorder=2)
        # --- NEW: ADD COUNTRY BORDERS ---
        # Load the lightweight world map from geopandas and plot the boundaries over the heat map
        # Load the lightweight world map (using our cached function to bypass GeoPandas 1.0 errors)
        world = load_world_map()
        world.boundary.plot(ax=ax, color='#333333', linewidth=0.8, zorder=3)
        
        # Lock the map view to our dynamic grid so we don't see the whole globe
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        
        # --- NEW: FILTER VISIBLE POINTS & LABELS ---
        # Define Regional Capitals + Mandalay & Yangon
        highlight_cities = [
            "Naypyidaw", "Yangon", "Mandalay", "Bangkok", "Vientiane", "Phnom Penh", 
            "Kuala Lumpur", "Jakarta", "Hanoi", "Singapore", "Bandar Seri Begawan", 
            "Dili", "Manila", "Beijing", "Taipei", "Tokyo", "New Delhi", "Dhaka", 
            "Islamabad", "Kathmandu",  "Colombo", "Male"
        ]
        
        # Filter dataframe to only show these specific cities
        visible_points = map_df[map_df['City'].isin(highlight_cities)]
        
        # Plot ONLY the filtered city data points on top (zorder=4)
        ax.scatter(visible_points['Lon'], visible_points['Lat'], color='red', edgecolor='black', s=15, zorder=4) # s=45 to 25
        
        # Label ONLY the filtered cities
        for idx, row in visible_points.iterrows():
            ax.text(row['Lon'] + 0.5, row['Lat'], row['City'], fontsize=8, color='black', weight='bold', zorder=5)
        # Formatting the chart
        plt.colorbar(contour, ax=ax, label=f"Temperature ({temp_unit})", shrink=0.8)
        ax.set_title(f"Continuous Thermal Surface Map ({latest_actual_time.strftime('%Y-%m-%d %H:%M')} MMT)", fontsize=16, pad=15)
        ax.set_xlabel("Longitude", fontsize=12)
        ax.set_ylabel("Latitude", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Send the Matplotlib figure to Streamlit
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Not enough data points currently loaded to compute interpolation grid. Error: {e}")