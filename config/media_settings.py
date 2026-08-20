import os

# AI Processing Limits
MAX_AI_IMAGES = 50
MAX_AI_VIDEOS = 5
MAX_AI_AUDIO = 10
MAX_OCR_FILES = 20

# Sampling Defaults
DEFAULT_SAMPLING_STRATEGY = "Random Sample"
SAMPLING_STRATEGIES = [
    "Random Sample",
    "Newest First",
    "Oldest First",
    "Largest Files"
]

# Media Handling
THUMBNAIL_SIZE = (250, 250)
MAX_UPLOAD_SIZE_MB = 500

# Supported Formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
SUPPORTED_VIDEO_FORMATS = {".mp4", ".mov", ".avi"}
SUPPORTED_AUDIO_FORMATS = {".opus", ".m4a", ".mp3", ".ogg"}
SUPPORTED_DOC_FORMATS = {".pdf", ".doc", ".docx", ".txt", ".csv"}

# Temporary Storage
TEMP_MEDIA_DIR = os.path.join(os.getcwd(), ".temp_media")
