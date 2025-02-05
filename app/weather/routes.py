from flask import render_template, current_app
from app.weather import bp
import requests
import os

@bp.route('/')
def index():
    try:
        # Get API key from environment
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        city = current_app.config.get('WEATHER_CITY', 'Utrecht')
        
        # Debug information
        print("\n=== Weather Route Debug ===")
        print(f"API Key configured: {'Yes' if api_key else 'No'}")
        print(f"Full API Key for debugging: {api_key}")
        print(f"City configured: {city}")
        
        if not api_key:
            error_msg = "OpenWeatherMap API key not configured. Please add OPENWEATHER_API_KEY to your .env file."
            print(f"Error: {error_msg}")
            return render_template('weather/index.html', error=error_msg)
        
        # Get weather data from OpenWeatherMap API using HTTPS
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        print(f"Requesting weather data for {city}...")
        print(f"Full URL with API key: {url}")
        
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather = {
                'city': city,
                'temperature': round(data['main']['temp']),
                'description': data['weather'][0]['description'].capitalize(),
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed']
            }
            print(f"Weather data retrieved successfully: {weather}")
            return render_template('weather/index.html', weather=weather)
        elif response.status_code == 401:
            error_msg = "Invalid API key. Please check your OPENWEATHER_API_KEY in the .env file."
            print(f"API Error: {error_msg}")
            return render_template('weather/index.html', error=error_msg)
        else:
            error_msg = f"Error fetching weather data: {data.get('message', 'Unknown error')}"
            print(f"API Error: {error_msg}")
            return render_template('weather/index.html', error=error_msg)
            
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Exception: {error_msg}")
        return render_template('weather/index.html', error=error_msg)
