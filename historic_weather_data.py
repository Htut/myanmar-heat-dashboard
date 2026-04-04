import requests
import csv

# Mandalay Coordinates
LAT = 21.9588
LON = 96.0891

# Open-Meteo API URL - Added &forecast_days=1 to prevent future projections
URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&past_days=7&forecast_days=1&hourly=temperature_2m,relative_humidity_2m&timezone=Asia%2FYangon"

print("Fetching strictly historical data for Mandalay...")

try:
    response = requests.get(URL)
    data = response.json()

    # Extract the lists of data from the JSON response
    times = data['hourly']['time']
    temps = data['hourly']['temperature_2m']
    humidities = data['hourly']['relative_humidity_2m']

    # Open your existing CSV file in "write" mode ('w') to overwrite it 
    with open(r"data\mandalay_heat_history.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        
        # Write the header row
        writer.writerow(["Timestamp", "Temperature", "Humidity"]) 
        
        # Loop through all the hours and write them to the CSV
        for i in range(len(times)):
            # Format the time string to match (YYYY-MM-DD HH:MM:SS)
            formatted_time = times[i].replace("T", " ") + ":00" 
            writer.writerow([formatted_time, temps[i], humidities[i]])

    print(f"Success! Wrote {len(times)} rows of clean historical data to your CSV.")

except Exception as e:
    print(f"Error fetching historical data: {e}")