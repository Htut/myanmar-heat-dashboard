import requests
import csv
import time

# Dictionary of key Myanmar cities and their coordinates
# You can add more cities here easily!
# Expanded dictionary of major Myanmar cities, including the Central Dry Zone
MYANMAR_CITIES = {
    # Original Cities
    "Mandalay": {"lat": 21.9588, "lon": 96.0891},
    "Yangon": {"lat": 16.8409, "lon": 96.1735},
    "Naypyidaw": {"lat": 19.7450, "lon": 96.1297},
    "Taunggyi": {"lat": 20.7814, "lon": 97.0333},
    "Sittwe": {"lat": 20.1444, "lon": 92.8986},
    
    # New Central Dry Zone Cities
    "Chauk": {"lat": 20.8906, "lon": 94.8236},
    "Minbu": {"lat": 20.1775, "lon": 94.8781},
    "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pakokku": {"lat": 21.3333, "lon": 95.0833},
    "Pyay": {"lat": 18.8239, "lon": 95.2247},  # Also known as Pyi
    "Magway": {"lat": 20.1458, "lon": 94.9153},
    "Sagaing": {"lat": 21.8787, "lon": 95.9797}
}
print("Fetching historical data for Myanmar regions...")

# Open the CSV to OVERWRITE it with our new multi-city structure
with open(r"data\myanmar_heat_history.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    # NEW HEADER: Added 'City'
    writer.writerow(["Timestamp", "City", "Temperature", "Humidity", "Lat", "Lon"]) 
    
    for city_name, coords in MYANMAR_CITIES.items():
        print(f"Pulling data for {city_name}...")
        
        URL = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&past_days=7&forecast_days=1&hourly=temperature_2m,relative_humidity_2m&timezone=Asia%2FYangon"
        
        try:
            response = requests.get(URL)
            data = response.json()

            times = data['hourly']['time']
            temps = data['hourly']['temperature_2m']
            humidities = data['hourly']['relative_humidity_2m']
            
            # Write all hours for this specific city
            for i in range(len(times)):
                formatted_time = times[i].replace("T", " ") + ":00" 
                # Write data including city name and coordinates (coords needed for the map later!)
                writer.writerow([formatted_time, city_name, temps[i], humidities[i], coords['lat'], coords['lon']])
                
            # Pause for 1 second between cities to be polite to the free API
            time.sleep(1)

        except Exception as e:
            print(f"Error fetching data for {city_name}: {e}")

print("Success! Multi-city regional data saved.")