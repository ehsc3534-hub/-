import os
import random

import question_gen
import seo
import sfx  # noqa: F401
import timeline
import tts
import video
import youtube_upload
from config import (OUT_DIR, QUESTIONS_PER_VIDEO, MAX_BLOCK, MAX_TOTAL, SR, TOPICS)

LETTERS = "ABCD"
DRY_RUN = os.getenv("DRY_RUN", "").lower() == "true"


def make_clips(q, n):
    clips = {
        "question": tts.speak(f"Question {n}. {q['question']}", f"q{n}"),
        "opts": [tts.speak(f"{LETTERS[i]}. {o}", f"q{n}_o{i}") for i, o in enumerate(q["options"])],
        "prompt": tts.speak("Ten seconds. Go!", f"q{n}_p"),
        "expl": tts.speak(q["explanation"], f"q{n}_e"),
        "answer": tts.speak(
            f"The correct answer is {LETTERS[q['answer']]}. {q['options'][q['answer']]}.", f"q{n}_a"),
    }
    durs = {
        "question": len(clips["question"]) / SR,
        "opts": [len(x) / SR for x in clips["opts"]],
        "prompt": len(clips["prompt"]) / SR,
        "expl": len(clips["expl"]) / SR,
        "answer": len(clips["answer"]) / SR,
    }
    return clips, durs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    hist = question_gen.load_history()

    intro_clip = tts.speak("Welcome to Quiz Time! Five questions, ten seconds each. Ready? Let's go!", "intro")
    outro_clip = tts.speak("How many did you get right? Comment your score, and subscribe for more quizzes!", "outro")

    topics = random.sample(TOPICS, QUESTIONS_PER_VIDEO)
    blocks, attempts = [], 0
    while len(blocks) < QUESTIONS_PER_VIDEO and attempts < 50:
        attempts += 1
        q = question_gen.generate(topics[len(blocks)], hist)
        if not q:
            continue
        n = len(blocks) + 1
        clips, durs = make_clips(q, n)
        if timeline.plan_block(durs, 0)["end"] > MAX_BLOCK:
            print("Question too long, regenerating...")
            continue
        blocks.append({"q": q, "clips": clips, "durs": durs})
        question_gen.register(hist, q)
        print(f"[{n}/{QUESTIONS_PER_VIDEO}] {q['question']}")

    if len(blocks) < QUESTIONS_PER_VIDEO:
        raise SystemExit("Could not generate enough valid questions.")

    tl = timeline.build(len(intro_clip) / SR, blocks, len(outro_clip) / SR)
    if tl["total"] > MAX_TOTAL:
        raise SystemExit(f"Video too long: {tl['total']:.1f}s")
    print(f"Total duration: {tl['total']:.1f}s")

    audio_path = f"{OUT_DIR}/audio.wav"
    out_path = f"{OUT_DIR}/quiz_short.mp4"
    timeline.mix_audio(tl, intro_clip, blocks, outro_clip, audio_path)
    video.render(tl, blocks, audio_path, out_path)

    meta = seo.build_seo([b["q"] for b in blocks])
    print("Title:", meta["title"])

    if DRY_RUN:
        print("DRY RUN: skipping upload and history save.")
        return

    youtube_upload.upload(out_path, meta)
    question_gen.save_history(hist)
    print("History saved.")


if __name__ == "__main__":
    main()
