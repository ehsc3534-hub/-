import os

import question_gen
import seo
import timeline
import tts
import video
import youtube_upload
from config import OUT_DIR, QUESTIONS_PER_VIDEO, MAX_TOTAL, SR, SUB_CLICK

LETTERS = "ABCD"
DRY_RUN = os.getenv("DRY_RUN", "").lower() == "true"

HOOK_TEXT = "Ninety percent of people fail this quiz! Can you beat it?"
OUTRO_TEXT = "Comment your score, and subscribe!"


def make_clips(q, n):
    clips = {
        "question": tts.speak(q["question"], f"q{n}"),
        "opts": [tts.speak(f"{LETTERS[i]}. {o}", f"q{n}_o{i}") for i, o in enumerate(q["options"])],
        "prompt": tts.speak("Go!", f"q{n}_p"),
        "expl": tts.speak(q["explanation"], f"q{n}_e"),
        "answer": tts.speak(
            f"Answer {LETTERS[q['answer']]}. {q['options'][q['answer']]}.", f"q{n}_a"),
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
    print(f"History: {len(hist['questions'])} old questions, {len(hist['subjects'])} old subjects")

    intro_clip = tts.speak(HOOK_TEXT, "intro")
    outro_clip = tts.speak(OUTRO_TEXT, "outro")
    outro_len = max(len(outro_clip) / SR + 0.3, SUB_CLICK + 1.5)
    fixed = len(intro_clip) / SR + 0.3 + outro_len

    # 2 least-used categories + 1 Finance (random position)
    cats = question_gen.pick_categories(hist, QUESTIONS_PER_VIDEO)
    print("Categories:", cats)
    blocks, attempts, used = [], 0, 0.0
    while len(blocks) < QUESTIONS_PER_VIDEO and attempts < 120:
        attempts += 1
        left = QUESTIONS_PER_VIDEO - len(blocks)
        limit = (MAX_TOTAL - fixed - used) / left       # dynamic time budget
        cat = cats[len(blocks)]
        sub = question_gen.pick_subtopic(cat, hist)
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
        print(f"[{n}/{QUESTIONS_PER_VIDEO}] ({cat} / {sub} / {q['subject']}) {q['question']} ({dur:.1f}s)")

    if len(blocks) < QUESTIONS_PER_VIDEO:
        raise SystemExit("Could not generate enough valid questions.")

    tl = timeline.build(len(intro_clip) / SR, blocks, len(outro_clip) / SR)
    print(f"Total duration: {tl['total']:.1f}s")
    if tl["total"] > 59.8:
        raise SystemExit(f"Video too long: {tl['total']:.1f}s (limit 60s)")

    audio_path = f"{OUT_DIR}/audio.wav"
    out_path = f"{OUT_DIR}/quiz_short.mp4"
    timeline.mix_audio(tl, intro_clip, blocks, outro_clip, audio_path)
    video.render(tl, blocks, audio_path, out_path)

    meta = seo.build_seo([b["q"] for b in blocks])
    print("Title:", meta["title"])

    if DRY_RUN:
        print("DRY RUN: skipping upload and history save.")
        return

    # save history BEFORE upload, so these questions never come again
    question_gen.save_history(hist)
    print("History saved.")
    youtube_upload.upload(out_path, meta)


if __name__ == "__main__":
    main()
