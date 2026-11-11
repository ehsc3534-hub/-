import os

SCALE = 2                          # 2 = 4K (2160x3840). Use 1 for 1080p.
DW, DH = 1080, 1920                # design size (layout units)
W, H = DW * SCALE, DH * SCALE
FPS = 24
SR = 44100
QUESTIONS_PER_VIDEO = 3
TIMER = 4
REVEAL_STEP = 0.4
MAX_TOTAL = 59.0          # whole video budget in seconds (must stay under 60)

SUB_APPEAR = 1.1          # seconds after outro start: subscribe button pops up
SUB_CLICK = 2.1           # seconds after outro start: button is clicked

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

VOICE_MODEL = "assets/voice.onnx"
LENGTH_SCALE = 0.8        # lower = faster speech
OUT_DIR = "out"
HISTORY_FILE = "data/history.json"

FINANCE_CAT = "Finance"   # every video gets exactly one question from this category

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
    "Finance": ["Money and Banking", "Stock Market and Investing", "Personal Finance",
                "Economics", "Business and Trade"],
}

ANGLES = [
    "origins", "records and extremes", "surprising facts", "dates and years",
    "famous people", "discoveries", "places", "numbers", "names and nicknames",
    "everyday objects", "firsts in history", "symbols", "units and measurements",
    "myths vs facts", "biggest and smallest", "inventions", "colors", "borders and neighbors",
]
