from dotenv import load_dotenv
import os
import google.generativeai as genai
import requests #used to send HTTP requests
import json
from pydantic import BaseModel, Field #help in how the datashould look like from the model.
