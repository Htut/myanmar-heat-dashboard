import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

st.set_page_config(page_title="Regional Heat Monitor", layout="wide", initial_sidebar_state="collapsed")

col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🇲🇲 Regional Heat & Humidity Dashboard")
    st.markdown("Live tracking and 7-day forecasting across Myanmar and Southeast Asia.")
with col_toggle:
    st.write("")
    st.write("")
    use_fahrenheit = st.toggle("Switch to Fahrenheit (°F)")

# --- 1. CLOUD-READY DATA LOADER ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    CITIES = {
        "Mandalay": {"lat": 21.9588, "lon": 96.0891},
        "Yangon": {"lat": 16.8409, "lon": 96.1735},
        "Naypyidaw": {"lat": 19.7450, "lon": 96.1297},
        "Taunggyi": {"lat": 20.7814, "lon": 97.0333},
        "Chauk": {"lat": 20.8906, "lon": 94.8236},
        "Minbu": {"lat": 20.1775, "lon": 94.8781},
        "Bangkok": {"lat": 13.7563, "lon": 100.5018},
        "Sittwe": {"lat": 20.1444, "lon": 92.8986},
        "Monywa": {"lat": 22.1167, "lon": 95.1333},
        "Pakokku": {"lat": 21.3333, "lon": 95.0833},
        "Pyay": {"lat": 18.8239, "lon": 95.2247},
        "Magway": {"lat": 20.1458, "lon": 94.9153},
        "Sagaing": {"lat": 21.8787, "lon": 95.9797}
    }
    
    all_data = []
    for city_name, coords in CITIES.items():
        URL = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&past_days=7&forecast_days=7&hourly=temperature_2m,relative_humidity_2m,apparent_temperature&timezone=Asia%2FYangon"
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
            
        time.sleep(1) # Prevents API blocking
        
    df = pd.DataFrame(all_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
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

sidebar_city = st.sidebar.selectbox(
    "Select a City to View Trends:", 
    city_list, 
    index=list(city_list).index(st.session_state.selected_city)
)

if sidebar_city != st.session_state.selected_city:
    st.session_state.selected_city = sidebar_city
    st.rerun()

active_city = st.session_state.selected_city

city_df = display_df[display_df['City'] == active_city].copy()
city_df['Daily Trend'] = city_df['Temperature'].rolling(window=24, min_periods=1, center=True).mean()

st.sidebar.divider()
st.sidebar.subheader("Data Export")
csv_data = display_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Download Full Dataset (CSV)",
    data=csv_data,
    file_name=f"regional_heat_forecast_{current_mm_time.strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# --- THE SIDEBAR MAP ---
st.sidebar.divider()
st.sidebar.subheader("Regional Map")

map_df = past_df[past_df['Timestamp'] == latest_actual_time]

fig_map = px.scatter_mapbox(
    map_df, lat="Lat", lon="Lon", hover_name="City", custom_data=["City"],
    hover_data={"Temperature": True, "Heat Index": True, "Lat": False, "Lon": False, "City": False},
    color="Temperature", color_continuous_scale=px.colors.sequential.YlOrRd, 
    size_max=12, 
    zoom=4.0, 
    center={"lat": 19.0, "lon": 96.0}, 
    height=550
)


# Shrink margins and move the color bar to the bottom horizontally
fig_map.update_layout(
    mapbox_style="open-street-map", 
    margin={"r":0,"t":0,"l":0,"b":0},
    coloraxis_colorbar=dict(
        orientation="h",
        yanchor="top",
        y=-0.1,      # Pushes the bar just below the map
        xanchor="center",
        x=0.5,
        thickness=10 # Makes the bar thinner to save space
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

col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperature", f"{latest_city_data['Temperature']:.1f} {temp_unit}")
col2.metric("Feels Like (Heat Index)", f"{latest_city_data['Heat Index']:.1f} {temp_unit}")
col3.metric("Humidity", f"{latest_city_data['Humidity']:.0f} %")
col4.metric("Last Updated", latest_city_data['Timestamp'].strftime("%Y-%m-%d %H:%M"))

st.divider()

dangerous_temp_c = 40.0
threshold = (dangerous_temp_c * 9/5) + 32 if use_fahrenheit else dangerous_temp_c

if latest_city_data['Heat Index'] >= threshold:
    st.error(f"⚠️ **EXTREME HEAT WARNING:** The Heat Index in {active_city} is currently {latest_city_data['Heat Index']:.1f} {temp_unit}. Please take precautions.")
elif latest_city_data['Heat Index'] >= threshold - 5:
    st.warning(f"⚠️ **HEAT ADVISORY:** The Heat Index in {active_city} is elevating ({latest_city_data['Heat Index']:.1f} {temp_unit}).")

st.divider()

# --- 4. MAIN LAYOUT (Full-Width Chart) ---
st.subheader(f"14-Day Trend & Forecast for {active_city}")
fig_temp = px.line(city_df, x='Timestamp', y=['Temperature', 'Heat Index', 'Daily Trend'], 
                   color_discrete_map={"Temperature": "#ff9999", "Heat Index": "#800080", "Daily Trend": "#cc0000"})
fig_temp.update_traces(line=dict(width=4), selector=dict(name="Daily Trend"))

fig_temp.update_layout(
    legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, title=None),
    margin=dict(b=80) 
)

fig_temp.add_vline(x=latest_actual_time, line_dash="dash", line_color="gray")
fig_temp.add_annotation(
    x=latest_actual_time, y=1, yref="paper", 
    text=" Forecast Begins ➔", showarrow=False, xanchor="left", font=dict(color="gray", size=12)
)

st.plotly_chart(fig_temp, use_container_width=True)