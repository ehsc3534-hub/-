import json
import hashlib
import random
import re
import requests

from config import OLLAMA_URL, OLLAMA_MODEL, ANGLES, HISTORY_FILE

LETTERS = "ABCD"


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _tokens(s):
    return set(norm(s).split())


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            h = json.load(f)
    except Exception:
        h = {}
    h.setdefault("hashes", [])
    h.setdefault("questions", [])
    return h


def save_history(h):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=0)


def is_repeat(question, h):
    n = norm(question)
    if hashlib.sha1(n.encode()).hexdigest() in h["hashes"]:
        return True
    t = _tokens(question)
    for old in h["questions"]:
        o = _tokens(old)
        if t and o and len(t & o) / len(t | o) > 0.6:
            return True
    return False


def register(h, q):
    n = norm(q["question"])
    h["hashes"].append(hashlib.sha1(n.encode()).hexdigest())
    h["questions"].append(q["question"])


def _prompt(topic, h):
    avoid = random.sample(h["questions"], min(12, len(h["questions"])))
    avoid_txt = "\n".join("- " + a for a in avoid) if avoid else "- (none)"
    diff = random.choice(["easy", "easy", "medium", "medium", "hard"])
    angle = random.choice(ANGLES)
    return f"""You write general knowledge quiz questions for a YouTube Shorts quiz.
Topic: {topic}
Difficulty: {diff}
Angle for variety: {angle}

Rules:
- One factual, unambiguous question, maximum 18 words, ending with a question mark.
- Exactly one correct answer, maximum 4 words.
- Exactly three wrong answers, plausible but clearly wrong, maximum 4 words each, all different.
- Never use "all of the above" or "none of the above".
- Explanation: 1 or 2 short sentences, maximum 25 words, giving an interesting accurate fact related to the question.
  The explanation MUST NOT state or contain the correct answer and must not mention any option.
- Do NOT repeat or paraphrase any of these earlier questions:
{avoid_txt}

Return ONLY valid JSON in this exact shape:
{{"question": "...", "correct_answer": "...", "wrong_answers": ["...", "...", "..."], "explanation": "..."}}"""


def _validate(d, h):
    try:
        q = str(d["question"]).strip()
        c = str(d["correct_answer"]).strip()
        w = [str(x).strip() for x in d["wrong_answers"]]
        e = str(d["explanation"]).strip()
    except Exception:
        return None
    if len(w) != 3 or not q or not c or not e:
        return None
    if not q.endswith("?"):
        return None
    if len(q.split()) > 24 or len(e.split()) > 32:
        return None
    opts = [c] + w
    if any(len(o.split()) > 5 or len(o) > 40 for o in opts):
        return None
    if len({norm(o) for o in opts}) != 4 or any(not norm(o) for o in opts):
        return None
    if any(x in norm(o) for o in opts for x in ("all of the above", "none of the above")):
        return None
    nc, ne, nq = norm(c), norm(e), norm(q)
    if len(nc) >= 3 and (nc in ne or nc in nq):
        return None
    for o in w:
        no = norm(o)
        if len(no) >= 4 and no in ne:
            return None
    if is_repeat(q, h):
        return None
    options = opts[:]
    random.shuffle(options)
    return {"question": q, "options": options, "answer": options.index(c), "explanation": e}


def generate(topic, h, tries=6):
    for _ in range(tries):
        try:
            r = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": _prompt(topic, h),
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.95,
                        "top_p": 0.95,
                        "num_predict": 320,
                        "seed": random.randint(1, 10**9),
                    },
                },
                timeout=600,
            )
            d = json.loads(r.json()["response"])
        except Exception as ex:
            print("LLM error:", ex)
            continue
        q = _validate(d, h)
        if q:
            q["topic"] = topic
            return q
    return None
