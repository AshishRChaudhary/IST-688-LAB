import json

import requests
import streamlit as st
from openai import OpenAI

CHAT_MODEL = "gpt-5-mini"
DEFAULT_LOCATION = "Syracuse, NY"

SYSTEM_PROMPT = """You are a "what to wear" assistant.

Use the get_current_weather tool to look up the weather for the location you are asked
about, then give practical advice:

- What to wear today. Take into account how conditions change through the day: the
  temperature swing between the high and low, how it actually feels, wind, and any
  chance of rain or snow. Say if they should carry a layer or an umbrella.
- Outdoor activities that suit the weather, and the best time of day for them, using
  the hourly forecast and the sunrise and sunset times.

Name the actual conditions your advice is based on. Keep it friendly and concrete.
"""

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get today's weather for a location, including current "
        "conditions, the high and low, and an hourly forecast.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city to look up, e.g. 'Syracuse, NY' or "
                    "'Paris'. May also be a zip code, airport code, or landmark.",
                }
            },
            "required": ["location"],
        },
    },
}

st.title("Lab 5: The What to Wear Bot")

if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def get_current_weather(location):
    """Today's weather from wttr.in, trimmed to what the bot needs for advice."""
    url = f"https://wttr.in/{location}?format=j1"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f"wttr.in error: status {response.status_code}")
    try:
        data = response.json()
    except ValueError:
        # unknown locations come back as plain text, not JSON
        raise Exception(f"Could not find a location named {location}")

    current = data["current_condition"][0]
    today = data["weather"][0]
    astronomy = today["astronomy"][0]
    area = data["nearest_area"][0]

    return {
        "location": f"{area['areaName'][0]['value']}, {area['region'][0]['value']}, "
        f"{area['country'][0]['value']}",
        "current": {
            "temperature_F": float(current["temp_F"]),
            "feels_like_F": float(current["FeelsLikeF"]),
            "description": current["weatherDesc"][0]["value"],
            "humidity_pct": int(current["humidity"]),
            "wind_mph": float(current["windspeedMiles"]),
            "wind_direction": current["winddir16Point"],
            "precip_inches": float(current["precipInches"]),
            "uv_index": int(current["uvIndex"]),
            "cloud_cover_pct": int(current["cloudcover"]),
        },
        "today": {
            "date": today["date"],
            "high_F": float(today["maxtempF"]),
            "low_F": float(today["mintempF"]),
            "sunrise": astronomy["sunrise"],
            "sunset": astronomy["sunset"],
        },
        # Three-hourly forecast so the bot can talk about how the day changes.
        "hourly": [
            {
                "time": f"{int(hour['time']) // 100:02d}:00",
                "temperature_F": float(hour["tempF"]),
                "feels_like_F": float(hour["FeelsLikeF"]),
                "description": hour["weatherDesc"][0]["value"],
                "chance_of_rain_pct": int(hour["chanceofrain"]),
                "chance_of_snow_pct": int(hour["chanceofsnow"]),
                "wind_mph": float(hour["windspeedMiles"]),
            }
            for hour in today["hourly"]
        ],
    }


def get_advice(city):
    client = st.session_state.openai_client
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"What should I wear today in {city}?"},
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=[WEATHER_TOOL],
        tool_choice="auto",
    )
    message = response.choices[0].message

    if not message.tool_calls:
        return message.content

    messages.append(message.to_dict())
    for tool_call in message.tool_calls:
        arguments = json.loads(tool_call.function.arguments)
        # A weather request without a location falls back to Syracuse.
        location = arguments.get("location") or DEFAULT_LOCATION
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(get_current_weather(location)),
            }
        )

    # Second call, now that the model can see the weather it asked for.
    followup = client.chat.completions.create(model=CHAT_MODEL, messages=messages)
    return followup.choices[0].message.content


city = st.text_input("Which city?", placeholder=DEFAULT_LOCATION)

if st.button("What should I wear?"):
    location = city.strip() or DEFAULT_LOCATION
    with st.spinner(f"Checking the weather in {location}..."):
        try:
            st.write(get_advice(location))
        except Exception as error:
            st.error(f"Could not get the weather: {error}")
