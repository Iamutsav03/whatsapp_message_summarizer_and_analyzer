import os
import json
import streamlit as st
from google import genai
from config.settings import GEMINI_API_KEY, AI_MODEL_NAME

class GeminiClient:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.is_configured = False
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.is_configured = True
            
    def _read_prompt(self, filename: str) -> str:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()

    @st.cache_data(show_spinner=False)
    def generate_summary(_self, context: dict) -> str:
        if not _self.is_configured:
            return "[!] Gemini API key is missing. Please configure your `.env` file to enable AI features."
            
        prompt_template = _self._read_prompt("summary_prompt.txt")
        prompt = prompt_template.replace("{context}", json.dumps(context, indent=2))
        
        try:
            response = _self.client.models.generate_content(
                model=AI_MODEL_NAME,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"[Error] AI Generation Failed: {str(e)}"

    @st.cache_data(show_spinner=False)
    def generate_insights(_self, context: dict) -> list:
        if not _self.is_configured:
            return ["[!] Gemini API key is missing. AI insights disabled."]
            
        prompt_template = _self._read_prompt("insights_prompt.txt")
        prompt = prompt_template.replace("{context}", json.dumps(context, indent=2))
        
        try:
            response = _self.client.models.generate_content(
                model=AI_MODEL_NAME,
                contents=prompt
            )
            # Try to parse the JSON array
            text = response.text
            # Strip markdown json blocks if gemini included them despite instructions
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Failed to generate insights: {e}")
            return ["Failed to generate insights due to an API or parsing error."]
