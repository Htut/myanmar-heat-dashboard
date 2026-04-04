import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

st.set_page_config(page_title="Regional Heat Monitor", layout="wide")

col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🇲🇲 Regional Heat & Humidity Dashboard")
    st.markdown("Live and historical weather tracking across Myanmar and Southeast Asia.")
with col_toggle:
    st.write("")
    st.write("")
    use_fahrenheit = st.toggle("Switch to Fahrenheit (°F)")

# --- 1. CLOUD-READY DATA LOADER ---
# ttl=3600 means Streamlit caches this data for 1 hour automatically!
@st.cache_data(ttl=3600)
def load_data():
    CITIES = {
        "Mandalay": {"lat": 21.9588, "lon": 96.0891},
        "Yangon": {"lat": 16.8409, "lon": 96.1735},
        "Naypyidaw": {"lat": 19.7450, "lon": 96.1297},
        "Taunggyi": {"lat": 20.7814, "lon": 97.0333},
        "Chauk": {"lat": 20.8906, "lon": 94.8236},
        "Minbu": {"lat": 20.1775, "lon": 94.8781},
        "Bangkok": {"lat": 13.7563, "lon": 100.5018}, # Added a regional neighbor!
        "Sittwe": {"lat": 20.1444, "lon": 92.8986},
    
        # New Central Dry Zone Cities
        "Monywa": {"lat": 22.1167, "lon": 95.1333},
        "Pakokku": {"lat": 21.3333, "lon": 95.0833},
        "Pyay": {"lat": 18.8239, "lon": 95.2247},  # Also known as Pyi
        "Magway": {"lat": 20.1458, "lon": 94.9153},
        "Sagaing": {"lat": 21.8787, "lon": 95.9797}
    }
    
    all_data = []
    
    for city_name, coords in CITIES.items():
        # Added apparent_temperature (Heat Index) to the API call
        URL = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&past_days=7&forecast_days=1&hourly=temperature_2m,relative_humidity_2m,apparent_temperature&timezone=Asia%2FYangon"
        try:
            response = requests.get(URL)
            data = response.json()
            
            times = data['hourly']['time']
            temps = data['hourly']['temperature_2m']
            humidities = data['hourly']['relative_humidity_2m']
            heat_indices = data['hourly']['apparent_temperature']
            
            for i in range(len(times)):
                formatted_time = times[i].replace("T", " ") + ":00"
                all_data.append({
                    "Timestamp": formatted_time,
                    "City": city_name,
                    "Temperature": temps[i],
                    "Humidity": humidities[i],
                    "Heat Index": heat_indices[i],
                    "Lat": coords['lat'],
                    "Lon": coords['lon']
                })
        except Exception as e:
            st.error(f"Failed to load data for {city_name}")
            
    df = pd.DataFrame(all_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

with st.spinner("Fetching latest regional weather data..."):
    df = load_data()

display_df = df.copy()
temp_unit = "°C"

if use_fahrenheit:
    display_df['Temperature'] = (display_df['Temperature'] * 9/5) + 32
    display_df['Heat Index'] = (display_df['Heat Index'] * 9/5) + 32
    temp_unit = "°F"

# --- 2. THE SIDEBAR ---
st.sidebar.header("Filter Options")
city_list = display_df['City'].unique()
selected_city = st.sidebar.selectbox("Select a City to View Trends:", city_list)

city_df = display_df[display_df['City'] == selected_city].copy()
city_df['Daily Trend'] = city_df['Temperature'].rolling(window=24, min_periods=1, center=True).mean()

# --- 3. CURRENT METRICS ---
st.subheader(f"Current Conditions in {selected_city}")
latest_city_data = city_df.iloc[-1]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperature", f"{latest_city_data['Temperature']:.1f} {temp_unit}")
col2.metric("Feels Like (Heat Index)", f"{latest_city_data['Heat Index']:.1f} {temp_unit}")
col3.metric("Humidity", f"{latest_city_data['Humidity']:.0f} %")
col4.metric("Last Updated", latest_city_data['Timestamp'].strftime("%Y-%m-%d %H:%M"))

st.divider()
# Check if the latest Heat Index is dangerously high
dangerous_temp_c = 40.0

# Adjust threshold if Fahrenheit is toggled
threshold = (dangerous_temp_c * 9/5) + 32 if use_fahrenheit else dangerous_temp_c

if latest_city_data['Heat Index'] >= threshold:
    st.error(f"⚠️ **EXTREME HEAT WARNING:** The Heat Index in {selected_city} is currently {latest_city_data['Heat Index']:.1f} {temp_unit}. Please take precautions.")
elif latest_city_data['Heat Index'] >= threshold - 5:
    st.warning(f"⚠️ **HEAT ADVISORY:** The Heat Index in {selected_city} is elevating ({latest_city_data['Heat Index']:.1f} {temp_unit}).")


st.divider()

# --- 4 & 5. COMMAND CENTER LAYOUT (Side-by-Side) ---
# Create two columns of equal width
col_left, col_right = st.columns([1, 1])

# Put the Map in the Left Column
with col_left:
    st.subheader("Regional Temperature Map")
    latest_time = display_df['Timestamp'].max()
    map_df = display_df[display_df['Timestamp'] == latest_time]

    fig_map = px.scatter_mapbox(
        map_df, lat="Lat", lon="Lon", hover_name="City", 
        hover_data={"Temperature": True, "Heat Index": True, "Lat": False, "Lon": False},
        color="Temperature", color_continuous_scale=px.colors.sequential.YlOrRd, 
        size_max=15, 
        zoom=4.8, # Perfect zoom for Myanmar
        center={"lat": 19.0, "lon": 96.0}, # Centered on the country
        height=650, # Forces the map to be tall
        title=f"Heat Map as of {latest_time.strftime('%H:%M')}"
    )
    # Shrink the map margins so it fits the column cleanly
    fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

# Put the Charts in the Right Column
with col_right:
    st.subheader(f"Trend Lines for {selected_city}")
    fig_temp = px.line(city_df, x='Timestamp', y=['Temperature', 'Heat Index', 'Daily Trend'], 
                       color_discrete_map={"Temperature": "#ff9999", "Heat Index": "#800080", "Daily Trend": "#cc0000"})
    fig_temp.update_traces(line=dict(width=4), selector=dict(name="Daily Trend"))
    st.plotly_chart(fig_temp, use_container_width=True)