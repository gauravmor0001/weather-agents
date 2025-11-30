from dotenv import load_dotenv
import os
import google.generativeai as genai
import requests #used to send HTTP requests
import json
from typing import Optional
from pydantic import BaseModel, Field #help in how the datashould look like from the model.

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_weather(city: str):
    url = f"https://wttr.in/{city.lower()}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The weather in {city} is: {response.text}"
    else:
        return "Could not retrieve weather data."
    

available_tools = {
    "get_weather": get_weather
}

SYSTEM_PROMPT = """
You are a Weather AI Agent.
Your job is to answer user queries using the following workflow: START → PLAN → TOOL → OUTPUT.

Rules:
- Output must be ONLY in JSON format.
- Only one step per response: START or PLAN or TOOL or OUTPUT.
- If a TOOL call is needed, return:
  {"step":"TOOL","tool":"get_weather","input":"city_name"}
- After TOOL execution, if developer sends OBSERVE with tool result, respond with PLAN or OUTPUT.

JSON Format:
{"step":"START"|"PLAN"|"TOOL"|"OUTPUT","CONTENT":"string","tool":"string","input":"string"}
"""

class MyOutputFormat(BaseModel):
    step: str = Field(..., description="START, PLAN, TOOL or OUTPUT")
    CONTENT: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[str] = None


model = genai.GenerativeModel(
    "gemini-2.0-flash", 
    system_instruction=SYSTEM_PROMPT
)
message_history = []

user_query = input("Ask about weather: ")
message_history.append({"role": "user", "parts": [user_query]})


while True:
    try:
        response = model.generate_content(
            contents=message_history,
            generation_config={"response_mime_type": "application/json"}
        )
        
        raw = response.text
        clean_raw = raw.replace("```json", "").replace("```", "")
        
        parsed = MyOutputFormat.model_validate(json.loads(clean_raw))
        
        message_history.append({"role": "model", "parts": [raw]})

        if parsed.step == "START":
            print(f"AI: {parsed.CONTENT}")
            continue

        if parsed.step == "PLAN":
            print(f"Planning: {parsed.CONTENT}")
            continue

        if parsed.step == "TOOL":
            tool_name = parsed.tool
            tool_input = parsed.input
            tool_response = available_tools[tool_name](tool_input)
            print(f"Tool result: {tool_response}")

            observation_json = json.dumps({
                "step": "OBSERVE",
                "tool": tool_name,
                "input": tool_input,
                "OUTPUT": tool_response
            })
            
            message_history.append({
                "role": "user", 
                "parts": [observation_json]
            })
            continue

        if parsed.step == "OUTPUT":
            print(f"Final Output: {parsed.CONTENT}")
            break
            
    except Exception as e:
        print(f"An error occurred: {e}")
        break