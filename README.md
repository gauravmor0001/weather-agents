🌤️ AI Weather Agent

This project is an AI-powered Weather Agent built with the Gemini API and Streamlit. It demonstrates agentic reasoning (Plan, Tool, Observe, Output) by using a structured JSON response format to decide when to call an external function (get_weather) to fetch real-time data.

The application is designed to be easily run locally or deployed to Streamlit Community Cloud.

🚀 Features

Agentic Reasoning: The AI processes the query in multiple steps (PLAN, TOOL, OBSERVE, OUTPUT).

Structured Output: Uses Pydantic to enforce a strict JSON response format, ensuring the tool calls are reliable.

Real-time Weather: Fetches live weather conditions using the OpenWeatherMap API (via PyOWM, assuming you finished the previous steps, or requests if you kept the simple wttr.in tool).

Web Interface: Hosted on a simple, interactive Streamlit web application.

