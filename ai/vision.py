import json
from google import genai
from google.genai import types
from ai.providers import VisionProvider
from config.settings import GEMINI_API_KEY, AI_MODEL_NAME

IMAGE_CATEGORIES = [
    "Food", "Travel", "Nature", "Pets", "Screenshots",
    "Documents", "Memes", "Selfies", "Sports", "Events",
    "Shopping", "Technology", "Vehicles", "Buildings", "Other"
]

class GeminiVisionProvider(VisionProvider):
    """Gemini-powered implementation of VisionProvider."""
    
    def __init__(self):
        self.is_configured = bool(GEMINI_API_KEY)
        if self.is_configured:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            
    def classify_image(self, image_bytes: bytes, categories: list = None) -> dict:
        """
        Classifies an image and returns structured JSON output.
        Returns: {"category": str, "confidence": float, "description": str}
        """
        if not self.is_configured:
            return {"category": "Unknown", "confidence": 0.0, "description": "AI not configured."}
            
        cats = categories or IMAGE_CATEGORIES
        prompt = f"""
Analyze this image and respond ONLY with a JSON object (no markdown).
{{
  "category": "<one of: {', '.join(cats)}>",
  "confidence": <float between 0 and 1>,
  "description": "<one sentence visual description>"
}}
"""
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[prompt, image_part]
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception as e:
            return {"category": "Other", "confidence": 0.0, "description": f"Error: {e}"}
    
    def extract_text(self, image_bytes: bytes) -> str:
        """Performs OCR on an image using Gemini Vision."""
        if not self.is_configured:
            return ""
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    "Extract ALL text visible in this image. Return only the text, nothing else. If no text, return empty string.",
                    image_part
                ]
            )
            return response.text.strip()
        except Exception as e:
            return ""
    
    def describe_image(self, image_bytes: bytes) -> str:
        if not self.is_configured:
            return ""
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    "Describe this image in one concise sentence.",
                    image_part
                ]
            )
            return response.text.strip()
        except Exception as e:
            return ""
