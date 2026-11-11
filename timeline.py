import wave
import numpy as np

import sfx
from config import SR, TIMER, REVEAL_STEP, SUB_APPEAR, SUB_CLICK


def plan_block(d, off):
    t = off
    p = {}
    p["q"] = (t, t + d["question"])
    t += d["question"] + 0.15
    p["opts"] = []
    for x in d["opts"]:
        p["opts"].append((t, t + x))
        t += x + 0.05
    t += 0.05
    p["prompt"] = (t, t + d["prompt"])
    t += d["prompt"] + 0.02
    p["timer"] = (t, t + TIMER)
    t += TIMER + 0.15
    p["expl"] = (t, t + d["expl"])
    t += d["expl"] + 0.25
    p["reveal"] = [t + i * REVEAL_STEP for i in range(4)]
    t += 4 * REVEAL_STEP + 0.15
    p["answer"] = (t, t + d["answer"])
    t += d["answer"] + 0.3
    p["end"] = t
    return p


def build(intro_d, blocks, outro_d):
    intro_end = intro_d + 0.3
    cursor = intro_end
    for b in blocks:
        b["p"] = plan_block(b["durs"], cursor)
        cursor = b["p"]["end"]
    outro_len = max(outro_d + 0.3, SUB_CLICK + 1.5)
    return {
        "intro_end": intro_end,
        "outro_start": cursor,
        "outro_len": outro_len,
        "total": cursor + outro_len,
    }


def mix_audio(tl, intro_clip, blocks, outro_clip, path):
    n = int((tl["total"] + 0.3) * SR)
    buf = np.zeros(n, np.float32)

    def put(x, at, g=1.0):
        i = int(max(0, at) * SR)
        if i >= n:
            return
        j = min(n, i + len(x))
        buf[i:j] += x[: j - i] * g

    buf += sfx.bgm(n / SR)[:n]

    # hook: big "90%" pops in
    put(sfx.whoosh(0.4), 0.0, 0.6)
    put(sfx.pop(), 0.02, 1.0)
    put(intro_clip, 0.1)

    for b in blocks:
        p, c, q = b["p"], b["clips"], b["q"]
        put(sfx.whoosh(0.3), p["q"][0] - 0.05, 0.5)
        put(c["question"], p["q"][0])
        for i in range(4):
            s, e = p["opts"][i]
            put(sfx.pop(), s - 0.02, 0.8)
            put(c["opts"][i], s)
        put(c["prompt"], p["prompt"][0])
        ts = p["timer"][0]
        for k in range(TIMER):
            put(sfx.tick(1400 if k < TIMER - 2 else 2000, 0.35), ts + k)
        put(sfx.timeup(), p["timer"][1] - 0.05, 0.8)
        put(c["expl"], p["expl"][0])
        put(sfx.whoosh(0.25), p["reveal"][0] - 0.25, 0.5)
        for i in range(4):
            if i == q["answer"]:
                put(sfx.ding(), p["reveal"][i], 0.8)
            else:
                put(sfx.buzz(), p["reveal"][i], 0.5)
        put(sfx.success(), p["answer"][0], 0.25)
        put(c["answer"], p["answer"][0])

    o = tl["outro_start"]
    put(sfx.whoosh(0.3), o, 0.5)
    put(outro_clip, o + 0.1)
    put(sfx.pop(), o + SUB_APPEAR, 1.0)       # subscribe button pops up
    put(sfx.pop(), o + SUB_CLICK, 1.0)        # click
    put(sfx.success(), o + SUB_CLICK + 0.05, 0.6)
    put(sfx.ding(), o + SUB_CLICK + 0.25, 0.5)  # bell

    peak = float(np.abs(buf).max())
    if peak > 0.92:
        buf *= 0.92 / peak
    pcm = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
