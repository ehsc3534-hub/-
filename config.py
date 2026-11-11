import os

W, H, FPS = 1080, 1920, 24
SR = 44100
QUESTIONS_PER_VIDEO = 5
TIMER = 10
REVEAL_STEP = 0.8
MAX_TOTAL = 176.0         # whole video budget in seconds (Shorts limit is 180)

SUB_APPEAR = 2.6          # seconds after outro start: subscribe button pops up
SUB_CLICK = 4.0           # seconds after outro start: hand clicks the button

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

VOICE_MODEL = "assets/voice.onnx"
LENGTH_SCALE = 0.85       # lower = faster speech
OUT_DIR = "out"
HISTORY_FILE = "data/history.json"

# 5 questions per video = 5 DIFFERENT categories
CATEGORIES = {
    "Science": ["Physics", "Chemistry", "Biology", "Human Body", "Everyday Science", "Space and Astronomy"],
    "History": ["World History", "Ancient Civilizations", "Famous Inventions", "Famous Scientists"],
    "Geography": ["World Geography", "Countries and Capitals", "Oceans, Rivers and Mountains", "Currencies and Flags"],
    "Pop Culture": ["Music", "Movies and Cinema (general)", "Art and Painting", "Literature and Authors"],
    "Sports": ["Sports and Olympics", "World Records"],
    "Nature": ["Animals and Wildlife", "Plants and Trees", "Weather and Climate"],
    "Technology": ["Technology and Computers", "Transport and Vehicles", "Architecture and Landmarks"],
    "Food & Culture": ["Food and Drinks", "Languages and Alphabets", "Mythology"],
    "Math": ["Mathematics"],
}

ANGLES = [
    "origins", "records and extremes", "surprising facts", "dates and years",
    "famous people", "discoveries", "places", "numbers", "names and nicknames",
    "everyday objects", "firsts in history", "symbols", "units and measurements",
    "myths vs facts", "biggest and smallest", "inventions", "colors", "borders and neighbors",
]
