import glob
import math
import os
import subprocess
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from config import W, H, FPS, TIMER

PAPER = (250, 244, 228)
INK = (35, 38, 70)
LINE = (190, 210, 235)
MARGIN = (238, 150, 150)
GREEN = (34, 160, 90)
RED = (215, 55, 65)
WHITE = (255, 255, 255)
ACCENTS = [(255, 112, 67), (66, 133, 244), (156, 39, 176), (0, 150, 136), (233, 160, 0)]

OPT_Y0, OPT_H, OPT_GAP, Q_Y = 660, 140, 26, 185
LETTERS = "ABCD"


def clip(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def pop_scale(a):
    a = clip(a)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (a - 1) ** 3 + c1 * (a - 1) ** 2


@lru_cache(None)
def font_path():
    cands = ["assets/hand.ttf"]
    cands += glob.glob("/usr/share/fonts/**/ComicNeue-Bold.ttf", recursive=True)
    cands += glob.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf", recursive=True)
    for c in cands:
        if os.path.exists(c):
            return c
    return None


@lru_cache(None)
def F(size):
    p = font_path()
    return ImageFont.truetype(p, size) if p else ImageFont.load_default()


def wrap(text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if font.getlength(test) <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Hand:
    """Handwriting-style progressive text reveal with a moving pencil."""

    def __init__(self, text, size, maxw, color=INK, gap=1.28):
        self.font = F(size)
        self.lines = wrap(text, self.font, maxw)
        self.lh = int(size * gap)
        self.total = max(1, sum(len(l) for l in self.lines))
        self.layers = []
        for l in self.lines:
            w = int(self.font.getlength(l)) + 12
            lay = Image.new("RGBA", (w, self.lh + 12), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((6, 0), l, font=self.font, fill=color + (255,))
            self.layers.append(lay)

    @property
    def height(self):
        return self.lh * len(self.lines)

    def draw(self, img, x, y, p, center=False, pen=True):
        shown = clip(p) * self.total
        used = 0
        for i, (l, lay) in enumerate(zip(self.lines, self.layers)):
            if shown <= used:
                break
            n = len(l)
            k = min(float(n), shown - used)
            ki = int(k)
            frac = k - ki
            wpx = self.font.getlength(l[:ki])
            if ki < n:
                wpx += frac * self.font.getlength(l[ki])
            x0 = x - lay.width / 2 if center else x
            yy = int(y + i * self.lh + 2 * math.sin(i * 1.7))
            crop = lay.crop((0, 0, min(lay.width, int(wpx) + 8), lay.height))
            img.paste(crop, (int(x0), yy), crop)
            if pen and k < n and p < 1:
                _pencil(img, x0 + 6 + wpx, yy + self.lh * 0.78 + 3 * math.sin(p * 400))
            used += n


def _pencil(img, x, y):
    d = ImageDraw.Draw(img)
    d.line([(x, y), (x + 70, y - 80)], fill=(240, 180, 40), width=16)
    d.line([(x, y), (x + 9, y - 11)], fill=(60, 60, 60), width=7)
    d.line([(x + 62, y - 71), (x + 78, y - 90)], fill=(235, 120, 130), width=16)


def fit_hand(text, sizes, maxw, maxlines, color=INK):
    h = None
    for s in sizes:
        h = Hand(text, s, maxw, color)
        if len(h.lines) <= maxlines:
            return h
    return h


def make_paper(accent, label=None):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for y in range(190, H, 72):
        d.line([(0, y), (W, y)], fill=LINE, width=2)
    d.line([(100, 0), (100, H)], fill=MARGIN, width=3)
    d.rectangle([0, 0, W, 150], fill=accent)
    if label:
        d.text((W // 2, 75), label, font=F(76), fill=WHITE, anchor="mm")
    return im


def draw_card(img, i, letter, hand, tprog, state, mark_age, accent, dx=0):
    d = ImageDraw.Draw(img)
    y = OPT_Y0 + i * (OPT_H + OPT_GAP)
    x0, x1, cy = 130 + dx, 990 + dx, y + OPT_H // 2
    fill, outline, wd = WHITE, accent, 6
    if state == "correct":
        fill, outline, wd = (222, 246, 230), GREEN, 10
    elif state == "wrong":
        fill, outline, wd = (252, 228, 230), RED, 10
    d.rounded_rectangle([x0, y, x1, y + OPT_H], radius=32, fill=fill, outline=outline, width=wd)
    d.ellipse([x0 + 28, cy - 42, x0 + 112, cy + 42], fill=outline)
    d.text((x0 + 70, cy), letter, font=F(60), fill=WHITE, anchor="mm")
    hand.draw(img, x0 + 150, cy - hand.height // 2 - 4, tprog)
    if state in ("correct", "wrong") and mark_age is not None:
        s = pop_scale(mark_age / 0.3)
        r = max(1, int(42 * s))
        mx = x1 - 70
        col = GREEN if state == "correct" else RED
        d.ellipse([mx - r, cy - r, mx + r, cy + r], fill=col)
        if state == "correct":
            pts = [(mx - 20 * s, cy + 2 * s), (mx - 6 * s, cy + 16 * s), (mx + 22 * s, cy - 16 * s)]
            d.line(pts, fill=WHITE, width=max(2, int(10 * s)), joint="curve")
        else:
            a = 16 * s
            d.line([(mx - a, cy - a), (mx + a, cy + a)], fill=WHITE, width=max(2, int(10 * s)))
            d.line([(mx - a, cy + a), (mx + a, cy - a)], fill=WHITE, width=max(2, int(10 * s)))


def draw_timer(img, left, acc):
    d = ImageDraw.Draw(img)
    cx, cy, r = W // 2, 1500, 95
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=(225, 220, 205), width=14)
    col = RED if left <= 3 else acc
    frac = clip(left / TIMER)
    if frac > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=col, width=14)
    d.text((cx, cy), str(int(math.ceil(left))), font=F(96), fill=col, anchor="mm")


def prepare(blocks):
    n_total = len(blocks)
    for n, b in enumerate(blocks, 1):
        q = b["q"]
        acc = ACCENTS[(n - 1) % len(ACCENTS)]
        b["assets"] = {
            "accent": acc,
            "bg": make_paper(acc, f"QUESTION {n} / {n_total}"),
            "qh": fit_hand(q["question"], [70, 62, 56, 50], 880, 5),
            "qs": fit_hand(q["question"], [56, 50, 44, 40], 880, 5),
            "oh": [fit_hand(o, [50, 44, 38], 600, 2) for o in q["options"]],
            "eh": fit_hand(q["explanation"], [56, 50, 44, 40], 800, 7),
            "ah": Hand(f"Answer: {LETTERS[q['answer']]}. {q['options'][q['answer']]}", 60, 860, GREEN),
        }


def draw_block(b, t):
    p, A, q = b["p"], b["assets"], b["q"]
    img = A["bg"].copy()
    d = ImageDraw.Draw(img)
    acc = A["accent"]
    timer_end = p["timer"][1]
    reveal0 = p["reveal"][0]

    if t < timer_end:
        qs, qe = p["q"]
        A["qh"].draw(img, W // 2, Q_Y, (t - qs) / (0.9 * (qe - qs)), center=True)
        for i in range(4):
            s, e = p["opts"][i]
            if t >= s:
                dx = int(320 * (1 - clip((t - s) / 0.25)) ** 2)
                draw_card(img, i, LETTERS[i], A["oh"][i], (t - s) / (0.9 * (e - s)), "neutral", None, acc, dx)
        if t >= p["prompt"][0]:
            left = TIMER if t < p["timer"][0] else timer_end - t
            draw_timer(img, left, acc)
    elif t < reveal0:
        A["qs"].draw(img, W // 2, Q_Y, 1, center=True)
        d.rounded_rectangle([90, 560, 990, 1330], radius=40, fill=WHITE, outline=acc, width=8)
        d.text((W // 2 - 60, 640), "DID YOU KNOW?", font=F(72), fill=acc, anchor="mm")
        d.ellipse([850, 600, 910, 660], fill=(255, 214, 80), outline=(200, 150, 20), width=4)
        d.rectangle([868, 660, 892, 682], fill=(120, 120, 130))
        for ang in range(-60, 61, 40):
            a = math.radians(ang - 90)
            d.line([(880 + 42 * math.cos(a), 630 + 42 * math.sin(a)),
                    (880 + 62 * math.cos(a), 630 + 62 * math.sin(a))], fill=(230, 170, 30), width=5)
        es, ee = p["expl"]
        A["eh"].draw(img, W // 2, 730, (t - es) / (0.92 * (ee - es)), center=True)
    else:
        A["qh"].draw(img, W // 2, Q_Y, 1, center=True)
        for i in range(4):
            if t >= p["reveal"][i]:
                st = "correct" if i == q["answer"] else "wrong"
                age = t - p["reveal"][i]
            else:
                st, age = "neutral", None
            draw_card(img, i, LETTERS[i], A["oh"][i], 1, st, age, acc)
        as_, ae = p["answer"]
        if t >= as_:
            A["ah"].draw(img, W // 2, 1370, (t - as_) / (0.9 * (ae - as_)), center=True)
    return img


def render(tl, blocks, audio_path, out_path):
    prepare(blocks)
    intro = {
        "bg": make_paper(ACCENTS[0]),
        "title": Hand("QUIZ TIME!", 160, 900, INK),
        "sub": Hand("5 Questions  |  10 Seconds Each", 62, 900, ACCENTS[1]),
    }
    outro = {
        "bg": make_paper(ACCENTS[1]),
        "l1": Hand("How many did you get right?", 90, 900, INK),
        "l2": Hand("Comment your score below!", 70, 900, ACCENTS[0]),
        "l3": Hand("New quizzes every day!", 64, 900, GREEN),
    }

    def frame_at(t):
        if t < tl["intro_end"]:
            img = intro["bg"].copy()
            d = ImageDraw.Draw(img)
            intro["title"].draw(img, W // 2, 520, t / 1.1, center=True)
            intro["sub"].draw(img, W // 2, 860, (t - 1.0) / 1.2, center=True)
            s = pop_scale((t - 0.3) / 0.6)
            d.text((W // 2, 1250), "?", font=F(max(10, int(420 * s))), fill=ACCENTS[0], anchor="mm")
            return img
        if t >= tl["outro_start"]:
            u = t - tl["outro_start"]
            img = outro["bg"].copy()
            d = ImageDraw.Draw(img)
            outro["l1"].draw(img, W // 2, 430, u / 1.5, center=True)
            outro["l2"].draw(img, W // 2, 760, (u - 1.5) / 1.2, center=True)
            if u > 2.0:
                s = pop_scale((u - 2.0) / 0.4) * (1 + 0.04 * math.sin(u * 6))
                bw, bh = 370 * s, 90 * s
                d.rounded_rectangle([W // 2 - bw, 1100 - bh, W // 2 + bw, 1100 + bh],
                                    radius=int(50 * s), fill=(230, 30, 30))
                d.text((W // 2, 1100), "SUBSCRIBE", font=F(max(10, int(100 * s))), fill=WHITE, anchor="mm")
            outro["l3"].draw(img, W // 2, 1320, (u - 3.0) / 1.2, center=True)
            return img
        for b in blocks:
            if t < b["p"]["end"]:
                return draw_block(b, t)
        return draw_block(blocks[-1], blocks[-1]["p"]["end"] - 0.01)

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", audio_path,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(tl["total"] * FPS)
    for f in range(n):
        proc.stdin.write(frame_at(f / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
