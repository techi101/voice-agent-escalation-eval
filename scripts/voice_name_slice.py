"""Optional small voice slice: name capture over a simulated phone line.

20 synthetic patient names, spoken by the two built-in Windows text-to-speech
voices (US English, "Microsoft David" and "Microsoft Zira"), degraded to
telephone conditions, then transcribed with faster-whisper "small" on CPU.

Conditions:
  phone        8 kHz, 300-3400 Hz band, 8-bit mu-law, background noise at 20 dB SNR
  speakerphone the same plus a simple room echo and noise at 10 dB SNR

Strategies:
  raw      plain transcription
  prompt   transcription with the practice's (synthetic) registered-name list as Whisper's initial_prompt
  fuzzy    "prompt" output, then the closest name on the list (rapidfuzz), accepted if score >= 80

LIMITS: TTS voices are not real people, not real accents and not impaired
speech. This only shows the pipeline and the size of the effect on clean
synthetic speech. No LLM calls. Windows only (uses System.Speech).
Usage: python scripts/voice_name_slice.py
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from rapidfuzz import fuzz, process
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "voice_names"
AUDIO = ROOT / "data" / "voice_names"

NAMES = ["Peter Holmes", "Siobhan Gallagher", "Agnieszka Wojcik", "Ionut Popescu", "Chinedu Okafor",
         "Oluwaseun Adeyemi", "Harpreet Kaur", "Gurpreet Sandhu", "Mohammed Rafiq", "Imran Qureshi",
         "Rahima Begum", "Sunita Sharma", "Krzysztof Nowak", "Andreea Ionescu", "Niamh O'Connor",
         "Gareth Llewellyn", "Ade Bankole", "Priya Raghunathan", "Zofia Kowalczyk", "Tomasz Wisniewski"]
# synthetic "registered patients" list: the 20 callers plus 40 distractors with similar sounds
DISTRACTORS = ["Peter Holme", "Pete Holmes", "Sharon Gallagher", "Agnes Wojcik", "Ion Popescu", "Chidi Okafor",
               "Olusegun Adeyemi", "Harjit Kaur", "Gurdeep Sandhu", "Mohammed Rafique", "Imran Qadri", "Rahim Begum",
               "Sunil Sharma", "Krystof Novak", "Andrea Ionescu", "Niamh Connor", "Gary Llewellyn", "Adey Bankole",
               "Priya Raghavan", "Zofia Kowalski", "Tomas Wisniewski", "Paul Holmes", "Sinead Gallagher",
               "Agata Wojcik", "Ionela Popescu", "Chukwuma Okafor", "Seun Adeyemi", "Manpreet Kaur", "Gurpal Sandhu",
               "Mohamed Rashid", "Irfan Qureshi", "Rehana Begum", "Sunita Verma", "Krzysztof Nowicki",
               "Andreea Ionita", "Nia O'Connor", "Gareth Lewis", "Ada Bankole", "Priya Raghunath", "Zofia Kowal"]
REGISTER = NAMES + DISTRACTORS
VOICES = ["Microsoft David Desktop", "Microsoft Zira Desktop"]


def tts(text: str, voice: str, path: Path) -> None:
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SelectVoice('{voice}'); $s.Rate = 0; "
        f"$s.SetOutputToWaveFile('{path}'); $s.Speak(\"{text}\"); $s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def mulaw(x: np.ndarray, mu: int = 255) -> np.ndarray:
    y = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
    y = np.round((y + 1) / 2 * mu) / mu * 2 - 1           # 8-bit quantisation
    return np.sign(y) * (1 / mu) * ((1 + mu) ** np.abs(y) - 1)


def degrade(x: np.ndarray, sr: int, condition: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
    x = resample_poly(x, 8000, sr)
    x = sosfilt(butter(4, [300, 3400], btype="band", fs=8000, output="sos"), x)
    if condition == "speakerphone":
        t = np.arange(int(0.25 * 8000)) / 8000
        ir = rng.standard_normal(len(t)) * np.exp(-t / 0.06)
        ir[0] = 1.0
        x = fftconvolve(x, ir)[: len(x)]
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
    snr_db = 20 if condition == "phone" else 10
    p = np.mean(x ** 2)
    x = x + rng.standard_normal(len(x)) * np.sqrt(p / 10 ** (snr_db / 10))
    x = np.clip(x, -1, 1)
    return mulaw(x).astype(np.float32)


def norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("'", "")).strip()


def extract_name(text: str) -> str:
    m = re.search(r"name is (.*)", text, flags=re.I)
    return (m.group(1) if m else text).strip(" .,!?")


def main():
    from faster_whisper import WhisperModel

    OUT.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    prompt = "Registered patients: " + ", ".join(REGISTER) + "."
    rows = []
    for i, name in enumerate(NAMES):
        voice = VOICES[i % 2]
        clean = AUDIO / f"{i:02d}_clean.wav"
        if not clean.exists():
            tts(f"Hello, my name is {name}.", voice, clean)
        x, sr = sf.read(clean)
        if x.ndim > 1:
            x = x.mean(axis=1)
        for condition in ("phone", "speakerphone"):
            y = degrade(x, sr, condition, seed=i)
            wav = AUDIO / f"{i:02d}_{condition}.wav"
            sf.write(wav, y, 8000)
            # faster-whisper resamples to 16 kHz internally
            raw = " ".join(s.text for s in model.transcribe(str(wav), language="en", beam_size=5)[0]).strip()
            pr = " ".join(s.text for s in model.transcribe(str(wav), language="en", beam_size=5, initial_prompt=prompt)[0]).strip()
            best, score, _ = process.extractOne(extract_name(pr), REGISTER, scorer=fuzz.WRatio)
            fz = best if score >= 80 else extract_name(pr)
            rows.append({"name": name, "voice": voice, "condition": condition,
                         "raw": raw, "raw_ok": norm(name) in norm(raw),
                         "prompt": pr, "prompt_ok": norm(name) in norm(pr),
                         "fuzzy": fz, "fuzzy_score": round(score, 1), "fuzzy_ok": norm(fz) == norm(name)})
            print(f"{name:22s} {condition:12s} raw={raw!r} | prompt={pr!r} | fuzzy={fz!r}", flush=True)
    with (OUT / "voice_names.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summarise()


def summarise():
    """Build the markdown table from voice_names.csv (no re-transcription needed)."""
    sys.path.insert(0, str(ROOT))
    from vaeval.metrics import fmt
    rows = list(csv.DictReader((OUT / "voice_names.csv").open(encoding="utf-8")))
    for r in rows:
        for k in ("raw_ok", "prompt_ok", "fuzzy_ok"):
            r[k] = r[k] == "True"
        # a confident match to a DIFFERENT registered patient is the dangerous error
        r["wrong_patient"] = r["fuzzy"] in REGISTER and not r["fuzzy_ok"]
    lines = ["| condition | raw ASR | + name-list prompt | + prompt and fuzzy match to list | matched to the WRONG registered patient |",
             "|---|---|---|---|---|"]
    for cond in ("phone", "speakerphone"):
        rs = [r for r in rows if r["condition"] == cond]
        lines.append(f"| {cond} | " + " | ".join(fmt(sum(r[k] for r in rs), len(rs)) for k in ("raw_ok", "prompt_ok", "fuzzy_ok", "wrong_patient")) + " |")
    md = ("# Voice slice: full-name capture (20 synthetic names x 2 line conditions)\n\n"
          "Exact full-name match, k/n = rate [Wilson 95%]. TTS voices (US English), not real speakers. "
          "The name list holds the 20 callers plus 40 similar-sounding distractors.\n\n" + "\n".join(lines) + "\n")
    (OUT / "voice_names.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    if "--summarise-only" in sys.argv:
        summarise()
    else:
        main()
