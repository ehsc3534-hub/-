import random

HOOKS = [
    "Only 1% Can Score 5/5!",
    "Can You Beat This Quiz?",
    "Test Your Brain in 60 Seconds!",
    "Genius Level Quiz Challenge!",
    "How Smart Are You?",
    "General Knowledge Challenge!",
    "Think Fast! 10 Seconds Only!",
    "Can You Get All 5 Right?",
]

BASE_TAGS = [
    "quiz", "trivia", "general knowledge", "gk quiz", "quiz shorts", "trivia shorts",
    "brain test", "can you answer", "test your knowledge", "iq test", "quiz challenge",
    "learn something new", "fun facts", "shorts", "5 question quiz",
]


def build_seo(questions):
    topics = []
    for q in questions:
        if q["topic"] not in topics:
            topics.append(q["topic"])
    hook = random.choice(HOOKS)
    title = f"{hook} {topics[0]} & More Quiz #Shorts"
    if len(title) > 100:
        title = f"{hook} Quiz #Shorts"
    title = title[:100]

    tag_line = " ".join("#" + t.lower().replace(" ", "").replace(",", "").replace("(", "").replace(")", "")
                        for t in topics[:3])
    desc = (
        f"{hook} Test your general knowledge with 5 quick quiz questions. "
        f"You get 10 seconds for each question. Pause, think, and comment your score!\n\n"
        f"Topics in this quiz: {', '.join(topics)}.\n\n"
        f"Subscribe for new quiz Shorts every day!\n\n"
        f"#shorts #quiz #trivia #generalknowledge #brainteaser #quizchallenge {tag_line}"
    )
    tags, total = [], 0
    for t in BASE_TAGS + [x.lower() for x in topics]:
        if total + len(t) + 1 > 450:
            break
        tags.append(t)
        total += len(t) + 1
    return {"title": title, "description": desc, "tags": tags}
