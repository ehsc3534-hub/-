import random
import re

HOOKS = [
    "90% Fail This Quiz!",
    "Only 1% Can Score 3/3!",
    "Can You Beat This Quiz?",
    "Test Your Brain in 60 Seconds!",
    "Genius Level Quiz Challenge!",
    "How Smart Are You?",
    "Think Fast! 60 Second Quiz!",
    "Can You Get All 3 Right?",
]

BASE_TAGS = [
    "quiz", "trivia", "general knowledge", "gk quiz", "quiz shorts", "trivia shorts",
    "brain test", "can you answer", "test your knowledge", "iq test", "quiz challenge",
    "learn something new", "fun facts", "shorts", "3 question quiz", "90% fail quiz",
    "finance quiz", "money quiz", "60 second quiz",
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
    title = f"{hook} Finance & {cats[0] if cats[0] != 'Finance' else cats[-1]} Quiz #Shorts"
    if len(title) > 100:
        title = f"{hook} Quiz #Shorts"
    title = title[:100]

    tag_line = " ".join(_tag(c) for c in cats[:3])
    desc = (
        f"{hook} Test your general knowledge with 3 quick quiz questions, including one finance question. "
        f"You get a few seconds for each question. Pause, think, and comment your score!\n\n"
        f"Categories in this quiz: {', '.join(cats)}.\n\n"
        f"Finance questions are for general knowledge only, not financial advice.\n\n"
        f"Subscribe for new quiz Shorts every day!\n\n"
        f"#shorts #quiz #trivia #generalknowledge #financequiz #brainteaser #quizchallenge {tag_line}"
    )
    tags, total = [], 0
    for t in BASE_TAGS + [x.lower() for x in cats]:
        if total + len(t) + 1 > 450:
            break
        tags.append(t)
        total += len(t) + 1
    return {"title": title, "description": desc, "tags": tags}
