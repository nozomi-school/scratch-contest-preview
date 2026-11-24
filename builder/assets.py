"""SVG vector costume/backdrop and WAV sound effect generation with MD5 hashing."""

from __future__ import annotations

import hashlib
import io
import math
import random
import re
import struct
import wave
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple


DEFAULT_SAMPLE_RATE = 22050


@dataclass(frozen=True)
class Asset:
    """Represents a Scratch 3.0 costume or sound asset."""

    name: str
    data_format: str  # "svg" or "wav"
    data: bytes
    asset_id: str
    md5ext: str
    # Costume metadata
    rotation_center_x: Optional[float] = None
    rotation_center_y: Optional[float] = None
    bitmap_resolution: int = 1
    # Sound metadata
    rate: Optional[int] = None
    sample_count: Optional[int] = None

    def to_costume_dict(self) -> dict:
        if self.data_format != "svg":
            raise ValueError(f"Asset {self.name!r} is not an SVG costume")
        return {
            "name": self.name,
            "bitmapResolution": self.bitmap_resolution,
            "dataFormat": self.data_format,
            "assetId": self.asset_id,
            "md5ext": self.md5ext,
            "rotationCenterX": self.rotation_center_x,
            "rotationCenterY": self.rotation_center_y,
        }

    def to_sound_dict(self) -> dict:
        if self.data_format != "wav":
            raise ValueError(f"Asset {self.name!r} is not a WAV sound")
        return {
            "name": self.name,
            "assetId": self.asset_id,
            "dataFormat": self.data_format,
            "rate": self.rate,
            "sampleCount": self.sample_count,
            "md5ext": self.md5ext,
        }


def compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _extract_svg_size(svg_text: str) -> Tuple[float, float]:
    """Extract (width, height) from SVG viewBox or width/height attributes."""
    vb_match = re.search(
        r'viewBox\s*=\s*["\']\s*([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)\s*["\']',
        svg_text,
    )
    if vb_match:
        return float(vb_match.group(3)), float(vb_match.group(4))

    w_match = re.search(r'\bwidth\s*=\s*["\']\s*([\d.]+)', svg_text)
    h_match = re.search(r'\bheight\s*=\s*["\']\s*([\d.]+)', svg_text)
    if w_match and h_match:
        return float(w_match.group(1)), float(h_match.group(1))
    return 480.0, 360.0


def make_svg_costume(
    name: str,
    svg_text: str,
    rotation_center_x: Optional[float] = None,
    rotation_center_y: Optional[float] = None,
) -> Asset:
    """Create a vector SVG costume or backdrop asset with exact MD5 hash."""
    cleaned = svg_text.strip() + "\n"
    raw = cleaned.encode("utf-8")
    md5 = compute_md5(raw)
    width, height = _extract_svg_size(cleaned)
    cx = width / 2.0 if rotation_center_x is None else float(rotation_center_x)
    cy = height / 2.0 if rotation_center_y is None else float(rotation_center_y)
    return Asset(
        name=name,
        data_format="svg",
        data=raw,
        asset_id=md5,
        md5ext=f"{md5}.svg",
        rotation_center_x=cx,
        rotation_center_y=cy,
        bitmap_resolution=1,
    )


def make_wav_sound(
    name: str,
    samples: Sequence[float],
    rate: int = DEFAULT_SAMPLE_RATE,
) -> Asset:
    """Encode normalized [-1.0, 1.0] mono float samples into a 16-bit PCM WAV asset."""
    clamped = [max(-1.0, min(1.0, float(s))) for s in samples]
    pcm_int16 = [int(round(s * 32767.0)) for s in clamped]
    pcm_bytes = struct.pack(f"<{len(pcm_int16)}h", *pcm_int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)

    raw = buf.getvalue()
    md5 = compute_md5(raw)
    return Asset(
        name=name,
        data_format="wav",
        data=raw,
        asset_id=md5,
        md5ext=f"{md5}.wav",
        rate=rate,
        sample_count=len(pcm_int16),
    )


def _oscillator(phase: float, waveform: str) -> float:
    if waveform == "sine":
        return math.sin(phase)
    if waveform == "triangle":
        t = (phase / (2.0 * math.pi)) % 1.0
        return 4.0 * abs(t - 0.5) - 1.0
    if waveform == "square":
        return 1.0 if math.sin(phase) >= 0.0 else -1.0
    if waveform == "bell":
        return (
            0.70 * math.sin(phase)
            + 0.22 * math.sin(2.0 * phase)
            + 0.08 * math.sin(3.0 * phase)
        )
    raise ValueError(f"Unknown waveform: {waveform!r}")


def _render_tone(
    freq_hz: float,
    duration_sec: float,
    rate: int = DEFAULT_SAMPLE_RATE,
    waveform: str = "sine",
    volume: float = 0.55,
    attack_sec: float = 0.012,
    decay_exp: float = 2.5,
) -> list[float]:
    n = max(1, int(round(duration_sec * rate)))
    attack_n = max(1, int(round(attack_sec * rate)))
    release_n = max(1, int(round(min(0.025, duration_sec * 0.25) * rate)))
    out: list[float] = []
    for i in range(n):
        t = i / rate
        if freq_hz <= 0:
            out.append(0.0)
            continue
        env = math.exp(-decay_exp * (t / max(duration_sec, 1e-6)))
        if i < attack_n:
            env *= i / attack_n
        if i > n - release_n:
            env *= max(0.0, (n - i) / release_n)
        phase = 2.0 * math.pi * freq_hz * t
        out.append(volume * env * _oscillator(phase, waveform))
    return out


def synth_melody(
    name: str,
    notes: Iterable[Tuple[float, float, float]],
    rate: int = DEFAULT_SAMPLE_RATE,
    waveform: str = "bell",
    volume: float = 0.55,
    decay_exp: float = 2.2,
) -> Asset:
    """Synthesize a sequence of (freq_hz, duration_sec, gap_sec) notes into a WAV Asset."""
    samples: list[float] = []
    for freq, dur, gap in notes:
        samples.extend(
            _render_tone(
                freq_hz=freq,
                duration_sec=dur,
                rate=rate,
                waveform=waveform,
                volume=volume,
                decay_exp=decay_exp,
            )
        )
        if gap > 0:
            samples.extend([0.0] * int(round(gap * rate)))
    return make_wav_sound(name, samples, rate=rate)


def synth_beep(
    name: str = "ビープおん",
    freq: float = 880.0,
    duration: float = 0.16,
    rate: int = DEFAULT_SAMPLE_RATE,
) -> Asset:
    """Short clean beep sound."""
    samples = _render_tone(
        freq_hz=freq,
        duration_sec=duration,
        rate=rate,
        waveform="sine",
        volume=0.52,
        decay_exp=1.2,
    )
    return make_wav_sound(name, samples, rate=rate)


def synth_note(
    name: str,
    freq: float,
    duration: float = 0.26,
    waveform: str = "bell",
    rate: int = DEFAULT_SAMPLE_RATE,
) -> Asset:
    """Single musical note sound."""
    samples = _render_tone(
        freq_hz=freq,
        duration_sec=duration,
        rate=rate,
        waveform=waveform,
        volume=0.58,
        decay_exp=2.5,
    )
    return make_wav_sound(name, samples, rate=rate)


def synth_chime_bath(name: str = "かんりょうおん") -> Asset:
    """Pleasant 4-note bath-ready chime (F4 -> A4 -> C5 -> F5)."""
    notes = [
        (349.23, 0.22, 0.03),
        (440.00, 0.22, 0.03),
        (523.25, 0.22, 0.03),
        (698.46, 0.52, 0.02),
    ]
    return synth_melody(name, notes, waveform="bell", volume=0.6, decay_exp=2.4)


def synth_chime_success(name: str = "せいこうおん") -> Asset:
    """Bright ascending success chime (C5 -> E5 -> G5 -> C6)."""
    notes = [
        (523.25, 0.12, 0.02),
        (659.25, 0.12, 0.02),
        (783.99, 0.14, 0.02),
        (1046.50, 0.42, 0.02),
    ]
    return synth_melody(name, notes, waveform="bell", volume=0.6, decay_exp=2.0)


def synth_buzzer_fail(name: str = "しっぱいおん") -> Asset:
    """Clear low descending buzzer sound (G3 -> Eb3)."""
    notes = [
        (196.00, 0.18, 0.03),
        (155.56, 0.36, 0.02),
    ]
    return synth_melody(name, notes, waveform="triangle", volume=0.6, decay_exp=1.2)


def synth_pop(name: str = "ポンおん", rate: int = DEFAULT_SAMPLE_RATE) -> Asset:
    """Short popping / pickup sound effect."""
    rng = random.Random(42)
    duration = 0.12
    n = int(round(duration * rate))
    samples: list[float] = []
    for i in range(n):
        t = i / rate
        freq = 520.0 * math.exp(-18.0 * t) + 120.0
        env = math.exp(-26.0 * t)
        tone = math.sin(2.0 * math.pi * freq * t)
        noise = (rng.random() * 2.0 - 1.0) * math.exp(-60.0 * t) * 0.25
        samples.append(0.65 * env * (tone + noise))
    return make_wav_sound(name, samples, rate=rate)


def synth_tick_high(name: str = "たかいおん", rate: int = DEFAULT_SAMPLE_RATE) -> Asset:
    """Crisp high accent metronome click (beat 1)."""
    samples = _render_tone(
        freq_hz=1320.0,
        duration_sec=0.09,
        rate=rate,
        waveform="bell",
        volume=0.68,
        attack_sec=0.003,
        decay_exp=5.5,
    )
    return make_wav_sound(name, samples, rate=rate)


def synth_tick_low(name: str = "ひくいおん", rate: int = DEFAULT_SAMPLE_RATE) -> Asset:
    """Crisp low regular metronome click (beats 2-4)."""
    samples = _render_tone(
        freq_hz=660.0,
        duration_sec=0.08,
        rate=rate,
        waveform="triangle",
        volume=0.58,
        attack_sec=0.003,
        decay_exp=6.0,
    )
    return make_wav_sound(name, samples, rate=rate)


def synth_warning_alarm(name: str = "けいこくおん") -> Asset:
    """Urgent 2-pulse warning beep for red-light violation."""
    notes = [
        (880.0, 0.14, 0.05),
        (660.0, 0.14, 0.05),
        (880.0, 0.18, 0.02),
    ]
    return synth_melody(name, notes, waveform="square", volume=0.35, decay_exp=0.6)


def synth_door_chime(name: str = "チャイムおん") -> Asset:
    """Classic cheerful 2-tone store entrance chime (Pin-Pon!)."""
    notes = [
        (659.25, 0.24, 0.04),
        (523.25, 0.44, 0.02),
    ]
    return synth_melody(name, notes, waveform="bell", volume=0.62, decay_exp=2.6)


def synth_tick_tock(name: str = "チクタクおん", rate: int = DEFAULT_SAMPLE_RATE) -> Asset:
    """Sharp clock-tick sound for bomb fuse countdown."""
    samples = _render_tone(
        freq_hz=1046.5,
        duration_sec=0.06,
        rate=rate,
        waveform="square",
        volume=0.32,
        attack_sec=0.002,
        decay_exp=8.0,
    )
    return make_wav_sound(name, samples, rate=rate)


def synth_explosion(name: str = "ばくはつおん", rate: int = DEFAULT_SAMPLE_RATE) -> Asset:
    """Low rumble + white-noise burst for bomb explosion or fireworks boom."""
    rng = random.Random(101)
    duration = 0.65
    n = int(round(duration * rate))
    samples: list[float] = []
    lp = 0.0
    for i in range(n):
        t = i / rate
        noise = rng.random() * 2.0 - 1.0
        lp = 0.82 * lp + 0.18 * noise
        sub = math.sin(2.0 * math.pi * (85.0 * math.exp(-3.5 * t) + 32.0) * t)
        env = math.exp(-5.0 * t)
        if i < 200:
            env *= i / 200.0
        samples.append(0.85 * env * (0.65 * lp + 0.35 * sub))
    return make_wav_sound(name, samples, rate=rate)


def synth_launch_whistle(
    name: str = "うちあげおん", rate: int = DEFAULT_SAMPLE_RATE
) -> Asset:
    """Ascending firework launch whistle."""
    duration = 0.45
    n = int(round(duration * rate))
    samples: list[float] = []
    phase = 0.0
    for i in range(n):
        t = i / rate
        progress = t / duration
        freq = 360.0 + 1150.0 * (progress ** 1.6)
        phase += 2.0 * math.pi * freq / rate
        env = math.sin(math.pi * progress) ** 0.7
        samples.append(0.42 * env * math.sin(phase))
    return make_wav_sound(name, samples, rate=rate)


def synth_inflate_pump(
    name: str = "くうきおん", rate: int = DEFAULT_SAMPLE_RATE
) -> Asset:
    """Short air-pump puff sound for balloon inflation."""
    rng = random.Random(77)
    duration = 0.16
    n = int(round(duration * rate))
    samples: list[float] = []
    phase = 0.0
    prev = 0.0
    for i in range(n):
        t = i / rate
        p = t / duration
        freq = 220.0 + 360.0 * p
        phase += 2.0 * math.pi * freq / rate
        noise = rng.random() * 2.0 - 1.0
        hp = noise - 0.65 * prev
        prev = noise
        env = math.sin(math.pi * p)
        samples.append(0.45 * env * (0.55 * math.sin(phase) + 0.45 * hp))
    return make_wav_sound(name, samples, rate=rate)


def synth_balloon_pop(
    name: str = "はれつおん", rate: int = DEFAULT_SAMPLE_RATE
) -> Asset:
    """Crisp sharp snap/burst sound for balloon pop."""
    rng = random.Random(303)
    duration = 0.22
    n = int(round(duration * rate))
    samples: list[float] = []
    for i in range(n):
        t = i / rate
        noise = rng.random() * 2.0 - 1.0
        snap = math.sin(2.0 * math.pi * (420.0 * math.exp(-32.0 * t) + 70.0) * t)
        env = math.exp(-20.0 * t)
        samples.append(0.85 * env * (0.72 * noise + 0.28 * snap))
    return make_wav_sound(name, samples, rate=rate)


def synth_pickup_coin(name: str = "ぽんおん") -> Asset:
    """Cute 2-note pickup chime (G5 -> C6) for dust collection."""
    notes = [
        (783.99, 0.07, 0.01),
        (1046.50, 0.12, 0.01),
    ]
    return synth_melody(name, notes, waveform="sine", volume=0.5, decay_exp=2.5)
