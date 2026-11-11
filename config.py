import os

W, H, FPS = 1080, 1920, 24
SR = 44100
QUESTIONS_PER_VIDEO = 5
TIMER = 10
REVEAL_STEP = 0.8
MAX_BLOCK = 33.0          # max seconds for one question block (keeps video under 3 min)
MAX_TOTAL = 178.0

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

VOICE_MODEL = "assets/voice.onnx"
LENGTH_SCALE = 0.85       # lower = faster speech
OUT_DIR = "out"
HISTORY_FILE = "data/history.json"

TOPICS = [
    "World Geography", "World History", "Space and Astronomy", "Animals and Wildlife",
    "Human Body", "Famous Inventions", "Physics", "Chemistry", "Biology",
    "Countries and Capitals", "Oceans, Rivers and Mountains", "Food and Drinks",
    "Music", "Art and Painting", "Literature and Authors", "Mathematics",
    "Technology and Computers", "Sports and Olympics", "Mythology", "World Records",
    "Languages and Alphabets", "Famous Scientists", "Architecture and Landmarks",
    "Plants and Trees", "Weather and Climate", "Ancient Civilizations",
    "Currencies and Flags", "Transport and Vehicles", "Movies and Cinema (general)",
    "Everyday Science",
]

ANGLES = [
    "origins", "records and extremes", "surprising facts", "dates and years",
    "famous people", "discoveries", "places", "numbers", "names and nicknames",
    "everyday objects", "firsts in history", "symbols", "units and measurements",
    "myths vs facts", "biggest and smallest", "inventions", "colors", "borders and neighbors",
]
