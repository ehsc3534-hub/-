import glob
import math
import os
import subprocess
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from config import W, H, FPS, TIMER, SUB_APPEAR, SUB_CLICK

PAPER = (250, 244, 228)
INK = (35, 38, 70)
LINE = (190, 210, 235)
MARGIN = (238, 150, 150)
GREEN = (34, 160, 90)
RED = (215, 55, 65)
WHITE = (255, 255, 255)
SKIN = (246, 205, 165)
SKIN_D = (205, 150, 110)
SLEEVE = (62, 72, 140)
ACCENTS = [(255, 112, 67), (66, 133, 244), (156, 39, 176), (0, 150, 136), (233, 160, 0)]

OPT_Y0, OPT_H, OPT_GAP, Q_Y = 660, 140, 26, 185
LETTERS = "ABCD"


def clip(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, k):
    return a + (b - a) * k


def lerp_col(c1, c2, k):
    return tuple(int(lerp(c1[i], c2[i], k)) for i in range(3))


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


# ---------------------------------------------------------------- hands
def _thick(d, a, b, w, fill):
    d.line([a, b], fill=fill, width=int(w))
    r = w / 2
    for p in (a, b):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def draw_hand(img, x, y, color=INK):
    """Cartoon hand holding a pen. (x, y) = pen tip."""
    d = ImageDraw.Draw(img)
    S = (x + 150, y - 170)
    E = (x + 340, y - 400)
    M = (lerp(S[0], E[0], 0.45), lerp(S[1], E[1], 0.45))
    _thick(d, S, E, 112, SKIN)
    _thick(d, M, E, 122, SLEEVE)
    _thick(d, (x, y), (x + 125, y - 146), 15, (55, 55, 65))
    _thick(d, (x, y), (x + 22, y - 26), 15, color)
    d.ellipse([S[0] - 60, S[1] - 56, S[0] + 60, S[1] + 56], fill=SKIN, outline=SKIN_D, width=4)
    _thick(d, (x + 135, y - 195), (x + 88, y - 118), 36, SKIN_D)
    _thick(d, (x + 135, y - 195), (x + 88, y - 118), 29, SKIN)
    _thick(d, (x + 120, y - 150), (x + 62, y - 84), 40, SKIN_D)
    _thick(d, (x + 120, y - 150), (x + 62, y - 84), 33, SKIN)


def draw_pointer(img, x, y, s=1.0):
    """Cartoon hand with pointing finger. (x, y) = fingertip."""
    d = ImageDraw.Draw(img)

    def P(dx, dy):
        return (x + dx * s, y + dy * s)

    _thick(d, P(60, 200), P(150, 470), 120 * s, SKIN)
    _thick(d, P(105, 335), P(150, 470), 130 * s, SLEEVE)
    c = P(50, 150)
    r = 66 * s
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=SKIN, outline=SKIN_D, width=4)
    for dx, dy in ((30, 118), (72, 124), (106, 144)):
        q = P(dx, dy)
        rr = 27 * s
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=SKIN, outline=SKIN_D, width=3)
    _thick(d, P(-8, 165), P(24, 118), 32 * s, SKIN_D)
    _thick(d, P(-8, 165), P(24, 118), 26 * s, SKIN)
    _thick(d, P(10, 115), P(0, 17), 42 * s, SKIN_D)
    _thick(d, P(10, 115), P(0, 17), 35 * s, SKIN)


def finish(img, tips):
    if tips:
        x, y, c = tips[-1]
        draw_hand(img, x, y, c)


class Hand:
    """Handwriting-style progressive text reveal. Returns pen tip via `tips`."""

    def __init__(self, text, size, maxw, color=INK, gap=1.28):
        self.font = F(size)
        self.color = color
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

    def draw(self, img, x, y, p, center=False, tips=None):
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
            if tips is not None and k < n and p < 1:
                tips.append((x0 + 6 + wpx, yy + self.lh * 0.78 + 3 * math.sin(p * 400), INK))
            used += n


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
        d.text((W // 2, 75), label, font=F(64), fill=WHITE, anchor="mm")
    return im


# ---------------------------------------------------------------- marks
def stroke(d, pts, p, color, width):
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    target = clip(p) * sum(lens)
    tip = pts[0]
    r = width / 2
    for (a, b), L in zip(segs, lens):
        if target <= 0:
            break
        f = min(1.0, target / L) if L else 1.0
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=color, width=width)
        d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=color)
        d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=color)
        tip = e
        target -= L
    return tip


def draw_mark(img, mx, cy, correct, age, tips):
    """Big badge + hand-drawn tick (correct) or cross (wrong)."""
    d = ImageDraw.Draw(img)
    col = GREEN if correct else RED
    s = pop_scale(age / 0.25)
    r = max(1, int(56 * s))
    d.ellipse([mx - r, cy - r, mx + r, cy + r], fill=WHITE, outline=col, width=8)
    p = clip((age - 0.2) / 0.4)
    if p <= 0:
        return
    if correct:
        pts = [(mx - 28, cy + 2), (mx - 9, cy + 24), (mx + 30, cy - 24)]
        tip = stroke(d, pts, p, col, 17)
    else:
        a = 25
        tip = stroke(d, [(mx - a, cy - a), (mx + a, cy + a)], clip(p * 2), col, 17)
        if p > 0.5:
            tip = stroke(d, [(mx - a, cy + a), (mx + a, cy - a)], clip(p * 2 - 1), col, 17)
    if tips is not None and age < 0.75:
        tips.append((tip[0], tip[1], col))


def draw_card(img, i, letter, hand, tprog, state, age, accent, dx=0, tips=None):
    d = ImageDraw.Draw(img)
    y = OPT_Y0 + i * (OPT_H + OPT_GAP)
    grow = 0
    if age is not None and state == "correct":
        grow = int(14 * math.sin(clip(age / 0.5) * math.pi))
    if age is not None and state == "wrong":
        dx += int(24 * math.sin(age * 55) * max(0.0, 1 - age / 0.5))
    x0, x1 = 130 + dx - grow, 990 + dx + grow
    top, bot = y - grow, y + OPT_H + grow
    cy = y + OPT_H // 2
    fill, outline, wd = WHITE, accent, 6
    if state == "correct":
        fill, outline, wd = (214, 247, 226), GREEN, 12
    elif state == "wrong":
        fill, outline, wd = (252, 222, 225), RED, 12
    if age is not None and state != "neutral" and age < 0.5:
        k = age / 0.5
        ring = int(6 + 18 * k)
        rc = lerp_col(outline, PAPER, k)
        d.rounded_rectangle([x0 - ring, top - ring, x1 + ring, bot + ring],
                            radius=32 + ring, outline=rc, width=8)
    d.rounded_rectangle([x0, top, x1, bot], radius=32, fill=fill, outline=outline, width=wd)
    d.ellipse([x0 + 28, cy - 42, x0 + 112, cy + 42], fill=outline)
    d.text((x0 + 70, cy), letter, font=F(60), fill=WHITE, anchor="mm")
    hand.draw(img, x0 + 150, cy - hand.height // 2 - 4, tprog, tips=tips)
    if state in ("correct", "wrong") and age is not None:
        draw_mark(img, x1 - 62, cy, state == "correct", age, tips)


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
        cat = q.get("category", q.get("topic", "")).upper()
        b["assets"] = {
            "accent": acc,
            "bg": make_paper(acc, f"Q{n}/{n_total} - {cat}"),
            "qh": fit_hand(q["question"], [70, 62, 56, 50], 880, 5),
            "qs": fit_hand(q["question"], [56, 50, 44, 40], 880, 5),
            "oh": [fit_hand(o, [50, 44, 38], 560, 2) for o in q["options"]],
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
    tips = []

    if t < timer_end:
        qs, qe = p["q"]
        A["qh"].draw(img, W // 2, Q_Y, (t - qs) / (0.9 * (qe - qs)), center=True, tips=tips)
        for i in range(4):
            s, e = p["opts"][i]
            if t >= s:
                dx = int(320 * (1 - clip((t - s) / 0.25)) ** 2)
                draw_card(img, i, LETTERS[i], A["oh"][i], (t - s) / (0.9 * (e - s)),
                          "neutral", None, acc, dx, tips)
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
        A["eh"].draw(img, W // 2, 730, (t - es) / (0.92 * (ee - es)), center=True, tips=tips)
    else:
        A["qh"].draw(img, W // 2, Q_Y, 1, center=True)
        for i in range(4):
            if t >= p["reveal"][i]:
                st = "correct" if i == q["answer"] else "wrong"
                age = t - p["reveal"][i]
            else:
                st, age = "neutral", None
            draw_card(img, i, LETTERS[i], A["oh"][i], 1, st, age, acc, 0, tips)
        as_, ae = p["answer"]
        if t >= as_:
            A["ah"].draw(img, W // 2, 1370, (t - as_) / (0.9 * (ae - as_)), center=True, tips=tips)
    finish(img, tips)
    return img


# ---------------------------------------------------------------- bell
def _bell(angle):
    lay = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    gold, edge = (255, 205, 45), (200, 140, 20)
    d.ellipse([42, 18, 128, 104], fill=gold, outline=edge, width=4)
    d.polygon([(42, 62), (128, 62), (150, 126), (20, 126)], fill=gold, outline=edge)
    d.rectangle([20, 118, 150, 130], fill=gold, outline=edge)
    d.ellipse([72, 128, 98, 154], fill=edge)
    d.ellipse([78, 4, 92, 20], fill=edge)
    return lay.rotate(angle, resample=Image.BICUBIC, center=(85, 14))


def render(tl, blocks, audio_path, out_path):
    prepare(blocks)
    intro = {
        "bg": make_paper(ACCENTS[0], "CHALLENGE!"),
        "l1": Hand("OF PEOPLE GET 3 OF THESE 5 QUESTIONS WRONG!", 84, 900, INK),
        "l2": Hand("Can YOU beat it?", 100, 900, GREEN),
    }
    outro = {
        "bg": make_paper(ACCENTS[1], "THANKS FOR PLAYING!"),
        "l1": Hand("How many did you get right?", 90, 900, INK),
        "l2": Hand("Comment your score below!", 72, 900, ACCENTS[0]),
        "l3": Hand("New quizzes every day!", 66, 900, GREEN),
    }

    def intro_frame(t):
        img = intro["bg"].copy()
        d = ImageDraw.Draw(img)
        tips = []
        s = pop_scale(t / 0.35)
        d.text((W // 2, 430), "90%", font=F(max(10, int(360 * s))), fill=RED, anchor="mm")
        intro["l1"].draw(img, W // 2, 640, (t - 0.3) / 1.7, center=True, tips=tips)
        intro["l2"].draw(img, W // 2, 1180, (t - 2.2) / 1.0, center=True, tips=tips)
        if t > 3.2:
            s2 = pop_scale((t - 3.2) / 0.5) * (1 + 0.05 * math.sin(t * 8))
            d.text((W // 2, 1550), "?", font=F(max(10, int(380 * s2))), fill=ACCENTS[0], anchor="mm")
        finish(img, tips)
        return img

    def outro_frame(t):
        u = t - tl["outro_start"]
        img = outro["bg"].copy()
        d = ImageDraw.Draw(img)
        tips = []
        outro["l1"].draw(img, W // 2, 330, u / 1.4, center=True, tips=tips)
        outro["l2"].draw(img, W // 2, 640, (u - 1.4) / 1.0, center=True, tips=tips)
        cy = 1100
        tx, ty = W // 2 + 130, cy + 20
        clicked = u >= SUB_CLICK
        c = u - SUB_CLICK

        if u >= SUB_APPEAR:
            s = pop_scale((u - SUB_APPEAR) / 0.5)
            if not clicked:
                s *= 1 + 0.035 * math.sin(u * 9)
            else:
                s *= 1 - 0.08 * math.sin(clip(c / 0.25) * math.pi)
            bw, bh = 380 * s, 95 * s
            col = (230, 30, 30) if not clicked else (95, 95, 108)
            d.rounded_rectangle([W // 2 - bw, cy - bh, W // 2 + bw, cy + bh],
                                radius=int(55 * s), fill=col)
            label = "SUBSCRIBE" if not clicked else "SUBSCRIBED"
            d.text((W // 2, cy), label, font=F(max(10, int(88 * s))), fill=WHITE, anchor="mm")
            if clicked:
                ang = 28 * math.sin(c * 14) * math.exp(-c * 1.3)
                bell = _bell(ang)
                img.paste(bell, (W // 2 + 380 - 20, cy - 85), bell)
                if c < 0.6:
                    for k in range(14):
                        a = k * (2 * math.pi / 14)
                        r1, r2 = 60 + 260 * c, 95 + 300 * c
                        d.line([(tx + r1 * math.cos(a), ty + r1 * math.sin(a)),
                                (tx + r2 * math.cos(a), ty + r2 * math.sin(a))],
                               fill=ACCENTS[k % 5], width=9)

        # pointing hand: moves in, taps, moves away
        t0 = SUB_CLICK - 1.0
        if u >= t0 and u < SUB_CLICK + 1.2:
            if u < SUB_CLICK:
                k = 1 - (1 - clip((u - t0) / 1.0)) ** 3
                px, py = lerp(W - 60, tx, k), lerp(1600, ty, k)
            else:
                kk = clip((u - SUB_CLICK - 0.5) / 0.7)
                px, py = tx + 420 * kk, ty + 520 * kk
            sc = 1.0
            if SUB_CLICK - 0.12 <= u < SUB_CLICK + 0.2:
                py += 14
                sc = 0.95
            draw_pointer(img, px, py, sc)

        if u >= SUB_CLICK + 0.3:
            outro["l3"].draw(img, W // 2, 1400, (u - SUB_CLICK - 0.3) / 1.0, center=True, tips=tips)
        finish(img, tips)
        return img

    def frame_at(t):
        if t < tl["intro_end"]:
            return intro_frame(t)
        if t >= tl["outro_start"]:
            return outro_frame(t)
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
