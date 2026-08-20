from abc import ABC, abstractmethod
from typing import Optional

class VisionProvider(ABC):
    """Abstract interface for vision AI providers."""
    
    @abstractmethod
    def classify_image(self, image_bytes: bytes, categories: list) -> dict:
        """Classifies an image into provided categories."""
        pass
    
    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        """Extracts text from an image (OCR)."""
        pass
    
    @abstractmethod
    def describe_image(self, image_bytes: bytes) -> str:
        """Generates a natural language description of an image."""
        pass


class TranscriptionProvider(ABC):
    """Abstract interface for audio transcription providers."""
    
    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribes an audio file to text."""
        pass
