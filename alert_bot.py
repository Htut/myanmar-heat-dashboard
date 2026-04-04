import os
import requests
from datetime import datetime, timedelta

# --- 1. SECURE TELEGRAM CREDENTIALS ---
# These are now securely pulled from GitHub's encrypted vault
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ ERROR: Missing Telegram credentials. Check GitHub Secrets.")
    exit()

# --- 2. CRITICAL BCDR THRESHOLDS ---
HEAT_INDEX_CRITICAL = 40.0   # Degrees Celsius
WIND_GUST_CRITICAL = 60.0    # km/h
AQI_CRITICAL = 150           # US AQI
MAGNITUDE_CRITICAL = 4.5     # Earthquake Magnitude

# --- 3. CORE INFRASTRUCTURE HUBS TO MONITOR ---
CITIES = {
    "Mandalay": {"lat": 21.9588, "lon": 96.0891},
    "Yangon": {"lat": 16.8409, "lon": 96.1735},
    "Naypyidaw": {"lat": 19.7450, "lon": 96.1297}
}

def send_telegram_alert(message):
    """Pushes the formatted text to your Telegram app."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # Keeps the alert clean by hiding the large URL preview box
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("🚨 Alert successfully beamed to your phone!")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def check_threats():
    """Scans the APIs for active threats and compiles an alert."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning regional BCDR threats...")
    alerts = []

    # --- A. CHECK ATMOSPHERIC & HEALTH THREATS ---
    for city, coords in CITIES.items():
        try:
            # 1. Fetch live weather (Current conditions only, no forecast needed here)
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=apparent_temperature,wind_gusts_10m&timezone=Asia/Yangon"
            w_data = requests.get(w_url).json()['current']

            # 2. Fetch live AQI
            aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={coords['lat']}&longitude={coords['lon']}&current=us_aqi&timezone=Asia/Yangon"
            aq_data = requests.get(aq_url).json()['current']

            heat = w_data['apparent_temperature']
            wind = w_data['wind_gusts_10m']
            aqi = aq_data['us_aqi']

            city_alerts = []
            if heat >= HEAT_INDEX_CRITICAL:
                city_alerts.append(f"🌡️ *Extreme Heat:* {heat}°C")
            if wind >= WIND_GUST_CRITICAL:
                city_alerts.append(f"🌪️ *Severe Wind Gusts:* {wind} km/h")
            if aqi >= AQI_CRITICAL:
                city_alerts.append(f"😷 *Hazardous Air (AQI):* {aqi}")

            if city_alerts:
                alerts.append(f"📍 *{city}*\n" + "\n".join(city_alerts))

        except Exception as e:
            print(f"⚠️ Could not fetch atmospheric data for {city}.")

    # --- B. CHECK TECTONIC THREATS (Past 1 Hour in Myanmar Region) ---
    try:
        # We check exactly 1 hour back so the bot doesn't send duplicate alerts
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        eq_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={one_hour_ago}&minmagnitude={MAGNITUDE_CRITICAL}&minlatitude=9.0&maxlatitude=29.0&minlongitude=92.0&maxlongitude=102.0"
        
        eq_data = requests.get(eq_url).json()
        features = eq_data.get('features', [])
        
        if features:
            alerts.append("🌍 *SEISMIC ACTIVITY DETECTED (Past Hour)*")
            for f in features:
                mag = f['properties']['mag']
                place = f['properties']['place']
                alerts.append(f"⚠️ *M{mag:.1f}* - {place}")
    except Exception as e:
        print("⚠️ Could not fetch seismic data.")

    # --- C. DISPATCH THE ALERT ---
    if alerts:
        # Build the main alert text
        final_message = "🚨 *BCDR TACTICAL ALERT* 🚨\n\n" + "\n\n".join(alerts)
        
        # Append the Streamlit Dashboard link at the very bottom
        final_message += "\n\n🔗 [🇲🇲 Regional Climate & Seismic Dashboard · Streamlit](https://myanmar-heat-dashboard.streamlit.app/)"
        
        send_telegram_alert(final_message)
    else:
        print("✅ No critical threats detected at this time. All clear.")

if __name__ == "__main__":
    check_threats()