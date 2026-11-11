import os
import random

import question_gen
import seo
import timeline
import tts
import video
import youtube_upload
from config import (OUT_DIR, QUESTIONS_PER_VIDEO, MAX_TOTAL, SR, CATEGORIES,
                    SUB_CLICK)

LETTERS = "ABCD"
DRY_RUN = os.getenv("DRY_RUN", "").lower() == "true"

HOOK_TEXT = "Ninety percent of people get three of these five questions wrong! Can you beat it?"
OUTRO_TEXT = "How many did you get right? Comment your score, and subscribe for more quizzes!"


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

    intro_clip = tts.speak(HOOK_TEXT, "intro")
    outro_clip = tts.speak(OUTRO_TEXT, "outro")
    outro_len = max(len(outro_clip) / SR + 0.5, SUB_CLICK + 2.0)
    fixed = len(intro_clip) / SR + 0.5 + outro_len + 0.5

    # 5 different categories, one question from each
    cats = random.sample(list(CATEGORIES.keys()), QUESTIONS_PER_VIDEO)
    blocks, attempts, used = [], 0, 0.0
    while len(blocks) < QUESTIONS_PER_VIDEO and attempts < 60:
        attempts += 1
        left = QUESTIONS_PER_VIDEO - len(blocks)
        limit = (MAX_TOTAL - fixed - used) / left       # dynamic time budget
        cat = cats[len(blocks)]
        sub = random.choice(CATEGORIES[cat])
        q = question_gen.generate(sub, hist)
        if not q:
            continue
        q["category"] = cat
        n = len(blocks) + 1
        clips, durs = make_clips(q, n)
        dur = timeline.plan_block(durs, 0)["end"]
        if dur > limit:
            print(f"Too long ({dur:.1f}s > {limit:.1f}s), regenerating...")
            continue
        blocks.append({"q": q, "clips": clips, "durs": durs})
        used += dur
        question_gen.register(hist, q)
        print(f"[{n}/{QUESTIONS_PER_VIDEO}] ({cat}) {q['question']} ({dur:.1f}s)")

    if len(blocks) < QUESTIONS_PER_VIDEO:
        raise SystemExit("Could not generate enough valid questions.")

    tl = timeline.build(len(intro_clip) / SR, blocks, len(outro_clip) / SR)
    print(f"Total duration: {tl['total']:.1f}s")
    if tl["total"] > 179:
        raise SystemExit(f"Video too long: {tl['total']:.1f}s")

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
