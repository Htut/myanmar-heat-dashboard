import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

st.set_page_config(page_title="🇲🇲 Regional Climate & Seismic Dashboard", layout="wide", initial_sidebar_state="collapsed")

col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🇲🇲 Climate & Seismic Dashboard")
    st.markdown("Live tracking and 7-day forecasting across Myanmar and Southeast Asia.")
with col_toggle:
    st.write("")
    st.write("")
    use_fahrenheit = st.toggle("Switch to Fahrenheit (°F)")

# --- 1. CLOUD-READY DATA LOADER (Upgraded with Pandas Merge) ---
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
        # Weather API (Added Surface Pressure)
        W_URL = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&past_days=7&forecast_days=7&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_gusts_10m,uv_index,shortwave_radiation,cloud_cover,surface_pressure&timezone=Asia%2FYangon"
        # Air Quality API (Added PM2.5 and AQI)
        AQ_URL = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={coords['lat']}&longitude={coords['lon']}&past_days=7&forecast_days=7&hourly=pm2_5,us_aqi&timezone=Asia%2FYangon"
        
        try:
            w_resp = requests.get(W_URL).json()
            aq_resp = requests.get(AQ_URL).json()
            
            # Convert both API responses directly into Pandas DataFrames
            w_df = pd.DataFrame(w_resp.get('hourly', {}))
            aq_df = pd.DataFrame(aq_resp.get('hourly', {}))
            
            if not w_df.empty and not aq_df.empty:
                # Merge the two databases securely matching the exact hour
                city_merged = pd.merge(w_df, aq_df, on='time', how='left')
                city_merged['City'] = city_name
                city_merged['Lat'] = coords['lat']
                city_merged['Lon'] = coords['lon']
                all_data.append(city_merged)
                
        except Exception as e:
            st.error(f"Failed to load data for {city_name}")
            
        time.sleep(1) # Prevent API blocks
        
    df = pd.concat(all_data, ignore_index=True)
    
    # Rename columns to clean, readable titles
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
        'pm2_5': 'PM2.5',
        'us_aqi': 'US AQI'
    }, inplace=True)
    
    df['Timestamp'] = df['Timestamp'].str.replace('T', ' ') + ':00'
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Air Quality forecast sometimes drops off a day early; this cleanly fills the gaps
    df['US AQI'] = df['US AQI'].ffill().bfill()
    df['PM2.5'] = df['PM2.5'].ffill().bfill()

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
        # Save earthquake data into Streamlit's session state so it can be used anywhere
        st.session_state.eq_df = pd.DataFrame(eq_data)
    except Exception as e:
        st.error("Failed to load live seismic data.")
        st.session_state.eq_df = pd.DataFrame() # Empty dataframe on failure
    
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
# Heat Alerts
dangerous_temp_c = 40.0
threshold = (dangerous_temp_c * 9/5) + 32 if use_fahrenheit else dangerous_temp_c
if latest_city_data['Heat Index'] >= threshold:
    st.error(f"⚠️ **EXTREME HEAT WARNING:** The Heat Index is currently {latest_city_data['Heat Index']:.1f} {temp_unit}. Please take precautions.")
elif latest_city_data['Heat Index'] >= threshold - 5:
    st.warning(f"⚠️ **HEAT ADVISORY:** The Heat Index is elevating ({latest_city_data['Heat Index']:.1f} {temp_unit}).")

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

# Tabs definition (Keep your existing tabs)
tab_heat, tab_storm, tab_health, tab_energy, tab_seismic = st.tabs([
    "🌡️ Thermal Dynamics", "🌪️ Storm Warning", "😷 Health & Safety", "⚡ Energy & Solar", "🌍 Seismic Activity"
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