import re

# Regex patterns for various WhatsApp export formats
WHATSAPP_PATTERNS = [
    # 1. Standard format: "12/03/24, 15:30 - User: message" or "12/03/24, 3:30 PM - User: message"
    re.compile(r"^(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}),?\s(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[aApP][mM])?)\s-\s([^:]+):\s(.*)$"),
    # 2. Bracketed format: "[12/03/24, 15:30:15] User: message" or "[12-03-24, 3:30 PM] User: message"
    re.compile(r"^\[(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}),?\s(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[aApP][mM])?)\]\s([^:]+):\s(.*)$")
]

# Legacy pattern for single-regex fallback/compatibility
WHATSAPP_PATTERN = WHATSAPP_PATTERNS[0]

# System messages to ignore or handle specially
OMITTED_MEDIA_MSG = "<Media omitted>"
DELETED_MSG = "This message was deleted"

# Common day names mapping
DAY_NAMES_ORDER = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

MONTH_NAMES_ORDER = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]
