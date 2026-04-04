import requests
import csv
import time
from datetime import datetime

# You'll need to sign up for a free API key at OpenWeatherMap
API_KEY = "758c9b877b822672a1b0e1558d73b817"
CITY = "Mandalay,MM"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

def fetch_and_log_weather():
    try:
        response = requests.get(URL)
        data = response.json()
        
        # Extract relevant data
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate a basic Heat Index (optional, complex formulas exist for precise metrics)
        # For now, we log the raw data
        
        # Append to a local CSV file
        with open(r"data\mandalay_heat_history.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            # Write headers if file is empty, otherwise just write data
            writer.writerow([timestamp, temp, humidity])
            
        print(f"[{timestamp}] Logged: {temp}°C, {humidity}% Humidity")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

# Run once immediately, then you can use a loop or cron job
fetch_and_log_weather()