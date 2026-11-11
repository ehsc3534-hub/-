import os
import sys
import wave
import subprocess
import numpy as np

from config import SR, VOICE_MODEL, LENGTH_SCALE, OUT_DIR


def _read_wav(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(w.getnframes())
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


def _trim(x):
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.03 * SR))
    b = min(len(x), idx[-1] + int(0.12 * SR))
    return x[a:b]


def speak(text, name):
    os.makedirs(f"{OUT_DIR}/tts", exist_ok=True)
    path = f"{OUT_DIR}/tts/{name}.wav"
    ok = False
    if os.path.exists(VOICE_MODEL):
        try:
            subprocess.run(
                [sys.executable, "-m", "piper", "--model", VOICE_MODEL,
                 "--output_file", path, "--length_scale", str(LENGTH_SCALE)],
                input=text.encode("utf-8"), check=True, capture_output=True,
            )
            ok = True
        except Exception as e:
            print("piper failed, using espeak-ng:", e)
    if not ok:
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "170", "-w", path, text], check=True)
    x = _trim(_read_wav(path))
    peak = float(np.abs(x).max()) if len(x) else 1.0
    if peak > 0:
        x = x * (0.9 / peak)
    return x.astype(np.float32)
