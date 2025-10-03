from flask import Flask, render_template_string
import anthropic
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ============================================
# SETUP - Add your API keys here
# ============================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

# User info
USER_EMAIL = "lizzysfca@yahoo.com"
LOCATION = "Seattle,WA,US"

# ============================================
# HARDCODED CALENDAR EVENTS
# ============================================
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

calendar_events = [
    {
        "title": "Morning Run in Prospect Park",
        "time": "7:00 AM",
        "location": "Prospect Park",
        "outdoor": True,
        "date": tomorrow
    },
    {
        "title": "Coffee with Sarah",
        "time": "10:30 AM", 
        "location": "Cafe Grumpy (outdoor seating)",
        "outdoor": True,
        "date": tomorrow
    },
    {
        "title": "Team Video Call",
        "time": "2:00 PM",
        "location": "Home office",
        "outdoor": False,
        "date": tomorrow
    }
]

# ============================================
# TOOL 1: Get Weather Data
# ============================================
def get_weather():
    """Call weather API to get tomorrow's forecast"""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={LOCATION}&appid={WEATHER_API_KEY}&units=imperial"
    
    response = requests.get(url)
    data = response.json()
    
    # Get tomorrow's forecasts
    tomorrow_forecasts = []
    for item in data['list'][:8]:  # Next 24 hours
        weather_info = {
            "temp": item['main']['temp'],
            "condition": item['weather'][0]['main'],
            "description": item['weather'][0]['description'],
            "time": item['dt_txt']
        }
        tomorrow_forecasts.append(weather_info)
    
    return tomorrow_forecasts

# ============================================
# TOOL 2: Get Calendar Events  
# ============================================
def get_calendar_events():
    """Get tomorrow's events (hardcoded for demo)"""
    outdoor_events = [e for e in calendar_events if e['outdoor']]
    return outdoor_events

# ============================================
# AGENT BRAIN: Decision Making
# ============================================
def run_agent():
    """Main agent logic - autonomy, tool use, decision making"""
    
    output = []
    output.append("🤖 AGENT STARTING...")
    output.append("=" * 60)
    
    # STEP 1: Gather information using tools
    output.append("\n📡 Calling Weather API for Brooklyn, NY...")
    weather_data = get_weather()
    output.append(f"✓ Got weather forecast: {len(weather_data)} data points")
    
    output.append("\n📅 Checking calendar for outdoor events...")
    outdoor_events = get_calendar_events()
    output.append(f"✓ Found {len(outdoor_events)} outdoor events")
    
    # STEP 2: Agent decides what to do
    output.append("\n🧠 AGENT THINKING...")
    
    if len(outdoor_events) == 0:
        output.append("Decision: No outdoor events tomorrow. No email needed.")
        return "\n".join(output)
    
    # Prepare data for Claude to analyze
    weather_summary = "\n".join([
        f"- {w['time']}: {w['temp']}°F, {w['description']}" 
        for w in weather_data[:4]
    ])
    
    events_summary = "\n".join([
        f"- {e['time']}: {e['title']} at {e['location']}"
        for e in outdoor_events
    ])
    
    # STEP 3: Use Claude API to make decision and compose email
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = f"""You are an intelligent personal assistant agent. Analyze this data and decide if the user needs a weather alert email.

TOMORROW'S WEATHER FORECAST (Brooklyn, NY):
{weather_summary}

OUTDOOR EVENTS TOMORROW:
{events_summary}

YOUR JOB:
1. Decide if weather conditions warrant sending an alert
2. Consider: Will weather impact these outdoor activities?
3. If YES, compose a helpful email with:
   - Appropriate subject line
   - Friendly tone
   - Specific advice based on conditions
   - Which events might be affected

If no alert needed, respond with: NO_EMAIL_NEEDED

If alert needed, format as:
SUBJECT: [your subject]
BODY: [your email body]"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    decision = message.content[0].text
    
    # STEP 4: Take action based on decision
    output.append("\n📋 AGENT DECISION:")
    
    if "NO_EMAIL_NEEDED" in decision:
        output.append("✓ Weather looks fine. No alert necessary.")
    else:
        output.append("✓ Weather alert needed! Composing email...")
        output.append("\n" + "=" * 60)
        output.append("📧 EMAIL OUTPUT:")
        output.append("=" * 60)
        output.append(f"To: {USER_EMAIL}")
        output.append(decision)
        output.append("=" * 60)
    
    return "\n".join(output)

# ============================================
# WEB INTERFACE
# ============================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Weather Calendar Agent Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 15px 32px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 20px 0;
        }
        button:hover {
            background-color: #45a049;
        }
        #output {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
            margin-top: 20px;
            display: none;
        }
        .loading {
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Weather Calendar Agent</h1>
        <p>This intelligent agent checks tomorrow's weather and your calendar to decide if you need a weather alert.</p>
        
        <p><strong>Demo Setup:</strong></p>
        <ul>
            <li>Location: Brooklyn, NY</li>
            <li>Checks: Real weather data via API</li>
            <li>Events: Morning run & coffee meeting (hardcoded for demo)</li>
        </ul>
        
        <button onclick="runAgent()">Run Agent</button>
        
        <div id="output"></div>
    </div>
    
    <script>
        function runAgent() {
            const output = document.getElementById('output');
            output.style.display = 'block';
            output.textContent = '⏳ Agent is running... calling APIs and making decisions...';
            output.className = 'loading';
            
            fetch('/run')
                .then(response => response.text())
                .then(data => {
                    output.textContent = data;
                    output.className = '';
                })
                .catch(error => {
                    output.textContent = 'Error: ' + error;
                });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run')
def run():
    result = run_agent()
    return result

# ============================================
# RUN THE APP
# ============================================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)