import streamlit as st
import google.generativeai as genai
import requests
import json
import os
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

def get_weather(city: str):
    try:
        url = f"https://wttr.in/{city.lower()}?format=%C+%t"
        response = requests.get(url)
        if response.status_code == 200:
            return f"The weather in {city} is: {response.text}"
        return "Could not retrieve weather data."
    except Exception:
        return "Error connecting to weather service."

available_tools = {"get_weather": get_weather}

SYSTEM_PROMPT = """
You are a Weather AI Agent.
Your job is to answer user queries using the following workflow: START -> PLAN -> TOOL -> OUTPUT.

Rules:
- Output must be ONLY in JSON format.
- Only one step per response.
- If a TOOL call is needed, return: {"step":"TOOL","tool":"get_weather","input":"city_name"}
- IMPORTANT: When step is "OUTPUT", you MUST put the final answer text in the "CONTENT" field. Do not leave it null.
"""

class MyOutputFormat(BaseModel):
    step: str = Field(..., description="START, PLAN, TOOL or OUTPUT")
    CONTENT: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[str] = None

model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)

st.title("🌤️ AI Weather Agent")
st.caption("I can find the weather for you.")

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

if user_query := st.chat_input("Ask about the weather (e.g., 'What is it like in Tokyo?')"):
    
    st.chat_message("user").write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    gemini_history = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})


    status_container = st.status("AI is thinking...", expanded=True)
    
    # here instead of while loop , as streamlit rerun the script on each interaction
    # We limit strictly to 5 steps to prevent infinite loops in web app
    for _ in range(5):
        try:
            response = model.generate_content(
                contents=gemini_history,
                generation_config={"response_mime_type": "application/json"}
            )
            
            raw = response.text
            parsed = MyOutputFormat.model_validate(json.loads(raw))
            
            gemini_history.append({"role": "model", "parts": [raw]})

            if parsed.step == "START":
                status_container.write(f"🚀 **Start:** {parsed.CONTENT}")
            
            elif parsed.step == "PLAN":
                status_container.write(f"🧠 **Plan:** {parsed.CONTENT}")
            
            elif parsed.step == "TOOL":
                status_container.write(f"🛠️ **Tool:** Calling `{parsed.tool}` for `{parsed.input}`...")
                tool_result = available_tools[parsed.tool](parsed.input)
                status_container.write(f"🔍 **Observation:** {tool_result}")

            
                obs_json = json.dumps({"step": "OBSERVE", "OUTPUT": tool_result})
                gemini_history.append({"role": "user", "parts": [obs_json]})
            
            elif parsed.step == "OUTPUT":
                status_container.update(label="Finished!", state="complete", expanded=False)
                final_text = parsed.CONTENT
                if not final_text:
                    final_text = "I found the weather, but I couldn't summarize it. Please check the steps above."
                st.chat_message("assistant").write(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                break
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break