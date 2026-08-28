#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
릴스용 로열티프리 배경음악 생성기 (numpy 합성).
사인 드론이 아니라 멜로디+베이스+드럼이 있는 경쾌한 신스 루프를 만든다.
100% 직접 합성이라 저작권 프리. 사용: python make_music.py <out.wav> <duration_sec>
"""
import sys
import wave
import numpy as np

SR = 44100


def _adsr(n, a=0.005, d=0.10, s=0.6, r=0.08):
    """플럭 느낌 엔벨로프 — 드론 방지(빠른 감쇠)."""
    env = np.ones(n)
    ai, di, ri = int(SR * a), int(SR * d), int(SR * r)
    ai = min(ai, n)
    env[:ai] = np.linspace(0, 1, ai)
    if di > 0 and ai + di < n:
        env[ai:ai + di] = np.linspace(1, s, di)
        env[ai + di:] = s
    if ri > 0 and ri < n:
        env[-ri:] *= np.linspace(1, 0, ri)
    # 전체적으로 살짝 지수 감쇠 → 통통 튀는 느낌
    t = np.linspace(0, 1, n)
    return env * np.exp(-1.6 * t)


def synth(freq, dur, vol=0.3, kind="saw"):
    n = int(SR * dur)
    if freq <= 0:
        return np.zeros(n)
    t = np.linspace(0, dur, n, False)
    if kind == "sine":
        w = np.sin(2 * np.pi * freq * t)
    elif kind == "tri":
        w = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:  # saw: 하모닉 몇 개 → 신스 느낌
        w = (np.sin(2 * np.pi * freq * t)
             + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
             + 0.3 * np.sin(2 * np.pi * 3 * freq * t)) / 1.8
    return w * _adsr(n) * vol


def kick(dur=0.18, vol=0.5):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, False)
    f = 120 * np.exp(-24 * t) + 45          # 피치 드롭
    w = np.sin(2 * np.pi * f * t)
    return w * np.exp(-9 * t) * vol


def hat(dur=0.05, vol=0.18):
    n = int(SR * dur)
    w = np.random.uniform(-1, 1, n)
    return w * np.exp(-40 * np.linspace(0, dur, n, False)) * vol


def place(buf, sig, at):
    i = int(SR * at)
    j = min(i + len(sig), len(buf))
    buf[i:j] += sig[:j - i]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0

    bpm = 112.0
    beat = 60.0 / bpm
    eighth = beat / 2
    total = int(SR * (dur + 0.5))
    buf = np.zeros(total)

    # 코드 진행: Am - F - C - G (각 2박) → 팝에서 가장 흔한 루프
    NOTE = {"A2": 110.00, "F2": 87.31, "C3": 130.81, "G2": 98.00,
            "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
            "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99}
    prog = [
        ("A2", ["A4", "C5", "E5", "C5"]),
        ("F2", ["A4", "C5", "F5", "C5"]),
        ("C3", ["G4", "C5", "E5", "G5"]),
        ("G2", ["G4", "B4", "D5", "B4"]),
    ]

    t = 0.0
    ci = 0
    while t < dur:
        bass_name, mel = prog[ci % len(prog)]
        # 베이스: 코드 루트 2박 유지(플럭)
        place(buf, synth(NOTE[bass_name], beat * 2 * 0.95, vol=0.32, kind="tri"), t)
        # 멜로디: 8분음표 4개
        for k, mn in enumerate(mel):
            place(buf, synth(NOTE[mn], eighth * 0.9, vol=0.26, kind="saw"), t + k * eighth)
        # 드럼: 킥은 매 박, 하이햇은 8분 오프비트
        for b in range(2):
            place(buf, kick(), t + b * beat)
            place(buf, hat(), t + b * beat + eighth)
        t += beat * 2
        ci += 1

    buf = buf[:int(SR * dur)]
    # 페이드 인/아웃 + 노멀라이즈
    fi, fo = int(SR * 0.15), int(SR * 0.8)
    buf[:fi] *= np.linspace(0, 1, fi)
    buf[-fo:] *= np.linspace(1, 0, fo)
    peak = np.max(np.abs(buf)) or 1.0
    buf = (buf / peak * 0.9 * 32767).astype(np.int16)

    with wave.open(out, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(buf.tobytes())
    print(f"🎵 음악 생성: {out} ({dur}s, {bpm:.0f}bpm, Am-F-C-G)")


if __name__ == "__main__":
    main()
