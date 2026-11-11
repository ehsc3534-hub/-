import json
import hashlib
import random
import re
from functools import lru_cache

import requests

from config import OLLAMA_URL, OLLAMA_MODEL, ANGLES, HISTORY_FILE, CATEGORIES

STOP = set("""what which who whom whose where when why how is are was were the a an of in on at to for from by
with and or as that this these those it its into than then does do did has have had be been first most one
name called known many much their there about also used use""".split())

BAD_WORDS = {"not", "except", "typical", "typically", "approximately", "average",
             "usually", "generally", "roughly", "about", "best"}

_subj_cache = {}


@lru_cache(maxsize=None)
def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def content_words(n):
    return {w for w in n.split() if len(w) > 3 and w not in STOP}


# ------------------------------------------------------------------ history
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            h = json.load(f)
    except Exception:
        h = {}
    h.setdefault("hashes", [])
    h.setdefault("questions", [])
    h.setdefault("answers", [])
    h.setdefault("subjects", [])
    h.setdefault("subtopics", {})
    h.setdefault("cats", {})
    return h


def save_history(h):
    h["questions"] = h["questions"][-3000:]
    h["answers"] = h["answers"][-1500:]
    h["subjects"] = h["subjects"][-1500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=0)


def register(h, q):
    n = norm(q["question"])
    h["hashes"].append(hashlib.sha1(n.encode()).hexdigest())
    h["questions"].append(q["question"])
    h["answers"].append(norm(q["options"][q["answer"]]))
    if q.get("subject"):
        h["subjects"].append(norm(q["subject"]))
    t = q.get("topic")
    if t:
        h["subtopics"][t] = h["subtopics"].get(t, 0) + 1
    c = q.get("category")
    if c:
        h["cats"][c] = h["cats"].get(c, 0) + 1


# ------------------------------------------------------------------ rotation
def pick_categories(h, n):
    cnt = h["cats"]
    cats = sorted(CATEGORIES.keys(), key=lambda c: cnt.get(c, 0) + random.random() * 0.9)
    return cats[:n]


def pick_subtopic(cat, h):
    cnt = h["subtopics"]
    subs = sorted(CATEGORIES[cat], key=lambda s: cnt.get(s, 0) + random.random() * 0.9)
    return subs[0]


# ------------------------------------------------------------------ repeat checks
def subject_used(s, h):
    ns = norm(s)
    if not ns:
        return True
    for old in h["subjects"]:
        if ns == old:
            return True
        if len(ns) >= 5 and len(old) >= 5 and (ns in old or old in ns):
            return True
    for oq in h["questions"][-1500:]:
        if len(ns) >= 5 and ns in norm(oq):
            return True
    return False


def is_repeat(question, answer, h):
    n = norm(question)
    if hashlib.sha1(n.encode()).hexdigest() in h["hashes"]:
        return True
    t = set(n.split())
    cw = content_words(n)
    for old in h["questions"]:
        on = norm(old)
        o = set(on.split())
        if t and o and len(t & o) / len(t | o) > 0.5:
            return True
        common = cw & content_words(on)
        if len(common) >= 3:
            return True
        if len(common) >= 2 and len(common) / max(1, min(len(cw), len(content_words(on)))) >= 0.6:
            return True
    if norm(answer) in h["answers"][-300:]:
        return True
    for os_ in h["subjects"][-800:]:
        if len(os_) >= 5 and os_ in n:
            return True
    return False


# ------------------------------------------------------------------ LLM
def _ollama(prompt, temp, num_predict):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temp,
                "top_p": 0.92,
                "num_predict": num_predict,
                "seed": random.randint(1, 10**9),
            },
        },
        timeout=600,
    )
    return json.loads(r.json()["response"])


def _fetch_subjects(subtopic, h):
    used = random.sample(h["subjects"], min(40, len(h["subjects"])))
    used_txt = ", ".join(used) if used else "(none)"
    prompt = f"""List 20 different, specific, well-known quiz subjects about "{subtopic}".
Mix different countries, eras and difficulty levels. Each subject is 1 to 4 words
(a person, place, object, event, animal, element, invention, etc.).
Do NOT list any of these already used subjects: {used_txt}
Return ONLY JSON: {{"subjects": ["...", "..."]}}"""
    try:
        d = _ollama(prompt, 1.0, 320)
        items = [str(x).strip() for x in d.get("subjects", [])]
    except Exception as ex:
        print("LLM subject error:", ex)
        return []
    out = []
    for s in items:
        if 2 <= len(s) <= 40 and not subject_used(s, h) and s not in out:
            out.append(s)
    random.shuffle(out)
    return out


def _next_subject(subtopic, h):
    pool = [s for s in _subj_cache.get(subtopic, []) if not subject_used(s, h)]
    if not pool:
        pool = _fetch_subjects(subtopic, h)
    if not pool:
        _subj_cache[subtopic] = []
        return None
    s = pool.pop()
    _subj_cache[subtopic] = pool
    return s


def _prompt(subtopic, subject, h):
    avoid = random.sample(h["questions"], min(12, len(h["questions"])))
    avoid_txt = "\n".join("- " + a for a in avoid) if avoid else "- (none)"
    diff = random.choice(["easy", "easy", "medium", "medium", "hard"])
    if subject:
        focus = f'The question MUST be specifically about this subject: "{subject}" (topic area: {subtopic}).'
    else:
        focus = f"Topic area: {subtopic}. Angle for variety: {random.choice(ANGLES)}."
    return f"""You write general knowledge quiz questions for a YouTube Shorts quiz.
{focus}
Difficulty: {diff}

Rules:
- One well-known, factual, unambiguous question, maximum 14 words, ending with a question mark.
- Never write negative questions (no "NOT", no "EXCEPT"). Never ask about opinions, estimates or averages.
- Exactly one correct answer, maximum 3 words.
- Exactly three wrong answers, plausible but clearly wrong, maximum 3 words each, all different.
- Never use "all of the above" or "none of the above".
- Explanation: ONE short sentence, maximum 18 words, giving an interesting accurate fact.
  The explanation MUST NOT state or contain the correct answer and must not mention any option.
- Do NOT repeat or paraphrase any of these earlier questions:
{avoid_txt}

Return ONLY valid JSON in this exact shape:
{{"question": "...", "correct_answer": "...", "wrong_answers": ["...", "...", "..."], "explanation": "..."}}"""


def _validate(d, h, subject):
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
    if len(q.split()) > 18 or len(e.split()) > 24:
        return None
    if set(norm(q).split()) & BAD_WORDS:
        return None
    opts = [c] + w
    if any(len(o.split()) > 4 or len(o) > 32 for o in opts):
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
    if is_repeat(q, c, h):
        return None
    options = opts[:]
    random.shuffle(options)
    return {"question": q, "options": options, "answer": options.index(c),
            "explanation": e, "subject": subject or c}


def generate(subtopic, h, tries=6):
    for _ in range(tries):
        subject = _next_subject(subtopic, h)
        try:
            d = _ollama(_prompt(subtopic, subject, h), 0.8, 260)
        except Exception as ex:
            print("LLM error:", ex)
            continue
        q = _validate(d, h, subject)
        if q:
            q["topic"] = subtopic
            return q
    return None
