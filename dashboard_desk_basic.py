import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Myanmar Heat Monitor", layout="wide")

col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🇲🇲 Myanmar Regional Heat Dashboard")
    st.markdown("Live and historical weather tracking across multiple regions.")
with col_toggle:
    st.write("")
    st.write("")
    use_fahrenheit = st.toggle("Switch to Fahrenheit (°F)")

# --- 1. LOAD DATA ---
@st.cache_data
def load_data():
    # Note the new file name!
    df = pd.read_csv(r"data\myanmar_heat_history.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

df = load_data()
display_df = df.copy()
temp_unit = "°C"

if use_fahrenheit:
    display_df['Temperature'] = (display_df['Temperature'] * 9/5) + 32
    temp_unit = "°F"

# --- 2. THE SIDEBAR (CITY FILTER) ---
st.sidebar.header("Filter Options")
# Create a dropdown menu of all unique cities in the CSV
city_list = display_df['City'].unique()
selected_city = st.sidebar.selectbox("Select a City to View Trends:", city_list)

# Filter the dataframe to ONLY show the selected city for the trend lines
city_df = display_df[display_df['City'] == selected_city].copy()

# Calculate trends just for the selected city
city_df['Daily Trend'] = city_df['Temperature'].rolling(window=24, min_periods=1, center=True).mean()
city_df['Daily Hum Trend'] = city_df['Humidity'].rolling(window=24, min_periods=1, center=True).mean()

# --- 3. CURRENT METRICS (For Selected City) ---
st.subheader(f"Current Conditions in {selected_city}")
latest_city_data = city_df.iloc[-1]
col1, col2, col3 = st.columns(3)
col1.metric("Temperature", f"{latest_city_data['Temperature']:.1f} {temp_unit}")
col2.metric("Humidity", f"{latest_city_data['Humidity']:.0f} %")
col3.metric("Last Updated", latest_city_data['Timestamp'].strftime("%Y-%m-%d %H:%M"))

st.divider()

# --- 4. THE MYANMAR HEAT MAP ---
st.subheader("Regional Temperature Map (Latest Hour)")
# Get only the very last hour of data for ALL cities to put on the map
latest_time = display_df['Timestamp'].max()
map_df = display_df[display_df['Timestamp'] == latest_time]

# Create an interactive map centered roughly on Myanmar
fig_map = px.scatter_mapbox(
    map_df, 
    lat="Lat", lon="Lon", 
    hover_name="City", 
    hover_data={"Temperature": True, "Humidity": True, "Lat": False, "Lon": False},
    color="Temperature", 
    color_continuous_scale=px.colors.sequential.YlOrRd, # Yellow to Orange to Red scale
    size_max=15, zoom=4.5, 
    title=f"Heat Map as of {latest_time.strftime('%H:%M')}"
)
# Use a free open-street-map style so we don't need a mapbox API key
fig_map.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_map, width='stretch')

st.divider()

# --- 5. CHARTS (For Selected City) ---
st.subheader(f"Trend Lines for {selected_city}")
fig_temp = px.line(city_df, x='Timestamp', y=['Temperature', 'Daily Trend'], 
                   color_discrete_map={"Temperature": "#ff9999", "Daily Trend": "#cc0000"})
fig_temp.update_traces(line=dict(width=4), selector=dict(name="Daily Trend"))
st.plotly_chart(fig_temp, width='stretch')