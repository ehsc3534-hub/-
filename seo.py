import random
import re

HOOKS = [
    "90% Fail This Quiz!",
    "Only 1% Can Score 5/5!",
    "Can You Beat This Quiz?",
    "Test Your Brain in 60 Seconds!",
    "Genius Level Quiz Challenge!",
    "How Smart Are You?",
    "Think Fast! 10 Seconds Only!",
    "Can You Get All 5 Right?",
]

BASE_TAGS = [
    "quiz", "trivia", "general knowledge", "gk quiz", "quiz shorts", "trivia shorts",
    "brain test", "can you answer", "test your knowledge", "iq test", "quiz challenge",
    "learn something new", "fun facts", "shorts", "5 question quiz", "90% fail quiz",
]


def _tag(s):
    return "#" + re.sub(r"[^a-z0-9]", "", s.lower())


def build_seo(questions):
    cats = []
    for q in questions:
        c = q.get("category") or q["topic"]
        if c not in cats:
            cats.append(c)
    hook = random.choice(HOOKS)
    title = f"{hook} {cats[0]} & More Quiz #Shorts"
    if len(title) > 100:
        title = f"{hook} Quiz #Shorts"
    title = title[:100]

    tag_line = " ".join(_tag(c) for c in cats[:3])
    desc = (
        f"{hook} Test your general knowledge with 5 quick quiz questions from 5 different categories. "
        f"You get 10 seconds for each question. Pause, think, and comment your score!\n\n"
        f"Categories in this quiz: {', '.join(cats)}.\n\n"
        f"Subscribe for new quiz Shorts every day!\n\n"
        f"#shorts #quiz #trivia #generalknowledge #brainteaser #quizchallenge {tag_line}"
    )
    tags, total = [], 0
    for t in BASE_TAGS + [x.lower() for x in cats]:
        if total + len(t) + 1 > 450:
            break
        tags.append(t)
        total += len(t) + 1
    return {"title": title, "description": desc, "tags": tags}
